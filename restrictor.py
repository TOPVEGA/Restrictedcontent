from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto, InputMediaVideo
from pyrogram.errors import FloodWait
from pyromod import listen
import os
import re
import time
import asyncio
import logging
from urllib.parse import urlparse

API_ID = int(os.environ.get("API_ID", 1846213))
API_HASH = os.environ.get("API_HASH", "c545c613b78f18a30744970910124d53")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DEVELOPER_ID = int(os.environ.get("DEVELOPER_ID", 481322119))

DOWNLOAD_DIR = "downloads"
MAX_CONCURRENT_DOWNLOADS = 3
PROGRESS_UPDATE_INTERVAL = 2.0

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

logger = logging.getLogger("downloader_bot")
logger.setLevel(logging.INFO)
_formatter = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%Y-%m-%d %H:%M:%S")

_file_handler = logging.FileHandler("bot.log", encoding="utf-8")
_file_handler.setFormatter(_formatter)

_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_formatter)

if not logger.handlers:
    logger.addHandler(_file_handler)
    logger.addHandler(_console_handler)

app = Client(
    "downloader",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=4,
)

_download_semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

LINK_PATTERNS = [
    re.compile(r"^(?:https?://)?t\.me/(?:c/)?([A-Za-z0-9_]+)/(\d+)(?:/.*)?(?:\?.*)?$"),
    re.compile(r"^(?:https?://)?t\.me/([A-Za-z0-9_]+)/(\d+)\?single$"),
    re.compile(r"^tg://resolve\?domain=([A-Za-z0-9_]+)&post=(\d+)(?:&.*)?$"),
]


def parse_telegram_link(link: str):
    link = link.strip()
    parsed = urlparse(link if link.startswith("http") or link.startswith("tg://") else f"https://{link}")

    for pattern in LINK_PATTERNS:
        m = pattern.match(link)
        if m:
            chat_id = m.group(1)
            msg_id = int(m.group(2))
            if msg_id <= 0:
                return None
            return chat_id, msg_id

    return None


async def forward_to_developer(client: Client, message: Message):
    try:
        text = message.text or message.caption or "(بدون نص)"
        await client.send_message(
            DEVELOPER_ID,
            f"رسالة جديدة من مستخدم:\n\n"
            f"اسم المستخدم: {message.from_user.mention}\n"
            f"آيدي المستخدم: {message.from_user.id}\n"
            f"المحتوى:\n{text}"
        )
    except Exception as e:
        logger.warning("فشل في إرسال الرسالة للمطور: %s", e)


class ProgressTracker:
    def __init__(self, message: Message, total_files: int):
        self.message = message
        self.total_files = total_files
        self.progress = {}
        self._last_edit = 0.0
        self._lock = asyncio.Lock()

    async def update(self, idx: int, current: int, total: int):
        if total == 0:
            return
        async with self._lock:
            self.progress[idx] = current * 100 / total
            now = time.time()
            if now - self._last_edit < PROGRESS_UPDATE_INTERVAL:
                return
            self._last_edit = now
            await self._render()

    async def _render(self):
        lines = ["جاري التحميل:"]
        for i in range(1, self.total_files + 1):
            pct = self.progress.get(i, 0)
            filled = int(pct // 10)
            bar = "█" * filled + "░" * (10 - filled)
            lines.append(f"ملف {i}: [{bar}] {pct:.1f}%")
        try:
            await self.message.edit_text("\n".join(lines))
        except Exception:
            pass


def _guess_extension(message: Message) -> tuple:
    if message.photo:
        return "photo", ".jpg"
    if message.video:
        return "video", ".mp4"
    if message.animation:
        return "animation", ".mp4"
    if message.audio:
        return "audio", ".mp3"
    if message.voice:
        return "voice", ".ogg"
    if message.sticker:
        return "sticker", ".webp"
    if message.document:
        name = message.document.file_name or "file.bin"
        ext = "." + name.rsplit(".", 1)[-1] if "." in name else ".bin"
        return "document", ext
    return "unknown", ".bin"


async def download_one(msg: Message, idx: int, tracker: ProgressTracker):
    try:
        ftype, ext = _guess_extension(msg)
        if ftype == "unknown":
            if msg.text or msg.caption:
                content = msg.text or msg.caption
                path = f"{DOWNLOAD_DIR}/{msg.chat.id}_{msg.id}_text.txt"
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                tracker.progress[idx] = 100
                await tracker._render()
                return {"path": path, "type": "text", "caption": content[:100]}
            return None

        file_name = f"{DOWNLOAD_DIR}/{msg.chat.id}_{msg.id}{ext}"

        async def _progress(current, total):
            await tracker.update(idx, current, total)

        async with _download_semaphore:
            path = await app.download_media(msg, file_name=file_name, progress=_progress)

        caption = msg.caption or {
            "photo": "صورة", "video": "فيديو", "animation": "متحرك",
            "audio": (msg.audio.title if msg.audio else "صوت"),
            "voice": "رسالة صوتية", "sticker": "ملصق",
            "document": (msg.document.file_name if msg.document else "مستند"),
        }.get(ftype, ftype)

        return {"path": path, "type": ftype, "caption": caption}

    except FloodWait as e:
        logger.warning("FloodWait أثناء التحميل: انتظار %s ثانية", e.value)
        await asyncio.sleep(e.value)
        return await download_one(msg, idx, tracker)
    except Exception as e:
        logger.exception("فشل تنزيل ملف %s: %s", idx, e)
        return None


async def download_all_parallel(messages, tracker: ProgressTracker):
    tasks = [download_one(m, i + 1, tracker) for i, m in enumerate(messages)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    clean = []
    for r in results:
        if isinstance(r, dict):
            clean.append(r)
        elif isinstance(r, Exception):
            logger.warning("استثناء أثناء التحميل المتوازي: %s", r)
    return clean


def _build_media_group(files, caption: str):
    group, others = [], []
    for f in files:
        p = f["path"]
        if f["type"] == "photo":
            group.append(InputMediaPhoto(media=p, caption=caption if not group else ""))
        elif f["type"] in ("video", "animation"):
            group.append(InputMediaVideo(media=p, caption=caption if not group else ""))
        else:
            others.append(f)
    return group, others


async def send_results(message: Message, files, chat_title: str):
    if not files:
        return

    texts = [f for f in files if f["type"] == "text"]
    media = [f for f in files if f["type"] != "text"]

    for t in texts:
        try:
            with open(t["path"], "r", encoding="utf-8") as fh:
                content = fh.read()
            await message.reply_text(f"المحتوى النصي:\n\n{content}")
        except Exception as e:
            logger.warning("فشل إرسال النص: %s", e)

    if media:
        base_caption = f"تم سحب المحتوى من: {chat_title}"
        group_items, others = _build_media_group(media, base_caption)

        if group_items:
            try:
                if len(group_items) == 1:
                    item = group_items[0]
                    if isinstance(item, InputMediaPhoto):
                        await message.reply_photo(photo=item.media, caption=base_caption)
                    else:
                        await message.reply_video(video=item.media, caption=base_caption)
                else:
                    for i in range(0, len(group_items), 10):
                        await message.reply_media_group(media=group_items[i:i + 10])
                logger.info("تم إرسال album يحتوي %d عنصر", len(group_items))
            except Exception as e:
                logger.exception("فشل إرسال media group، سأرسلها منفردة: %s", e)
                others.extend([{"path": g.media, "type": "photo", "caption": base_caption}
                               for g in group_items])

        for f in others:
            p = f["path"]
            try:
                if f["type"] == "photo":
                    await message.reply_photo(photo=p, caption=f.get("caption", ""))
                elif f["type"] in ("video", "animation"):
                    await message.reply_video(video=p, caption=f.get("caption", ""))
                elif f["type"] == "sticker":
                    await message.reply_sticker(sticker=p)
                else:
                    await message.reply_document(document=p, caption=f.get("caption", ""))
            except Exception as e:
                logger.warning("فشل إرسال %s: %s", p, e)


@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        "مرحبًا! أنا بوت سحب المحتوى المقيد.\n"
        "أرسل لي رابط الرسالة مباشرة وسأحاول سحب محتواها.\n\n"
        "الصيغ المدعومة:\n"
        "https://t.me/username/123\n"
        "https://t.me/c/123456789/123\n"
        "https://t.me/username/123?single\n"
        "tg://resolve?domain=username&post=123\n\n"
        "تم برمجتي بواسطة : @TopVeGa\n"
        "لا تنسي حقوق النشر لـVEGA©"
    )
    await forward_to_developer(client, message)


@app.on_message(filters.text & ~filters.command(["start"]))
async def handle_links(client, message: Message):
    try:
        link = message.text.strip()
        parsed = parse_telegram_link(link)

        if not parsed:
            await forward_to_developer(client, message)
            return

        chat_identifier, msg_id = parsed
        logger.info("طلب من %s: %s chat=%s msg=%s",
                    message.from_user.id, link, chat_identifier, msg_id)

        await message.reply_text("جاري معالجة الرابط...")

        if chat_identifier.isdigit():
            chat_id = int(f"-100{chat_identifier}")
        else:
            chat_id = chat_identifier if chat_identifier.startswith("@") else f"@{chat_identifier}"

        try:
            topkim_msg = await app.get_messages(chat_id, msg_id)
        except Exception as e:
            logger.warning("get_messages فشل: %s", e)
            await message.reply_text(f"لا يمكن العثور على الرسالة.\nالخطأ: {e}")
            return

        if not topkim_msg or topkim_msg.empty:
            await message.reply_text("الرسالة غير موجودة أو محذوفة.")
            return

        if topkim_msg.media_group_id:
            try:
                messages_to_download = await app.get_media_group(chat_id, msg_id)
            except Exception as e:
                logger.warning("get_media_group فشل: %s", e)
                await message.reply_text(f"فشل جلب مجموعة الوسائط: {e}")
                return
        else:
            messages_to_download = [topkim_msg]

        progress_msg = await message.reply_text("جاري التحميل...")
        tracker = ProgressTracker(progress_msg, len(messages_to_download))

        all_files = await download_all_parallel(messages_to_download, tracker)

        try:
            await progress_msg.delete()
        except Exception:
            pass

        if not all_files:
            await message.reply_text("لم يُعثر على محتوى قابل للتنزيل.")
            return

        chat_title = getattr(topkim_msg.chat, "title", None) or "غير معروف"
        await send_results(message, all_files, chat_title)

        for f in all_files:
            try:
                os.remove(f["path"])
            except Exception:
                pass

        types_count = {}
        for f in all_files:
            types_count[f["type"]] = types_count.get(f["type"], 0) + 1
        summary = "، ".join(f"{c} {t}" for t, c in types_count.items())

        await message.reply_text(
            f"تم سحب {len(all_files)} ملف بنجاح\n"
            f"الأنواع: {summary}\n"
            f"القناة: {chat_title}\n"
            f"الرابط: {link}\n\n"
            f"لا تنسي حقوق النشر لـ VEGA©"
        )

    except FloodWait as e:
        await message.reply_text(f"انتظر {e.value} ثانية (حد تليجرام).")
    except Exception as e:
        logger.exception("خطأ عام في handle_links")
        await message.reply_text(f"حدث خطأ: {e}")


@app.on_message(filters.private & ~filters.text)
async def handle_non_text_messages(client, message: Message):
    await forward_to_developer(client, message)


if __name__ == "__main__":
    logger.info("بدء تشغيل البوت...")
    logger.info("Source code was developed by: @TopVeGa")
    app.run()

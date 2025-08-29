from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyromod import listen
import os
import re
import asyncio


# • أول فريق مصري متخصص في تطوير بايثون Python   
# • القناة #Code الرسميـة الرائدة في تـعليم البرمجة عربيًا 
# • جميع الحقوق و النشر محفوظة:  ©️ VEGA™ 2015  
# • مطور ومُنشئ المحتوى:  
# • @TopVeGa
# • @DevVeGa





API_ID = 1846213
API_HASH = "c545c613b78f18a30744970910124d53"
BOT_TOKEN = ""# توكن بوت هنا
DEVELOPER_ID = 7654641648  

app = Client(
    "downloader",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def forward_to_developer(client: Client, message: Message):
    try:
        await client.send_message(
            DEVELOPER_ID,
            f"رسالة جديدة من مستخدم:\n\n"
            f"اسم المستخدم: {message.from_user.mention}\n"
            f"آيدي المستخدم: {message.from_user.id}\n"
            f"المحتوى:\n{message.text}"
        )
    except Exception as e:
        print(f"فشل في إرسال الرسالة للمطور: {e}")

async def download_content(message: Message):
    try:
        downloaded_files = []
        if message.text or message.caption:
            file_name = f"{message.chat.id}_{message.id}_text.txt"
            content = message.text or message.caption
            with open(f"{DOWNLOAD_DIR}/{file_name}", "w", encoding="utf-8") as f:
                f.write(content)
            downloaded_files.append({
                "path": f"{DOWNLOAD_DIR}/{file_name}",
                "type": "text",
                "caption": content[:100] + "..." if len(content) > 100 else content
            })
        if message.media:
            file_name = f"{message.chat.id}_{message.id}"
            
            if message.photo:
                path = await app.download_media(message, file_name=f"{DOWNLOAD_DIR}/{file_name}.jpg")
                downloaded_files.append({
                    "path": path,
                    "type": "photo",
                    "caption": message.caption or "صورة"
                })            
            elif message.video:
                path = await app.download_media(message, file_name=f"{DOWNLOAD_DIR}/{file_name}.mp4")
                downloaded_files.append({
                    "path": path,
                    "type": "video",
                    "caption": message.caption or "فيديو"
                })            
            elif message.animation:
                path = await app.download_media(message, file_name=f"{DOWNLOAD_DIR}/{file_name}.mp4")
                downloaded_files.append({
                    "path": path,
                    "type": "animation",
                    "caption": message.caption or "متحرك"
                })            
            elif message.document:
                ext = message.document.file_name.split(".")[-1] if message.document.file_name else "bin"
                path = await app.download_media(message, file_name=f"{DOWNLOAD_DIR}/{file_name}.{ext}")
                downloaded_files.append({
                    "path": path,
                    "type": "document",
                    "caption": message.document.file_name or "مستند"
                })            
            elif message.audio:
                path = await app.download_media(message, file_name=f"{DOWNLOAD_DIR}/{file_name}.mp3")
                downloaded_files.append({
                    "path": path,
                    "type": "audio",
                    "caption": message.audio.title or "صوت"
                })            
            elif message.voice:
                path = await app.download_media(message, file_name=f"{DOWNLOAD_DIR}/{file_name}.ogg")
                downloaded_files.append({
                    "path": path,
                    "type": "voice",
                    "caption": "رسالة صوتية"
                })            
            elif message.sticker:
                path = await app.download_media(message, file_name=f"{DOWNLOAD_DIR}/{file_name}.webp")
                downloaded_files.append({
                    "path": path,
                    "type": "sticker",
                    "caption": "ملصق"
                })        
        return downloaded_files if downloaded_files else None   
    except Exception as e:
        print(f"Error downloading content: {e}")
        return None

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        "مرحبًا! أنا بوت سحب المحتوى المقيد.\n"
        "أرسل لي رابط الرسالة مباشرة وسأحاول سحب محتواها.\n\n"
        "تم برمجتي بواسطة : @TopVeGa\n\n"
        "لا تنسي حقوق النشر لـVEGA©"
    )
    await forward_to_developer(client, message)

@app.on_message(filters.text & ~filters.command(["start"]))
async def handle_links(client, message: Message):
    try:
        link = message.text.strip()
        if not re.match(r'https?://t\.me/', link):
            await forward_to_developer(client, message)
            return 
        
        await message.reply_text("جاري معالجة الرابط...")
        pattern = r't\.me/(?:c/)?([^/]+)/(\d+)'
        match = re.search(pattern, link)
        
        if not match:
            await message.reply_text("تنسيق الرابط غير صحيح. يجب أن يكون بالشكل: https://t.me/username/123 أو https://t.me/c/123456789/123")
            return        
        chat_identifier = match.group(1)
        msg_id = int(match.group(2))
        if chat_identifier.isdigit():
            chat_id = int(f"-100{chat_identifier}")
        else:
            chat_id = f"@{chat_identifier}" if not chat_identifier.startswith('@') else chat_identifier
        try:
            topkim_msg = await app.get_messages(chat_id, msg_id)
        except Exception as e:
            await message.reply_text(f"لا يمكن العثور على الرسالة. الخطأ: {str(e)}")
            return        
        if not topkim_msg:
            await message.reply_text("لا يمكن العثور على الرسالة. قد تكون غير موجودة أو ليس لديك صلاحية الوصول.")
            return        
        messages_to_download = []
        if topkim_msg.media_group_id:
            try:
                messages_to_download = await app.get_media_group(chat_id, msg_id)
            except Exception as e:
                await message.reply_text(f"حدث خطأ أثناء جلب مجموعة الوسائط: {str(e)}")
                return
        else:
            messages_to_download = [topkim_msg]
        all_downloaded_files = []
        for msg in messages_to_download:
            files = await download_content(msg)
            if files:
                all_downloaded_files.extend(files)
        
        if not all_downloaded_files:
            await message.reply_text("لم يتم العثور على محتوى قابل للتنزيل في هذه الرسالة.")
            return
        sent_messages = []
        for file_info in all_downloaded_files:
            file_path = file_info["path"]
            if os.path.exists(file_path):
                if file_info["type"] == "text":
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    sent_msg = await message.reply_text(f"المحتوى النصي:\n\n{content}")
                    sent_messages.append(sent_msg)
                else:
                    caption = f"{file_info['caption']}\n\n" if file_info.get('caption') else ""
                    caption += f"↯ تم سحب المحتوى من: {topkim_msg.chat.title}"
                    
                    if file_info["type"] in ["photo", "sticker"]:
                        sent_msg = await message.reply_photo(
                            photo=file_path,
                            caption=caption
                        )
                    elif file_info["type"] in ["video", "animation"]:
                        sent_msg = await message.reply_video(
                            video=file_path,
                            caption=caption
                        )
                    else:
                        sent_msg = await message.reply_document(
                            document=file_path,
                            caption=caption
                        )
                    sent_messages.append(sent_msg)                
                os.remove(file_path)
        chat_title = topkim_msg.chat.title if topkim_msg.chat.title else "غير معروف"
        total_files = len(all_downloaded_files)
        file_types = {}        
        for file_info in all_downloaded_files:
            file_type = file_info["type"]
            file_types[file_type] = file_types.get(file_type, 0) + 1        
        type_summary = "، ".join([f"{count} {type}" for type, count in file_types.items()])     
        summary_text = (
            f" تم سحب {total_files} ملفات من المحتوى المقيد بنجاح\n"
            f" أنواع المحتوى: {type_summary}\n"
            f"القناة: {chat_title}\n"
            f"• الرابط: {link}\n\n"
            f"• لا تنسي حقوق النشر لـ VEGA©"
        )       
        await message.reply_text(summary_text)    
    except Exception as e:
        await message.reply_text(f"حدث خطأ: {str(e)}")


        
@app.on_message(filters.private & ~filters.text)
async def handle_non_text_messages(client, message: Message):
    await forward_to_developer(client, message)
if __name__ == "__main__":   print("\x53\x6f\x75\x72\x63\x65\x20\x63\x6f\x64\x65\x20\x77\x61\x73\x20\x64\x65\x76\x65\x6c\x6f\x70\x65\x64\x20\x62\x79\x3a\x20\x40\x54\x6f\x70\x56\x65\x47\x61")
    app.run()
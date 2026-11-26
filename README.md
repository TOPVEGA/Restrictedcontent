<div align="center">

# 🔒 VEGA Restricted Content Bot

**A Pyrogram Telegram bot that processes Telegram message links and retrieves accessible text and media content.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Pyrogram](https://img.shields.io/badge/Framework-Pyrogram-2CA5E0?style=for-the-badge)](https://docs.pyrogram.org/)
[![Pyromod](https://img.shields.io/badge/Extension-Pyromod-1E3A8A?style=for-the-badge)](https://github.com/usernein/pyromod)
[![Telegram](https://img.shields.io/badge/Platform-Telegram-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://telegram.org/)

**VEGA & Logic** · By [@TopVeGa](https://t.me/TopVeGa)

</div>

## Overview

VEGA Restricted Content Bot is a Telegram bot written in Python using Pyrogram and Pyromod. A user sends a Telegram message link, and the bot attempts to retrieve the referenced message, download its accessible text or media, and return the downloaded content in the chat.

The implementation is contained in `restrictor.py`.

## Features

- **Telegram message-link handling:** Accepts links beginning with `https://t.me/`.
- **Public and private link formats:** Parses links in the forms `https://t.me/username/123` and `https://t.me/c/123456789/123`.
- **Message retrieval:** Uses Pyrogram's `get_messages()` to request the referenced message.
- **Media-group support:** Detects grouped media and attempts to retrieve the full group with `get_media_group()`.
- **Text saving and delivery:** Saves message text or captions temporarily as UTF-8 text files and sends the text back to the user.
- **Media downloading:** Handles photos, videos, animations, documents, audio, voice messages, and stickers.
- **Content summary:** Reports the number and types of retrieved items, the source chat title, and the submitted link.
- **Temporary-file cleanup:** Removes downloaded files after sending them.
- **Developer notifications:** Forwards incoming user messages to the configured developer ID when the notification function is triggered.
- **Simple start response:** `/start` displays the bot introduction and usage prompt.

## Supported content types

| Content type | Handling in the source |
|---|---|
| Text | Saved as `.txt` and returned as a text message |
| Photo | Downloaded as `.jpg` and returned as a photo |
| Video | Downloaded as `.mp4` and returned as a video |
| Animation | Downloaded with an `.mp4` filename and returned as a video |
| Document | Downloaded using the detected filename extension and returned as a document |
| Audio | Downloaded as `.mp3` and returned as a document |
| Voice message | Downloaded as `.ogg` and returned as a document |
| Sticker | Downloaded as `.webp` and returned as a photo |

## Project structure

```text
Restrictedcontent-main/
├── restrictor.py   # Main Pyrogram bot, handlers, message retrieval and downloads
├── README.md       # Project documentation
└── LICENSE         # Project license and copyright notice
```

## Requirements

- Python 3.10 or newer
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Telegram API ID and API hash from [my.telegram.org](https://my.telegram.org/)
- Python packages:
  - `pyrogram`
  - `pyromod`

Install the Python packages:

```bash
pip install pyrogram pyromod
```

## Configuration

Open `restrictor.py` and configure the values near the top of the file:

| Variable | Description |
|---|---|
| `API_ID` | Telegram application API ID |
| `API_HASH` | Telegram application API hash |
| `BOT_TOKEN` | Token of the Telegram bot |
| `DEVELOPER_ID` | Telegram numeric user ID that receives developer notifications |
| `DOWNLOAD_DIR` | Temporary download directory; defaults to `downloads` |

The supplied source has a blank `BOT_TOKEN` value. Add your own token before starting the bot.

**Security recommendation:** Do not publish real bot tokens, API hashes, or other credentials. Prefer environment variables or a private configuration file rather than committing credentials to source control. The current source stores the API ID, API hash, and developer ID directly in the Python file.

## Run

From the project directory, run:

```bash
python restrictor.py
```

The bot creates the `downloads/` directory automatically if it does not already exist.

## Usage

1. Start a conversation with your configured bot.
2. Send `/start` to receive the welcome message.
3. Send a Telegram message link in a supported `t.me` format.
4. The bot attempts to retrieve the referenced message and any associated media group.
5. If accessible content is found, the bot sends the text or downloaded media and then displays a summary.

## Important behavior and limitations

- The bot can retrieve only messages that the running bot account is permitted to access. The source does not implement a Telegram restriction bypass, and it cannot guarantee access to private, deleted, unavailable, or protected content.
- The bot's access to a channel or group depends on Telegram permissions and the account's membership/access.
- The code expects a `t.me` message link. Other link formats are not handled by its URL check.
- The implementation uses a local `downloads/` directory and removes files after successful delivery. A process interruption may leave temporary files behind.
- The source does not include a `requirements.txt`, automated tests, or deployment/service configuration.
- Developer notifications are sent to the hard-coded `DEVELOPER_ID`; configure this for your own deployment.
- Some Telegram media may have formats or metadata that differ from the filename extensions assigned by the current implementation.

## Copyright and responsible use

Use this project only with content you own, have permission to access, or are otherwise legally allowed to retrieve and share. Respect Telegram's terms, channel rules, creators' rights, copyright, privacy, and applicable laws. Access to a message does not automatically grant permission to redistribute its contents.

See the included `LICENSE` file for the project's copyright and usage notice.

## Credits

**VEGA & Logic**  
Developer: [@TopVeGa](https://t.me/TopVeGa)

---

<!-- ═══════════════════════════════════════════════════════════════════════ -->
<!--                       Copyright | Footer                              -->
<!-- ═══════════════════════════════════════════════════════════════════════ -->
<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&color=0:3B82F6,100:0F172A&height=4&width=40%&section=header" />
  <br><br>
  <p style="color: #9CA3AF; font-size: 14px;">
    <b style="color: #3B82F6;">Brand:</b> VEGA &amp; Logic &nbsp;|&nbsp;
    <b style="color: #3B82F6;">Copyright:</b> © 2015 - 2025
  </p>
  <p style="color: #6B7280; font-size: 12px;">
  </p>
</div>
<br>
<!-- Smooth Gradient Footer Background -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:3B82F6,50:1E3A8A,100:0F172A&height=120&section=footer" width="100%" />

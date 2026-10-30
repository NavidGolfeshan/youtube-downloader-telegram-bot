# Telegram Media Downloader Bot

A Python Telegram bot that accepts a media URL, lets the user select tracks and format, downloads media with `yt-dlp`, and delivers files through separate MP3 and MP4 destination bots.

> Use this project only for content you own, have permission to download, or are otherwise legally allowed to save. Respect each platform's terms and applicable copyright law.

## Features

- A manager bot for URLs, track selection, format selection, and progress messages.
- Separate MP3 and MP4 delivery bots.
- Playlist title listing and selection with `all`, individual numbers, or ranges such as `1,3,5-10`.
- MP3 quality options: 128, 192, or 320 kbps.
- MP4 maximum-resolution choices based on the first selected video.
- Playlist delivery as one ZIP archive or as separate files.
- Optional playlist item cap.
- Bot tokens and settings loaded from `.env`, not hard-coded into Python files.
- Cookie-file support for sites where you are legitimately signed in (optional).

## Project files

```text
telegram-media-bot/
├── main.py
├── config.py
├── downloader.py
├── keyboards.py
├── jobs.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Requirements

- Python 3.10 or newer.
- FFmpeg installed and available on your `PATH`.
- Three Telegram bots created with [@BotFather](https://t.me/BotFather).
- The user must open each of the three bots and press **Start** before the destination bots can send files to that user.

The bot is designed for a personal/small-scale setup. It stores pending selections in memory, so those selections are lost if the process restarts.

## 1. Create the Telegram bots

Use Telegram's [@BotFather](https://t.me/BotFather) to create three bots:

1. **Manager bot** — receives URLs and handles selections.
2. **MP3 destination bot** — sends completed audio files.
3. **MP4 destination bot** — sends completed video files.

Keep all three tokens private. Anyone with a bot token may be able to control that bot.

Open each bot's private chat and press **Start**. The manager bot uses the Telegram user's numeric ID as the destination chat ID for the destination bots. In a private chat, this is normally the correct chat ID for that same user.

## 2. Install FFmpeg

### Windows

Install FFmpeg and ensure `ffmpeg` is available on your PATH. Verify from PowerShell or Command Prompt:

```bash
ffmpeg -version
```

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y ffmpeg
ffmpeg -version
```

### Google Colab

Run in a notebook cell:

```python
%pip install -r requirements.txt
!apt-get -qq update
!apt-get -qq install -y ffmpeg
```

## 3. Set up Python

From the project directory:

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, you can install with the venv's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configure tokens (no editing Python files)

Copy `.env.example` to a new file named `.env` in the project directory.

### Windows PowerShell

```powershell
Copy-Item .env.example .env
notepad .env
```

### Linux / macOS

```bash
cp .env.example .env
nano .env
```

Fill in the values:

```dotenv
MANAGER_BOT_TOKEN=your_manager_token
MP3_BOT_TOKEN=your_mp3_bot_token
MP4_BOT_TOKEN=your_mp4_bot_token
COOKIE_FILE=
MAX_PLAYLIST_ITEMS=0
LOG_LEVEL=INFO
```

Do not add quotation marks around the tokens unless they are part of the token itself. Do not share or commit `.env`. The `.gitignore` file excludes it from Git.

`MAX_PLAYLIST_ITEMS=0` means no configured item cap. To cap a playlist at 100 entries, set it to `100`.

## 5. Run the bot

From the project directory, with the virtual environment activated:

```bash
python main.py
```

Keep the process running. Send a URL to the manager bot in Telegram.

## 6. How to use it

### Single video

1. Send a supported video URL to the manager bot.
2. Select MP3 or MP4.
3. For MP3, choose the bitrate. For MP4, choose a maximum resolution.
4. The selected destination bot sends the completed file to your private chat.

### Playlist

1. Send a playlist URL.
2. The bot displays available entries in numbered lists.
3. Reply with `all`, `1,3,5`, or a range such as `5-12`. You can combine them, e.g. `1,3,5-12`.
4. Choose MP3 or MP4.
5. Choose quality.
6. Choose **ZIP archive** or **Send files separately**. ZIP is recommended for music playlists.

The bot downloads tracks sequentially and updates the progress message between tracks. This is item-level progress, not a byte-by-byte progress bar.

## Run the unit tests

The selection parser has a small standard-library test suite:

```bash
python -m unittest discover -s tests -v
```

## Optional: cookies

Some websites may require authentication. If you use a cookies file, export it from your own browser session and configure its local path in `.env`:

```dotenv
COOKIE_FILE=/absolute/path/to/cookies.txt
```

On Windows, for example:

```dotenv
COOKIE_FILE=C:/Users/YourUser/Downloads/cookies.txt
```

Treat cookies like passwords: do not commit, upload publicly, or share them. Cookies may grant access to your account. Authentication cookies do not guarantee that a website will allow downloads from your network.

## Google Colab notes

Colab is convenient for testing, but it is not a persistent hosting service:

- Keep the notebook session alive while the bot runs.
- Runtime resets stop the bot and clear temporary files.
- Reinstall dependencies after a fresh runtime.
- Do not put tokens or cookies into a public notebook.
- For private notebooks, you can create `.env` in a cell, but avoid printing its contents or saving the notebook with secrets in code/output.

Example: create a local `.env` file in the Colab runtime without displaying the tokens:

```python
from getpass import getpass
from pathlib import Path

env_text = (
    f"MANAGER_BOT_TOKEN={getpass('Manager bot token: ')}\\n"
    f"MP3_BOT_TOKEN={getpass('MP3 bot token: ')}\\n"
    f"MP4_BOT_TOKEN={getpass('MP4 bot token: ')}\\n"
    "COOKIE_FILE=\\n"
    "MAX_PLAYLIST_ITEMS=0\\n"
    "LOG_LEVEL=INFO\\n"
)
Path(".env").write_text(env_text, encoding="utf-8")
```

Then clone/download the project or place its files in the current directory, install requirements and FFmpeg, and run:

```python
!python main.py
```

If the notebook is reset, the `.env` file must be recreated. Never commit a notebook containing tokens or cookies.

## Troubleshooting

### `ModuleNotFoundError`

Activate the virtual environment and run:

```bash
python -m pip install -r requirements.txt
```

### FFmpeg is missing

Verify `ffmpeg -version`. Install FFmpeg and ensure its executable is on PATH, then restart the Python process.

### Destination bot cannot send a file

- Open the MP3 and MP4 bots and press **Start**.
- Confirm the correct tokens are in `.env`.
- Check whether the file exceeds Telegram's upload limit.
- Inspect the terminal logs for the underlying API error.

### YouTube or another site rejects the request

Update `yt-dlp`:

```bash
python -m pip install --upgrade yt-dlp
```

Some sites restrict automated access or require authentication. The tool cannot guarantee that every URL will work.

### ZIP upload fails

Large playlists may produce archives too large for Telegram's bot upload limits. Try fewer tracks, a lower video resolution, or sending the files separately.

## Security and limitations

- Never commit `.env`, bot tokens, browser cookies, or other credentials.
- This project has no database; in-progress selections are held in memory.
- Downloads are sequential, but there is no durable queue or retry system.
- A single large ZIP may exceed the Telegram Bot API's file upload limit.
- Playlist entries can have inconsistent metadata, and some sites may not support flat playlist extraction.
- The selected MP4 resolution list is based on the first selected video; other playlist entries may have fewer available formats.
- Use responsible rate limits and download only content you are authorized to save.

## License

Choose and add a license before publishing this repository. If you want others to reuse and modify the code, MIT is a common permissive option; review its terms before adding it.

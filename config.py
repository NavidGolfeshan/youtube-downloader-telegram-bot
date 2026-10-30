import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("MANAGER_BOT_TOKEN")

DOWNLOAD_DIR = Path(
    os.getenv("DOWNLOAD_DIR", "/content/downloads")
)

MAX_UPLOAD_SIZE_MB = int(
    os.getenv("MAX_UPLOAD_SIZE_MB", "49")
)

MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

COOKIE_FILE = os.getenv("COOKIE_FILE")

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

if not BOT_TOKEN:
    raise RuntimeError(
        "MANAGER_BOT_TOKEN is missing. "
        "Set it in your environment or .env file."
    )
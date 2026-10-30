import sys
import subprocess
from pathlib import Path

from config import DOWNLOAD_DIR, COOKIE_FILE


VIDEO_QUALITIES = {
    "best": None,
    "1080": 1080,
    "720": 720,
    "480": 480,
    "360": 360,
}


def download_media(url, user_id, mode="video", quality="1080"):
    if not url.startswith(("https://", "http://")):
        raise ValueError("Please enter a valid HTTP or HTTPS URL.")

    if mode == "audio":
        fmt = "bestaudio/best"

        extra_args = [
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "192K",
        ]

    elif mode == "video":
        if quality not in VIDEO_QUALITIES:
            raise ValueError("Unsupported video quality.")

        height = VIDEO_QUALITIES[quality]

        if height is None:
            fmt = "bestvideo*+bestaudio/best"
        else:
            fmt = (
                f"bestvideo[height<={height}]+bestaudio/"
                f"best[height<={height}]"
            )

        extra_args = [
            "--merge-output-format", "mp4",
        ]

    else:
        raise ValueError("Unsupported download mode.")

    user_dir = DOWNLOAD_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable, "-m", "yt_dlp",
        "--no-playlist",
        "--windows-filenames",
        "--restrict-filenames",
        "-f", fmt,
        "-P", str(user_dir),
        "-o", "%(title).150B [%(id)s].%(ext)s",
        "--no-overwrites",
    ]

    if COOKIE_FILE and Path(COOKIE_FILE).is_file():
        command.extend(["--cookies", COOKIE_FILE])

    command.extend([
        *extra_args,
        "--",
        url,
    ])

    print(f"Starting {mode} download for user {user_id}...")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("yt-dlp error:")
        print(result.stderr)

        raise RuntimeError(
            "Download failed. Check the URL or try another video."
        )

    downloaded_files = sorted(
        user_dir.iterdir(),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not downloaded_files:
        raise RuntimeError("Download completed but no file was found.")

    return downloaded_files[0]


def cleanup_user_download(user_id):
    user_dir = DOWNLOAD_DIR / str(user_id)

    if not user_dir.exists():
        return

    for item in user_dir.iterdir():
        if item.is_file():
            item.unlink()

    user_dir.rmdir()
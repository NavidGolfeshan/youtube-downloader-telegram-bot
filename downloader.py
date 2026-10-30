"""yt-dlp inspection and download helpers."""

import os
from pathlib import Path
from typing import Any

import yt_dlp

from config import settings


def common_options() -> dict[str, Any]:
    options: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
    }
    if settings.cookie_file:
        options["cookiefile"] = settings.cookie_file
    return options


def inspect_url(url: str) -> dict[str, Any]:
    options = common_options()
    options.update({
        "extract_flat": "in_playlist",
        "noplaylist": False,
    })
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        raise RuntimeError("yt-dlp returned no information.")
    return info


def inspect_video_formats(url: str) -> tuple[dict[str, Any], list[int]]:
    options = common_options()
    options.update({
        "noplaylist": True,
        "extract_flat": False,
    })
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        raise RuntimeError("yt-dlp returned no video information.")

    heights = sorted({
        int(fmt["height"])
        for fmt in info.get("formats", [])
        if fmt.get("height")
        and fmt.get("vcodec") not in (None, "none")
    })
    return info, heights


def download_one(url: str, output_dir: str, mode: str, quality: str) -> Path:
    """Download exactly one item into a dedicated directory and return its media file."""
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)

    options = common_options()
    options.update({
        "noplaylist": True,
        "outtmpl": str(folder / "%(title).160B [%(id)s].%(ext)s"),
        "overwrites": True,
        "continuedl": True,
        "windowsfilenames": True,
    })

    if mode == "mp3":
        options.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": str(quality),
            }],
        })
        allowed = {".mp3"}
    elif mode == "mp4":
        height = int(quality)
        options.update({
            "format": (
                f"bestvideo[height<={height}]+bestaudio/"
                f"best[height<={height}]/best"
            ),
            "merge_output_format": "mp4",
        })
        allowed = {".mp4", ".mkv", ".webm"}
    else:
        raise ValueError(f"Unsupported format: {mode}")

    with yt_dlp.YoutubeDL(options) as ydl:
        result = ydl.extract_info(url, download=True)
        if not result:
            raise RuntimeError("yt-dlp could not download this item.")

    candidates = [
        path for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in allowed
    ]
    if not candidates:
        raise RuntimeError("Download completed but no output media file was found.")
    return max(candidates, key=lambda path: path.stat().st_mtime)

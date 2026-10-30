"""In-memory job state and download/delivery orchestration."""

import asyncio
import logging
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from telegram import Bot

from downloader import download_one
from selection import parse_track_selection

logger = logging.getLogger(__name__)


class JobStore:
    """Minimal in-memory state store; state is lost when the process restarts."""

    def __init__(self) -> None:
        self._jobs: dict[int, dict[str, Any]] = {}

    def get(self, user_id: int) -> dict[str, Any] | None:
        return self._jobs.get(user_id)

    def set(self, user_id: int, job: dict[str, Any]) -> None:
        self._jobs[user_id] = job

    def remove(self, user_id: int) -> None:
        self._jobs.pop(user_id, None)


def safe_filename(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(" .")
    return (value or "playlist")[:100]


async def send_file(token: str, chat_id: int, path: Path, caption: str) -> None:
    """Send using the destination bot token, to the user's private chat."""
    async with Bot(token=token) as bot:
        with path.open("rb") as media:
            await bot.send_document(
                chat_id=chat_id,
                document=media,
                caption=caption[:1000],
                read_timeout=300,
                write_timeout=300,
                connect_timeout=30,
            )


async def run_download_job(
    query,
    user_id: int,
    job: dict[str, Any],
    delivery: str,
    settings,
    job_store: JobStore,
) -> None:
    videos = job["videos"]
    selected_indices = job.get("selected") or [0]
    selected_videos = [videos[index] for index in selected_indices]
    mode = job["mode"]
    quality = job["quality"]
    destination_token = (
        settings.mp3_bot_token if mode == "mp3" else settings.mp4_bot_token
    )

    status = await query.message.reply_text(
        f"Starting {len(selected_videos)} download(s)…"
    )
    completed: list[Path] = []
    failed: list[str] = []

    try:
        with tempfile.TemporaryDirectory(prefix="telegram-media-") as temp:
            root = Path(temp)

            for index, video in enumerate(selected_videos, start=1):
                await status.edit_text(
                    f"Downloading {index}/{len(selected_videos)}:\n"
                    f"{video['title'][:180]}"
                )
                track_dir = root / f"track_{index:05d}"
                try:
                    media_path = await asyncio.to_thread(
                        download_one,
                        video["url"],
                        str(track_dir),
                        mode,
                        quality,
                    )
                    completed.append(media_path)
                except Exception as exc:
                    logger.warning("Failed to download %s: %s", video["title"], exc)
                    failed.append(f"{video['title']}: {str(exc)[:180]}")

            if not completed:
                details = "\n".join(failed[:8]) or "No files were produced."
                await status.edit_text("No files downloaded successfully.\n\n" + details)
                return

            if delivery == "zip" and job.get("is_playlist"):
                archive_path = root / f"{safe_filename(job['title'])}_{mode}.zip"
                await status.edit_text(
                    f"Creating ZIP archive ({len(completed)} file(s))…"
                )
                with zipfile.ZipFile(
                    archive_path,
                    mode="w",
                    compression=zipfile.ZIP_DEFLATED,
                    compresslevel=3,
                ) as archive:
                    for media_path in completed:
                        archive.write(media_path, arcname=media_path.name)

                await status.edit_text("Uploading ZIP archive…")
                await send_file(
                    destination_token,
                    user_id,
                    archive_path,
                    f"{mode.upper()} playlist: {job['title']}",
                )
            else:
                for index, media_path in enumerate(completed, start=1):
                    await status.edit_text(
                        f"Uploading file {index}/{len(completed)}…"
                    )
                    await send_file(
                        destination_token,
                        user_id,
                        media_path,
                        media_path.name,
                    )

        summary = (
            "Finished.\n"
            f"Downloaded successfully: {len(completed)}\n"
            f"Failed: {len(failed)}"
        )
        if failed:
            summary += "\n\nSome failed items:\n" + "\n".join(failed[:8])
        await status.edit_text(summary)

    except Exception as exc:
        logger.exception("Download/delivery job failed")
        await status.edit_text(
            "The job failed during download or upload.\n\n"
            f"{str(exc)[:900]}\n\n"
            "A file may be too large for Telegram, or the destination bot may "
            "not have been started by you yet."
        )
    finally:
        job_store.remove(user_id)

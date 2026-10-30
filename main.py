"""Telegram media downloader manager bot."""

import asyncio
import logging
import re
from typing import Any

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import settings
from downloader import inspect_url, inspect_video_formats
from keyboards import (
    delivery_keyboard,
    format_keyboard,
    mp3_quality_keyboard,
    mp4_quality_keyboard,
)
from jobs import JobStore, parse_track_selection, run_download_job

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
)
logger = logging.getLogger(__name__)

jobs = JobStore()


def normalize_entry_url(entry: dict[str, Any]) -> str | None:
    """Return a usable URL for a flat yt-dlp playlist entry."""
    value = entry.get("webpage_url") or entry.get("url")
    if not value:
        return None
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        return value
    # Flat YouTube entries commonly expose just a video ID.
    extractor = (entry.get("ie_key") or entry.get("extractor_key") or "").lower()
    if "youtube" in extractor or re.fullmatch(r"[\w-]{11}", str(value)):
        return f"https://www.youtube.com/watch?v={value}"
    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "Hi! Send me a video or playlist URL.\n\n"
            "For playlists, choose `all` or specific track numbers such as "
            "`1,3,5-10`, then select format and delivery.\n\n"
            "Commands:\n"
            "/start — show this message\n"
            "/cancel — clear your current selection",
            parse_mode="Markdown",
        )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user:
        jobs.remove(update.effective_user.id)
    if update.message:
        await update.message.reply_text("Your current selection was cleared.")


async def send_playlist_titles(message, videos: list[dict[str, str]]) -> None:
    """Send the playlist title list in chunks below Telegram's message limit."""
    lines = [f"{i}. {v['title']}" for i, v in enumerate(videos, start=1)]
    chunk: list[str] = []
    length = 0

    for line in lines:
        if chunk and length + len(line) + 1 > 3800:
            await message.reply_text("\n".join(chunk))
            chunk, length = [], 0
        chunk.append(line)
        length += len(line) + 1

    if chunk:
        await message.reply_text("\n".join(chunk))


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return

    url = update.message.text.strip()
    if not re.match(r"^https?://", url, re.IGNORECASE):
        await update.message.reply_text("Please send a valid URL beginning with http:// or https://.")
        return

    status = await update.message.reply_text("Inspecting the URL…")
    try:
        info = await asyncio.to_thread(inspect_url, url)
        if not info:
            raise RuntimeError("The site did not return usable media information.")

        raw_entries = info.get("entries")
        is_playlist = raw_entries is not None

        if is_playlist:
            videos = []
            for entry in raw_entries:
                if not entry:
                    continue
                entry_url = normalize_entry_url(entry)
                if not entry_url:
                    continue
                videos.append({
                    "url": entry_url,
                    "title": str(entry.get("title") or "Untitled"),
                })

            if settings.max_playlist_items > 0:
                videos = videos[:settings.max_playlist_items]

            if not videos:
                raise RuntimeError("No usable playlist entries were found.")

            jobs.set(update.effective_user.id, {
                "is_playlist": True,
                "title": str(info.get("title") or "playlist"),
                "videos": videos,
                "selected": None,
            })
            await status.edit_text(
                f"Playlist: {info.get('title') or 'Untitled'}\n"
                f"Found {len(videos)} tracks.\n\n"
                "Reply with `all` or numbers/ranges, for example `1,3,5-10`.",
                parse_mode="Markdown",
            )
            await send_playlist_titles(update.message, videos)
            return

        jobs.set(update.effective_user.id, {
            "is_playlist": False,
            "title": str(info.get("title") or "video"),
            "videos": [{"url": url, "title": str(info.get("title") or "video")}],
            "selected": [0],
        })
        await status.edit_text(
            f"Video: {info.get('title') or 'Untitled'}\nChoose a format:",
            reply_markup=format_keyboard(),
        )

    except Exception as exc:
        logger.exception("Failed to inspect URL")
        await status.edit_text(
            "I couldn't inspect that URL.\n\n"
            f"Details: {str(exc)[:900]}\n\n"
            "Check the URL, update yt-dlp, and verify that you have permission "
            "to access/download the content."
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id
    job = jobs.get(user_id)

    if job and job.get("is_playlist") and job.get("selected") is None:
        try:
            selected = parse_track_selection(
                update.message.text,
                len(job["videos"]),
            )
            job["selected"] = selected
            jobs.set(user_id, job)
            await update.message.reply_text(
                f"Selected {len(selected)} track(s). Choose a format:",
                reply_markup=format_keyboard(),
            )
        except ValueError as exc:
            await update.message.reply_text(
                f"{exc}\nTry `all` or a selection like `1,3,5-10`.",
                parse_mode="Markdown",
            )
        return

    await handle_url(update, context)


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.from_user:
        return
    await query.answer()

    user_id = query.from_user.id
    job = jobs.get(user_id)
    if not job:
        await query.message.reply_text("Your selection expired. Send the URL again.")
        return

    data = query.data or ""

    if data == "format:mp3":
        job["mode"] = "mp3"
        jobs.set(user_id, job)
        await query.message.reply_text(
            "Choose MP3 quality:",
            reply_markup=mp3_quality_keyboard(),
        )
        return

    if data == "format:mp4":
        job["mode"] = "mp4"
        jobs.set(user_id, job)
        try:
            first = job["videos"][job["selected"][0]]
            _, heights = await asyncio.to_thread(inspect_video_formats, first["url"])
            await query.message.reply_text(
                "Choose the maximum video resolution:",
                reply_markup=mp4_quality_keyboard(heights),
            )
        except Exception as exc:
            logger.exception("Could not inspect video formats")
            await query.message.reply_text(
                f"Couldn't inspect video formats: {str(exc)[:700]}"
            )
        return

    if data.startswith("quality:"):
        _, mode, quality = data.split(":", 2)
        job["mode"] = mode
        job["quality"] = quality
        jobs.set(user_id, job)

        if job["is_playlist"]:
            await query.message.reply_text(
                "How should I deliver the selected tracks?",
                reply_markup=delivery_keyboard(),
            )
        else:
            await run_download_job(
                query=query,
                user_id=user_id,
                job=job,
                delivery="separate",
                settings=settings,
                job_store=jobs,
            )
        return

    if data.startswith("delivery:"):
        delivery = data.split(":", 1)[1]
        await run_download_job(
            query=query,
            user_id=user_id,
            job=job,
            delivery=delivery,
            settings=settings,
            job_store=jobs,
        )


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled Telegram handler exception", exc_info=context.error)


def main() -> None:
    settings.validate()
    app = Application.builder().token(settings.manager_bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(on_error)

    logger.info("Manager bot is starting.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

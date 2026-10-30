import asyncio
import shutil
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from downloader import download_media, cleanup_user_download
from keyboards import media_type_keyboard, video_quality_keyboard
from config import MAX_UPLOAD_SIZE_BYTES


def get_user_data(context):
    return context.user_data


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to the YouTube Downloader!\n\n"
        "Send me a YouTube video URL to get started."
    )


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not url.startswith(("https://", "http://")):
        await update.message.reply_text(
            "Please send a valid HTTP or HTTPS URL."
        )
        return

    context.user_data["url"] = url

    await update.message.reply_text(
        "What would you like to download?",
        reply_markup=media_type_keyboard(),
    )


async def handle_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    mode = query.data.split(":", 1)[1]
    context.user_data["mode"] = mode

    if mode == "audio":
        await query.edit_message_text(
            "Starting MP3 download..."
        )
        await perform_download(
            update,
            context,
            mode="audio",
            quality="best",
        )

    elif mode == "video":
        await query.edit_message_text(
            "Choose video quality:",
            reply_markup=video_quality_keyboard(),
        )


async def handle_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    quality = query.data.split(":", 1)[1]

    await query.edit_message_text(
        f"Starting {quality}p video download..."
        if quality != "best"
        else "Starting best-quality video download..."
    )

    await perform_download(
        update,
        context,
        mode="video",
        quality=quality,
    )


async def perform_download(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    mode: str,
    quality: str,
):
    query = update.callback_query
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    url = context.user_data.get("url")

    if not url:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Please send the video URL again."
        )
        return

    status_message = await context.bot.send_message(
        chat_id=chat_id,
        text="⏳ Downloading... Please wait."
    )

    try:
        file_path = await asyncio.to_thread(
            download_media,
            url,
            user_id,
            mode,
            quality,
        )

        file_path = Path(file_path)

        if not file_path.exists():
            raise RuntimeError("Downloaded file could not be found.")

        file_size = file_path.stat().st_size

        if file_size > MAX_UPLOAD_SIZE_BYTES:
            raise RuntimeError(
                f"The file is too large to send through this bot. "
                f"Maximum configured size: "
                f"{MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB."
            )

        await status_message.edit_text(
            "📤 Download complete. Uploading to Telegram..."
        )

        with file_path.open("rb") as media_file:
            if mode == "audio":
                await context.bot.send_audio(
                    chat_id=chat_id,
                    audio=media_file,
                    filename=file_path.name,
                )
            else:
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=media_file,
                    filename=file_path.name,
                    supports_streaming=True,
                )

        await status_message.delete()

    except Exception as error:
        print(f"Download error for user {user_id}: {error}")

        await status_message.edit_text(
            f"❌ Something went wrong:\n{error}"
        )

    finally:
        await asyncio.to_thread(
            cleanup_user_download,
            user_id,
        )

        context.user_data.pop("url", None)
        context.user_data.pop("mode", None)
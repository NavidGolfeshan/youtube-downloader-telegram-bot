"""Inline keyboards used by the manager bot."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def format_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🎵 MP3", callback_data="format:mp3"),
        InlineKeyboardButton("🎬 MP4", callback_data="format:mp4"),
    ]])


def mp3_quality_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("128 kbps", callback_data="quality:mp3:128"),
        InlineKeyboardButton("192 kbps", callback_data="quality:mp3:192"),
        InlineKeyboardButton("320 kbps", callback_data="quality:mp3:320"),
    ]])


def mp4_quality_keyboard(heights: list[int]) -> InlineKeyboardMarkup:
    preferred = [360, 480, 720, 1080, 1440, 2160]
    available = [height for height in preferred if height in heights]
    if not available:
        available = sorted(set(heights))[-6:] if heights else [720]

    buttons = [
        InlineKeyboardButton(f"{height}p", callback_data=f"quality:mp4:{height}")
        for height in available
    ]
    rows = [buttons[index:index + 3] for index in range(0, len(buttons), 3)]
    return InlineKeyboardMarkup(rows)


def delivery_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 ZIP archive (recommended)", callback_data="delivery:zip")],
        [InlineKeyboardButton("📄 Send files separately", callback_data="delivery:separate")],
    ])

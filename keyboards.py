from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def media_type_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                "🎵 MP3 Audio",
                callback_data="mode:audio"
            ),
            InlineKeyboardButton(
                "🎬 MP4 Video",
                callback_data="mode:video"
            ),
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


def video_quality_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Best", callback_data="quality:best"),
            InlineKeyboardButton("1080p", callback_data="quality:1080"),
        ],
        [
            InlineKeyboardButton("720p", callback_data="quality:720"),
            InlineKeyboardButton("480p", callback_data="quality:480"),
        ],
        [
            InlineKeyboardButton("360p", callback_data="quality:360"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)
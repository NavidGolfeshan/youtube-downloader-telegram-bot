from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import BOT_TOKEN
from handlers import (
    start,
    handle_url,
    handle_mode,
    handle_quality,
)


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    application.add_handler(
        CallbackQueryHandler(
            handle_mode,
            pattern=r"^mode:"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            handle_quality,
            pattern=r"^quality:"
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_url,
        )
    )

    print("Telegram downloader bot is running...")

    application.run_polling()


if __name__ == "__main__":
    main()
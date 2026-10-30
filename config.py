"""Configuration loaded from environment variables or a local .env file."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


def _integer(name: str, default: int) -> int:
    value = os.getenv(name, str(default)).strip()
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc


@dataclass(frozen=True)
class Settings:
    manager_bot_token: str = os.getenv("MANAGER_BOT_TOKEN", "").strip()
    mp3_bot_token: str = os.getenv("MP3_BOT_TOKEN", "").strip()
    mp4_bot_token: str = os.getenv("MP4_BOT_TOKEN", "").strip()
    cookie_file: str = os.getenv("COOKIE_FILE", "").strip()
    max_playlist_items: int = _integer("MAX_PLAYLIST_ITEMS", 0)
    log_level: str = os.getenv("LOG_LEVEL", "INFO").strip()

    def validate(self) -> None:
        missing = [
            name for name, value in (
                ("MANAGER_BOT_TOKEN", self.manager_bot_token),
                ("MP3_BOT_TOKEN", self.mp3_bot_token),
                ("MP4_BOT_TOKEN", self.mp4_bot_token),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                "Missing bot token(s): " + ", ".join(missing) +
                ". Copy .env.example to .env and fill in the values."
            )
        if self.max_playlist_items < 0:
            raise RuntimeError("MAX_PLAYLIST_ITEMS must be 0 or greater.")
        if self.cookie_file and not os.path.isfile(self.cookie_file):
            raise RuntimeError(
                f"COOKIE_FILE was set but the file does not exist: {self.cookie_file}"
            )


settings = Settings()

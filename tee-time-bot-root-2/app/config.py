import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _get_list(name: str, default: str = "*") -> list[str]:
    raw = os.getenv(name, default).strip()
    if not raw:
        return []
    if raw == "*":
        return ["*"]
    return [item.strip() for item in raw.split(",") if item.strip()]


class Settings:
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_WEBHOOK_SECRET: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    TELEGRAM_TIMEOUT_SEC: int = _get_int("TELEGRAM_TIMEOUT_SEC", 10)

    # Encryption
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/teebot.db")
    DB_PATH: str = DATABASE_URL.replace("sqlite:///", "")

    # Location
    HOME_LAT: float = float(os.getenv("HOME_LAT", "41.8781"))
    HOME_LNG: float = float(os.getenv("HOME_LNG", "-87.6298"))

    # Weather
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")

    # Scan intervals (minutes)
    SCAN_INTERVAL_STANDARD: int = _get_int("SCAN_INTERVAL_STANDARD", 10)
    SCAN_INTERVAL_MORNING: int = _get_int("SCAN_INTERVAL_MORNING", 5)
    SCAN_INTERVAL_SURGE: int = _get_int("SCAN_INTERVAL_SURGE", 3)
    SLOT_STALE_MINUTES: int = _get_int("SLOT_STALE_MINUTES", 30)
    ALERT_LOOKBACK_MINUTES: int = _get_int("ALERT_LOOKBACK_MINUTES", 30)

    # Scoring thresholds
    ALERT_THRESHOLD: int = _get_int("ALERT_THRESHOLD", 55)
    CONFIRM_THRESHOLD: int = _get_int("CONFIRM_THRESHOLD", 75)
    AUTOBOOK_THRESHOLD: int = _get_int("AUTOBOOK_THRESHOLD", 90)

    # Safety limits
    MAX_AUTOBOOKS_PER_DAY: int = _get_int("MAX_AUTOBOOKS_PER_DAY", 1)
    MAX_AUTOBOOKS_PER_WEEK: int = _get_int("MAX_AUTOBOOKS_PER_WEEK", 2)
    AUTOBOOK_COOLDOWN_HOURS: int = _get_int("AUTOBOOK_COOLDOWN_HOURS", 24)

    # App
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = _get_int("APP_PORT", 8000)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    APP_API_KEY: str = os.getenv("APP_API_KEY", "")
    USER_AUTH_REQUIRED: bool = _get_bool("USER_AUTH_REQUIRED", False)
    CORS_ORIGINS: list[str] = _get_list("CORS_ORIGINS", "*")
    ENABLE_SCHEDULER: bool = _get_bool("ENABLE_SCHEDULER", True)

    # Data directory
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", "data"))

    def __init__(self):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()

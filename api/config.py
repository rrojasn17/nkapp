import os


def _get_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "y", "on")


APP_ENV = os.getenv("APP_ENV", "local").strip().lower()
APP_DEBUG = _get_bool("APP_DEBUG", "true")

APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
APP_BASE_URL = os.getenv("APP_BASE_URL", f"http://localhost:{APP_PORT}")

CORS_ORIGINS_RAW = os.getenv("CORS_ORIGINS", "")
CORS_ORIGINS = [o.strip() for o in CORS_ORIGINS_RAW.split(",") if o.strip()]

SECRET_KEY = os.getenv("SECRET_KEY", "")
TTN_WEBHOOK_SECRET = os.getenv("TTN_WEBHOOK_SECRET", "")

IS_PROD = APP_ENV == "prod"

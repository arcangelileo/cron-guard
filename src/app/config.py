from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "CronGuard"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR / 'cronguard.db'}"

    # Auth
    secret_key: str = "change-me-in-production-use-a-real-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # SMTP (email alerts)
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_tls: bool = False
    smtp_from_email: str = "alerts@cronguard.dev"

    # App URL (for ping URLs displayed to users)
    base_url: str = "http://localhost:8000"

    model_config = {"env_prefix": "CRONGUARD_", "env_file": ".env", "extra": "ignore"}


settings = Settings()

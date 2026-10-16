"""
ARGUS — Application configuration.
All settings are loaded from environment variables via pydantic-settings.
No secrets are hardcoded here.
"""

from typing import Optional
from pydantic import field_validator, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=["../.env", ".env"],  # look in parent dir (project root) and current dir
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Application ---
    APP_ENV: str = "development"
    APP_NAME: str = "ARGUS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # --- Backend ---
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # --- Security ---
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # --- Database ---
    DATABASE_URL: str

    # --- Redis ---
    REDIS_URL: str = "redis://redis:6379/0"

    # --- CORS ---
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    # --- Rate Limiting ---
    LOGIN_RATE_LIMIT_ATTEMPTS: int = 5
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 300

    # --- AI Provider (optional) ---
    AI_PROVIDER: str = "none"  # "openai" | "anthropic" | "none"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    AI_MODEL: str = "gpt-4o-mini"

    # --- Threat Intelligence (optional) ---
    VIRUSTOTAL_API_KEY: Optional[str] = None
    ABUSEIPDB_API_KEY: Optional[str] = None

    # --- Seed Data ---
    SEED_DATABASE: bool = True
    SEED_ADMIN_EMAIL: str = "admin@argus.local"
    SEED_ADMIN_PASSWORD: str = "ChangeMe123!"

    @property
    def ai_enabled(self) -> bool:
        """Returns True if an AI provider is configured."""
        if self.AI_PROVIDER == "openai" and self.OPENAI_API_KEY:
            return True
        if self.AI_PROVIDER == "anthropic" and self.ANTHROPIC_API_KEY:
            return True
        return False

    @property
    def virustotal_enabled(self) -> bool:
        return bool(self.VIRUSTOTAL_API_KEY)

    @property
    def abuseipdb_enabled(self) -> bool:
        return bool(self.ABUSEIPDB_API_KEY)


settings = Settings()

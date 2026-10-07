import os
from typing import Any
from pydantic_settings import BaseSettings
from pydantic import model_validator
from functools import lru_cache


class Settings(BaseSettings):
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    DATABASE_URL: str = ""
    JWT_SECRET: str = "attendx-dev-secret-change-in-production-min32chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440
    FRONTEND_URL: str = "http://localhost:5173"
    ALLOWED_ORIGINS: str = ""

    # Account Activation & Security Tokens
    ACCOUNT_ACTIVATION_TOKEN_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 2

    # Email Service Configuration
    EMAIL_PROVIDER: str = "console"
    EMAIL_HOST: str = ""
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@attendx.edu"
    EMAIL_FROM_NAME: str = "AttendX Administration"
    EMAIL_USE_TLS: bool = True

    # Production Administrator Provisioning (Backend-only, never committed to git)
    ADMIN_ROOPIKA_PASSWORD: str = ""
    ADMIN_SRIKANTH_PASSWORD: str = ""
    ADMIN_1_PASSWORD: str = ""
    ADMIN_2_PASSWORD: str = ""

    # Module 8 — Observability & Request Timing Configuration
    SLOW_REQUEST_THRESHOLD_MS: float = 1000.0
    ENABLE_STRUCTURED_LOGGING: bool = True

    @model_validator(mode="before")
    @classmethod
    def resolve_email_env_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Resolve common SMTP_* environment variable aliases
            if not data.get("EMAIL_HOST") and data.get("SMTP_HOST"):
                data["EMAIL_HOST"] = data["SMTP_HOST"]
            if not data.get("EMAIL_PORT") and data.get("SMTP_PORT"):
                data["EMAIL_PORT"] = data["SMTP_PORT"]
            if not data.get("EMAIL_USERNAME") and (data.get("SMTP_USER") or data.get("SMTP_USERNAME")):
                data["EMAIL_USERNAME"] = data.get("SMTP_USER") or data.get("SMTP_USERNAME")
            if not data.get("EMAIL_PASSWORD") and (data.get("SMTP_PASSWORD") or data.get("SMTP_PASS")):
                data["EMAIL_PASSWORD"] = data.get("SMTP_PASSWORD") or data.get("SMTP_PASS")
            if not data.get("EMAIL_FROM") and data.get("SMTP_FROM"):
                data["EMAIL_FROM"] = data["SMTP_FROM"]
            # If SMTP_HOST is provided but EMAIL_PROVIDER was not specified, default to smtp
            if data.get("EMAIL_HOST") and not data.get("EMAIL_PROVIDER"):
                data["EMAIL_PROVIDER"] = "smtp"
        return data

    @model_validator(mode="after")
    def validate_production_secrets(self):
        # Sanitize FRONTEND_URL trailing slashes
        if self.FRONTEND_URL:
            self.FRONTEND_URL = self.FRONTEND_URL.strip().rstrip("/")

        is_production = os.getenv("RENDER") == "true" or os.getenv("ENVIRONMENT") == "production"
        if is_production:
            if (
                not self.JWT_SECRET
                or self.JWT_SECRET == "attendx-dev-secret-change-in-production-min32chars"
                or len(self.JWT_SECRET) < 32
            ):
                raise ValueError(
                    "Insecure default JWT_SECRET cannot be used in production. "
                    "Set JWT_SECRET environment variable to a secure key with at least 32 characters."
                )
        return self

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

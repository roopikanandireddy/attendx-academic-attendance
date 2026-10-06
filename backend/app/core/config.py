import os
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

    @model_validator(mode="after")
    def validate_production_secrets(self):
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

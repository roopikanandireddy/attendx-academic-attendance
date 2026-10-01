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

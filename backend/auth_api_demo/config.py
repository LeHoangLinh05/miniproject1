from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings class using pydantic-settings.
    Loads configurations from environment variables or a .env file.
    """

    DATABASE_URL: str = "sqlite:///./auth_demo.db"
    JWT_SECRET: str = (
        "super-secret-development-key-that-is-at-least-thirty-two-chars-long"
    )

    REDIS_URL: str | None = None
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @field_validator("DATABASE_URL", "JWT_SECRET", "REDIS_URL", mode="before")
    @classmethod
    def strip_quotes(cls, v: str | None) -> str | None:
        if isinstance(v, str):
            return v.strip().strip("'").strip('"')
        return v

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()

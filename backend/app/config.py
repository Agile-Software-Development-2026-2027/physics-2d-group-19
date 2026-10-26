from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Read from environment variables with the APP_ prefix, or from backend/.env."""

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env")

    data_dir: Path = Path("data")
    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()

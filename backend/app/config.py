"""
Charlie — Cognitive Operating System
Configuration module.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Default SQLite database path: Brain/backend/charlie.db
_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "charlie.db"
_DEFAULT_DB_URL = f"sqlite+aiosqlite:///{_DEFAULT_DB_PATH}"
_DEFAULT_DB_URL_SYNC = f"sqlite:///{_DEFAULT_DB_PATH}"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "Charlie — Cognitive Operating System"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Database — defaults to SQLite (no server required)
    DATABASE_URL: str = os.getenv("DATABASE_URL", _DEFAULT_DB_URL)
    DATABASE_URL_SYNC: str = os.getenv("DATABASE_URL_SYNC", _DEFAULT_DB_URL_SYNC)

    # Knowledge base path (PARA structure)
    KNOWLEDGE_BASE_PATH: str = os.getenv(
        "KNOWLEDGE_BASE_PATH",
        str(Path(__file__).resolve().parent.parent.parent / "knowledge"),
    )

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()

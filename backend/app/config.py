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

    # ── OpenAI / AI Cognitive Layer ──────────────────────────────────────────
    # Add your API key to backend/.env (never commit that file — it's in .gitignore)
    # Example: OPENAI_API_KEY=sk-...
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Model used for each cognitive level
    # L1 Classification — fast, cheap
    AI_MODEL_L1: str = os.getenv("AI_MODEL_L1", "gpt-4o-mini")
    # L2 Interpretation — balanced
    AI_MODEL_L2: str = os.getenv("AI_MODEL_L2", "gpt-4o-mini")
    # L3 Analysis — most capable
    AI_MODEL_L3: str = os.getenv("AI_MODEL_L3", "gpt-4o")

    # Maximum tokens per AI response
    AI_MAX_TOKENS_L1: int = int(os.getenv("AI_MAX_TOKENS_L1", "256"))
    AI_MAX_TOKENS_L2: int = int(os.getenv("AI_MAX_TOKENS_L2", "1024"))
    AI_MAX_TOKENS_L3: int = int(os.getenv("AI_MAX_TOKENS_L3", "2048"))

    # Temperature per level
    AI_TEMPERATURE_L1: float = float(os.getenv("AI_TEMPERATURE_L1", "0.1"))
    AI_TEMPERATURE_L2: float = float(os.getenv("AI_TEMPERATURE_L2", "0.4"))
    AI_TEMPERATURE_L3: float = float(os.getenv("AI_TEMPERATURE_L3", "0.7"))

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    @property
    def ai_enabled(self) -> bool:
        """Returns True if an OpenAI API key is configured."""
        return bool(self.OPENAI_API_KEY and self.OPENAI_API_KEY.startswith("sk-"))

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()

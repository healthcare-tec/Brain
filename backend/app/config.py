"""
Charlie — Cognitive Operating System
Configuration module.

The .env file is expected at the PROJECT ROOT (Brain/.env),
one level above the backend/ directory.

Resolution order:
  1. Environment variables already set in the shell (e.g. from start-local.sh)
  2. Brain/.env  (project root)
  3. Brain/backend/.env  (legacy fallback, kept for compatibility)
  4. Built-in defaults
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings

# ── Path resolution ───────────────────────────────────────────────────────────
# app/config.py  →  app/  →  backend/  →  Brain/  (project root)
_APP_DIR     = Path(__file__).resolve().parent          # Brain/backend/app/
_BACKEND_DIR = _APP_DIR.parent                          # Brain/backend/
_PROJECT_ROOT = _BACKEND_DIR.parent                     # Brain/

# .env search order: project root first, then backend/ as legacy fallback
_ENV_FILE_ROOT    = _PROJECT_ROOT / ".env"
_ENV_FILE_BACKEND = _BACKEND_DIR  / ".env"

# Pick whichever exists (root takes priority)
_ENV_FILE = str(_ENV_FILE_ROOT) if _ENV_FILE_ROOT.exists() else str(_ENV_FILE_BACKEND)

# ── Default SQLite paths ──────────────────────────────────────────────────────
_DEFAULT_DB_PATH     = _BACKEND_DIR / "charlie.db"
_DEFAULT_DB_URL      = f"sqlite+aiosqlite:///{_DEFAULT_DB_PATH}"
_DEFAULT_DB_URL_SYNC = f"sqlite:///{_DEFAULT_DB_PATH}"

# ── Default knowledge base path ───────────────────────────────────────────────
_DEFAULT_KNOWLEDGE_PATH = str(_PROJECT_ROOT / "knowledge")


class Settings(BaseSettings):
    """Application settings loaded from Brain/.env (project root)."""

    APP_NAME:    str = "Charlie — Cognitive Operating System"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Database — defaults to SQLite (no server required)
    DATABASE_URL:      str = os.getenv("DATABASE_URL",      _DEFAULT_DB_URL)
    DATABASE_URL_SYNC: str = os.getenv("DATABASE_URL_SYNC", _DEFAULT_DB_URL_SYNC)

    # Knowledge base path (PARA structure)
    KNOWLEDGE_BASE_PATH: str = os.getenv("KNOWLEDGE_BASE_PATH", _DEFAULT_KNOWLEDGE_PATH)

    # ── OpenAI / AI Cognitive Layer ──────────────────────────────────────────
    # Add your API key to Brain/.env (never commit — it's in .gitignore)
    # Example: OPENAI_API_KEY=sk-...
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Model used for each cognitive level
    AI_MODEL_L1: str = os.getenv("AI_MODEL_L1", "gpt-4o-mini")   # L1 Classification
    AI_MODEL_L2: str = os.getenv("AI_MODEL_L2", "gpt-4o-mini")   # L2 Interpretation
    AI_MODEL_L3: str = os.getenv("AI_MODEL_L3", "gpt-4o")        # L3 Analysis

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
        # Load from project root .env; fallback to backend/.env
        env_file = _ENV_FILE
        extra = "allow"


settings = Settings()

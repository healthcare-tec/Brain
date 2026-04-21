"""
Charlie — Cognitive Operating System
Configuration module.

The .env file is expected at the PROJECT ROOT (Brain/.env).
Resolution is done via __file__ so it works regardless of the
working directory from which uvicorn is launched.

Load order:
  1. Brain/.env  (project root — loaded explicitly with python-dotenv)
  2. Brain/backend/.env  (legacy fallback)
  3. Environment variables already set in the shell (override .env values)
  4. Built-in defaults
"""

import os
from pathlib import Path

# ── Path resolution (absolute, independent of CWD) ───────────────────────────
# config.py lives at:  Brain/backend/app/config.py
#   → parent           Brain/backend/app/
#   → parent.parent    Brain/backend/
#   → parent * 3       Brain/  (project root)
_APP_DIR      = Path(__file__).resolve().parent          # Brain/backend/app/
_BACKEND_DIR  = _APP_DIR.parent                          # Brain/backend/
_PROJECT_ROOT = _BACKEND_DIR.parent                      # Brain/

_ENV_ROOT    = _PROJECT_ROOT / ".env"
_ENV_BACKEND = _BACKEND_DIR  / ".env"

# ── Explicitly load .env with python-dotenv BEFORE pydantic-settings ─────────
# This ensures the values are in os.environ when Settings() is instantiated,
# regardless of the working directory or how uvicorn was launched.
try:
    from dotenv import load_dotenv  # python-dotenv
    if _ENV_ROOT.exists():
        load_dotenv(dotenv_path=str(_ENV_ROOT), override=False)
    elif _ENV_BACKEND.exists():
        load_dotenv(dotenv_path=str(_ENV_BACKEND), override=False)
except ImportError:
    # python-dotenv not installed — fall back to pydantic-settings env_file
    pass

# ── Pydantic-settings (reads from os.environ, which now includes .env) ───────
from pydantic_settings import BaseSettings  # noqa: E402

# ── Default SQLite paths ──────────────────────────────────────────────────────
_DEFAULT_DB_PATH     = _BACKEND_DIR / "charlie.db"
_DEFAULT_DB_URL      = f"sqlite+aiosqlite:///{_DEFAULT_DB_PATH}"
_DEFAULT_DB_URL_SYNC = f"sqlite:///{_DEFAULT_DB_PATH}"

# ── Default knowledge base path ───────────────────────────────────────────────
_DEFAULT_KNOWLEDGE_PATH = str(_PROJECT_ROOT / "knowledge")


class Settings(BaseSettings):
    """Application settings — reads from os.environ (populated by dotenv above)."""

    APP_NAME:    str = "Charlie — Cognitive Operating System"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database — defaults to SQLite (no server required)
    DATABASE_URL:      str = _DEFAULT_DB_URL
    DATABASE_URL_SYNC: str = _DEFAULT_DB_URL_SYNC

    # Knowledge base path (PARA structure)
    KNOWLEDGE_BASE_PATH: str = _DEFAULT_KNOWLEDGE_PATH

    # ── OpenAI / AI Cognitive Layer ──────────────────────────────────────────
    # Add your API key to Brain/.env (never commit — it's in .gitignore)
    # Example:  OPENAI_API_KEY=sk-...
    OPENAI_API_KEY: str = ""

    # Model used for each cognitive level
    AI_MODEL_L1: str = "gpt-4o-mini"   # L1 Classification
    AI_MODEL_L2: str = "gpt-4o-mini"   # L2 Interpretation
    AI_MODEL_L3: str = "gpt-4o"        # L3 Analysis

    # Maximum tokens per AI response
    AI_MAX_TOKENS_L1: int = 256
    AI_MAX_TOKENS_L2: int = 1024
    AI_MAX_TOKENS_L3: int = 2048

    # Temperature per level
    AI_TEMPERATURE_L1: float = 0.1
    AI_TEMPERATURE_L2: float = 0.4
    AI_TEMPERATURE_L3: float = 0.7

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    @property
    def ai_enabled(self) -> bool:
        """Returns True if an OpenAI API key is configured."""
        key = self.OPENAI_API_KEY or ""
        return bool(key and key.startswith("sk-"))

    class Config:
        # pydantic-settings will also read from env_file as a secondary source
        # Primary loading is done above via python-dotenv / load_dotenv()
        env_file = str(_ENV_ROOT) if _ENV_ROOT.exists() else str(_ENV_BACKEND)
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings()

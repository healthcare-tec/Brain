"""
Charlie — Cognitive Operating System
Configuration module.

The .env file is expected at the PROJECT ROOT (Brain/.env).

Load order (first found wins):
  1. /Brain/.env                   — absolute path (proot-distro / Docker)
  2. <project_root>/.env           — resolved via __file__ (portable)
  3. Brain/backend/.env            — legacy fallback
  4. Environment variables already in os.environ (always respected)
"""

import os
from pathlib import Path

# ── Candidate .env paths ──────────────────────────────────────────────────────
# config.py lives at:  <project>/backend/app/config.py
_APP_DIR      = Path(__file__).resolve().parent          # backend/app/
_BACKEND_DIR  = _APP_DIR.parent                          # backend/
_PROJECT_ROOT = _BACKEND_DIR.parent                      # project root (Brain/)

_ENV_CANDIDATES = [
    Path("/Brain/.env"),                    # absolute — proot-distro / Docker
    _PROJECT_ROOT / ".env",                 # relative to __file__
    _BACKEND_DIR  / ".env",                 # legacy backend/.env
]

# ── Load .env with python-dotenv BEFORE pydantic-settings ────────────────────
# We load ALL candidate files (override=False so the first found wins and
# existing os.environ values are never overwritten).
try:
    from dotenv import load_dotenv, dotenv_values

    _loaded_env_path: str | None = None
    for _candidate in _ENV_CANDIDATES:
        if _candidate.exists():
            load_dotenv(dotenv_path=str(_candidate), override=False)
            _loaded_env_path = str(_candidate)
            break  # stop at first found

except ImportError:
    _loaded_env_path = None  # python-dotenv not installed; rely on pydantic-settings

# ── Pydantic-settings ─────────────────────────────────────────────────────────
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
    AI_MODEL_L1: str = "gpt-4.1-nano"   # L1 Classification (fast, cheap)
    AI_MODEL_L2: str = "gpt-4.1-mini"   # L2 Interpretation
    AI_MODEL_L3: str = "gpt-4.1-mini"   # L3 Analysis
    OPENAI_MODEL: str = "gpt-4.1-mini"  # Legacy fallback for older code

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
        key = (self.OPENAI_API_KEY or "").strip()
        return bool(key and len(key) > 8)

    class Config:
        # pydantic-settings secondary source: first existing candidate
        env_file = next(
            (str(p) for p in _ENV_CANDIDATES if p.exists()),
            str(_ENV_CANDIDATES[1]),  # default to project root path
        )
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings()

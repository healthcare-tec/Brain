"""
Charlie — Cognitive Operating System
Configuration module.

The .env file is expected at the PROJECT ROOT (Brain/.env).

Load order (first found wins):
  1. /Brain/.env                   — absolute path (proot-distro / Docker)
  2. <project_root>/.env           — resolved via __file__ (portable)
  3. Brain/backend/.env            — legacy fallback
  4. Environment variables already in os.environ (always respected)

AI Provider:
  Set AI_PROVIDER=ollama  (default) to use a local Ollama instance.
  Set AI_PROVIDER=openai          to use the OpenAI API directly.

  Ollama:  http://localhost:11434/v1  (OpenAI-compatible endpoint)
  OpenAI:  https://api.openai.com/v1
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
    from dotenv import load_dotenv

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

    # ── AI Provider selection ────────────────────────────────────────────────
    # "ollama"  → local Ollama instance (default, no API key required)
    # "openai"  → OpenAI API (requires OPENAI_API_KEY)
    AI_PROVIDER: str = "ollama"

    # ── Ollama configuration ─────────────────────────────────────────────────
    # Ollama exposes an OpenAI-compatible API at /v1
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL:    str = "gemma3:27b"   # default model for all levels

    # Per-level Ollama model overrides (fall back to OLLAMA_MODEL if empty)
    OLLAMA_MODEL_L1: str = ""   # e.g. "gemma3:4b" for faster classification
    OLLAMA_MODEL_L2: str = ""   # e.g. "gemma3:27b" for interpretation
    OLLAMA_MODEL_L3: str = ""   # e.g. "gemma3:27b" for analysis

    # ── OpenAI configuration ─────────────────────────────────────────────────
    # Add your API key to Brain/.env (never commit — it's in .gitignore)
    # Example:  OPENAI_API_KEY=sk-...
    OPENAI_API_KEY:  str = ""
    OPENAI_BASE_URL: str = ""   # leave empty to use the default OpenAI endpoint

    # Per-level OpenAI model overrides
    AI_MODEL_L1: str = "gpt-4o-mini"   # L1 Classification (fast, cheap)
    AI_MODEL_L2: str = "gpt-4o-mini"   # L2 Interpretation
    AI_MODEL_L3: str = "gpt-4o"        # L3 Analysis
    OPENAI_MODEL: str = "gpt-4o-mini"  # Legacy fallback for older code

    # ── AI Parameters (shared across providers) ──────────────────────────────
    AI_MAX_TOKENS_L1: int = 512
    AI_MAX_TOKENS_L2: int = 2048
    AI_MAX_TOKENS_L3: int = 4096

    AI_TEMPERATURE_L1: float = 0.1
    AI_TEMPERATURE_L2: float = 0.4
    AI_TEMPERATURE_L3: float = 0.7

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    @property
    def ai_enabled(self) -> bool:
        """Returns True if a working AI provider is configured."""
        provider = (os.environ.get("AI_PROVIDER") or self.AI_PROVIDER).lower().strip()
        if provider == "ollama":
            # Ollama is always considered enabled (no key required)
            return True
        # OpenAI — requires a non-trivial key
        key = os.environ.get("OPENAI_API_KEY") or self.OPENAI_API_KEY or ""
        return bool(key.strip() and len(key.strip()) > 8)

    class Config:
        # pydantic-settings secondary source: first existing candidate
        env_file = next(
            (str(p) for p in _ENV_CANDIDATES if p.exists()),
            str(_ENV_CANDIDATES[1]),  # default to project root path
        )
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings()


# ── Provider helper — used by all AI modules ─────────────────────────────────

def get_ai_client_params(level: str = "L1") -> dict:
    """
    Return a dict with {api_key, base_url, model} for the active AI provider.

    level: "L1" | "L2" | "L3"

    Usage:
        params = get_ai_client_params("L1")
        client = AsyncOpenAI(api_key=params["api_key"], base_url=params["base_url"])
        response = await client.chat.completions.create(model=params["model"], ...)
    """
    provider = (os.environ.get("AI_PROVIDER") or settings.AI_PROVIDER).lower().strip()

    if provider == "ollama":
        base_url = (
            os.environ.get("OLLAMA_BASE_URL")
            or settings.OLLAMA_BASE_URL
            or "http://localhost:11434/v1"
        )
        # Per-level model: env var OLLAMA_MODEL_L1 / L2 / L3 → OLLAMA_MODEL fallback
        level_env = os.environ.get(f"OLLAMA_MODEL_{level}")
        level_setting = getattr(settings, f"OLLAMA_MODEL_{level}", "")
        default_model = os.environ.get("OLLAMA_MODEL") or settings.OLLAMA_MODEL
        model = level_env or level_setting or default_model
        return {
            "api_key": "ollama",   # Ollama ignores the key but the SDK requires it
            "base_url": base_url,
            "model": model,
            "provider": "ollama",
        }

    # OpenAI (or any OpenAI-compatible endpoint)
    api_key = os.environ.get("OPENAI_API_KEY") or settings.OPENAI_API_KEY
    base_url = os.environ.get("OPENAI_BASE_URL") or settings.OPENAI_BASE_URL or None
    level_env = os.environ.get(f"AI_MODEL_{level}")
    level_setting = getattr(settings, f"AI_MODEL_{level}", "gpt-4o-mini")
    model = level_env or level_setting
    return {
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
        "provider": "openai",
    }

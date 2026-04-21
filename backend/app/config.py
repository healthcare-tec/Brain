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
    # OLLAMA_MODEL has NO hardcoded default — must be set in .env.
    # get_ai_client_params() reads os.environ directly to avoid pydantic
    # Settings being frozen at import time before .env is fully loaded.
    OLLAMA_MODEL:    str = ""

    # Per-level Ollama model overrides (fall back to OLLAMA_MODEL if empty)
    OLLAMA_MODEL_L1: str = ""   # e.g. "gemma3:4b" for faster classification
    OLLAMA_MODEL_L2: str = ""   # e.g. "gemma3:270m" for interpretation
    OLLAMA_MODEL_L3: str = ""   # e.g. "gemma3:270m" for analysis

    # Timeout in seconds for Ollama API calls.
    # Large models (e.g. gemma3:270b) can take several minutes to respond.
    # Default: 300s (5 minutes). Set to 0 to disable timeout.
    OLLAMA_TIMEOUT: int = 300

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

    IMPORTANT: All values are read from os.environ FIRST to avoid the pydantic
    Settings being frozen at import time before load_dotenv has run.
    Settings values are used only as a last resort.

    Usage:
        params = get_ai_client_params("L1")
        client = AsyncOpenAI(api_key=params["api_key"], base_url=params["base_url"])
        response = await client.chat.completions.create(model=params["model"], ...)
    """
    # Always read AI_PROVIDER from os.environ first (never from frozen Settings)
    provider = (
        os.environ.get("AI_PROVIDER")
        or settings.AI_PROVIDER
        or "ollama"
    ).lower().strip()

    if provider == "ollama":
        base_url = (
            os.environ.get("OLLAMA_BASE_URL")
            or settings.OLLAMA_BASE_URL
            or "http://localhost:11434/v1"
        )

        # Resolution order for model (all via os.environ to avoid stale Settings):
        #   1. OLLAMA_MODEL_L1 / OLLAMA_MODEL_L2 / OLLAMA_MODEL_L3  (per-level override)
        #   2. OLLAMA_MODEL                                          (global model)
        #   3. settings.OLLAMA_MODEL_Lx / settings.OLLAMA_MODEL     (pydantic fallback)
        #   4. Empty string → caller must handle gracefully
        level_from_env     = os.environ.get(f"OLLAMA_MODEL_{level}", "").strip()
        default_from_env   = os.environ.get("OLLAMA_MODEL", "").strip()
        level_from_setting = (getattr(settings, f"OLLAMA_MODEL_{level}", "") or "").strip()
        default_from_setting = (settings.OLLAMA_MODEL or "").strip()

        model = (
            level_from_env
            or default_from_env
            or level_from_setting
            or default_from_setting
            or ""   # no hardcoded fallback — user must set OLLAMA_MODEL in .env
        )

        # Timeout: read from env first (avoids stale Settings), then Settings, then default
        try:
            timeout = int(os.environ.get("OLLAMA_TIMEOUT", "") or settings.OLLAMA_TIMEOUT or 300)
        except (ValueError, TypeError):
            timeout = 300

        return {
            "api_key": "ollama",   # Ollama ignores the key but the SDK requires it
            "base_url": base_url,
            "model": model,
            "provider": "ollama",
            "timeout": timeout,
        }

    # OpenAI (or any OpenAI-compatible endpoint)
    # Read api_key from os.environ first — Settings may be stale
    api_key = (
        os.environ.get("OPENAI_API_KEY", "").strip()
        or settings.OPENAI_API_KEY
        or ""
    )
    base_url = (
        os.environ.get("OPENAI_BASE_URL", "").strip()
        or settings.OPENAI_BASE_URL
        or None
    )
    level_from_env     = os.environ.get(f"AI_MODEL_{level}", "").strip()
    level_from_setting = (getattr(settings, f"AI_MODEL_{level}", "") or "").strip()
    model = level_from_env or level_from_setting or "gpt-4o-mini"

    return {
        "api_key": api_key,
        "base_url": base_url or None,
        "model": model,
        "provider": "openai",
    }

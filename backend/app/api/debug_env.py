"""
Charlie — Debug endpoint (temporary)
GET /api/debug/env — diagnose .env loading and OPENAI_API_KEY detection.
Remove this file after confirming the AI is working.
"""

import os
from pathlib import Path
from fastapi import APIRouter

router = APIRouter()


@router.get("/env")
async def debug_env():
    """
    Diagnostic endpoint — returns .env loading details.
    REMOVE after confirming AI works.
    """
    # Candidate paths (same logic as config.py)
    app_dir      = Path(__file__).resolve().parent.parent  # backend/app/ → backend/
    project_root = app_dir.parent                          # backend/ → Brain/

    candidates = [
        Path("/Brain/.env"),
        project_root / ".env",
        app_dir / ".env",
    ]

    env_files_status = {}
    for c in candidates:
        env_files_status[str(c)] = {
            "exists": c.exists(),
            "has_openai_key": False,
        }
        if c.exists():
            try:
                content = c.read_text(encoding="utf-8", errors="replace")
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith("OPENAI_API_KEY"):
                        env_files_status[str(c)]["has_openai_key"] = True
                        # Show first 8 chars of value (masked)
                        if "=" in line:
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            env_files_status[str(c)]["key_preview"] = val[:8] + "..." if len(val) > 8 else "(too short)"
                        break
            except Exception as e:
                env_files_status[str(c)]["read_error"] = str(e)

    raw_key = os.environ.get("OPENAI_API_KEY", "")
    from app.config import settings, _loaded_env_path  # type: ignore

    return {
        "working_directory": os.getcwd(),
        "python_file": str(Path(__file__).resolve()),
        "project_root_detected": str(project_root),
        "env_file_loaded_by_dotenv": _loaded_env_path,
        "OPENAI_API_KEY_in_os_environ": bool(raw_key),
        "OPENAI_API_KEY_preview": (raw_key[:8] + "...") if len(raw_key) > 8 else "(empty or too short)",
        "settings_ai_enabled": settings.ai_enabled,
        "settings_OPENAI_API_KEY_len": len(settings.OPENAI_API_KEY),
        "env_files": env_files_status,
    }

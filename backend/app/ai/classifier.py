"""
Charlie — AI Cognitive Layer
Level 1: Classification

Classifies raw input into actionable categories using GPT.
Fast, low-cost, deterministic (temperature=0.1).

Categories:
  - task      → single actionable item with a clear next action
  - project   → multi-step outcome requiring more than one action
  - note      → reference information, no action required
  - idea      → creative or exploratory thought, not yet actionable
  - trash     → noise, duplicate, or irrelevant content

If OPENAI_API_KEY is not set, falls back to heuristic classification.
"""

import json
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"task", "project", "note", "idea", "trash"}
VALID_PRIORITIES = {"low", "medium", "high", "critical"}
VALID_CONTEXTS = {
    "@work", "@home", "@computer", "@phone",
    "@errands", "@waiting", "@anywhere", None,
}

SYSTEM_PROMPT = """You are Charlie's Classification Engine (Level 1).

Classify a raw inbox item into exactly one category and extract basic metadata.
Respond with valid JSON only — no explanation, no markdown fences.

Categories:
- "task"    → a single, concrete, actionable item (done in one session)
- "project" → a multi-step outcome requiring more than one action
- "note"    → reference information or knowledge (no action required)
- "idea"    → creative or exploratory thought, not yet actionable
- "trash"   → noise, duplicate, unclear, or irrelevant content

Response schema (JSON only):
{
  "category": "task|project|note|idea|trash",
  "confidence": 0.0-1.0,
  "suggested_title": "concise title (max 80 chars)",
  "suggested_context": "@work|@home|@computer|@phone|@errands|@waiting|@anywhere|null",
  "suggested_priority": "low|medium|high|critical",
  "is_time_sensitive": true|false,
  "estimated_minutes": null or integer,
  "reasoning": "one sentence explaining the classification"
}"""


def _stub_classify(content: str, reason: str = "AI not configured") -> dict:
    """Heuristic fallback when AI is not configured or unavailable."""
    content_lower = content.lower()

    if any(w in content_lower for w in [
        "buy", "call", "send", "write", "fix", "update", "review", "check",
        "fazer", "comprar", "ligar", "enviar", "corrigir", "atualizar",
    ]):
        category, priority = "task", "medium"
    elif any(w in content_lower for w in [
        "project", "plan", "build", "create", "launch", "develop",
        "projeto", "plano", "criar", "desenvolver",
    ]):
        category, priority = "project", "medium"
    elif any(w in content_lower for w in [
        "idea", "what if", "maybe", "could", "imagine",
        "ideia", "e se", "talvez", "poderia",
    ]):
        category, priority = "idea", "low"
    elif len(content.split()) < 4:
        category, priority = "trash", "low"
    else:
        category, priority = "note", "low"

    return {
        "category": category,
        "confidence": 0.6,
        "suggested_title": content[:80],
        "suggested_context": None,
        "suggested_priority": priority,
        "is_time_sensitive": False,
        "estimated_minutes": None,
        "reasoning": f"Heuristic classification ({reason})",
        "ai_enabled": False,
    }


async def classify_input(content: str, context: Optional[str] = None) -> dict:
    """
    Classify an inbox item using GPT L1.
    """
    import os
    api_key = os.environ.get("OPENAI_API_KEY") or settings.OPENAI_API_KEY
    ai_enabled = bool(api_key and len(api_key) > 8)

    if not ai_enabled:
        logger.debug("AI not configured — using heuristic classification")
        return _stub_classify(content, reason="add OPENAI_API_KEY to .env (project root)")

    try:
        from openai import AsyncOpenAI

        # Support proxied endpoints (e.g. Manus sandbox) via OPENAI_BASE_URL env var
        base_url = os.environ.get("OPENAI_BASE_URL") or None
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        user_message = content
        if context:
            user_message = f"Context: {context}\n\nItem: {content}"

        # Append JSON instruction to system prompt (some models ignore response_format)
        system_with_json = SYSTEM_PROMPT + "\n\nIMPORTANT: Respond with valid JSON only, no markdown."

        model = os.environ.get("AI_MODEL_L1") or settings.AI_MODEL_L1

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_with_json},
                {"role": "user", "content": user_message},
            ],
            max_tokens=settings.AI_MAX_TOKENS_L1,
            temperature=settings.AI_TEMPERATURE_L1,
        )

        raw = response.choices[0].message.content
        result = json.loads(raw)

        # Validate and sanitize
        if result.get("category") not in VALID_CATEGORIES:
            result["category"] = "note"
        if result.get("suggested_priority") not in VALID_PRIORITIES:
            result["suggested_priority"] = "medium"
        if result.get("suggested_context") not in VALID_CONTEXTS:
            result["suggested_context"] = None

        result["ai_enabled"] = True
        result["model"] = model
        return result

    except ImportError:
        logger.warning("openai package not installed — using heuristic classification")
        return _stub_classify(content, reason="openai package not installed")
    except Exception as exc:
        # Key is configured but the API call failed — return heuristic result
        # but with ai_enabled=True and the real error message so the frontend
        # can show the actual problem instead of 'not configured'
        logger.error("AI classification failed (key is set, API call failed): %s", exc)
        result = _stub_classify(content, reason=f"API call failed: {str(exc)[:120]}")
        result["ai_enabled"] = True   # key IS configured — error is in the call
        result["ai_error"] = str(exc)
        return result

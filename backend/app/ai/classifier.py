"""
Charlie — AI Cognitive Layer
Level 1: Classification

Classifies raw input into actionable categories.
Fast, low-cost, deterministic (temperature=0.1).

Supports two AI providers (configured via AI_PROVIDER in .env):
  - ollama  (default) — local Ollama instance, e.g. gemma3:270m
  - openai            — OpenAI API, e.g. gpt-4o-mini

Falls back to heuristic classification if AI is unavailable.

Categories:
  - task      → single actionable item with a clear next action
  - project   → multi-step outcome requiring more than one action
  - note      → reference information, no action required
  - idea      → creative or exploratory thought, not yet actionable
  - trash     → noise, duplicate, or irrelevant content
"""

import json
import logging
from typing import Optional

from app.config import settings, get_ai_client_params

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
    Classify an inbox item using the configured AI provider (L1).

    Uses Ollama by default (AI_PROVIDER=ollama in .env).
    Falls back to heuristic classification on any error.
    """
    params = get_ai_client_params("L1")
    provider = params["provider"]

    # For OpenAI, verify the key is present
    if provider == "openai":
        api_key = params["api_key"]
        if not api_key or len(api_key.strip()) <= 8:
            logger.debug("OpenAI key not configured — using heuristic classification")
            return _stub_classify(content, reason="add OPENAI_API_KEY to .env")

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=params["api_key"],
            base_url=params["base_url"],
        )

        user_message = content
        if context:
            user_message = f"Context: {context}\n\nItem: {content}"

        # Append JSON instruction — some models (especially local ones) need this
        system_with_json = SYSTEM_PROMPT + "\n\nIMPORTANT: Respond with valid JSON only, no markdown fences, no extra text."

        model = params["model"]
        logger.debug("Classifying with provider=%s model=%s", provider, model)

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

        # Strip markdown fences if the model added them anyway
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

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
        result["provider"] = provider
        return result

    except ImportError:
        logger.warning("openai package not installed — using heuristic classification")
        return _stub_classify(content, reason="openai package not installed")
    except Exception as exc:
        # Provider is configured but the call failed — return heuristic result
        # with ai_enabled=True and the real error so the frontend can show it
        logger.error("AI classification failed (provider=%s): %s", provider, exc)
        result = _stub_classify(content, reason=f"API call failed: {str(exc)[:120]}")
        result["ai_enabled"] = True   # provider IS configured — error is in the call
        result["ai_error"] = str(exc)
        result["provider"] = provider
        return result

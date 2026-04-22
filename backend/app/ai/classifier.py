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

import logging
from typing import Optional

from app.config import settings, get_ai_client_params
from app.ai.json_parser import parse_ai_json, is_template_response

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"task", "project", "note", "idea", "trash"}
VALID_PRIORITIES = {"low", "medium", "high", "critical"}
VALID_CONTEXTS = {
    "@work", "@home", "@computer", "@phone",
    "@errands", "@waiting", "@anywhere", None,
}

# ── Prompt designed for local LLMs (gemma3, llama, mistral, etc.) ─────────────
# Key principles for local model prompts:
#   1. Show a concrete input→output example — models learn by example
#   2. Never put pipe-separated options as the value in the schema
#      (models echo them literally instead of choosing one)
#   3. Keep the schema small — fewer fields = fewer mistakes
#   4. Put the user input LAST in the message, after all instructions
#   5. Use "assistant:" priming trick to force JSON-first output

SYSTEM_PROMPT = """You are a productivity assistant. Classify the user's inbox item.

Return ONLY a JSON object. No explanation. No markdown. No extra text.

Valid values:
- category: task, project, note, idea, or trash
- confidence: number from 0.0 to 1.0
- suggested_title: short title under 80 characters
- suggested_context: one of @work @home @computer @phone @errands @waiting @anywhere
- suggested_priority: low, medium, high, or critical
- is_time_sensitive: true or false
- estimated_minutes: a number or null
- reasoning: one short sentence

Example input: "Call dentist to schedule appointment"
Example output:
{"category":"task","confidence":0.95,"suggested_title":"Call dentist to schedule appointment","suggested_context":"@phone","suggested_priority":"medium","is_time_sensitive":false,"estimated_minutes":5,"reasoning":"Single concrete action requiring a phone call."}

Now classify the following item and return ONLY the JSON object:"""


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
            timeout=params.get("timeout", 60),
        )

        # Build the user message — item goes AFTER all instructions
        user_message = content
        if context:
            user_message = f"[Context: {context}]\n{content}"

        model = params["model"]
        logger.debug("Classifying with provider=%s model=%s", provider, model)

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            max_tokens=settings.AI_MAX_TOKENS_L1,
            temperature=settings.AI_TEMPERATURE_L1,
        )

        raw = response.choices[0].message.content
        logger.debug("Raw AI response (classifier): %r", raw[:400] if raw else "<empty>")

        # Detect if the model echoed the template instead of filling it in
        if is_template_response(raw):
            logger.warning(
                "classifier: model echoed the prompt template — falling back to heuristic. "
                "Consider using a larger/different model. Preview: %r", raw[:120]
            )
            result = _stub_classify(content, reason="model echoed template (try a larger model)")
            result["ai_enabled"] = True
            result["ai_error"] = "Model returned template instead of real classification"
            result["provider"] = provider
            return result

        result = parse_ai_json(raw)

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

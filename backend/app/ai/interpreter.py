"""
Charlie — AI Cognitive Layer
Level 2: Interpretation

Provides deeper understanding of tasks, notes, and decisions.
Extracts next actions, dependencies, risks, and context.
Balanced model, moderate temperature.

Supports two AI providers (configured via AI_PROVIDER in .env):
  - ollama  (default) — local Ollama instance, e.g. gemma3:270m
  - openai            — OpenAI API, e.g. gpt-4o-mini

Falls back to structured stub response if AI is unavailable.
"""

import logging
from typing import Optional

from app.config import settings, get_ai_client_params
from app.ai.json_parser import parse_ai_json

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TASK = """You are Charlie's Interpretation Engine (Level 2).

Analyze a task and extract actionable intelligence.
Respond with valid JSON only — no explanation, no markdown fences.

Response schema:
{
  "next_physical_action": "the very next concrete physical action to take",
  "why_it_matters": "one sentence on why this task is important",
  "dependencies": ["list of things needed before starting"],
  "potential_blockers": ["list of things that could prevent completion"],
  "suggested_context": "@work|@home|@computer|@phone|@errands|@waiting|@anywhere",
  "estimated_minutes": integer or null,
  "energy_required": "low|medium|high",
  "can_delegate": true|false,
  "delegate_to": "who could do this, or null",
  "related_areas": ["life areas this touches: work, health, finance, relationships, etc."],
  "tags": ["relevant tags"],
  "notes": "any additional observations"
}"""

SYSTEM_PROMPT_NOTE = """You are Charlie's Interpretation Engine (Level 2).

Analyze a note or piece of knowledge and extract its essence.
Respond with valid JSON only — no explanation, no markdown fences.

Response schema:
{
  "summary": "2-3 sentence summary of the key insight",
  "key_concepts": ["main concepts or ideas"],
  "actionable_insights": ["things you could do based on this knowledge"],
  "related_topics": ["related areas or subjects"],
  "para_category": "projects|areas|resources|archive",
  "para_reasoning": "why this belongs in that PARA category",
  "tags": ["relevant tags"],
  "questions_raised": ["questions this note raises that deserve exploration"]
}"""

SYSTEM_PROMPT_DECISION = """You are Charlie's Interpretation Engine (Level 2).

Analyze a decision or problem and provide structured thinking support.
Respond with valid JSON only — no explanation, no markdown fences.

Response schema:
{
  "problem_restatement": "restate the problem clearly in one sentence",
  "key_assumptions": ["assumptions being made"],
  "options": [
    {
      "option": "description",
      "pros": ["advantages"],
      "cons": ["disadvantages"],
      "risk_level": "low|medium|high"
    }
  ],
  "recommended_option": "which option and why (brief)",
  "reversibility": "reversible|partially-reversible|irreversible",
  "urgency": "low|medium|high|critical",
  "information_gaps": ["what you don't know that would help decide"],
  "second_order_effects": ["consequences of consequences"]
}"""


def _stub_interpret(content: str, interpret_type: str = "task") -> dict:
    """Heuristic fallback when AI is not configured."""
    if interpret_type == "note":
        return {
            "summary": f"Note: {content[:200]}",
            "key_concepts": [],
            "actionable_insights": [],
            "related_topics": [],
            "para_category": "resources",
            "para_reasoning": "Default classification (AI not configured)",
            "tags": [],
            "questions_raised": [],
            "ai_enabled": False,
        }
    elif interpret_type == "decision":
        return {
            "problem_restatement": content[:200],
            "key_assumptions": [],
            "options": [],
            "recommended_option": "Gather more information before deciding",
            "reversibility": "unknown",
            "urgency": "medium",
            "information_gaps": ["AI not configured — configure AI_PROVIDER in .env"],
            "second_order_effects": [],
            "ai_enabled": False,
        }
    else:
        return {
            "next_physical_action": f"Review: {content[:100]}",
            "why_it_matters": "Not analyzed (AI not configured)",
            "dependencies": [],
            "potential_blockers": [],
            "suggested_context": "@anywhere",
            "estimated_minutes": None,
            "energy_required": "medium",
            "can_delegate": False,
            "delegate_to": None,
            "related_areas": [],
            "tags": [],
            "notes": "Configure AI_PROVIDER in .env to enable AI interpretation",
            "ai_enabled": False,
        }


async def interpret_context(
    query: str,
    context: Optional[dict] = None,
) -> dict:
    """
    Legacy interface — interprets a query with optional context dict.
    Delegates to interpret_content with type 'task'.
    """
    extra = None
    if context:
        extra = str(context)
    return await interpret_content(query, interpret_type="task", extra_context=extra)


async def interpret_content(
    content: str,
    interpret_type: str = "task",
    extra_context: Optional[str] = None,
) -> dict:
    """
    Interpret content using the configured AI provider (L2).
    """
    params = get_ai_client_params("L2")
    provider = params["provider"]

    # For OpenAI, verify the key is present
    if provider == "openai":
        api_key = params["api_key"]
        if not api_key or len(api_key.strip()) <= 8:
            logger.debug("OpenAI key not configured — using stub interpretation")
            return _stub_interpret(content, interpret_type)

    system_prompts = {
        "task": SYSTEM_PROMPT_TASK,
        "note": SYSTEM_PROMPT_NOTE,
        "decision": SYSTEM_PROMPT_DECISION,
    }
    system_prompt = system_prompts.get(interpret_type, SYSTEM_PROMPT_TASK)
    system_with_json = system_prompt + "\n\nIMPORTANT: Respond with valid JSON only, no markdown fences, no extra text."

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=params["api_key"],
            base_url=params["base_url"],
            timeout=params.get("timeout", 60),
        )

        user_message = content
        if extra_context:
            user_message = f"Context: {extra_context}\n\nContent: {content}"

        model = params["model"]
        logger.debug("Interpreting with provider=%s model=%s", provider, model)

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_with_json},
                {"role": "user", "content": user_message},
            ],
            max_tokens=settings.AI_MAX_TOKENS_L2,
            temperature=settings.AI_TEMPERATURE_L2,
        )

        raw = response.choices[0].message.content
        logger.debug("Raw AI response (interpreter): %r", raw[:300] if raw else "<empty>")

        result = parse_ai_json(raw)
        result["ai_enabled"] = True
        result["model"] = model
        result["provider"] = provider
        result["interpret_type"] = interpret_type
        return result

    except ImportError:
        logger.warning("openai package not installed — using stub interpretation")
        return _stub_interpret(content, interpret_type)
    except Exception as exc:
        logger.error("AI interpretation failed (provider=%s): %s", provider, exc)
        result = _stub_interpret(content, interpret_type)
        result["ai_enabled"] = True
        result["ai_error"] = str(exc)
        result["provider"] = provider
        return result

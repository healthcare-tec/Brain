"""
Charlie — AI Cognitive Layer
Level 3: Analysis

Detects patterns, behavioral trends, and generates strategic insights
from aggregated task events, completion data, and decision logs.

Most capable model, higher temperature for creative synthesis.

If OPENAI_API_KEY is not set, returns structured stub response.
"""

import json
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_PATTERNS = """You are Charlie's Analysis Engine (Level 3).

You receive aggregated data about a person's tasks, completions, and decisions
over a time period. Your job is to detect behavioral patterns and provide
strategic, actionable insights.

Respond with valid JSON only — no explanation, no markdown fences.

Response schema:
{
  "patterns": [
    {
      "pattern": "description of the pattern",
      "evidence": "what data supports this",
      "impact": "positive|negative|neutral",
      "significance": "low|medium|high"
    }
  ],
  "strengths": ["things the person is doing well"],
  "improvement_areas": ["areas that need attention"],
  "estimation_accuracy": {
    "assessment": "overestimates|underestimates|accurate|insufficient_data",
    "average_error_percent": null or number,
    "recommendation": "one actionable suggestion"
  },
  "bottlenecks": ["recurring blockers or friction points"],
  "energy_patterns": "observations about when/how energy is used",
  "focus_score": 0-100,
  "focus_assessment": "brief assessment of focus quality",
  "top_recommendations": [
    {
      "recommendation": "specific, actionable recommendation",
      "priority": "low|medium|high",
      "expected_impact": "what will improve"
    }
  ],
  "weekly_theme": "one-sentence theme or insight for this period"
}"""

SYSTEM_PROMPT_REVIEW = """You are Charlie's Analysis Engine (Level 3).

Generate a thoughtful weekly review based on the provided data.
Be honest, specific, and constructive. Focus on learning and improvement.

Respond with valid JSON only — no explanation, no markdown fences.

Response schema:
{
  "headline": "one sentence capturing the essence of this week",
  "wins": ["notable accomplishments or positive outcomes"],
  "lessons": ["what was learned this week"],
  "incomplete_items": "honest assessment of what was left undone and why",
  "energy_assessment": "how energy was managed this week",
  "focus_quality": "assessment of focus and deep work",
  "next_week_priorities": ["top 3-5 priorities for next week"],
  "one_thing_to_stop": "one habit or behavior to stop",
  "one_thing_to_start": "one new habit or behavior to start",
  "reflection_question": "a deep question to sit with this week"
}"""


def _stub_patterns(timeframe_days: int = 30) -> dict:
    """Stub fallback when AI is not configured."""
    return {
        "timeframe_days": timeframe_days,
        "patterns": [],
        "strengths": [],
        "improvement_areas": [],
        "estimation_accuracy": {
            "assessment": "insufficient_data",
            "average_error_percent": None,
            "recommendation": "Add OPENAI_API_KEY to backend/.env to enable AI analysis",
        },
        "bottlenecks": [],
        "energy_patterns": "AI not configured",
        "focus_score": 0,
        "focus_assessment": "AI not configured — add OPENAI_API_KEY to backend/.env",
        "top_recommendations": [],
        "weekly_theme": "Configure AI to unlock pattern analysis",
        "ai_enabled": False,
    }


async def detect_patterns(
    timeframe_days: int = 30,
    task_data: Optional[dict] = None,
) -> dict:
    """
    Detect behavioral patterns using GPT L3.

    Args:
        timeframe_days: Number of days to analyze.
        task_data: Optional pre-aggregated task/event data dict.

    Returns:
        dict with patterns, insights, and recommendations.
    """
    if not settings.ai_enabled:
        logger.debug("AI not configured — using stub pattern detection")
        return _stub_patterns(timeframe_days)

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        data_summary = f"Timeframe: last {timeframe_days} days\n"
        if task_data:
            data_summary += f"\nData summary:\n{json.dumps(task_data, indent=2, default=str)}"
        else:
            data_summary += "\nNo detailed task data provided — provide general insights."

        response = await client.chat.completions.create(
            model=settings.AI_MODEL_L3,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_PATTERNS},
                {"role": "user", "content": data_summary},
            ],
            max_tokens=settings.AI_MAX_TOKENS_L3,
            temperature=settings.AI_TEMPERATURE_L3,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        result = json.loads(raw)
        result["ai_enabled"] = True
        result["model"] = settings.AI_MODEL_L3
        result["timeframe_days"] = timeframe_days
        return result

    except ImportError:
        logger.warning("openai package not installed — using stub analysis")
        return _stub_patterns(timeframe_days)
    except Exception as exc:
        logger.error("AI pattern detection failed: %s", exc)
        result = _stub_patterns(timeframe_days)
        result["error"] = str(exc)
        return result


async def generate_weekly_review(review_data: Optional[dict] = None) -> dict:
    """
    Generate a weekly review narrative using GPT L3.

    Args:
        review_data: Dict with weekly metrics (tasks completed, inbox count, etc.)

    Returns:
        dict with structured weekly review insights.
    """
    if not settings.ai_enabled:
        return {
            "headline": "Weekly review (AI not configured)",
            "wins": [],
            "lessons": [],
            "incomplete_items": "Add OPENAI_API_KEY to backend/.env to enable AI review",
            "energy_assessment": "Not available",
            "focus_quality": "Not available",
            "next_week_priorities": [],
            "one_thing_to_stop": "Not available",
            "one_thing_to_start": "Not available",
            "reflection_question": "What would you do differently this week?",
            "ai_enabled": False,
        }

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        data_str = json.dumps(review_data, indent=2, default=str) if review_data else "No data provided"

        response = await client.chat.completions.create(
            model=settings.AI_MODEL_L3,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_REVIEW},
                {"role": "user", "content": f"Weekly data:\n{data_str}"},
            ],
            max_tokens=settings.AI_MAX_TOKENS_L3,
            temperature=settings.AI_TEMPERATURE_L3,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        result = json.loads(raw)
        result["ai_enabled"] = True
        result["model"] = settings.AI_MODEL_L3
        return result

    except ImportError:
        logger.warning("openai package not installed — using stub review")
        return {"ai_enabled": False, "error": "openai not installed"}
    except Exception as exc:
        logger.error("AI weekly review failed: %s", exc)
        return {"ai_enabled": False, "error": str(exc)}

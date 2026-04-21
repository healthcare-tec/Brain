"""
Charlie — AI Cognitive Layer API
Endpoints for the 3-level cognitive system.

L1 — Classification  : POST /api/ai/classify
L2 — Interpretation  : POST /api/ai/interpret
L3 — Analysis        : GET  /api/ai/patterns
                       POST /api/ai/weekly-review
Status               : GET  /api/ai/status
"""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.ai.classifier import classify_input
from app.ai.interpreter import interpret_content
from app.ai.analyzer import detect_patterns, generate_weekly_review
from app.config import settings

router = APIRouter()


# ── Request / Response models ─────────────────────────────────────────────────

class ClassifyRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Raw inbox item text to classify")
    context: Optional[str] = Field(None, description="Optional additional context")


class InterpretRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Content to interpret")
    interpret_type: str = Field(
        "task",
        description="Type of interpretation: task | note | decision",
    )
    extra_context: Optional[str] = Field(None, description="Optional additional context")


class WeeklyReviewRequest(BaseModel):
    review_data: Optional[dict] = Field(None, description="Weekly metrics data")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/status")
async def ai_status():
    """
    Check AI configuration status.
    Returns provider, models, and whether the AI is ready.
    """
    from app.config import get_ai_client_params
    p1 = get_ai_client_params("L1")
    p2 = get_ai_client_params("L2")
    p3 = get_ai_client_params("L3")
    provider = p1["provider"]
    ai_enabled = settings.ai_enabled

    if provider == "ollama":
        message = f"AI active — Ollama ({p1['model']} / {p2['model']} / {p3['model']})"
    elif ai_enabled:
        message = f"AI active — OpenAI ({p1['model']} / {p2['model']} / {p3['model']})"
    else:
        message = "AI disabled. Set AI_PROVIDER=ollama or add OPENAI_API_KEY to .env"

    return {
        "ai_enabled": ai_enabled,
        "provider": provider,
        "models": {
            "l1_classification": p1["model"],
            "l2_interpretation": p2["model"],
            "l3_analysis": p3["model"],
        },
        "ollama_base_url": p1.get("base_url") if provider == "ollama" else None,
        "message": message,
    }


@router.post("/classify")
async def classify(request: ClassifyRequest):
    """
    AI Level 1 — Classification.

    Classifies a raw inbox item into: task | project | note | idea | trash.
    Also suggests title, context, priority, and time estimate.

    Works with or without OPENAI_API_KEY (falls back to heuristics).
    """
    return await classify_input(request.content, context=request.context)


@router.post("/interpret")
async def interpret(request: InterpretRequest):
    """
    AI Level 2 — Interpretation.

    Provides deep analysis of a task, note, or decision.
    - task     → next physical action, blockers, energy, delegation
    - note     → summary, key concepts, PARA category, questions raised
    - decision → options analysis, reversibility, second-order effects

    Requires OPENAI_API_KEY to be configured.
    """
    return await interpret_content(
        request.content,
        interpret_type=request.interpret_type,
        extra_context=request.extra_context,
    )


@router.get("/patterns")
async def patterns(timeframe_days: int = 30):
    """
    AI Level 3 — Pattern Analysis.

    Detects behavioral patterns over the specified timeframe.
    Returns strengths, bottlenecks, estimation accuracy, and recommendations.

    Requires OPENAI_API_KEY to be configured.
    """
    return await detect_patterns(timeframe_days=timeframe_days)


@router.post("/weekly-review")
async def weekly_review(request: WeeklyReviewRequest):
    """
    AI Level 3 — Weekly Review Generation.

    Generates a structured weekly review narrative with wins, lessons,
    priorities, and a reflection question.

    Requires OPENAI_API_KEY to be configured.
    """
    return await generate_weekly_review(review_data=request.review_data)

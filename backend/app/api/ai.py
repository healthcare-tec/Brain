"""
AI Cognitive Layer — API endpoints (stubs).
"""

from fastapi import APIRouter, Query

from app.ai import classify_input, interpret_context, detect_patterns

router = APIRouter()


@router.post("/classify")
async def classify(content: str = Query(..., min_length=1)):
    """AI Level 1: Classify input and suggest type (stub)."""
    return await classify_input(content)


@router.post("/interpret")
async def interpret(query: str = Query(..., min_length=1)):
    """AI Level 2: Interpret context and retrieve relevant knowledge (stub)."""
    return await interpret_context(query)


@router.get("/patterns")
async def patterns(timeframe_days: int = Query(30, ge=1, le=365)):
    """AI Level 3: Detect patterns over time (stub)."""
    return await detect_patterns(timeframe_days)

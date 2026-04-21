"""
Charlie — AI Cognitive Layer
Three levels of cognitive assistance:

  L1 — Classification  : fast, cheap, deterministic (gpt-4o-mini)
  L2 — Interpretation  : balanced, contextual (gpt-4o-mini)
  L3 — Analysis        : deep, creative synthesis (gpt-4o)

AI amplifies thinking, does not replace it.
Configure OPENAI_API_KEY in backend/.env to enable.
"""

from app.ai.classifier import classify_input
from app.ai.interpreter import interpret_context, interpret_content
from app.ai.analyzer import detect_patterns, generate_weekly_review

__all__ = [
    "classify_input",
    "interpret_context",
    "interpret_content",
    "detect_patterns",
    "generate_weekly_review",
]

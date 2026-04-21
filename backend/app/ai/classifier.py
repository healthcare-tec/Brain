"""
AI Level 1 — Classification.
Stub: input categorization, suggest task vs note vs project, suggest next action.
"""


async def classify_input(content: str) -> dict:
    """
    Classify an inbox item and suggest its type.

    TODO: Integrate with LLM for intelligent classification.
    Currently returns a placeholder suggestion.
    """
    content_lower = content.lower()

    # Simple heuristic classification
    if any(kw in content_lower for kw in ["fazer", "comprar", "ligar", "enviar", "todo", "task"]):
        suggested_type = "task"
    elif any(kw in content_lower for kw in ["projeto", "project", "iniciativa", "plano"]):
        suggested_type = "project"
    elif any(kw in content_lower for kw in ["ideia", "idea", "pensar", "reflexão", "nota"]):
        suggested_type = "note"
    else:
        suggested_type = "task"  # Default

    return {
        "suggested_type": suggested_type,
        "confidence": 0.5,
        "suggested_next_action": f"Review and clarify: {content[:100]}",
        "ai_powered": False,
        "message": "AI classification is a stub. Integrate LLM for real classification.",
    }

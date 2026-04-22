"""Voice Capture API — receives transcribed text and uses AI to split into multiple inbox items."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.ai.json_parser import parse_ai_json

from app.config import settings
from app.models.inbox import InboxItem
from app.events.emitter import emit_event
from app.models.event import EventType

logger = logging.getLogger(__name__)

router = APIRouter()


class VoiceCaptureRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Transcribed voice text")


class VoiceCaptureResponse(BaseModel):
    items_created: int
    items: list[dict]


async def _split_with_ai(text: str) -> list[dict]:
    """Use the configured AI provider to split a voice capture into multiple inbox items."""
    if not settings.ai_enabled:
        return _split_simple(text)

    try:
        from openai import AsyncOpenAI
        from app.config import get_ai_client_params
        params = get_ai_client_params("L2")
        client = AsyncOpenAI(
            api_key=params["api_key"],
            base_url=params["base_url"],
            timeout=params.get("timeout", 60),
        )
        model = params["model"]

        system_content = (
            "You are a smart assistant that processes voice captures for a personal "
            "productivity system. The user will speak freely and mention multiple "
            "tasks, ideas, reminders, or notes in a single stream of consciousness.\n\n"
            "Your job is to:\n"
            "1. Identify each distinct actionable item, idea, or note\n"
            "2. Separate them into individual inbox entries\n"
            "3. Clean up the language (fix grammar, make concise)\n"
            "4. Preserve the original intent\n\n"
            "Return valid JSON only (no markdown fences): "
            '{"items": [{"content": "...", "type_hint": "task|note|idea"}]}\n'
            "Always return at least 1 item."
        )

        response = await client.chat.completions.create(
            model=model,
            temperature=0.3,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": text},
            ],
        )

        raw = response.choices[0].message.content
        logger.debug("Raw AI response (voice): %r", raw[:300] if raw else "<empty>")
        result = parse_ai_json(raw)
        return result.get("items", [{"content": text, "type_hint": "task"}])
    except Exception as exc:
        logger.warning("AI voice split failed: %s", exc)
        return _split_simple(text)


def _split_simple(text: str) -> list[dict]:
    """Fallback: split by common delimiters."""
    delimiters = [" também ", " e também ", " e não posso ", " além disso ",
                  " preciso ", " tenho que ", " não esquecer "]
    items = [text]
    for delim in delimiters:
        new_items = []
        for item in items:
            parts = item.split(delim)
            new_items.extend(parts)
        items = new_items

    # Clean up
    result = []
    for item in items:
        cleaned = item.strip().strip(",").strip(".")
        if len(cleaned) > 2:
            result.append({"content": cleaned, "type_hint": "task"})

    return result if result else [{"content": text, "type_hint": "task"}]


@router.post("/capture", response_model=VoiceCaptureResponse)
async def voice_capture(
    data: VoiceCaptureRequest,
    db: AsyncSession = Depends(get_db),
):
    """Process voice text: AI splits into multiple inbox items."""
    parsed_items = await _split_with_ai(data.text)

    created = []
    for item_data in parsed_items:
        content = item_data.get("content", "").strip()
        if not content:
            continue
        inbox_item = InboxItem(
            content=content,
            item_type=item_data.get("type_hint", "task"),
        )
        db.add(inbox_item)
        await db.flush()
        await emit_event(
            db, EventType.CAPTURED, task_id=None,
            description=f"Voice capture: {content[:100]}",
            metadata={"source": "voice", "type_hint": item_data.get("type_hint")},
        )
        created.append({
            "id": inbox_item.id,
            "content": inbox_item.content,
            "type_hint": item_data.get("type_hint"),
        })

    await db.commit()
    return VoiceCaptureResponse(items_created=len(created), items=created)

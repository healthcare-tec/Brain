"""
Event emitter — creates TaskEvent records for every significant action.
"""

import json
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import TaskEvent, EventType


async def emit_event(
    db: AsyncSession,
    event_type: EventType,
    task_id: str | None = None,
    description: str | None = None,
    metadata: dict | None = None,
) -> TaskEvent:
    """Create and persist a new event."""
    event = TaskEvent(
        task_id=task_id,
        event_type=event_type,
        description=description,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(event)
    await db.flush()
    return event

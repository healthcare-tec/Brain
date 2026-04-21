"""
Event System — API endpoints for querying events.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.event import TaskEvent, EventType
from app.schemas.event import TaskEventResponse

router = APIRouter()


@router.get("/", response_model=list[TaskEventResponse])
async def list_events(
    event_type: EventType | None = Query(None),
    task_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List events, optionally filtered by type or task."""
    stmt = select(TaskEvent).order_by(TaskEvent.created_at.desc()).limit(limit)
    if event_type:
        stmt = stmt.where(TaskEvent.event_type == event_type)
    if task_id:
        stmt = stmt.where(TaskEvent.task_id == task_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())

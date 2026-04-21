"""Event schemas."""

from datetime import datetime
from pydantic import BaseModel
from app.models.event import EventType


class TaskEventCreate(BaseModel):
    task_id: str | None = None
    event_type: EventType
    description: str | None = None
    metadata_json: str | None = None


class TaskEventResponse(BaseModel):
    id: str
    task_id: str | None
    event_type: EventType
    description: str | None
    metadata_json: str | None
    created_at: datetime

    class Config:
        from_attributes = True


__all__ = ["TaskEventCreate", "TaskEventResponse"]

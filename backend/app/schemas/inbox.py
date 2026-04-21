"""Inbox schemas."""

from datetime import datetime
from pydantic import BaseModel, Field
from app.models.inbox import InboxStatus


class InboxItemCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    item_type: str | None = Field(None, max_length=50)


class InboxItemClarify(BaseModel):
    """Clarification Engine: process an inbox item."""
    clarified_as: str = Field(..., pattern="^(task|project|note|trash)$")
    # Optional fields for creating the target entity
    title: str | None = None
    description: str | None = None
    project_id: str | None = None
    context: str | None = None
    category: str | None = None  # For notes: project, area, resource, archive


class InboxItemResponse(BaseModel):
    id: str
    content: str
    item_type: str | None
    status: InboxStatus
    clarified_as: str | None
    clarified_ref_id: str | None
    captured_at: datetime
    processed_at: datetime | None

    class Config:
        from_attributes = True


__all__ = ["InboxItemCreate", "InboxItemClarify", "InboxItemResponse"]

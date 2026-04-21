"""Inbox schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.inbox import InboxStatus


class InboxItemCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    item_type: Optional[str] = Field(None, max_length=50)


class InboxItemClarify(BaseModel):
    """
    Clarification Engine: process an inbox item.

    clarified_as must be one of: task | project | note | idea | trash
    (idea is treated as note internally)
    """
    clarified_as: str = Field(..., pattern="^(task|project|note|idea|trash)$")

    # Optional fields for creating the target entity
    title:       Optional[str] = None
    description: Optional[str] = None
    project_id:  Optional[str] = None
    context:     Optional[str] = None
    priority:    Optional[str] = None   # low | medium | high | urgent
    category:    Optional[str] = None   # For notes: project | area | resource | archive

    # Allow any extra fields sent by the frontend without causing 422
    model_config = {"extra": "allow"}


class InboxItemResponse(BaseModel):
    id: str
    content: str
    item_type: Optional[str]
    status: InboxStatus
    clarified_as: Optional[str]
    clarified_ref_id: Optional[str]
    captured_at: datetime
    processed_at: Optional[datetime]

    model_config = {"from_attributes": True}


__all__ = ["InboxItemCreate", "InboxItemClarify", "InboxItemResponse"]

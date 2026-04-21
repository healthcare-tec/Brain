"""Note schemas."""

from datetime import datetime
from pydantic import BaseModel, Field
from app.models.note import NoteCategory


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    category: NoteCategory = NoteCategory.RESOURCE
    tags: str | None = None
    content: str | None = None
    linked_note_ids: str | None = None


class NoteUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    category: NoteCategory | None = None
    tags: str | None = None
    content: str | None = None
    linked_note_ids: str | None = None


class NoteResponse(BaseModel):
    id: str
    title: str
    category: NoteCategory
    tags: str | None
    markdown_path: str | None
    content: str | None
    linked_note_ids: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


__all__ = ["NoteCreate", "NoteUpdate", "NoteResponse"]

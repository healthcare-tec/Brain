"""
Knowledge System — Note metadata model.
Content is stored as Markdown files; this table holds metadata and indexing info.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.database import Base


class NoteCategory(str, enum.Enum):
    PROJECT = "project"
    AREA = "area"
    RESOURCE = "resource"
    ARCHIVE = "archive"


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[NoteCategory] = mapped_column(
        SAEnum(NoteCategory), default=NoteCategory.RESOURCE, nullable=False
    )
    tags: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Comma-separated tags"
    )
    markdown_path: Mapped[str | None] = mapped_column(
        String(1000), nullable=True, comment="Relative path to Markdown file"
    )
    content: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Inline content if no file"
    )
    linked_note_ids: Mapped[str | None] = mapped_column(
        String(2000), nullable=True, comment="Comma-separated IDs of linked notes"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

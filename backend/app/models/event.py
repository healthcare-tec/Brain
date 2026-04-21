"""
Event System — TaskEvent model.
All key actions generate events: captured, clarified, scheduled, completed, reviewed.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class EventType(str, enum.Enum):
    CAPTURED = "captured"
    CLARIFIED = "clarified"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    REVIEWED = "reviewed"
    UPDATED = "updated"
    CREATED = "created"


class TaskEvent(Base):
    __tablename__ = "task_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    task_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True
    )
    event_type: Mapped[EventType] = mapped_column(
        SAEnum(EventType), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="JSON string with extra event data"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    task: Mapped["Task"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Task", back_populates="events"
    )

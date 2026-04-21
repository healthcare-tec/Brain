"""
Task System — Task model.
Supports GTD statuses: next, waiting, someday, done.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class TaskStatus(str, enum.Enum):
    NEXT = "next"
    WAITING = "waiting"
    SOMEDAY = "someday"
    DONE = "done"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus), default=TaskStatus.NEXT, nullable=False
    )
    priority: Mapped[TaskPriority] = mapped_column(
        SAEnum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False
    )
    context: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="@home, @work, @computer, etc."
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    estimated_time: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Estimated time in minutes"
    )
    actual_time: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Actual time in minutes"
    )
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Project", back_populates="tasks", lazy="selectin"
    )
    events: Mapped[list["TaskEvent"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "TaskEvent", back_populates="task", lazy="selectin", cascade="all, delete-orphan"
    )

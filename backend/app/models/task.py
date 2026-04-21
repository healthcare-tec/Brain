"""
Task System — Task model.
Supports GTD statuses: next, waiting, someday, done.
Recurring tasks: daily, weekly, monthly, custom.
Tags: comma-separated free-form tags.
Uses String columns for enum values (SQLite-compatible).
"""

import uuid
import enum
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TaskStatus(str, enum.Enum):
    NEXT = "next"
    WAITING = "waiting"
    SOMEDAY = "someday"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecurrenceType(str, enum.Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default=TaskStatus.NEXT.value, nullable=False
    )
    priority: Mapped[str] = mapped_column(
        String(20), default=TaskPriority.MEDIUM.value, nullable=False
    )
    context: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="@home, @work, @computer, etc."
    )
    tags: Mapped[str | None] = mapped_column(
        String(1000), nullable=True, comment="Comma-separated free-form tags"
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

    # Recurring task fields
    recurrence: Mapped[str] = mapped_column(
        String(20), default=RecurrenceType.NONE.value, nullable=False
    )
    recurrence_interval: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Custom interval in days"
    )
    parent_task_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, comment="ID of the original recurring task"
    )

    # Reminder
    reminder_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="When to send a reminder"
    )

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

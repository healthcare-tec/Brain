"""
Capture Engine — Inbox model.
Frictionless capture: every input lands here first.
Uses String columns for enum values (SQLite-compatible).
"""

import uuid
import enum
from datetime import datetime

from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InboxStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    TRASHED = "trashed"


class InboxItem(Base):
    __tablename__ = "inbox_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    item_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="quick_note | task | idea | other"
    )
    status: Mapped[str] = mapped_column(
        String(20), default=InboxStatus.PENDING.value, nullable=False
    )
    clarified_as: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="task | project | note | trash"
    )
    clarified_ref_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, comment="ID of the created task/project/note"
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

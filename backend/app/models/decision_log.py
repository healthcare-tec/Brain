"""
Thinking Engine — Decision Log model.
Stores metadata for thinking notes; content lives in Markdown files.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.database import Base


class DecisionLogType(str, enum.Enum):
    DECISION = "decision"
    RISK_ANALYSIS = "risk_analysis"
    PROBLEM_BREAKDOWN = "problem_breakdown"


class DecisionLog(Base):
    __tablename__ = "decision_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    log_type: Mapped[DecisionLogType] = mapped_column(
        SAEnum(DecisionLogType), default=DecisionLogType.DECISION, nullable=False
    )
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    hypotheses: Mapped[str | None] = mapped_column(Text, nullable=True)
    options: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    actual_outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    markdown_path: Mapped[str | None] = mapped_column(
        String(1000), nullable=True, comment="Path to the full Markdown document"
    )
    tags: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Comma-separated tags"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

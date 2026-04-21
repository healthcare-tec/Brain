"""Decision Log schemas."""

from datetime import datetime
from pydantic import BaseModel, Field
from app.models.decision_log import DecisionLogType


class DecisionLogCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    log_type: DecisionLogType = DecisionLogType.DECISION
    context: str | None = None
    hypotheses: str | None = None
    options: str | None = None
    decision: str | None = None
    expected_outcome: str | None = None
    tags: str | None = None


class DecisionLogUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    log_type: DecisionLogType | None = None
    context: str | None = None
    hypotheses: str | None = None
    options: str | None = None
    decision: str | None = None
    expected_outcome: str | None = None
    actual_outcome: str | None = None
    tags: str | None = None


class DecisionLogResponse(BaseModel):
    id: str
    title: str
    log_type: DecisionLogType
    context: str | None
    hypotheses: str | None
    options: str | None
    decision: str | None
    expected_outcome: str | None
    actual_outcome: str | None
    markdown_path: str | None
    tags: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


__all__ = ["DecisionLogCreate", "DecisionLogUpdate", "DecisionLogResponse"]

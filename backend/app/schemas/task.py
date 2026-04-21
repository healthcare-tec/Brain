"""Task schemas."""

from datetime import datetime
from pydantic import BaseModel, Field
from app.models.task import TaskStatus, TaskPriority


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    status: TaskStatus = TaskStatus.NEXT
    priority: TaskPriority = TaskPriority.MEDIUM
    context: str | None = Field(None, max_length=100)
    project_id: str | None = None
    estimated_time: int | None = Field(None, ge=0, description="Minutes")
    due_date: datetime | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    context: str | None = None
    project_id: str | None = None
    estimated_time: int | None = None
    due_date: datetime | None = None


class TaskComplete(BaseModel):
    """Mark a task as DONE with execution metadata."""
    actual_time: int | None = Field(None, ge=0, description="Actual time in minutes")
    context: str | None = None
    notes: str | None = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    context: str | None
    project_id: str | None
    estimated_time: int | None
    actual_time: int | None
    due_date: datetime | None
    created_at: datetime
    completed_at: datetime | None
    updated_at: datetime

    class Config:
        from_attributes = True


__all__ = ["TaskCreate", "TaskUpdate", "TaskComplete", "TaskResponse"]

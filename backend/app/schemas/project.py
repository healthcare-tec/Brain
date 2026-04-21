"""Project schemas."""

from datetime import datetime
from pydantic import BaseModel, Field
from app.models.project import ProjectStatus


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    area: str | None = Field(None, max_length=200)


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    status: ProjectStatus | None = None
    area: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str | None
    status: ProjectStatus
    area: str | None
    created_at: datetime
    updated_at: datetime
    task_count: int = 0
    completed_task_count: int = 0

    class Config:
        from_attributes = True


__all__ = ["ProjectCreate", "ProjectUpdate", "ProjectResponse"]

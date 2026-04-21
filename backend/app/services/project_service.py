"""
Project management service.
"""

from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.schemas.project import ProjectCreate, ProjectUpdate


async def create_project(db: AsyncSession, data: ProjectCreate) -> Project:
    project = Project(**data.model_dump(exclude_none=True))
    db.add(project)
    await db.flush()
    return project


async def list_projects(db: AsyncSession, status=None) -> list[dict]:
    stmt = select(Project).order_by(Project.created_at.desc())
    if status:
        stmt = stmt.where(Project.status == status)
    result = await db.execute(stmt)
    projects = list(result.scalars().all())

    enriched = []
    for p in projects:
        # Count tasks
        total_q = await db.execute(
            select(func.count()).where(Task.project_id == p.id)
        )
        total = total_q.scalar() or 0
        done_q = await db.execute(
            select(func.count()).where(
                Task.project_id == p.id, Task.status == TaskStatus.DONE
            )
        )
        done = done_q.scalar() or 0
        enriched.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "status": p.status,
            "area": p.area,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "task_count": total,
            "completed_task_count": done,
        })
    return enriched


async def get_project(db: AsyncSession, project_id: str) -> Project | None:
    return await db.get(Project, project_id)


async def update_project(
    db: AsyncSession, project_id: str, data: ProjectUpdate
) -> Project | None:
    project = await db.get(Project, project_id)
    if not project:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    project.updated_at = datetime.utcnow()
    await db.flush()
    return project


async def delete_project(db: AsyncSession, project_id: str) -> bool:
    project = await db.get(Project, project_id)
    if not project:
        return False
    await db.delete(project)
    await db.flush()
    return True

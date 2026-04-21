"""
Task System + Task Completion System service.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus
from app.models.event import EventType
from app.schemas.task import TaskCreate, TaskUpdate, TaskComplete
from app.events.emitter import emit_event


async def create_task(db: AsyncSession, data: TaskCreate) -> Task:
    task = Task(**data.model_dump(exclude_none=True))
    db.add(task)
    await db.flush()
    await emit_event(
        db, EventType.CREATED, task_id=task.id,
        description=f"Task created: {task.title}",
    )
    return task


async def list_tasks(
    db: AsyncSession,
    status: TaskStatus | None = None,
    project_id: str | None = None,
    context: str | None = None,
) -> list[Task]:
    stmt = select(Task).order_by(Task.created_at.desc())
    if status:
        stmt = stmt.where(Task.status == status)
    if project_id:
        stmt = stmt.where(Task.project_id == project_id)
    if context:
        stmt = stmt.where(Task.context == context)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_task(db: AsyncSession, task_id: str) -> Task | None:
    return await db.get(Task, task_id)


async def update_task(db: AsyncSession, task_id: str, data: TaskUpdate) -> Task | None:
    task = await db.get(Task, task_id)
    if not task:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    task.updated_at = datetime.utcnow()
    await db.flush()
    await emit_event(
        db, EventType.UPDATED, task_id=task.id,
        description=f"Task updated: {task.title}",
        metadata={"fields": list(update_data.keys())},
    )
    return task


async def complete_task(db: AsyncSession, task_id: str, data: TaskComplete) -> Task | None:
    """Mark a task as DONE with execution metadata."""
    task = await db.get(Task, task_id)
    if not task:
        return None

    task.status = TaskStatus.DONE
    task.completed_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()
    if data.actual_time is not None:
        task.actual_time = data.actual_time
    if data.context:
        task.context = data.context

    await db.flush()
    await emit_event(
        db, EventType.COMPLETED, task_id=task.id,
        description=f"Task completed: {task.title}",
        metadata={
            "estimated_time": task.estimated_time,
            "actual_time": task.actual_time,
            "context": task.context,
            "project_id": task.project_id,
            "notes": data.notes,
        },
    )
    return task


async def delete_task(db: AsyncSession, task_id: str) -> bool:
    task = await db.get(Task, task_id)
    if not task:
        return False
    await db.delete(task)
    await db.flush()
    return True

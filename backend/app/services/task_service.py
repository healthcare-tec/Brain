"""
Task System + Task Completion System + Recurring Tasks service.
"""
from datetime import datetime, timedelta
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus, RecurrenceType
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
    status: str | None = None,
    project_id: str | None = None,
    context: str | None = None,
    tags: str | None = None,
    priority: str | None = None,
    search: str | None = None,
) -> list[Task]:
    stmt = select(Task).order_by(Task.created_at.desc())
    if status:
        stmt = stmt.where(Task.status == status)
    if project_id:
        stmt = stmt.where(Task.project_id == project_id)
    if context:
        stmt = stmt.where(Task.context == context)
    if priority:
        stmt = stmt.where(Task.priority == priority)
    if tags:
        tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
        if tag_list:
            conditions = [Task.tags.ilike(f"%{tag}%") for tag in tag_list]
            stmt = stmt.where(or_(*conditions))
    if search:
        stmt = stmt.where(
            or_(
                Task.title.ilike(f"%{search}%"),
                Task.description.ilike(f"%{search}%"),
                Task.tags.ilike(f"%{search}%"),
            )
        )
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


def _compute_next_due(task: Task) -> datetime | None:
    """Compute the next due date for a recurring task."""
    base = task.due_date or task.completed_at or datetime.utcnow()
    if task.recurrence == RecurrenceType.DAILY.value:
        return base + timedelta(days=1)
    elif task.recurrence == RecurrenceType.WEEKLY.value:
        return base + timedelta(weeks=1)
    elif task.recurrence == RecurrenceType.MONTHLY.value:
        return base + timedelta(days=30)
    elif task.recurrence == RecurrenceType.CUSTOM.value and task.recurrence_interval:
        return base + timedelta(days=task.recurrence_interval)
    return None


async def complete_task(db: AsyncSession, task_id: str, data: TaskComplete) -> Task | None:
    """Mark a task as DONE with execution metadata. If recurring, create next occurrence."""
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

    # Create next occurrence for recurring tasks
    if task.recurrence and task.recurrence != RecurrenceType.NONE.value:
        next_due = _compute_next_due(task)
        next_reminder = None
        if task.reminder_at and task.due_date and next_due:
            delta = task.due_date - task.reminder_at
            next_reminder = next_due - delta

        next_task = Task(
            title=task.title,
            description=task.description,
            status=TaskStatus.NEXT.value,
            priority=task.priority,
            context=task.context,
            tags=task.tags,
            project_id=task.project_id,
            estimated_time=task.estimated_time,
            due_date=next_due,
            recurrence=task.recurrence,
            recurrence_interval=task.recurrence_interval,
            parent_task_id=task.parent_task_id or task.id,
            reminder_at=next_reminder,
        )
        db.add(next_task)
        await db.flush()
        await emit_event(
            db, EventType.CREATED, task_id=next_task.id,
            description=f"Recurring task created: {next_task.title}",
            metadata={"parent_task_id": task.id, "recurrence": task.recurrence},
        )

    return task


async def get_reminders(db: AsyncSession) -> list[Task]:
    """Get tasks with reminders that are due now or overdue."""
    now = datetime.utcnow()
    stmt = (
        select(Task)
        .where(Task.reminder_at <= now)
        .where(Task.status != TaskStatus.DONE.value)
        .order_by(Task.reminder_at.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def delete_task(db: AsyncSession, task_id: str) -> bool:
    task = await db.get(Task, task_id)
    if not task:
        return False
    await db.delete(task)
    await db.flush()
    return True

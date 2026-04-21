"""Tasks API router with advanced filters, reminders, tags."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.task import TaskCreate, TaskUpdate, TaskComplete, TaskResponse
from app.services import task_service

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(data: TaskCreate, db: AsyncSession = Depends(get_db)):
    """Create a new task."""
    return await task_service.create_task(db, data)


@router.get("/", response_model=list[TaskResponse])
async def list_tasks(
    status: str | None = Query(None),
    project_id: str | None = Query(None),
    context: str | None = Query(None),
    tags: str | None = Query(None, description="Comma-separated tags"),
    priority: str | None = Query(None),
    search: str | None = Query(None, description="Search title, description, tags"),
    db: AsyncSession = Depends(get_db),
):
    """List tasks with optional filters."""
    return await task_service.list_tasks(
        db, status=status, project_id=project_id, context=context,
        tags=tags, priority=priority, search=search,
    )


@router.get("/reminders", response_model=list[TaskResponse])
async def get_reminders(db: AsyncSession = Depends(get_db)):
    """Get tasks with due or overdue reminders."""
    return await task_service.get_reminders(db)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single task."""
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str, data: TaskUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a task."""
    task = await task_service.update_task(db, task_id, data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: str, data: TaskComplete, db: AsyncSession = Depends(get_db)
):
    """Mark a task as DONE. If recurring, auto-creates next occurrence."""
    task = await task_service.complete_task(db, task_id, data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a task."""
    if not await task_service.delete_task(db, task_id):
        raise HTTPException(status_code=404, detail="Task not found")

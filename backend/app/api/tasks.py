"""
Task System + Task Completion System API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.task import TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate, TaskComplete, TaskResponse
from app.services import task_service

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(data: TaskCreate, db: AsyncSession = Depends(get_db)):
    """Create a new task."""
    return await task_service.create_task(db, data)


@router.get("/", response_model=list[TaskResponse])
async def list_tasks(
    status: TaskStatus | None = Query(None),
    project_id: str | None = Query(None),
    context: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List tasks with optional filters (status, project, context)."""
    return await task_service.list_tasks(db, status, project_id, context)


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
    """Mark a task as DONE with execution metadata."""
    task = await task_service.complete_task(db, task_id, data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a task."""
    if not await task_service.delete_task(db, task_id):
        raise HTTPException(status_code=404, detail="Task not found")

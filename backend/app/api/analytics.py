"""Analytics / Dashboard API — productivity metrics and charts data."""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.task import Task, TaskStatus
from app.models.event import TaskEvent
from app.models.project import Project

router = APIRouter()


@router.get("/summary")
async def analytics_summary(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Overall productivity summary for the given period."""
    since = datetime.utcnow() - timedelta(days=days)

    # Total tasks
    total = (await db.execute(select(func.count(Task.id)))).scalar() or 0

    # Completed in period
    completed = (await db.execute(
        select(func.count(Task.id))
        .where(Task.status == TaskStatus.DONE.value)
        .where(Task.completed_at >= since)
    )).scalar() or 0

    # Created in period
    created = (await db.execute(
        select(func.count(Task.id)).where(Task.created_at >= since)
    )).scalar() or 0

    # By status
    status_counts = {}
    for s in TaskStatus:
        cnt = (await db.execute(
            select(func.count(Task.id)).where(Task.status == s.value)
        )).scalar() or 0
        status_counts[s.value] = cnt

    # Estimation accuracy
    stmt = select(
        func.avg(Task.estimated_time).label("avg_est"),
        func.avg(Task.actual_time).label("avg_act"),
    ).where(
        and_(
            Task.estimated_time.isnot(None),
            Task.actual_time.isnot(None),
            Task.status == TaskStatus.DONE.value,
        )
    )
    row = (await db.execute(stmt)).first()
    avg_est = float(row.avg_est) if row and row.avg_est else None
    avg_act = float(row.avg_act) if row and row.avg_act else None
    accuracy_pct = None
    if avg_est and avg_act and avg_est > 0:
        accuracy_pct = round(min(avg_act / avg_est, avg_est / avg_act) * 100, 1)

    # Active projects
    active_projects = (await db.execute(
        select(func.count(Project.id)).where(Project.status == "active")
    )).scalar() or 0

    return {
        "period_days": days,
        "total_tasks": total,
        "created_in_period": created,
        "completed_in_period": completed,
        "status_counts": status_counts,
        "avg_estimated_minutes": round(avg_est, 1) if avg_est else None,
        "avg_actual_minutes": round(avg_act, 1) if avg_act else None,
        "estimation_accuracy_pct": accuracy_pct,
        "active_projects": active_projects,
    }


@router.get("/completions-by-day")
async def completions_by_day(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Tasks completed per day for charting."""
    since = datetime.utcnow() - timedelta(days=days)
    stmt = (
        select(
            func.date(Task.completed_at).label("day"),
            func.count(Task.id).label("count"),
        )
        .where(Task.status == TaskStatus.DONE.value)
        .where(Task.completed_at >= since)
        .group_by(func.date(Task.completed_at))
        .order_by(func.date(Task.completed_at))
    )
    rows = (await db.execute(stmt)).all()
    return [{"day": str(r.day), "count": r.count} for r in rows]


@router.get("/by-context")
async def tasks_by_context(db: AsyncSession = Depends(get_db)):
    """Distribution of active tasks by context."""
    stmt = (
        select(
            func.coalesce(Task.context, "none").label("context"),
            func.count(Task.id).label("count"),
        )
        .where(Task.status != TaskStatus.DONE.value)
        .group_by(Task.context)
        .order_by(func.count(Task.id).desc())
    )
    rows = (await db.execute(stmt)).all()
    return [{"context": r.context, "count": r.count} for r in rows]


@router.get("/by-project")
async def tasks_by_project(db: AsyncSession = Depends(get_db)):
    """Distribution of tasks by project."""
    stmt = (
        select(
            Project.name.label("project"),
            func.count(Task.id).label("total"),
            func.sum(case((Task.status == TaskStatus.DONE.value, 1), else_=0)).label("done"),
        )
        .join(Project, Task.project_id == Project.id)
        .group_by(Project.name)
        .order_by(func.count(Task.id).desc())
    )
    rows = (await db.execute(stmt)).all()
    return [{"project": r.project, "total": r.total, "done": r.done} for r in rows]


@router.get("/time-estimation")
async def time_estimation_accuracy(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Estimated vs actual time for completed tasks (for scatter/bar chart)."""
    since = datetime.utcnow() - timedelta(days=days)
    stmt = (
        select(
            Task.title,
            Task.estimated_time,
            Task.actual_time,
            Task.completed_at,
            Task.context,
            Task.project_id,
        )
        .where(
            and_(
                Task.estimated_time.isnot(None),
                Task.actual_time.isnot(None),
                Task.status == TaskStatus.DONE.value,
                Task.completed_at >= since,
            )
        )
        .order_by(Task.completed_at.desc())
    )
    rows = (await db.execute(stmt)).all()
    return [
        {
            "title": r.title,
            "estimated": r.estimated_time,
            "actual": r.actual_time,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "context": r.context,
        }
        for r in rows
    ]


@router.get("/events-timeline")
async def events_timeline(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Recent events timeline for activity feed."""
    since = datetime.utcnow() - timedelta(days=days)
    stmt = (
        select(TaskEvent)
        .where(TaskEvent.created_at >= since)
        .order_by(TaskEvent.created_at.desc())
        .limit(100)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "description": e.description,
            "task_id": e.task_id,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in rows
    ]

"""
Feedback System — Review service.
Provides weekly/monthly review data.
"""

from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inbox import InboxItem, InboxStatus
from app.models.task import Task, TaskStatus
from app.models.project import Project, ProjectStatus
from app.models.event import TaskEvent, EventType


async def get_weekly_review(db: AsyncSession) -> dict:
    """Generate a weekly review summary."""
    one_week_ago = datetime.utcnow() - timedelta(days=7)

    # Pending inbox items
    inbox_q = await db.execute(
        select(func.count()).where(InboxItem.status == InboxStatus.PENDING)
    )
    pending_inbox = inbox_q.scalar() or 0

    # Tasks completed this week
    completed_q = await db.execute(
        select(func.count()).where(
            Task.status == TaskStatus.DONE,
            Task.completed_at >= one_week_ago,
        )
    )
    completed_tasks = completed_q.scalar() or 0

    # Active tasks (next actions)
    next_q = await db.execute(
        select(func.count()).where(Task.status == TaskStatus.NEXT)
    )
    next_actions = next_q.scalar() or 0

    # Waiting tasks
    waiting_q = await db.execute(
        select(func.count()).where(Task.status == TaskStatus.WAITING)
    )
    waiting_tasks = waiting_q.scalar() or 0

    # Active projects
    projects_q = await db.execute(
        select(func.count()).where(Project.status == ProjectStatus.ACTIVE)
    )
    active_projects = projects_q.scalar() or 0

    # Time estimation accuracy (tasks completed this week with both estimates)
    time_tasks_q = await db.execute(
        select(Task).where(
            Task.status == TaskStatus.DONE,
            Task.completed_at >= one_week_ago,
            Task.estimated_time.isnot(None),
            Task.actual_time.isnot(None),
        )
    )
    time_tasks = list(time_tasks_q.scalars().all())
    estimation_accuracy = None
    if time_tasks:
        total_estimated = sum(t.estimated_time for t in time_tasks)
        total_actual = sum(t.actual_time for t in time_tasks)
        if total_estimated > 0:
            estimation_accuracy = round(total_actual / total_estimated * 100, 1)

    # Events this week
    events_q = await db.execute(
        select(func.count()).where(TaskEvent.created_at >= one_week_ago)
    )
    total_events = events_q.scalar() or 0

    return {
        "period": "weekly",
        "from_date": one_week_ago.isoformat(),
        "to_date": datetime.utcnow().isoformat(),
        "pending_inbox": pending_inbox,
        "completed_tasks": completed_tasks,
        "next_actions": next_actions,
        "waiting_tasks": waiting_tasks,
        "active_projects": active_projects,
        "estimation_accuracy_pct": estimation_accuracy,
        "total_events": total_events,
    }

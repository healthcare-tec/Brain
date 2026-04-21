"""Global search API — searches across tasks, notes, projects, decision logs."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.task import Task
from app.models.note import Note
from app.models.project import Project
from app.models.decision_log import DecisionLog

router = APIRouter()


@router.get("/")
async def global_search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Search across all content types."""
    results = []
    pattern = f"%{q}%"

    # Search tasks
    stmt = (
        select(Task)
        .where(or_(
            Task.title.ilike(pattern),
            Task.description.ilike(pattern),
            Task.tags.ilike(pattern),
        ))
        .order_by(Task.updated_at.desc())
        .limit(limit)
    )
    tasks = (await db.execute(stmt)).scalars().all()
    for t in tasks:
        results.append({
            "type": "task",
            "id": t.id,
            "title": t.title,
            "snippet": (t.description or "")[:200],
            "status": t.status,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        })

    # Search notes
    stmt = (
        select(Note)
        .where(or_(
            Note.title.ilike(pattern),
            Note.content.ilike(pattern),
            Note.tags.ilike(pattern),
        ))
        .order_by(Note.updated_at.desc())
        .limit(limit)
    )
    notes = (await db.execute(stmt)).scalars().all()
    for n in notes:
        results.append({
            "type": "note",
            "id": n.id,
            "title": n.title,
            "snippet": (n.content or "")[:200],
            "category": n.category,
            "updated_at": n.updated_at.isoformat() if n.updated_at else None,
        })

    # Search projects
    stmt = (
        select(Project)
        .where(or_(
            Project.name.ilike(pattern),
            Project.description.ilike(pattern),
        ))
        .order_by(Project.updated_at.desc())
        .limit(limit)
    )
    projects = (await db.execute(stmt)).scalars().all()
    for p in projects:
        results.append({
            "type": "project",
            "id": p.id,
            "title": p.name,
            "snippet": (p.description or "")[:200],
            "status": p.status,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        })

    # Search decision logs
    stmt = (
        select(DecisionLog)
        .where(or_(
            DecisionLog.title.ilike(pattern),
            DecisionLog.context.ilike(pattern),
            DecisionLog.decision.ilike(pattern),
            DecisionLog.tags.ilike(pattern),
        ))
        .order_by(DecisionLog.updated_at.desc())
        .limit(limit)
    )
    logs = (await db.execute(stmt)).scalars().all()
    for d in logs:
        results.append({
            "type": "decision_log",
            "id": d.id,
            "title": d.title,
            "snippet": (d.context or "")[:200],
            "log_type": d.log_type,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        })

    # Sort all results by updated_at descending
    results.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
    return results[:limit]

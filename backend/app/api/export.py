"""Export API — export tasks, notes, decision logs in CSV, JSON, or Markdown."""

import csv
import io
import json
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.task import Task
from app.models.note import Note
from app.models.decision_log import DecisionLog

router = APIRouter()


def _task_to_dict(t: Task) -> dict:
    return {
        "id": t.id, "title": t.title, "description": t.description or "",
        "status": t.status, "priority": t.priority, "context": t.context or "",
        "tags": t.tags or "", "project_id": t.project_id or "",
        "estimated_time": t.estimated_time, "actual_time": t.actual_time,
        "due_date": t.due_date.isoformat() if t.due_date else "",
        "recurrence": t.recurrence,
        "created_at": t.created_at.isoformat() if t.created_at else "",
        "completed_at": t.completed_at.isoformat() if t.completed_at else "",
    }


def _note_to_dict(n: Note) -> dict:
    return {
        "id": n.id, "title": n.title, "category": n.category,
        "tags": n.tags or "", "content": n.content or "",
        "created_at": n.created_at.isoformat() if n.created_at else "",
    }


def _decision_to_dict(d: DecisionLog) -> dict:
    return {
        "id": d.id, "title": d.title, "log_type": d.log_type,
        "context": d.context or "", "options": d.options or "",
        "decision": d.decision or "", "expected_outcome": d.expected_outcome or "",
        "actual_outcome": d.actual_outcome or "", "tags": d.tags or "",
        "created_at": d.created_at.isoformat() if d.created_at else "",
    }


def _to_csv(data: list[dict]) -> str:
    if not data:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()


def _to_markdown(data: list[dict], entity_type: str) -> str:
    lines = [f"# {entity_type.title()} Export", f"Exported: {datetime.utcnow().isoformat()}", ""]
    for item in data:
        lines.append(f"## {item.get('title', 'Untitled')}")
        for k, v in item.items():
            if k != "title" and v:
                lines.append(f"- **{k}**: {v}")
        lines.append("")
    return "\n".join(lines)


@router.get("/{entity_type}")
async def export_data(
    entity_type: str,
    format: str = Query("json", description="json, csv, or markdown"),
    db: AsyncSession = Depends(get_db),
):
    """Export tasks, notes, or decision_logs in the specified format."""
    if entity_type == "tasks":
        rows = (await db.execute(select(Task).order_by(Task.created_at.desc()))).scalars().all()
        data = [_task_to_dict(r) for r in rows]
    elif entity_type == "notes":
        rows = (await db.execute(select(Note).order_by(Note.created_at.desc()))).scalars().all()
        data = [_note_to_dict(r) for r in rows]
    elif entity_type == "decision_logs":
        rows = (await db.execute(select(DecisionLog).order_by(DecisionLog.created_at.desc()))).scalars().all()
        data = [_decision_to_dict(r) for r in rows]
    else:
        return {"error": f"Unknown entity type: {entity_type}. Use tasks, notes, or decision_logs."}

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    if format == "csv":
        content = _to_csv(data)
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={entity_type}_{ts}.csv"},
        )
    elif format == "markdown":
        content = _to_markdown(data, entity_type)
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={entity_type}_{ts}.md"},
        )
    else:
        return data

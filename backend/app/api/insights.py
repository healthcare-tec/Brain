"""AI Proactive Insights API — detects patterns, stale tasks, estimation issues."""

import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.models.task import Task, TaskStatus
from app.models.event import TaskEvent

router = APIRouter()


async def _gather_insight_data(db: AsyncSession) -> dict:
    """Collect data for AI analysis."""
    now = datetime.utcnow()

    # Stale tasks: created > 14 days ago, still not done
    stale_stmt = (
        select(Task)
        .where(Task.status != TaskStatus.DONE.value)
        .where(Task.created_at < now - timedelta(days=14))
        .order_by(Task.created_at.asc())
        .limit(20)
    )
    stale = (await db.execute(stale_stmt)).scalars().all()

    # Overdue tasks
    overdue_stmt = (
        select(Task)
        .where(Task.due_date < now)
        .where(Task.status != TaskStatus.DONE.value)
        .order_by(Task.due_date.asc())
        .limit(20)
    )
    overdue = (await db.execute(overdue_stmt)).scalars().all()

    # Estimation mismatches (> 50% off)
    est_stmt = (
        select(Task)
        .where(
            and_(
                Task.estimated_time.isnot(None),
                Task.actual_time.isnot(None),
                Task.status == TaskStatus.DONE.value,
            )
        )
        .order_by(Task.completed_at.desc())
        .limit(50)
    )
    est_tasks = (await db.execute(est_stmt)).scalars().all()
    bad_estimates = []
    for t in est_tasks:
        if t.estimated_time and t.actual_time:
            ratio = t.actual_time / t.estimated_time
            if ratio > 1.5 or ratio < 0.5:
                bad_estimates.append({
                    "title": t.title,
                    "estimated": t.estimated_time,
                    "actual": t.actual_time,
                    "ratio": round(ratio, 2),
                })

    # Completion rate last 7 days
    week_ago = now - timedelta(days=7)
    completed_7d = (await db.execute(
        select(func.count(Task.id))
        .where(Task.completed_at >= week_ago)
        .where(Task.status == TaskStatus.DONE.value)
    )).scalar() or 0
    created_7d = (await db.execute(
        select(func.count(Task.id)).where(Task.created_at >= week_ago)
    )).scalar() or 0

    return {
        "stale_tasks": [{"id": t.id, "title": t.title, "days_old": (now - t.created_at).days, "status": t.status} for t in stale],
        "overdue_tasks": [{"id": t.id, "title": t.title, "due_date": t.due_date.isoformat() if t.due_date else None} for t in overdue],
        "bad_estimates": bad_estimates[:10],
        "completion_rate_7d": {"completed": completed_7d, "created": created_7d},
    }


@router.get("/")
async def get_insights(db: AsyncSession = Depends(get_db)):
    """Get proactive insights: stale tasks, overdue, estimation issues."""
    data = await _gather_insight_data(db)

    # Build rule-based insights
    insights = []

    if data["stale_tasks"]:
        insights.append({
            "type": "stale_tasks",
            "severity": "warning",
            "title": f"{len(data['stale_tasks'])} tasks paradas ha mais de 14 dias",
            "description": "Considere revisar, delegar ou mover para 'someday'.",
            "items": data["stale_tasks"][:5],
        })

    if data["overdue_tasks"]:
        insights.append({
            "type": "overdue",
            "severity": "critical",
            "title": f"{len(data['overdue_tasks'])} tasks com prazo vencido",
            "description": "Atualize os prazos ou complete essas tasks.",
            "items": data["overdue_tasks"][:5],
        })

    if data["bad_estimates"]:
        insights.append({
            "type": "estimation",
            "severity": "info",
            "title": f"{len(data['bad_estimates'])} tasks com estimativa imprecisa",
            "description": "Suas estimativas estao mais de 50% fora do tempo real.",
            "items": data["bad_estimates"][:5],
        })

    rate = data["completion_rate_7d"]
    if rate["created"] > 0 and rate["completed"] < rate["created"] * 0.5:
        insights.append({
            "type": "throughput",
            "severity": "warning",
            "title": "Throughput baixo esta semana",
            "description": f"Criou {rate['created']} tasks mas completou apenas {rate['completed']}.",
            "items": [],
        })

    # If OpenAI is available, enhance with AI analysis
    ai_analysis = None
    if settings.OPENAI_API_KEY and (data["stale_tasks"] or data["bad_estimates"]):
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                temperature=0.7,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a productivity coach analyzing a user's task data. "
                            "Provide 2-3 actionable insights in Portuguese (BR). Be concise and specific. "
                            "Format as a JSON object: {\"insights\": [\"insight1\", \"insight2\"]}"
                        ),
                    },
                    {"role": "user", "content": json.dumps(data, default=str)},
                ],
                response_format={"type": "json_object"},
            )
            ai_result = json.loads(response.choices[0].message.content)
            ai_analysis = ai_result.get("insights", [])
        except Exception:
            pass

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "insights": insights,
        "ai_analysis": ai_analysis,
        "raw_data": {
            "stale_count": len(data["stale_tasks"]),
            "overdue_count": len(data["overdue_tasks"]),
            "bad_estimate_count": len(data["bad_estimates"]),
            "completion_rate_7d": data["completion_rate_7d"],
        },
    }

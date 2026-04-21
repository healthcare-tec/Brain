"""
Thinking Engine — Decision Log service.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.decision_log import DecisionLog
from app.schemas.decision_log import DecisionLogCreate, DecisionLogUpdate


async def create_decision_log(
    db: AsyncSession, data: DecisionLogCreate
) -> DecisionLog:
    log = DecisionLog(**data.model_dump(exclude_none=True))
    db.add(log)
    await db.flush()
    return log


async def list_decision_logs(db: AsyncSession, log_type=None) -> list[DecisionLog]:
    stmt = select(DecisionLog).order_by(DecisionLog.created_at.desc())
    if log_type:
        stmt = stmt.where(DecisionLog.log_type == log_type)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_decision_log(db: AsyncSession, log_id: str) -> DecisionLog | None:
    return await db.get(DecisionLog, log_id)


async def update_decision_log(
    db: AsyncSession, log_id: str, data: DecisionLogUpdate
) -> DecisionLog | None:
    log = await db.get(DecisionLog, log_id)
    if not log:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(log, field, value)
    log.updated_at = datetime.utcnow()
    await db.flush()
    return log


async def delete_decision_log(db: AsyncSession, log_id: str) -> bool:
    log = await db.get(DecisionLog, log_id)
    if not log:
        return False
    await db.delete(log)
    await db.flush()
    return True

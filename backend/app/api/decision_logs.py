"""
Thinking Engine — Decision Log API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.decision_log import DecisionLogType
from app.schemas.decision_log import (
    DecisionLogCreate, DecisionLogUpdate, DecisionLogResponse,
)
from app.services import decision_log_service

router = APIRouter()


@router.post("/", response_model=DecisionLogResponse, status_code=201)
async def create_decision_log(
    data: DecisionLogCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new decision log / thinking note."""
    return await decision_log_service.create_decision_log(db, data)


@router.get("/", response_model=list[DecisionLogResponse])
async def list_decision_logs(
    log_type: DecisionLogType | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List decision logs, optionally filtered by type."""
    return await decision_log_service.list_decision_logs(db, log_type)


@router.get("/{log_id}", response_model=DecisionLogResponse)
async def get_decision_log(log_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single decision log."""
    log = await decision_log_service.get_decision_log(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Decision log not found")
    return log


@router.patch("/{log_id}", response_model=DecisionLogResponse)
async def update_decision_log(
    log_id: str, data: DecisionLogUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a decision log."""
    log = await decision_log_service.update_decision_log(db, log_id, data)
    if not log:
        raise HTTPException(status_code=404, detail="Decision log not found")
    return log


@router.delete("/{log_id}", status_code=204)
async def delete_decision_log(log_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a decision log."""
    if not await decision_log_service.delete_decision_log(db, log_id):
        raise HTTPException(status_code=404, detail="Decision log not found")

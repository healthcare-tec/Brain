"""
Capture Engine + Clarification Engine API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.inbox import InboxStatus
from app.schemas.inbox import InboxItemCreate, InboxItemClarify, InboxItemResponse
from app.services import inbox_service

router = APIRouter()


@router.post("/", response_model=InboxItemResponse, status_code=201)
async def capture_item(data: InboxItemCreate, db: AsyncSession = Depends(get_db)):
    """Capture a new item into the inbox (frictionless input)."""
    item = await inbox_service.capture(db, data)
    return item


@router.get("/", response_model=list[InboxItemResponse])
async def list_inbox(
    status: InboxStatus | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List inbox items, optionally filtered by status."""
    return await inbox_service.list_inbox(db, status)


@router.get("/{item_id}", response_model=InboxItemResponse)
async def get_inbox_item(item_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single inbox item."""
    item = await inbox_service.get_inbox_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inbox item not found")
    return item


@router.post("/{item_id}/clarify", response_model=InboxItemResponse)
async def clarify_item(
    item_id: str, data: InboxItemClarify, db: AsyncSession = Depends(get_db)
):
    """Clarification Engine: process an inbox item into task/project/note/trash."""
    try:
        return await inbox_service.clarify(db, item_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{item_id}", status_code=204)
async def delete_inbox_item(item_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an inbox item."""
    if not await inbox_service.delete_inbox_item(db, item_id):
        raise HTTPException(status_code=404, detail="Inbox item not found")

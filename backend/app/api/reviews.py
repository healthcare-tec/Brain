"""
Feedback System — Review API endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import review_service

router = APIRouter()


@router.get("/weekly")
async def weekly_review(db: AsyncSession = Depends(get_db)):
    """Generate a weekly review summary."""
    return await review_service.get_weekly_review(db)

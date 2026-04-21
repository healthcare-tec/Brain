"""
Charlie — API routers.
"""

from fastapi import APIRouter

from app.api.inbox import router as inbox_router
from app.api.tasks import router as tasks_router
from app.api.projects import router as projects_router
from app.api.decision_logs import router as decision_logs_router
from app.api.notes import router as notes_router
from app.api.reviews import router as reviews_router
from app.api.ai import router as ai_router
from app.api.events import router as events_router

api_router = APIRouter(prefix="/api")

api_router.include_router(inbox_router, prefix="/inbox", tags=["Inbox (Capture Engine)"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
api_router.include_router(decision_logs_router, prefix="/decision-logs", tags=["Thinking Engine"])
api_router.include_router(notes_router, prefix="/notes", tags=["Knowledge System"])
api_router.include_router(reviews_router, prefix="/reviews", tags=["Feedback System"])
api_router.include_router(ai_router, prefix="/ai", tags=["AI Cognitive Layer"])
api_router.include_router(events_router, prefix="/events", tags=["Event System"])

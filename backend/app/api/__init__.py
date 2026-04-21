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
from app.api.search import router as search_router
from app.api.analytics import router as analytics_router
from app.api.export import router as export_router
from app.api.voice import router as voice_router
from app.api.insights import router as insights_router
from app.api.debug_env import router as debug_env_router

api_router = APIRouter(prefix="/api")

api_router.include_router(inbox_router, prefix="/inbox", tags=["Inbox (Capture Engine)"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
api_router.include_router(decision_logs_router, prefix="/decision-logs", tags=["Thinking Engine"])
api_router.include_router(notes_router, prefix="/notes", tags=["Knowledge System"])
api_router.include_router(reviews_router, prefix="/reviews", tags=["Feedback System"])
api_router.include_router(ai_router, prefix="/ai", tags=["AI Cognitive Layer"])
api_router.include_router(events_router, prefix="/events", tags=["Event System"])
api_router.include_router(search_router, prefix="/search", tags=["Global Search"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics Dashboard"])
api_router.include_router(export_router, prefix="/export", tags=["Data Export"])
api_router.include_router(voice_router, prefix="/voice", tags=["Voice Capture"])
api_router.include_router(insights_router, prefix="/insights", tags=["AI Proactive Insights"])
api_router.include_router(debug_env_router, prefix="/debug", tags=["Debug (Temporary)"])

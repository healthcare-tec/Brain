"""
Charlie — Event System.
All key actions generate events that feed the Memory Palace and AI analysis.
"""

from app.events.emitter import emit_event

__all__ = ["emit_event"]

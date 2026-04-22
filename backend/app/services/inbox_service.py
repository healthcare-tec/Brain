"""
Capture Engine + Clarification Engine service.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inbox import InboxItem, InboxStatus
from app.models.task import Task, TaskStatus
from app.models.project import Project
from app.models.note import Note, NoteCategory
from app.models.decision_log import DecisionLog, DecisionLogType
from app.models.event import EventType
from app.schemas.inbox import InboxItemCreate, InboxItemClarify
from app.events.emitter import emit_event


async def capture(db: AsyncSession, data: InboxItemCreate) -> InboxItem:
    """Capture a new item into the inbox."""
    item = InboxItem(content=data.content, item_type=data.item_type)
    db.add(item)
    await db.flush()
    await emit_event(
        db,
        EventType.CAPTURED,
        description=f"Captured inbox item: {data.content[:80]}",
        metadata={"inbox_id": item.id, "item_type": data.item_type},
    )
    return item


async def list_inbox(
    db: AsyncSession, status: Optional[InboxStatus] = None
) -> list[InboxItem]:
    """List inbox items, optionally filtered by status."""
    stmt = select(InboxItem).order_by(InboxItem.captured_at.desc())
    if status:
        stmt = stmt.where(InboxItem.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_inbox_item(db: AsyncSession, item_id: str) -> Optional[InboxItem]:
    return await db.get(InboxItem, item_id)


async def clarify(
    db: AsyncSession, item_id: str, data: InboxItemClarify
) -> InboxItem:
    """
    Clarification Engine: process an inbox item into task/project/note/idea/trash.

    Supported values for clarified_as:
      task    → creates a Task (status=next)
      project → creates a Project
      note    → creates a Note (PARA category)
      idea    → creates DecisionLog and/or Note depending on idea_destination:
                  "thinking" → DecisionLog only (for analysis)
                  "notes"    → Note only (for reference)
                  "both"     → DecisionLog + Note (default)
      trash   → marks item as trashed, no entity created

    Extra field for idea routing:
      idea_destination: "thinking" | "notes" | "both"  (default: "both")
    """
    item = await db.get(InboxItem, item_id)
    if not item:
        raise ValueError("Inbox item not found")

    ref_id = None
    title = data.title or item.content[:500]

    if data.clarified_as == "task":
        # Map priority to a value accepted by TaskPriority enum: low|medium|high|critical
        # "urgent" (legacy frontend value) is mapped to "critical"
        _raw_priority = (data.priority or "").lower()
        if _raw_priority == "urgent":
            priority = "critical"
        elif _raw_priority in ("low", "medium", "high", "critical"):
            priority = _raw_priority
        else:
            priority = "medium"
        # Blind project_id: pass None if empty string or non-existent to avoid FK error
        project_id = data.project_id or None
        task = Task(
            title=title,
            description=data.description or item.content,
            context=data.context,
            project_id=project_id,
            status=TaskStatus.NEXT,
            priority=priority,
        )
        db.add(task)
        await db.flush()
        ref_id = task.id
        await emit_event(
            db, EventType.CLARIFIED, task_id=task.id,
            description=f"Inbox item clarified as task: {task.title}",
            metadata={"inbox_id": item.id},
        )

    elif data.clarified_as == "project":
        project = Project(
            name=title,
            description=data.description or item.content,
        )
        db.add(project)
        await db.flush()
        ref_id = project.id
        await emit_event(
            db, EventType.CLARIFIED,
            description=f"Inbox item clarified as project: {project.name}",
            metadata={"inbox_id": item.id, "project_id": project.id},
        )

    elif data.clarified_as == "note":
        # Resolve PARA category
        cat = NoteCategory.RESOURCE
        if data.category:
            try:
                cat = NoteCategory(data.category)
            except ValueError:
                pass
        note = Note(
            title=title,
            content=item.content,
            category=cat,
        )
        db.add(note)
        await db.flush()
        ref_id = note.id
        await emit_event(
            db, EventType.CLARIFIED,
            description=f"Inbox item clarified as note: {note.title}",
            metadata={"inbox_id": item.id, "note_id": note.id},
        )

    elif data.clarified_as == "idea":
        # idea_destination controls where the idea is routed:
        #   "thinking" → DecisionLog only
        #   "notes"    → Note only (PARA category: resource)
        #   "both"     → DecisionLog + Note (default)
        destination = (getattr(data, "idea_destination", None) or "both").lower()
        if destination not in ("thinking", "notes", "both"):
            destination = "both"

        decision_log_id = None
        note_id = None

        # ── Create DecisionLog (Thinking Engine) ──────────────────────────────
        if destination in ("thinking", "both"):
            log = DecisionLog(
                title=title,
                log_type=DecisionLogType.PROBLEM_BREAKDOWN.value,
                context=item.content,
                hypotheses=data.description or None,
                tags="idea,inbox",
            )
            db.add(log)
            await db.flush()
            decision_log_id = log.id
            ref_id = log.id  # primary ref points to the decision log

        # ── Create Note (Knowledge Base) ──────────────────────────────────────
        if destination in ("notes", "both"):
            note = Note(
                title=title,
                content=item.content,
                category=NoteCategory.RESOURCE,
                tags="idea,inbox",
            )
            db.add(note)
            await db.flush()
            note_id = note.id
            if ref_id is None:
                ref_id = note.id  # if no decision log, note is the primary ref

        await emit_event(
            db, EventType.CLARIFIED,
            description=f"Inbox item clarified as idea ({destination}): {title}",
            metadata={
                "inbox_id": item.id,
                "idea_destination": destination,
                "decision_log_id": decision_log_id,
                "note_id": note_id,
            },
        )

    elif data.clarified_as == "trash":
        await emit_event(
            db, EventType.CLARIFIED,
            description=f"Inbox item trashed: {item.content[:80]}",
            metadata={"inbox_id": item.id},
        )

    item.status = (
        InboxStatus.PROCESSED if data.clarified_as != "trash" else InboxStatus.TRASHED
    )
    item.clarified_as = data.clarified_as
    item.clarified_ref_id = ref_id
    item.processed_at = datetime.utcnow()
    await db.flush()
    return item


async def delete_inbox_item(db: AsyncSession, item_id: str) -> bool:
    item = await db.get(InboxItem, item_id)
    if not item:
        return False
    await db.delete(item)
    await db.flush()
    return True

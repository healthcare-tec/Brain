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
    Clarification Engine: process an inbox item into task/project/note/trash.

    Supported values for clarified_as:
      task    → creates a Task (status=next)
      project → creates a Project
      note    → creates a Note (PARA category)
      idea    → treated as note (category=resource)
      trash   → marks item as trashed, no entity created
    """
    item = await db.get(InboxItem, item_id)
    if not item:
        raise ValueError("Inbox item not found")

    ref_id = None
    # Normalise "idea" → "note" for entity creation
    target = data.clarified_as if data.clarified_as != "idea" else "note"

    if target == "task":
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
            title=data.title or item.content[:500],
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

    elif target == "project":
        project = Project(
            name=data.title or item.content[:500],
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

    elif target == "note":
        # Resolve PARA category
        cat = NoteCategory.RESOURCE
        if data.category:
            try:
                cat = NoteCategory(data.category)
            except ValueError:
                pass
        note = Note(
            title=data.title or item.content[:500],
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

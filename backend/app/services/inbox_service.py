"""
Capture Engine + Clarification Engine service.
"""

from datetime import datetime

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
    db: AsyncSession, status: InboxStatus | None = None
) -> list[InboxItem]:
    """List inbox items, optionally filtered by status."""
    stmt = select(InboxItem).order_by(InboxItem.captured_at.desc())
    if status:
        stmt = stmt.where(InboxItem.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_inbox_item(db: AsyncSession, item_id: str) -> InboxItem | None:
    return await db.get(InboxItem, item_id)


async def clarify(
    db: AsyncSession, item_id: str, data: InboxItemClarify
) -> InboxItem:
    """Clarification Engine: process an inbox item into task/project/note/trash."""
    item = await db.get(InboxItem, item_id)
    if not item:
        raise ValueError("Inbox item not found")

    ref_id = None

    if data.clarified_as == "task":
        task = Task(
            title=data.title or item.content[:500],
            description=data.description or item.content,
            context=data.context,
            project_id=data.project_id,
            status=TaskStatus.NEXT,
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

    elif data.clarified_as == "note":
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

    item.status = InboxStatus.PROCESSED if data.clarified_as != "trash" else InboxStatus.TRASHED
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

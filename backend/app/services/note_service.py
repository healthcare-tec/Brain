"""
Knowledge System — Note service.
Manages note metadata in PostgreSQL and Markdown files on the filesystem.
"""

import os
import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note, NoteCategory
from app.schemas.note import NoteCreate, NoteUpdate
from app.config import settings


def _slugify(text: str) -> str:
    """Create a filesystem-safe slug from text."""
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug[:80] or "untitled"


def _category_dir(category: NoteCategory) -> str:
    mapping = {
        NoteCategory.PROJECT: "projects",
        NoteCategory.AREA: "areas",
        NoteCategory.RESOURCE: "resources",
        NoteCategory.ARCHIVE: "archive",
    }
    return mapping.get(category, "resources")


async def create_note(db: AsyncSession, data: NoteCreate) -> Note:
    note = Note(**data.model_dump(exclude_none=True))
    db.add(note)
    await db.flush()

    # Write Markdown file (skip if knowledge base path is not writable)
    if data.content:
        cat_dir = _category_dir(note.category)
        base_path = os.path.join(settings.KNOWLEDGE_BASE_PATH, cat_dir)
        try:
            os.makedirs(base_path, exist_ok=True)
            filename = f"{_slugify(note.title)}.md"
            filepath = os.path.join(base_path, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# {note.title}\n\n")
                if note.tags:
                    f.write(f"**Tags:** {note.tags}\n\n")
                f.write(data.content)
            note.markdown_path = f"{cat_dir}/{filename}"
            await db.flush()
        except OSError:
            # Knowledge base path not writable (e.g., in tests)
            pass

    return note


async def list_notes(
    db: AsyncSession, category: NoteCategory | None = None
) -> list[Note]:
    stmt = select(Note).order_by(Note.created_at.desc())
    if category:
        stmt = stmt.where(Note.category == category)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_note(db: AsyncSession, note_id: str) -> Note | None:
    return await db.get(Note, note_id)


async def update_note(
    db: AsyncSession, note_id: str, data: NoteUpdate
) -> Note | None:
    note = await db.get(Note, note_id)
    if not note:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)
    note.updated_at = datetime.utcnow()

    # Update Markdown file if content changed
    if "content" in update_data and note.markdown_path:
        filepath = os.path.join(settings.KNOWLEDGE_BASE_PATH, note.markdown_path)
        if os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# {note.title}\n\n")
                if note.tags:
                    f.write(f"**Tags:** {note.tags}\n\n")
                f.write(note.content or "")

    await db.flush()
    return note


async def delete_note(db: AsyncSession, note_id: str) -> bool:
    note = await db.get(Note, note_id)
    if not note:
        return False
    # Remove Markdown file
    if note.markdown_path:
        filepath = os.path.join(settings.KNOWLEDGE_BASE_PATH, note.markdown_path)
        if os.path.exists(filepath):
            os.remove(filepath)
    await db.delete(note)
    await db.flush()
    return True

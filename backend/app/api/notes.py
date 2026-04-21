"""
Knowledge System — Notes API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.note import NoteCategory
from app.schemas.note import NoteCreate, NoteUpdate, NoteResponse
from app.services import note_service

router = APIRouter()


@router.post("/", response_model=NoteResponse, status_code=201)
async def create_note(data: NoteCreate, db: AsyncSession = Depends(get_db)):
    """Create a new note (stored in DB + Markdown file)."""
    return await note_service.create_note(db, data)


@router.get("/", response_model=list[NoteResponse])
async def list_notes(
    category: NoteCategory | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List notes, optionally filtered by PARA category."""
    return await note_service.list_notes(db, category)


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single note."""
    note = await note_service.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.patch("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str, data: NoteUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a note."""
    note = await note_service.update_note(db, note_id, data)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a note and its Markdown file."""
    if not await note_service.delete_note(db, note_id):
        raise HTTPException(status_code=404, detail="Note not found")

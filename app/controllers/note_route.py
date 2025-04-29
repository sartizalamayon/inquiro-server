# app/controllers/note_route.py
from fastapi import APIRouter, Depends, HTTPException, Path, Body
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.mongodb import get_database
from app.models.note import NoteCreate, NoteUpdate
from app.services import note_service
from typing import List, Dict, Any
from bson import ObjectId

router = APIRouter(
    prefix="/notes",
    tags=["notes"],
    responses={404: {"description": "Not found"}},
)

@router.post("/")
async def create_note(
    note: NoteCreate = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create a new note for a paper section.
    """
    try:
        note_id = await note_service.create_note(db, note)
        return {"success": True, "note_id": note_id}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create note: {str(e)}"
        )

@router.get("/paper/{paper_id}")
async def get_notes_by_paper(
    paper_id: str = Path(..., description="The ID of the paper"),
    user_email: str = None,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get all notes for a specific paper.
    Optionally filter by user_email.
    """
    try:
        notes = await note_service.get_notes_by_paper(db, paper_id, user_email)
        return notes
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch notes: {str(e)}"
        )

@router.get("/{note_id}")
async def get_note(
    note_id: str = Path(..., description="The ID of the note to get"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get a note by its ID.
    """
    note = await note_service.get_note(db, note_id)
    if note is None:
        raise HTTPException(
            status_code=404,
            detail=f"Note with ID {note_id} not found"
        )
    return note

@router.put("/{note_id}")
async def update_note(
    note_id: str = Path(..., description="The ID of the note to update"),
    note_update: NoteUpdate = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update a note's content.
    """
    # First check if note exists
    note = await note_service.get_note(db, note_id)
    if note is None:
        raise HTTPException(
            status_code=404,
            detail=f"Note with ID {note_id} not found"
        )
    
    success = await note_service.update_note(db, note_id, note_update)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to update note"
        )
    
    return {"success": True, "message": "Note updated successfully"}

@router.delete("/{note_id}")
async def delete_note(
    note_id: str = Path(..., description="The ID of the note to delete"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Delete a note by its ID.
    """
    # First check if note exists
    note = await note_service.get_note(db, note_id)
    if note is None:
        raise HTTPException(
            status_code=404,
            detail=f"Note with ID {note_id} not found"
        )
    
    success = await note_service.delete_note(db, note_id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete note"
        )
    
    return {"success": True, "message": "Note deleted successfully"}

@router.delete("/paper/{paper_id}")
async def delete_notes_by_paper(
    paper_id: str = Path(..., description="The ID of the paper"),
    user_email: str = None,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Delete all notes for a specific paper.
    Optionally filter by user_email.
    """
    try:
        deleted_count = await note_service.delete_notes_by_paper(db, paper_id, user_email)
        return {"success": True, "deleted_count": deleted_count}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete notes: {str(e)}"
        )

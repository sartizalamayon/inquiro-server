from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson.objectid import ObjectId
from app.models.note import NoteModel, NoteCreate, NoteUpdate
from typing import List, Optional

async def create_note(db: AsyncIOMotorDatabase, note: NoteCreate) -> str:
    """
    Create a new note in the database.
    Returns the ID of the created note.
    """
    note_data = note.model_dump(exclude={"id"})
    note_data["created_at"] = datetime.now()
    
    result = await db["notes"].insert_one(note_data)
    return str(result.inserted_id)

async def get_notes_by_paper(db: AsyncIOMotorDatabase, paper_id: str, user_email: Optional[str] = None) -> List[NoteModel]:
    """
    Get all notes for a specific paper.
    If user_email is provided, only returns notes for that user.
    """
    query = {"paper_id": paper_id}
    if user_email:
        query["user_email"] = user_email
        
    cursor = db["notes"].find(query).sort("created_at", -1)
    notes = []
    
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
        notes.append(doc)
        
    return notes

async def get_note(db: AsyncIOMotorDatabase, note_id: str) -> Optional[dict]:
    """
    Get a note by its ID.
    """
    note = await db["notes"].find_one({"_id": ObjectId(note_id)})
    if note:
        note["_id"] = str(note["_id"])  # Convert ObjectId to string
    return note

async def update_note(db: AsyncIOMotorDatabase, note_id: str, note_update: NoteUpdate) -> bool:
    """
    Update a note in the database.
    Returns True if the update was successful, False otherwise.
    """
    update_data = note_update.model_dump(exclude={"id"})
    update_data["updated_at"] = datetime.now()
    
    result = await db["notes"].update_one(
        {"_id": ObjectId(note_id)},
        {"$set": update_data}
    )
    
    return result.modified_count > 0

async def delete_note(db: AsyncIOMotorDatabase, note_id: str) -> bool:
    """
    Delete a note from the database.
    Returns True if the deletion was successful, False otherwise.
    """
    result = await db["notes"].delete_one({"_id": ObjectId(note_id)})
    return result.deleted_count > 0

async def delete_notes_by_paper(db: AsyncIOMotorDatabase, paper_id: str, user_email: Optional[str] = None) -> int:
    """
    Delete all notes for a specific paper.
    If user_email is provided, only deletes notes for that user.
    Returns the number of deleted notes.
    """
    query = {"paper_id": paper_id}
    if user_email:
        query["user_email"] = user_email
        
    result = await db["notes"].delete_many(query)
    return result.deleted_count

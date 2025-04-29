from pydantic import Field, EmailStr
from typing import Optional
from datetime import datetime
from .base import MongoBaseModel, PyObjectId
from bson import ObjectId

class NoteModel(MongoBaseModel):
    paper_id: str
    user_email: EmailStr
    section_id: str
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

class NoteCreate(MongoBaseModel):
    paper_id: str
    user_email: EmailStr
    section_id: str
    content: str

class NoteUpdate(MongoBaseModel):
    content: str
    updated_at: datetime = Field(default_factory=datetime.now)

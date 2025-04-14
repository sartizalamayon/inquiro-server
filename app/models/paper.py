# app/models/paper.py
from pydantic import Field, EmailStr
from typing import Optional, List
from datetime import datetime
from .base import MongoBaseModel, PyObjectId

class AuthorModel(MongoBaseModel):
    name: str = ""
    affiliation: str = ""
    email: str = ""

class PaperModel(MongoBaseModel):
    user_email: EmailStr
    title: str = ""
    authors: List[AuthorModel] = []
    date_published: str = ""
    metadata: dict = {}
    references: List[str] = []
    summary: dict = {}
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

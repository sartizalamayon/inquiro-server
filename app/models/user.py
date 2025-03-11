# models/user.py
from pydantic import Field, EmailStr
from typing import Optional
from datetime import datetime
from .base import MongoBaseModel

class UserModel(MongoBaseModel):
    name: str
    email: EmailStr
    profile_picture: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

# Model for creating a new user.
class UserCreate(MongoBaseModel):
    name: str
    email: EmailStr
    profile_picture: Optional[str] = None

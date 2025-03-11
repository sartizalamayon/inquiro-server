# models/user.py
from pydantic import Field, EmailStr
from typing import Optional, List
from datetime import datetime
from .base import MongoBaseModel, PyObjectId

class UserModel(MongoBaseModel):
    name: str
    email: EmailStr
    favorites: Optional[List[PyObjectId]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

# For creating a new user, we only need name and email.
class UserCreate(MongoBaseModel):
    name: str
    email: EmailStr

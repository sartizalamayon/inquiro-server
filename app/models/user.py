# models/user.py
from pydantic import Field, EmailStr
from typing import Optional, List
from datetime import datetime
from .base import MongoBaseModel, PyObjectId

class UserModel(MongoBaseModel):
    name: str
    email: EmailStr
    hashed_password: Optional[str] = None  # Store hashed password as base64 string
    favorites: Optional[List[PyObjectId]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    auth_provider: Optional[str] = None  # Track auth provider (email, google, github)

# For creating a new user
class UserCreate(MongoBaseModel):
    name: str
    email: EmailStr
    password: Optional[str] = None  # Make password optional for OAuth

# For validating credentials
class UserCredentials(MongoBaseModel):
    email: EmailStr
    password: str
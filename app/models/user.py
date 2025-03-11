# Import necessary modules from Pydantic, typing, datetime, and bson.
from pydantic import BaseModel, Field, EmailStr, root_validator
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    # Validator for ObjectId: accepts the value and context info.
    @classmethod
    def validate(cls, v, info):
        # Check if the value is a valid ObjectId.
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        # Return the value as a string.
        return str(v)

# Main Pydantic model for a user.
class UserModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    email: EmailStr
    profile_picture: Optional[str] = None
    favorites: Optional[List[PyObjectId]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        # Allow using field names instead of aliases during population.
        populate_by_name = True


# Model for creating a new user.
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    profile_picture: Optional[str] = None
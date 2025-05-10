from pydantic import Field, EmailStr, BaseModel
from typing import Optional, List
from datetime import datetime
from .base import MongoBaseModel, PyObjectId
from bson import ObjectId

class CollectionModel(MongoBaseModel):
    """MongoDB Collection model for storing paper collections"""
    user_email: str = Field(..., description="Email of the collection owner")
    name: str = Field(..., description="Name of the collection")
    tags: List[str] = Field(default_factory=list, description="User-defined tags for the collection")
    papers: List[str] = Field(default_factory=list, description="List of paper IDs in the collection")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
    
class CollectionCreate(BaseModel):
    """Model for creating a new collection"""
    name: str = Field(..., min_length=1, description="Name of the collection")
    tags: List[str] = Field(default_factory=list, description="User-defined tags for the collection")
    
class CollectionUpdate(BaseModel):
    """Model for updating an existing collection"""
    name: Optional[str] = Field(None, min_length=1, description="New name for the collection")
    tags: Optional[List[str]] = Field(None, description="Updated tags for the collection")
    
class CollectionResponse(BaseModel):
    """Model for collection response"""
    id: str = Field(..., alias="_id")
    user_email: str
    name: str
    tags: List[str]
    papers: List[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        
class PaperInCollection(BaseModel):
    """Model for papers in a collection"""
    paper_id: str = Field(..., description="Paper ID to add/remove from collection")


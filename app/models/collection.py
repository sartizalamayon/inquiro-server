from pydantic import Field, EmailStr
from typing import Optional, List
from datetime import datetime
from .base import MongoBaseModel, PyObjectId

class CollectionModel(MongoBaseModel):
    user_id: PyObjectId
    name: str
    description: str
    tags: List[PyObjectId]
    papers: List[PyObjectId]
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
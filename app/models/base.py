# models/base.py
from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId

# Custom ObjectId type for validation.
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, info):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

# Base model for MongoDB documents with _id to id conversion and custom JSON serialization.
class MongoBaseModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    class Config:
        populate_by_name = True
        # Custom JSON encoder for ObjectId (and PyObjectId) to convert it to a string.
        json_encoders = {
            ObjectId: lambda oid: str(oid)
        }

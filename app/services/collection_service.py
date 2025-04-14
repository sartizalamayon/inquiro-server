from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException

from app.models.collection import CollectionModel


async def create_collection(
    db: AsyncIOMotorDatabase,
    user_id: str,
    name: str,
    description: str,
    tags: List[str]
):
    # Check if user exists
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if that user already has a collection with that name
    existing_collection = await db.collections.find_one({"user_id": ObjectId(user_id), "name": name})
    if existing_collection:
        raise HTTPException(status_code=409, detail="Collection with this name already exists")
    
    collection_data = {
        "user_id": ObjectId(user_id),
        "name": name,
        "description": description,
        "tags": [ObjectId(tag) for tag in tags],
        "papers": [],
        "created_at": datetime.now(),
        "updated_at": None
    }

    result = await db.collections.insert_one(collection_data)
    created_doc = await db.collections.find_one({"_id": result.inserted_id})
    return CollectionModel(**created_doc)       


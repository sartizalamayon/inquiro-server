# services/user_service.py
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import UserModel, UserCreate

async def create_user(db: AsyncIOMotorDatabase, user: UserCreate) -> UserModel:
    user_data = user.model_dump(exclude_unset=True)
    user_data["created_at"] = datetime.utcnow()
    result = await db.users.insert_one(user_data)
    created_doc = await db.users.find_one({"_id": result.inserted_id})
    return UserModel(**created_doc)

async def get_all_users(db: AsyncIOMotorDatabase, skip: int = 0, limit: int = 100) -> List[UserModel]:
    cursor = db.users.find().skip(skip).limit(limit)
    users = []
    async for doc in cursor:
        users.append(UserModel(**doc))
    return users

async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[UserModel]:
    doc = await db.users.find_one({"email": email})
    if doc:
        return UserModel(**doc)
    return None

async def get_user_favorites_by_id(db: AsyncIOMotorDatabase, user_id: str) -> Optional[List[str]]:
    if not ObjectId.is_valid(user_id):
        return None
    doc = await db.users.find_one({"_id": ObjectId(user_id)})
    if doc:
        favorites = doc.get("favorites", [])
        return [str(fav) for fav in favorites]
    return None

async def add_favorite(db: AsyncIOMotorDatabase, user_id: str, favorite_id: str) -> Optional[UserModel]:
    """
    Adds a favorite item to the user's favorites list.
    Returns the updated UserModel, or None if user or favorite_id is invalid.
    """
    if not ObjectId.is_valid(user_id) or not ObjectId.is_valid(favorite_id):
        return None
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$push": {"favorites": ObjectId(favorite_id)}}
    )
    if result.modified_count:
        doc = await db.users.find_one({"_id": ObjectId(user_id)})
        return UserModel(**doc)
    return None

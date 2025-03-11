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

async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> Optional[UserModel]:
    if not ObjectId.is_valid(user_id):
        return None
    doc = await db.users.find_one({"_id": ObjectId(user_id)})
    if doc:
        return UserModel(**doc)
    return None

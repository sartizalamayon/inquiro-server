# services/user_service.py
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException
import hashlib
import os
import base64

from app.models.user import UserModel, UserCreate

def hash_password(password: str) -> str:
    """Hash a password for storing.
    Returns base64 encoded string of salt+key"""
    salt = os.urandom(32)  # 32 bytes salt
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    # Convert bytes to base64 string for storage
    return base64.b64encode(salt + key).decode('utf-8')

def verify_password(stored_password_b64: str, provided_password: str) -> bool:
    """Verify a stored password against a provided password"""
    # Convert from base64 string back to bytes
    stored_password = base64.b64decode(stored_password_b64.encode('utf-8'))
    salt = stored_password[:32]  # Get the salt
    stored_key = stored_password[32:]  # Get the key
    key = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return key == stored_key

async def create_user(db: AsyncIOMotorDatabase, user: UserCreate) -> UserModel:
    """Create a new user, handling both email/password and OAuth sign-ups."""
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        # For OAuth users, just return the existing user
        if not user.password:
            return UserModel(**existing_user)
        # For email/password, raise error
        raise HTTPException(status_code=409, detail="User with this email already exists")
    
    user_data = user.model_dump(exclude_unset=True)
    
    # Handle password if provided (email/password flow)
    if "password" in user_data and user_data["password"]:
        user_data["hashed_password"] = hash_password(user_data.pop("password"))
        user_data["auth_provider"] = "email"
    else:
        # OAuth flow
        user_data["auth_provider"] = "oauth"
    
    user_data["created_at"] = datetime.now()
    user_data["favorites"] = []
    
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

async def validate_credentials(db: AsyncIOMotorDatabase, email: str, password: str) -> Optional[UserModel]:
    """Validate user credentials for email/password login."""
    user_doc = await db.users.find_one({"email": email})
    
    if not user_doc or "hashed_password" not in user_doc:
        return None
    
    if verify_password(user_doc["hashed_password"], password):
        return UserModel(**user_doc)
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

async def update_user_name(db: AsyncIOMotorDatabase, email: str, new_user_name: str) -> Optional[UserModel]:
    """
    Update the user's name.
    Returns the updated UserModel, or None if user is not found.
    """
    result = await db.users.update_one(
        {"email": email},
        {"$set": {"name": new_user_name}}
    )
    if result.modified_count:
        doc = await db.users.find_one({"email": email})
        return UserModel(**doc)
    return None






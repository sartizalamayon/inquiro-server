# controllers/user_routes.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongodb import get_database
from app.models.user import UserModel, UserCreate
from app.services import user_service

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=UserModel)
async def create_new_user(user: UserCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    return await user_service.create_user(db, user)

@router.get("/", response_model=List[UserModel])
async def read_users(db: AsyncIOMotorDatabase = Depends(get_database), skip: int = 0, limit: int = 100):
    return await user_service.get_all_users(db, skip, limit)

@router.get("/{user_id}", response_model=UserModel)
async def read_user(user_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

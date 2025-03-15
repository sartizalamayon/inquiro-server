# controllers/user_routes.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

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

@router.get("/{email}", response_model=UserModel)
async def read_user(email: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    user = await user_service.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/{user_id}/favorites", response_model=List[str])
async def read_user_favorites(user_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    favorites = await user_service.get_user_favorites_by_id(db, user_id)
    if favorites is None:
        raise HTTPException(status_code=404, detail="User not found")
    return favorites

# Define a simple model for adding a favorite
class FavoriteCreate(BaseModel):
    favorite_id: str

@router.post("/{user_id}/favorites", response_model=UserModel)
async def add_favorite_route(
    user_id: str,
    favorite: FavoriteCreate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    updated_user = await user_service.add_favorite(db, user_id, favorite.favorite_id)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User or favorite invalid")
    return updated_user

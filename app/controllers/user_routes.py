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



# Create a new user
@router.post("/", response_model=UserModel)
async def create_new_user(user: UserCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    try:
        return await user_service.create_user(db, user)
    except HTTPException as e:
        raise e
    except Exception as e:
        error_msg = str(e)
        if "validation error" in error_msg:
            raise HTTPException(status_code=400, detail="Invalid data format. Please check your inputs.")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to create user: {error_msg}")


# Get all users
@router.get("/", response_model=List[UserModel])
async def read_users(db: AsyncIOMotorDatabase = Depends(get_database), skip: int = 0, limit: int = 100):
    return await user_service.get_all_users(db, skip, limit)

# Get a user by email
@router.get("/{email}", response_model=UserModel)
async def read_user(email: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    user = await user_service.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user



class CredentialsModel(BaseModel):
    email: str
    password: str

# Validate user credentials
@router.post("/validate", response_model=UserModel)
async def validate_user_credentials(
    credentials: CredentialsModel,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    user = await user_service.validate_credentials(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

# Get user favorites
@router.get("/{user_id}/favorites", response_model=List[str])
async def read_user_favorites(user_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    favorites = await user_service.get_user_favorites_by_id(db, user_id)
    if favorites is None:
        raise HTTPException(status_code=404, detail="User not found")
    return favorites


class FavoriteCreate(BaseModel):
    favorite_id: str

# Add a favorite to a user
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
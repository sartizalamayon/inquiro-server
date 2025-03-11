from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.database.mongodb import get_database
from app.models.user import UserModel 
from app.services.user_service import UserService
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

async def get_user_service(db: AsyncIOMotorDatabase = Depends(get_database)):
    return UserService(db)

# Get all users
@router.get("/", response_model=List[UserModel])
async def read_users(user_service: UserService = Depends(get_user_service)):
    return await user_service.get_all_users()

# Get a specific user by ID
@router.get("/{user_id}", response_model=UserModel)
async def read_user(
    user_id: str, 
    user_service: UserService = Depends(get_user_service)
):
    """
    Retrieve a specific user by ID.
    """
    user = await user_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


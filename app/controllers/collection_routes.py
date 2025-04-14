from fastapi import APIRouter, Depends
from app.database.mongodb import get_db
import os
from app.services import collection_service
from typing import List

router = APIRouter(
    prefix="/collection",
    tags=["collection"],
    responses={404: {"description": "Not found"}},
)   

@router.post('/create-collection')
async def create_collection(user_id: str, name: str, description: str, tags: List[str], db = Depends(get_db)):
    collection = await collection_service.create_collection(db, user_id, name, description, tags)
    return {"collection": collection}
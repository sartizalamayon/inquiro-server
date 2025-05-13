from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.mongodb import get_database
from app.services.permission_service import (
    grant_permission,
    revoke_permission,
    list_permissions_for_collection,
    list_collections_for_user,
    get_paper_access,
)
from typing import List
from app.models.permission import PermissionDoc, PermissionCreate

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.post("/", response_model=PermissionDoc, status_code=status.HTTP_201_CREATED)
async def share_collection(
    data: PermissionCreate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        return await grant_permission(db, data, data.granted_by)
    except Exception as e:
        raise HTTPException(500, str(e))


@router.delete(
    "/{collection_id}/{user_email}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def unshare_collection(
    collection_id: str,
    user_email: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        await revoke_permission(db, collection_id, user_email)
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get(
    "/collections/{collection_id}",
    response_model=List[PermissionDoc]
)
async def get_collection_shares(
    collection_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        return await list_permissions_for_collection(db, collection_id)
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get(
    "/users/{user_email}",
    response_model=List[PermissionDoc]
)
async def get_user_permissions(
    user_email: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        return await list_collections_for_user(db, user_email)
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get(
    "/paper/{paper_id}/{user_email}",
    response_model=str
)
async def paper_access(
    paper_id: str,
    user_email: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Determine access on a single paper.
    Returns one of "none", "scan", "modify", or "control".
    """
    try:
        access = await get_paper_access(db, paper_id, user_email)
        return access
    except Exception as e:
        raise HTTPException(500, str(e))

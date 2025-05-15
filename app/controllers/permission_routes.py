from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.mongodb import get_database
from app.services.permission_service import (
    grant_permission,
    revoke_permission,
    update_permission,
    list_permissions_for_collection,
    list_collections_for_user,
    get_paper_access,
    get_users_with_access,
    get_user_collection_access_level  # Added import
)
from typing import List, Literal, Union  # Added Union
from app.models.permission import PermissionDoc, PermissionCreate, UserSummary, PermissionUpdate, AccessLevel  # Added AccessLevel


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


@router.get(
    "/{collection_id}/users",
    response_model=List[UserSummary],
    status_code=status.HTTP_200_OK
)
async def get_users_access(
    collection_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get a list of users with access to a specific collection.
    """
    res = await get_users_with_access(
        collection_id,  # Corrected order: collection_id first
        db  # Corrected order: db second
    )
    if not res:
        raise HTTPException(status_code=404, detail="No users found with access to this collection.")
    return res


@router.put(
    "/{collection_id}/{user_email}",
    response_model=PermissionDoc,
    status_code=status.HTTP_200_OK
)
async def update_user_permission(
    collection_id: str,
    user_email: str,
    data: PermissionUpdate,  # Use the new PermissionUpdate model
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update a user's permission for a specific collection.
    """
    try:
        # The granted_by field should be the authenticated user, 
        # for now, it's passed in the request body.
        # You might want to extract this from an auth token in a real app.
        updated_permission = await update_permission(
            db,
            collection_id,
            user_email,
            data.access_level,
            data.granted_by
        )
        return updated_permission
    except ValueError as ve:  # Catch specific error from service
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/{collection_id}/access/{user_email}",
    response_model=Union[AccessLevel, Literal["none"]],
    status_code=status.HTTP_200_OK
)
async def get_user_access_for_collection(
    collection_id: str,
    user_email: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get the access level for a specific user on a specific collection.
    Returns "scan", "modify", "control", or "none".
    """
    try:
        access_level = await get_user_collection_access_level(
            db,
            collection_id,
            user_email
        )
        if access_level == "none":
            return 'scan'  # or whatever default you want to return
            pass 
        return access_level
    except Exception as e:
        # Log the exception e for debugging
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
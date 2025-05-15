from fastapi import APIRouter, Depends, HTTPException, Path, Body, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
import os
from app.services import collection_service
from typing import List, Optional, Dict, Any
from app.models.collection import CollectionCreate, CollectionUpdate, CollectionResponse, PaperInCollection
from app.database.mongodb import get_database

router = APIRouter(
    prefix="/collections",
    tags=["collections"],
    responses={404: {"description": "Not found"}},
)   

# GET all collections for a user
@router.get("/", response_model=List[Dict[str, Any]])
async def get_collections(
    user_email: str = Query(..., description="User email to fetch collections for"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get all collections for a user
    """
    collections = await collection_service.get_collections(db, user_email)
    return collections

# GET a specific collection
@router.get("/{collection_id}", response_model=Dict[str, Any])
async def get_collection(
    collection_id: str = Path(..., description="Collection ID to fetch"),
    user_email: Optional[str] = Query(None, description="Optional user email to verify ownership"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get a specific collection by ID
    """
    collection = await collection_service.get_collection(db, collection_id, user_email)
    return collection

# CREATE a new collection
@router.post("/", response_model=Dict[str, Any])
async def create_collection(
    collection: CollectionCreate,
    user_email: str = Query(..., description="User email creating the collection"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create a new collection
    """
    created_collection = await collection_service.create_collection(db, collection, user_email)
    return created_collection

# UPDATE a collection
@router.patch("/{collection_id}", response_model=Dict[str, Any])
async def update_collection(
    collection_update: CollectionUpdate,
    collection_id: str = Path(..., description="Collection ID to update"),
    user_email: Optional[str] = Query(None, description="Optional user email to verify ownership"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update a collection's name or tags
    """
    updated_collection = await collection_service.update_collection(db, collection_id, collection_update, user_email)
    return updated_collection

# DELETE a collection
@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: str = Path(..., description="Collection ID to delete"),
    user_email: Optional[str] = Query(None, description="Optional user email to verify ownership"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Delete a collection
    """
    success = await collection_service.delete_collection(db, collection_id, user_email)
    return {"success": success, "message": f"Collection {collection_id} deleted successfully"}

# ADD a paper to a collection
@router.post("/{collection_id}/papers")
async def add_paper_to_collection(
    paper: PaperInCollection,
    collection_id: str = Path(..., description="Collection ID to add paper to"),
    user_email: Optional[str] = Query(None, description="Optional user email to verify ownership"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Add a paper to a collection
    """
    result = await collection_service.add_paper_to_collection(db, collection_id, paper.paper_id, user_email)
    return result

# REMOVE a paper from a collection
@router.delete("/{collection_id}/papers/{paper_id}")
async def remove_paper_from_collection(
    collection_id: str = Path(..., description="Collection ID to remove paper from"),
    paper_id: str = Path(..., description="Paper ID to remove"),
    user_email: Optional[str] = Query(None, description="Optional user email to verify ownership"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Remove a paper from a collection
    """
    result = await collection_service.remove_paper_from_collection(db, collection_id, paper_id, user_email)
    return result

# ADD a tag to a collection
@router.post("/{collection_id}/tags/{tag}")
async def add_tag_to_collection(
    collection_id: str = Path(..., description="Collection ID to add tag to"),
    tag: str = Path(..., description="Tag to add"),
    user_email: Optional[str] = Query(None, description="Optional user email to verify ownership"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Add a tag to a collection
    """
    print(f"Adding tag {tag} to collection {collection_id} for user {user_email}")
    result = await collection_service.add_tag_to_collection(db, collection_id, tag, user_email)
    return result

# REMOVE a tag from a collection
@router.delete("/{collection_id}/tags/{tag}")
async def remove_tag_from_collection(
    collection_id: str = Path(..., description="Collection ID to remove tag from"),
    tag: str = Path(..., description="Tag to remove"),
    user_email: Optional[str] = Query(None, description="Optional user email to verify ownership"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Remove a tag from a collection
    """
    result = await collection_service.remove_tag_from_collection(db, collection_id, tag, user_email)
    return result

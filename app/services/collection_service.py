from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException

from app.models.collection import CollectionModel, CollectionCreate, CollectionUpdate

async def get_collections(
    db: AsyncIOMotorDatabase,
    user_email: str
) -> List[Dict[str, Any]]:
    """Get all collections for a user"""
    cursor = db["collections"].find({"user_email": user_email})
    collections = []
    async for collection in cursor:
        collection["_id"] = str(collection["_id"])
        collections.append(collection)
    return collections

async def get_collection(
    db: AsyncIOMotorDatabase,
    collection_id: str,
    user_email: Optional[str] = None
) -> Dict[str, Any]:
    """Get a collection by ID, optionally filtering by user_email"""
    query = {"_id": ObjectId(collection_id)}
    if user_email:
        query["user_email"] = user_email
        
    collection = await db["collections"].find_one(query)
    if not collection:
        raise HTTPException(status_code=404, detail=f"Collection with ID {collection_id} not found")
    
    collection["_id"] = str(collection["_id"])
    return collection

async def create_collection(
    db: AsyncIOMotorDatabase,
    collection: CollectionCreate,
    user_email: str
) -> Dict[str, Any]:
    """Create a new collection"""
    now = datetime.now()
    collection_dict = collection.dict()
    collection_dict.update({
        "user_email": user_email,
        "papers": [],
        "created_at": now,
        "updated_at": now
    })
    
    result = await db["collections"].insert_one(collection_dict)
    
    created_collection = await db["collections"].find_one({"_id": result.inserted_id})
    created_collection["_id"] = str(created_collection["_id"])
    return created_collection

async def update_collection(
    db: AsyncIOMotorDatabase,
    collection_id: str,
    update_data: CollectionUpdate,
    user_email: Optional[str] = None
) -> Dict[str, Any]:
    """Update a collection"""
    query = {"_id": ObjectId(collection_id)}
    if user_email:
        query["user_email"] = user_email
        
    # Check if collection exists
    collection = await db["collections"].find_one(query)
    if not collection:
        raise HTTPException(status_code=404, detail=f"Collection with ID {collection_id} not found")
    
    # Prepare update data
    update_dict = {k: v for k, v in update_data.dict(exclude_unset=True).items() if v is not None}
    if update_dict:
        update_dict["updated_at"] = datetime.now()
        
        await db["collections"].update_one(
            query,
            {"$set": update_dict}
        )
    
    # Get updated collection
    updated_collection = await db["collections"].find_one({"_id": ObjectId(collection_id)})
    updated_collection["_id"] = str(updated_collection["_id"])
    return updated_collection

async def delete_collection(
    db: AsyncIOMotorDatabase,
    collection_id: str,
    user_email: Optional[str] = None
) -> bool:
    """Delete a collection"""
    query = {"_id": ObjectId(collection_id)}
    if user_email:
        query["user_email"] = user_email
        
    result = await db["collections"].delete_one(query)
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Collection with ID {collection_id} not found")
    
    return True

async def add_paper_to_collection(
    db: AsyncIOMotorDatabase,
    collection_id: str,
    paper_id: str,
    user_email: Optional[str] = None
) -> Dict[str, Any]:
    """Add a paper to a collection"""
    query = {"_id": ObjectId(collection_id)}
    if user_email:
        query["user_email"] = user_email
        
    # Check if collection exists
    collection = await db["collections"].find_one(query)
    if not collection:
        raise HTTPException(status_code=404, detail=f"Collection with ID {collection_id} not found")
    
    # Check if paper is already in the collection
    if paper_id in collection.get("papers", []):
        return {
            "message": f"Paper {paper_id} is already in collection {collection_id}",
            "collection_id": str(collection_id)
        }
    
    # Add paper to collection
    result = await db["collections"].update_one(
        query,
        {
            "$push": {"papers": paper_id},
            "$set": {"updated_at": datetime.now()}
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to add paper to collection")
    
    return {
        "message": f"Paper {paper_id} added to collection {collection_id}",
        "collection_id": str(collection_id)
    }

async def remove_paper_from_collection(
    db: AsyncIOMotorDatabase,
    collection_id: str,
    paper_id: str,
    user_email: Optional[str] = None
) -> Dict[str, Any]:
    """Remove a paper from a collection"""
    query = {"_id": ObjectId(collection_id)}
    if user_email:
        query["user_email"] = user_email
        
    # Check if collection exists
    collection = await db["collections"].find_one(query)
    if not collection:
        raise HTTPException(status_code=404, detail=f"Collection with ID {collection_id} not found")
    
    # Remove paper from collection
    result = await db["collections"].update_one(
        query,
        {
            "$pull": {"papers": paper_id},
            "$set": {"updated_at": datetime.now()}
        }
    )
    
    if result.modified_count == 0:
        # If no changes were made, check if the paper was already not in the collection
        updated_collection = await db["collections"].find_one({"_id": ObjectId(collection_id)})
        if paper_id not in updated_collection.get("papers", []):
            return {
                "message": f"Paper {paper_id} was not in collection {collection_id}",
                "collection_id": str(collection_id)
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to remove paper from collection")
    
    return {
        "message": f"Paper {paper_id} removed from collection {collection_id}",
        "collection_id": str(collection_id)
    }

async def add_tag_to_collection(
    db: AsyncIOMotorDatabase,
    collection_id: str,
    tag: str,
    user_email: Optional[str] = None
) -> Dict[str, Any]:
    """Add a tag to a collection"""
    query = {"_id": ObjectId(collection_id)}
    if user_email:
        query["user_email"] = user_email
        
    # Check if collection exists
    collection = await db["collections"].find_one(query)
    if not collection:
        raise HTTPException(status_code=404, detail=f"Collection with ID {collection_id} not found")
    
    # Check if tag already exists
    if tag in collection.get("tags", []):
        return {
            "message": f"Tag '{tag}' is already in collection {collection_id}",
            "collection_id": str(collection_id)
        }
    
    # Add tag to collection
    result = await db["collections"].update_one(
        query,
        {
            "$push": {"tags": tag},
            "$set": {"updated_at": datetime.now()}
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to add tag to collection")
    
    return {
        "message": f"Tag '{tag}' added to collection {collection_id}",
        "collection_id": str(collection_id)
    }

async def remove_tag_from_collection(
    db: AsyncIOMotorDatabase,
    collection_id: str,
    tag: str,
    user_email: Optional[str] = None
) -> Dict[str, Any]:
    """Remove a tag from a collection"""
    query = {"_id": ObjectId(collection_id)}
    if user_email:
        query["user_email"] = user_email
        
    # Check if collection exists
    collection = await db["collections"].find_one(query)
    if not collection:
        raise HTTPException(status_code=404, detail=f"Collection with ID {collection_id} not found")
    
    # Remove tag from collection
    result = await db["collections"].update_one(
        query,
        {
            "$pull": {"tags": tag},
            "$set": {"updated_at": datetime.now()}
        }
    )
    
    if result.modified_count == 0:
        # If no changes were made, check if the tag was already not in the collection
        updated_collection = await db["collections"].find_one({"_id": ObjectId(collection_id)})
        if tag not in updated_collection.get("tags", []):
            return {
                "message": f"Tag '{tag}' was not in collection {collection_id}",
                "collection_id": str(collection_id)
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to remove tag from collection")
    
    return {
        "message": f"Tag '{tag}' removed from collection {collection_id}",
        "collection_id": str(collection_id)
    }


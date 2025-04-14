from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException, Path
import os
from app.services import paper_service
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.mongodb import get_database
from bson import ObjectId



router = APIRouter(
    prefix="/paper",
    tags=["pdf"],
    responses={404: {"description": "Not found"}},
)

@router.post('/extract-pdf')
async def extract_text(
    email: str = Form(...),
    pdf: UploadFile = File(...),
    fields: List[str] = Form([]),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    print(fields)
    extract_data = await paper_service.extract_data(email, pdf, fields, db)
    return {"data": extract_data}


@router.get("/")
async def get_papers(
    db: AsyncIOMotorDatabase = Depends(get_database),
    email: str = "",
    search: str = "",
    filter_by: str = ""
):
    """
    Returns papers belonging to `email`. 
    Allows optional 'search' on the 'title' field, 
    and a 'filter_by' param you can customize.
    """
    query = {}

    # Filter by user email if provided
    if email:
        query["user_email"] = email

    # If 'search' is provided, do a partial match on 'title'
    if search:
        # case‐insensitive partial match
        query["title"] = {"$regex": search, "$options": "i"}

    # Handle custom filter logic
    # e.g. if filter_by="recent", we sort by created_at descending
    cursor = db["papers"].find(query)
    
    # Default sort by created_at in descending order (newest first)
    # Override with specific filter logic if provided
    if filter_by == "oldest":
        cursor = cursor.sort("created_at", 1)  # Ascending for oldest first
    else:
        # By default or if filter_by="recent", sort by created_at descending
        cursor = cursor.sort("created_at", -1)  # Descending for newest first

    results = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])  # convert ObjectId to string for JSON
        results.append(doc)

    return results


@router.delete("/{paper_id}")
async def delete_paper(
    paper_id: str = Path(..., description="The ID of the paper to delete"),
    email: str = "",
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Delete a paper by ID.
    Optionally verify the email ownership.
    """
    try:
        # Create query with paper ID
        query = {"_id": ObjectId(paper_id)}
        
        # If email is provided, verify ownership
        if email:
            query["user_email"] = email
            
        # Try to delete the paper
        result = await db["papers"].delete_one(query)
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404, 
                detail=f"Paper with ID {paper_id} not found or doesn't belong to {email}")
            
        return {"success": True, "message": f"Paper {paper_id} deleted successfully"}
            
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to delete paper: {str(e)}")


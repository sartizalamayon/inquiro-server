from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException, Path, Body
import os
from app.services import paper_service
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.mongodb import get_database
from bson import ObjectId
import json



router = APIRouter(
    prefix="/paper",
    tags=["pdf"],
    responses={404: {"description": "Not found"}},
)

@router.post('/extract-pdf')
async def extract_text(
    email: str = Form(...),
    pdf: UploadFile = File(...),
    fields: str = Form("[]"),  # Default to empty JSON array
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    # Parse fields from JSON string to list
    try:
        fields_list = json.loads(fields)
    except json.JSONDecodeError:
        fields_list = []
    
    print(f"Custom fields: {fields_list}")
    extract_data = await paper_service.extract_data(email, pdf, fields_list, db)
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


@router.get("/{paper_id}")
async def get_paper(
    paper_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    paper = await paper_service.get_paper(paper_id, db)
    if paper is None:
        raise HTTPException(
            status_code=404,
            detail=f"Paper with ID {paper_id} not found"
        )
    return paper

@router.patch("/{paper_id}/update")
async def update_paper_sections(
    paper_id: str,
    data: Dict[str, Any] = Body(..., description="Update data. Can be either sections directly or wrapped in a 'sections' field"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update specific sections of a paper.
    The data can be either:
    1. Direct sections dictionary where keys are section identifiers and values are content
    2. A dictionary with a 'sections' field containing the sections to update
    """
    try:
        # Validate paper exists
        paper = await paper_service.get_paper(paper_id, db)
        if paper is None:
            raise HTTPException(
                status_code=404,
                detail=f"Paper with ID {paper_id} not found"
            )
        
        # Handle both formats: direct sections dict or wrapped in 'sections' field
        sections = data.get("sections", data)
        
        # Process updates to standard summary fields
        updates = {}
        user_field_updates = []
        
        for key, content in sections.items():
            if key.startswith("user_field_"):
                # Handle user-given fields updates
                field_name = key.replace("user_field_", "")
                
                # Find the index of this field in user_given_fields array
                found = False
                for i, field in enumerate(paper.get("summary", {}).get("user_given_fields", [])):
                    if field.get("field_name") == field_name:
                        # Update in user_given_fields array
                        updates[f"summary.user_given_fields.{i}.value"] = content
                        found = True
                        break
                
                if not found:
                    # If field doesn't exist, it will be added later
                    user_field_updates.append({"field_name": field_name, "value": content})
                
            else:
                # Handle standard summary fields
                updates[f"summary.{key}"] = content
        
        # If there are any updates
        if updates or user_field_updates:
            # First apply direct field updates
            if updates:
                await db["papers"].update_one(
                    {"_id": ObjectId(paper_id)},
                    {"$set": updates}
                )
            
            # Then handle any new user fields that need to be added
            if user_field_updates:
                await db["papers"].update_one(
                    {"_id": ObjectId(paper_id)},
                    {"$push": {"summary.user_given_fields": {"$each": user_field_updates}}}
                )
            
            return {"success": True, "message": "Paper sections updated successfully"}
        else:
            return {"success": False, "message": "No valid sections to update"}
            
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to update paper: {str(e)}"
        )
    

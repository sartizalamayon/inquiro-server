from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
import os
from app.services import paper_service
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.mongodb import get_database



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
    if filter_by == "recent":
        cursor = cursor.sort("created_at", -1)

    results = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])  # convert ObjectId to string for JSON
        results.append(doc)

    return results


from fastapi import APIRouter, Depends, Body
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.mongodb import get_database
from app.models.search import SearchQuery, SearchResponse
from app.services.search_service import search_papers
from typing import Optional, List, Dict
from collections import Counter

router = APIRouter(
    prefix="/papers",
    tags=["search"],
    responses={404: {"description": "Not found"}},
)

@router.post("/search", response_model=SearchResponse)
async def search(
    search_data: dict = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Search for papers using natural language query and optional filters.
    
    The frontend can send either:
    1. A simple { query: "search text" } object
    2. A full SearchQuery object with filters
    """
    # Extract the query and any filter parameters
    print(search_data)
    query = search_data.get("query", "")
    if not query:
        return {"results": [], "total": 0}
    
    # Create the search query object with optional filters
    search_query = SearchQuery(
        query=query,
        tags=search_data.get("tags")
    )
    
    # Call the search service
    search_response = await search_papers(search_query, db)

    print(search_response)
    return search_response

@router.get("/top-tags")
async def get_top_tags(
    limit: int = 15,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get the top most common tags across all papers
    """
    # Aggregate all tags from papers
    pipeline = [
        {"$match": {"metadata.tags": {"$exists": True, "$ne": []}}},
        {"$unwind": "$metadata.tags"},
        {"$group": {"_id": "$metadata.tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]
    
    tags = []
    async for tag_doc in db["papers"].aggregate(pipeline):
        tags.append({"name": tag_doc["_id"], "count": tag_doc["count"]})
    
    return {"tags": tags}

@router.get("/top-authors")
async def get_top_authors(
    limit: int = 15,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get the top most common authors across all papers
    """
    # Aggregate all authors from papers
    pipeline = [
        {"$match": {"authors": {"$exists": True, "$ne": []}}},
        {"$unwind": "$authors"},
        {"$group": {"_id": "$authors.name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]
    
    authors = []
    async for author_doc in db["papers"].aggregate(pipeline):
        if author_doc["_id"]:  # Ensure author name is not None
            authors.append({"name": author_doc["_id"], "count": author_doc["count"]})
    
    return {"authors": authors}

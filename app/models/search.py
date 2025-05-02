from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SearchQuery(BaseModel):
    """Model for search query requests"""
    query: str = Field(..., description="Natural language search query")
    tags: Optional[List[str]] = Field(None, description="Tags to filter by")


class SearchResult(BaseModel):
    """Model for individual search result"""
    id: str = Field(..., alias="_id")
    score: float = Field(..., alias="_score")
    userUploadName: str
    title: str
    authors: List[str]
    research_problem: str
    date_published: str
    tags: List[str]

class SearchResponse(BaseModel):
    """Model for search query response"""
    results: List[SearchResult]
    total: int

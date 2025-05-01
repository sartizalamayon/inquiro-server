from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.services.pinecone_service import semantic_search
from app.models.search import SearchQuery, SearchResponse
from app.services.user_service import get_user_by_email
from bson import ObjectId

async def search_papers(search_query: SearchQuery, db: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """
    Search for papers using natural language query and optional filters
    """
    try:
        # 1. Perform semantic search using Pinecone
        search_results = await semantic_search(search_query.query)
        
        if not search_results:
            print(f"No search results found for query: {search_query.query}")
            return {"results": [], "total": 0}
        
        # 2. Get paper IDs from search results
        paper_ids = [hit._id for hit in search_results]
        print(paper_ids)
        
        # 3. Fetch full paper documents from MongoDB
        papers = []
        try:
            # Note: paper_ids are already string format from Pinecone
            async for paper in db["papers"].find({"_id": {"$in": [ObjectId(pid) for pid in paper_ids]}}):
                papers.append(paper)
        except Exception as db_error:
            print(f"Error fetching papers from database: {db_error}")
            return {"results": [], "total": 0}
        
        # Create a mapping of paper IDs to their documents for easier lookup
        paper_map = {str(paper["_id"]): paper for paper in papers}
    
        # 4. Create the enhanced search results with required format
        enhanced_results = []
        for hit in search_results:
            paper_id = hit._id
            if paper_id not in paper_map:
                continue
                
            paper = paper_map[paper_id]
            
            # Get user information
            user_email = paper.get("user_email", "")
            user_name = user_email
            
            # Get user name if available
            if user_email:
                user = await get_user_by_email(db, user_email)
                if user and hasattr(user, "name") and user.name:
                    user_name = user.name
            
            # Extract author names
            author_names = []
            if "authors" in paper and paper["authors"]:
                for author in paper["authors"]:
                    if isinstance(author, dict) and "name" in author:
                        author_names.append(author["name"])
                    elif isinstance(author, str):
                        author_names.append(author)
            
            # Get research problem
            research_problem = ""
            if "summary" in paper and paper["summary"] and "research_problem" in paper["summary"]:
                research_problem = paper["summary"]["research_problem"]
            
            # Get date published
            date_published = paper.get("date_published", "")
            
            # Get tags for filtering
            tags = paper.get("metadata", {}).get("tags", [])
            
            # Create result object
            result = {
                "_id": paper_id,
                "_score": hit._score,
                "userUploadName": user_name,
                "title": paper.get("title", "Untitled"),
                "authors": author_names,
                "research_problem": research_problem,
                "date_published": date_published,
                "tags": tags  # Add tags for filtering
            }
            
            enhanced_results.append(result)
            
        # 5. Apply tag filtering if requested
        filtered_results = enhanced_results
        if search_query.tags and len(search_query.tags) > 0:
            filtered_results = [
                r for r in filtered_results 
                if any(tag in r["tags"] for tag in search_query.tags)
            ]
        
        # Sort by score (already done in Pinecone response)
        
        return {
            "results": filtered_results,
            "total": len(filtered_results)
        }
    except Exception as e:
        print(f"Error in search_papers: {e}")
        return {"results": [], "total": 0}

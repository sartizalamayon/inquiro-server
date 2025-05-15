import datetime as dt, math
from typing import Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.models.analytics import NumericMetrics, AIInsights, AnalyticsDoc
from app.utils.get_ai_analysis import get_ai_analysis
     # heuristically: Gemini saves 40 %

async def _calc_numeric(db: AsyncIOMotorDatabase,
                        email: str,
                        window: int = 30) -> NumericMetrics:
    """Aggregate counts on the fly each call."""
    today = dt.datetime.utcnow()
    start = today - dt.timedelta(days=window)

    # papers
    total_papers = await db["papers"].count_documents({"user_email": email})
    summarised   = await db["papers"].count_documents({
        "user_email": email,
        "summary.research_problem": {"$exists": True}
    })

    # collections
    collections = await db["collections"].count_documents({"user_email": email})

    # notes
    notes = await db["notes"].count_documents({"user_email": email})

    # uploads/summaries/notes per day arrays (30 ints each)
    async def _daily(col, match):
        pipeline = [
            {"$match": match},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "c": {"$sum": 1}
            }}
        ]
        rows = await db[col].aggregate(pipeline).to_list(None)
        m = {r["_id"]: r["c"] for r in rows}
        return [m.get((start + dt.timedelta(days=i)).strftime("%Y-%m-%d"), 0)
                for i in range(window)]

    uploads_arr   = await _daily("papers", {"user_email": email,
                                            "created_at": {"$gte": start}})
    summaries_arr = await _daily("papers", {"user_email": email,
                                            "summary.research_problem": {"$exists": True},
                                            "created_at": {"$gte": start}})
    notes_arr     = await _daily("notes", {"user_email": email,
                                           "created_at": {"$gte": start}})

    # coverage
    coverage = (summarised / total_papers * 100) if total_papers else 0

    # time-saved heuristic  (tokens ≈ ¾ words)   summary length not stored,
    # fallback 5 min per paper summarised
    time_saved = summarised * 5 / 60

    # streak (consecutive days with ≥1 upload OR summary)
    streak = 0
    for day_papers in reversed(uploads_arr):
        if day_papers > 0:
            streak += 1
        else:
            break

    try:
        most_active = {
            'collection' : await db["collections"].aggregate([
                {"$match": {"user_email": email}},
                {"$group": {
                    "_id": "$name",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}},
                {"$limit": 1}
            ]).to_list(1),
            'tag' : await db["papers"].aggregate([
                {"$match": {"user_email": email}},
                {"$unwind": "$metadata.tags"},
                {"$group": {
                    "_id": "$metadata.tags",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}},
                {"$limit": 1}
            ]).to_list(1),
            'year' : await db["papers"].aggregate([
                {"$match": {"user_email": email}},
                {"$group": {
                    "_id": {"$year": "$created_at"},
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}},
                {"$limit": 1}
            ]).to_list(1),
            'month' : await db["papers"].aggregate([
                {"$match": {"user_email": email}},
                {"$group": {
                    "_id": {"$month": "$created_at"},
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}},
                {"$limit": 1}
            ]).to_list(1),
            'day' : await db["papers"].aggregate([
                {"$match": {"user_email": email}},
                {"$group": {
                    "_id": {"$dayOfWeek": "$created_at"},
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}},
                {"$limit": 1}
            ]).to_list(1)
        }

        

        # papers_by_month (created this year)
        papers_by_month = await db["papers"].aggregate([
            {"$match": {
                "user_email": email,
                "created_at": {
                    "$gte": dt.datetime(today.year, 1, 1),
                    "$lt": dt.datetime(today.year + 1, 1, 1)
                }
            }},
            {"$group": {
                "_id": {"$month": "$created_at"},
                "count": {"$sum": 1}
            }},
        ]).to_list()
  

        # # [{ name: 'Jan', value: 12 }]
        papers_by_month = [
            {"name": dt.date(today.year, m["_id"], 1).strftime("%b"), "value": m["count"]}
            for m in papers_by_month
        ]

 
    except Exception as e:
        print("Error in aggregation: ", e)
        most_active = {}
        papers_by_month = []
    # most_active = {



    return NumericMetrics(
        total_papers=total_papers,
        summarised_papers=summarised,
        coverage_pct=coverage,
        collections=collections,
        notes=notes,
        time_saved_hours=time_saved,
        streak_days=streak,
        research_activity={
            "uploads": uploads_arr,
            "summaries": summaries_arr,
            "notes": notes_arr
        },
        most_active=most_active,
        papers_by_month=papers_by_month,
    )

async def get_metrics(db: AsyncIOMotorDatabase, email: str) -> NumericMetrics:
    data =  await _calc_numeric(db, email)
    return data

async def get_or_create_insights(db: AsyncIOMotorDatabase,
                                 email: str) -> AIInsights:
    today_str = dt.date.today().isoformat() 
    doc = await db["analytics"].find_one({
        "user_email": email, "generated_at": today_str
    })
    if doc and "ai_insights" in doc:
        return AIInsights(**doc["ai_insights"])

    # need fresh generation
    papers = await db["papers"].find({"user_email": email}).to_list(1000)
    ai_blob = await get_ai_analysis(papers)

    await db["analytics"].update_one(
        {"user_email": email, "generated_at": today_str},
         {"$set": {
            "user_email": email,
            "generated_at": today_str,
            "timeframe": "30d",
            "ai_insights": ai_blob,
         }},
         upsert=True,
     )
    return AIInsights(**ai_blob)

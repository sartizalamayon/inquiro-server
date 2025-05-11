from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.mongodb import get_database
from app.services.analytics_service import get_metrics, get_or_create_insights
from app.models.analytics import NumericMetrics, AIInsights

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/metrics/{user_email}", response_model=NumericMetrics)
async def metrics(user_email: str,
                  db: AsyncIOMotorDatabase = Depends(get_database)):
    try:
        return await get_metrics(db, user_email)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/insights/{user_email}", response_model=AIInsights)
async def insights(user_email: str,
                   db: AsyncIOMotorDatabase = Depends(get_database)):
    try:
        return await get_or_create_insights(db, user_email)
    except Exception as e:
        raise HTTPException(500, str(e))

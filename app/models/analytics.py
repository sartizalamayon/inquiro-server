from datetime import datetime, date
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class NumericMetrics(BaseModel):
    total_papers: int
    summarised_papers: int
    coverage_pct: float            # 0-100
    collections: int
    notes: int
    time_saved_hours: float        # crude WPM estimate
    streak_days: int
    research_activity: Dict[str, List[int]]  # uploads / summaries / notes last 30 d
    most_active: Dict[str, List[Dict[str, Any]]]  # Results from MongoDB aggregations
    papers_by_month: List[Dict[str, Any]]  # 
    


class AIInsights(BaseModel):
    trend_gaps: List[str]
    recommendations: List[Dict[str, Any]]
    assistant_cards: List[Dict[str, Any]]


class AnalyticsDoc(BaseModel):
    user_email: str
    generated_at: str
    timeframe: str                 # “30d”
    metrics: NumericMetrics
    ai_insights: Optional[AIInsights] = None

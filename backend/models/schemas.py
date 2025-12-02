from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class ForecastRequest(BaseModel):
    """Request model for growth forecast"""
    current_followers: Dict[str, int] = Field(
        description="Current follower counts per platform",
        example={"Instagram": 384000, "TikTok": 572700, "YouTube": 381000, "Facebook": 590000}
    )
    posts_per_week_total: float = Field(
        ge=0, le=200,
        description="Total posts per week across all platforms"
    )
    platform_allocation: Dict[str, float] = Field(
        description="Platform allocation percentages (0-100)",
        example={"Instagram": 35.0, "TikTok": 35.0, "YouTube": 15.0, "Facebook": 15.0}
    )
    content_mix_by_platform: Dict[str, Dict[str, float]] = Field(
        description="Content mix percentages per platform"
    )
    months: int = Field(ge=3, le=24, description="Projection horizon in months")
    preset: str = Field(description="Strategy preset: Conservative, Balanced, or Ambitious")


class MonthlyForecast(BaseModel):
    """Single month forecast data"""
    month: int
    Instagram: float
    TikTok: float
    YouTube: float
    Facebook: float
    total: float
    added: float


class ForecastResponse(BaseModel):
    """Response model for growth forecast"""
    monthly_data: List[MonthlyForecast]
    goal: float
    projected_total: float
    progress_to_goal: float


class HistoricalDataResponse(BaseModel):
    """Historical data for charts"""
    mentions: List[Dict]
    sentiment: List[Dict]
    tags: List[Dict]
    engagement_index: List[float]


class StatusResponse(BaseModel):
    """API status response"""
    status: str
    version: str

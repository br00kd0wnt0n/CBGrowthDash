from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


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
    # Optional paid media inputs
    paid_impressions_per_week_total: Optional[float] = Field(
        default=0.0,
        ge=0,
        description="Total paid impressions per week across platforms"
    )
    paid_allocation: Optional[Dict[str, float]] = Field(
        default=None,
        description="Paid impressions allocation percentages per platform (0-100). Defaults to platform_allocation if omitted."
    )
    paid_funnel: Optional[Dict[str, Dict[str, float]]] = Field(
        default=None,
        description="Optional per-platform paid funnel rates: {platform: {vtr, er, fcr}} where vtr=view-through rate (views/impressions), er=engagement rate (engagements/views), fcr=follow conversion rate (follows/engagement)."
    )
    # Optional budget-based acquisition (direct CPF modeling)
    paid_budget_per_week_total: Optional[float] = Field(
        default=0.0, ge=0,
        description="Weekly paid boosting budget in USD (direct follower acquisition via CPF)."
    )
    creator_budget_per_week_total: Optional[float] = Field(
        default=0.0, ge=0,
        description="Weekly creator/collab budget in USD (modeled via CPF)."
    )
    acquisition_budget_per_week_total: Optional[float] = Field(
        default=0.0, ge=0,
        description="Weekly acquisition budget in USD (giveaways, promo)."
    )
    cpf_paid: Optional[Dict[str, float]] = Field(
        default=None,
        description="Paid boosting CPF range: {min, mid, max}. Defaults to {3,4,5}."
    )
    cpf_creator: Optional[Dict[str, float]] = Field(
        default=None,
        description="Creator CPF range: {min, mid, max}. Defaults to {3,4,5}."
    )
    cpf_acquisition: Optional[Dict[str, float]] = Field(
        default=None,
        description="Acquisition CPF range: {min, mid, max}. Defaults to {3,4,5}."
    )
    # Sheet-driven calibration
    use_sheet_calibration: Optional[bool] = Field(
        default=False,
        description="If true, parse the multi-tab workbook to calibrate assumptions (rates, caps, per-post gains, CPF)."
    )
    sheet_path: Optional[str] = Field(
        default=None,
        description="Optional override path to the Excel workbook (defaults to public/Care Bears Audience Growth KPis .xlsx)."
    )
    # AI context fields (passed from frontend for better recommendations)
    projected_total: Optional[float] = Field(
        default=None,
        description="Current projected total followers from forecast"
    )
    goal_followers: Optional[float] = Field(
        default=None,
        description="User's goal follower count"
    )


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
    # Optional acquisition breakdown by month
    added_breakdown: Optional[List[dict]] = None


# Insight API models
class InsightRequest(BaseModel):
    goal: float
    projected_total: float
    posts_per_week_total: float
    platform_allocation: Dict[str, float]
    months: int
    progress_to_goal: float

class InsightResponse(BaseModel):
    insight: str


# Assumptions API
class AssumptionsResponse(BaseModel):
    assumptions: List[Dict[str, Any]]


# Parameter tuning API
class ParamTuneRequest(BaseModel):
    current_params: Dict[str, Any]
    historical_summary: Dict[str, Any]
    gap_to_goal: float

class ParamSuggestion(BaseModel):
    key: str
    current: float
    suggested: float
    reason: str
    confidence: str

class ParamTuneResponse(BaseModel):
    suggestions: List[ParamSuggestion]


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


class AIScenario(BaseModel):
    """AI-generated strategy scenario"""
    name: str = Field(description="Scenario name: Optimized, Aggressive, or Conservative")
    posts_per_week: int = Field(ge=14, le=50)
    platform_allocation: Dict[str, int] = Field(description="Platform allocation percentages")
    reasoning: str = Field(description="Brief explanation of strategy")
    risk_level: str = Field(description="Risk level: LOW, MEDIUM, or HIGH")
    expected_outcome: str = Field(description="Expected result vs goal")


class AIInsightsResponse(BaseModel):
    """AI strategy analysis and recommendations"""
    analysis: str = Field(description="Overall assessment of current strategy")
    scenarios: List[AIScenario] = Field(description="3 alternative scenarios")
    key_insights: List[str] = Field(description="Key insights and recommendations")


# AI Strategy Critique models
class CritiqueRequest(BaseModel):
    """Request model for AI strategy critique"""
    current_followers: Dict[str, Any] = Field(description="Current follower counts per platform")
    posts_per_week: float = Field(ge=1, le=100, description="Total posts per week")
    platform_allocation: Dict[str, Any] = Field(description="Platform allocation percentages")
    content_mix: Dict[str, Dict[str, Any]] = Field(description="Content mix by platform")
    months: int = Field(ge=1, le=24, description="Forecast period in months")
    preset: str = Field(description="Strategy preset name")
    audience_mix: Dict[str, Any] = Field(description="Audience segment mix percentages")
    projected_total: float = Field(description="Projected total followers")
    goal: float = Field(description="Goal follower count")
    # Optional fields
    paid_budget_week: Optional[float] = Field(default=0, description="Weekly paid budget")
    creator_budget_week: Optional[float] = Field(default=0, description="Weekly creator budget")
    acquisition_budget_week: Optional[float] = Field(default=0, description="Weekly acquisition budget")
    cpf_range: Optional[Dict[str, float]] = Field(default=None, description="CPF range {min, mid, max}")
    # Previous suggestions context for re-analysis
    previous_suggestions: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Previous optimization suggestions to provide context for re-analysis"
    )


class CategoryAssessment(BaseModel):
    """Individual category assessment"""
    category: str
    rating: str
    current_value: str
    assessment: str
    suggestion: Optional[str] = None
    suggested_value: Optional[str] = None


class Optimization(BaseModel):
    """Optimization suggestion"""
    priority: int
    action: str
    impact: str
    effort: str


class OverallAssessment(BaseModel):
    """Overall strategy assessment"""
    rating: str
    summary: str


class CritiqueResponse(BaseModel):
    """Response model for AI strategy critique"""
    overall_assessment: OverallAssessment
    category_assessments: List[CategoryAssessment]
    top_optimizations: List[Optimization]
    gwi_alignment_notes: List[str]

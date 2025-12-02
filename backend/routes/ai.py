"""
AI Insights API Routes
"""
from fastapi import APIRouter, HTTPException
from models.schemas import ForecastRequest, AIInsightsResponse, AIScenario
from services.ai_service import analyze_strategy
from services.forecast_service import load_historical_data

router = APIRouter(prefix="/api", tags=["AI Insights"])

@router.post("/ai-insights", response_model=AIInsightsResponse)
async def get_ai_insights(request: ForecastRequest):
    """
    Get AI-powered strategy recommendations
    Returns 3 scenario alternatives: Optimized, Aggressive, Conservative
    """
    try:
        # Get historical data for context
        historical_data = load_historical_data()

        # Get AI analysis
        ai_result = analyze_strategy(
            current_followers=request.current_followers,
            posts_per_week=request.posts_per_week_total,
            platform_allocation=request.platform_allocation,
            months=request.months,
            preset=request.preset,
            historical_data=historical_data
        )

        # Convert to response schema
        scenarios = [
            AIScenario(
                name=s["name"],
                posts_per_week=s["posts_per_week"],
                platform_allocation=s["platform_allocation"],
                reasoning=s["reasoning"],
                risk_level=s["risk_level"],
                expected_outcome=s["expected_outcome"]
            )
            for s in ai_result["scenarios"]
        ]

        return AIInsightsResponse(
            analysis=ai_result["analysis"],
            scenarios=scenarios,
            key_insights=ai_result["key_insights"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

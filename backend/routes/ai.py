"""
AI Insights API Routes
"""
from pathlib import Path
from fastapi import APIRouter, HTTPException
from models.schemas import ForecastRequest, AIInsightsResponse, AIScenario, InsightRequest, InsightResponse, ParamTuneRequest, ParamTuneResponse
from services.ai_service import analyze_strategy, generate_gap_insight, tune_parameters
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
        data_dir = Path(__file__).parent.parent / "data"
        historical_data = load_historical_data(data_dir)

        # Build budget info from request
        paid_weekly = (request.paid_budget_per_week_total or 0) + (request.creator_budget_per_week_total or 0)
        growth_weekly = request.acquisition_budget_per_week_total or 0
        cpf = request.cpf_paid or {"min": 0.50, "mid": 0.75, "max": 1.00}

        budget_info = {
            "total_annual_budget": (paid_weekly + growth_weekly) * 52,
            "paid_media_weekly": request.paid_budget_per_week_total or 0,
            "growth_strategy_weekly": (request.creator_budget_per_week_total or 0) + (request.acquisition_budget_per_week_total or 0),
            "cpf_range": cpf,
            "projected_total": request.projected_total,
            "goal_followers": request.goal_followers,
        }

        # Get AI analysis
        ai_result = analyze_strategy(
            current_followers=request.current_followers,
            posts_per_week=request.posts_per_week_total,
            platform_allocation=request.platform_allocation,
            months=request.months,
            preset=request.preset,
            historical_data=historical_data,
            budget_info=budget_info
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


@router.post("/ai/insight", response_model=InsightResponse)
async def ai_gap_insight(req: InsightRequest):
    try:
        text = generate_gap_insight(req)
        return InsightResponse(insight=text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insight generation failed: {e}")


@router.post("/ai/tune-parameters", response_model=ParamTuneResponse)
async def ai_tune_parameters(req: ParamTuneRequest):
    try:
        resp = tune_parameters(req)
        return ParamTuneResponse(**resp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parameter tuning failed: {e}")

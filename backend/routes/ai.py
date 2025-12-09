"""
AI Insights API Routes
"""
from pathlib import Path
from fastapi import APIRouter, HTTPException
from models.schemas import (
    ForecastRequest, AIInsightsResponse, AIScenario, InsightRequest, InsightResponse,
    ParamTuneRequest, ParamTuneResponse, CritiqueRequest, CritiqueResponse
)
from services.ai_service import analyze_strategy, generate_gap_insight, tune_parameters, critique_strategy
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
        cpf = request.cpf_paid or {"min": 0.10, "mid": 0.15, "max": 0.20}

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


@router.post("/ai/critique", response_model=CritiqueResponse)
async def ai_critique_strategy(req: CritiqueRequest):
    """
    Provide a balanced AI critique of the user's current strategy.
    Assesses posts/week, platform allocation, content mix, audience alignment,
    and goal feasibility against GWI research and best practices.
    """
    try:
        # Get historical data for context
        data_dir = Path(__file__).parent.parent / "data"
        historical_data = load_historical_data(data_dir)

        # Build budget info
        budget_info = {
            "paid_media_weekly": req.paid_budget_week or 0,
            "creator_weekly": req.creator_budget_week or 0,
            "acquisition_weekly": req.acquisition_budget_week or 0,
            "cpf_range": req.cpf_range or {"min": 0.10, "mid": 0.15, "max": 0.20}
        }

        # Get critique
        result = critique_strategy(
            current_followers=req.current_followers,
            posts_per_week=req.posts_per_week,
            platform_allocation=req.platform_allocation,
            content_mix=req.content_mix,
            months=req.months,
            preset=req.preset,
            audience_mix=req.audience_mix,
            projected_total=req.projected_total,
            goal=req.goal,
            historical_data=historical_data,
            budget_info=budget_info
        )

        return CritiqueResponse(**result)

    except Exception as e:
        import traceback
        print(f"Critique error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Strategy critique failed: {str(e)}")

from fastapi import APIRouter, HTTPException
from pathlib import Path
import pandas as pd

from models.schemas import (
    ForecastRequest,
    ForecastResponse,
    MonthlyForecast,
    HistoricalDataResponse
)
from services.forecast_service import (
    forecast_growth,
    load_historical_data,
    compute_engagement_index,
    PRESETS,
    PLATFORMS
)

router = APIRouter(prefix="/api", tags=["forecast"])

# Load data once at startup
DATA_DIR = Path(__file__).parent.parent / "data"


@router.get("/historical", response_model=HistoricalDataResponse)
async def get_historical_data():
    """Get historical mentions, sentiment, and tags data"""
    try:
        data = load_historical_data(DATA_DIR)
        return HistoricalDataResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forecast", response_model=ForecastResponse)
async def run_forecast(request: ForecastRequest):
    """Run growth forecast based on input parameters"""
    try:
        # Get preset configuration
        if request.preset not in PRESETS:
            raise ValueError(f"Invalid preset: {request.preset}")

        preset_cfg = PRESETS[request.preset]

        # Load engagement index from historical data
        mentions_df = pd.read_csv(DATA_DIR / "generaldynamics.csv")
        sentiment_df = pd.read_csv(DATA_DIR / "sentiment-dynamics.csv")

        # Clean column names
        for df in [mentions_df, sentiment_df]:
            df.columns = [c.strip().strip('\ufeff').strip('"') for c in df.columns]

        # Compute engagement index
        eng_index = compute_engagement_index(mentions_df, sentiment_df)

        # Run forecast
        monthly_df = forecast_growth(
            current_followers=request.current_followers,
            posts_per_week_total=request.posts_per_week_total,
            platform_allocation=request.platform_allocation,
            content_mix_by_platform=request.content_mix_by_platform,
            engagement_index_series=eng_index,
            months=request.months,
            campaign_lift=preset_cfg["campaign_lift"],
            sensitivity=preset_cfg["sensitivity"],
            acq_scalar=preset_cfg["acq_scalar"],
            paid_impressions_per_week_total=(request.paid_impressions_per_week_total or 0.0),
            paid_allocation=(request.paid_allocation or None),
            paid_funnel=(request.paid_funnel or None),
            paid_budget_per_week_total=(request.paid_budget_per_week_total or 0.0),
            creator_budget_per_week_total=(request.creator_budget_per_week_total or 0.0),
            acquisition_budget_per_week_total=(request.acquisition_budget_per_week_total or 0.0),
            cpf_paid=(request.cpf_paid or None),
            cpf_creator=(request.cpf_creator or None),
            cpf_acquisition=(request.cpf_acquisition or None),
        )

        # Convert to response format
        monthly_data = []
        added_breakdown = []
        for _, row in monthly_df.iterrows():
            monthly_data.append(MonthlyForecast(
                month=int(row["Month"]),
                Instagram=float(row["Instagram"]),
                TikTok=float(row["TikTok"]),
                YouTube=float(row["YouTube"]),
                Facebook=float(row["Facebook"]),
                total=float(row["Total"]),
                added=float(row["Added"])
            ))
            added_breakdown.append({
                "month": int(row["Month"]),
                "organic_added": float(row.get("Added_Organic", 0.0)),
                "paid_added": float(row.get("Added_Paid", 0.0)),
                "total_added": float(row.get("Added", 0.0)),
            })

        # Calculate goal metrics
        total_current = sum(request.current_followers.values())
        goal = total_current * 2
        projected_total = float(monthly_df.iloc[-1]["Total"])
        progress_to_goal = (projected_total / goal * 100) if goal > 0 else 0

        return ForecastResponse(
            monthly_data=monthly_data,
            goal=goal,
            projected_total=projected_total,
            progress_to_goal=progress_to_goal,
            added_breakdown=added_breakdown
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

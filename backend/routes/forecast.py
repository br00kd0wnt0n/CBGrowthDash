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
    get_historical_data_cached,
    get_engagement_index_cached,
    PRESETS,
    PLATFORMS,
    CONTENT_MULT,
    FREQ_HALF_SAT,
    RECOMMENDED_FREQ,
    PLATFORM_MONTHLY_CAP,
    BASE_MONTHLY_RATE,
    PER_POST_GAIN_BASE,
    PAID_FUNNEL_DEFAULT,
    CPF_DEFAULT,
)
from services.calibration import load_calibration_from_xlsx, load_follower_history_from_xlsx

router = APIRouter(prefix="/api", tags=["forecast"])

# Load data once at startup
DATA_DIR = Path(__file__).parent.parent / "data"


@router.get("/historical", response_model=HistoricalDataResponse)
async def get_historical_data():
    """Get historical mentions, sentiment, and tags data"""
    try:
        # Use cached loader for throughput
        data = get_historical_data_cached(DATA_DIR)
        return HistoricalDataResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assumptions", response_model=HistoricalDataResponse, include_in_schema=False)
async def assumptions_hidden():
    # kept to avoid breaking schema generation; real endpoint below
    return HistoricalDataResponse(mentions=[], sentiment=[], tags=[], engagement_index=[])


@router.get("/assumptions-plain")
async def get_assumptions_plain():
    try:
        assumptions = [
            {"label": "Content multipliers (examples)", "value": {
                "Instagram": CONTENT_MULT['Instagram'],
                "TikTok": CONTENT_MULT['TikTok'],
                "YouTube": CONTENT_MULT['YouTube'],
                "Facebook": CONTENT_MULT['Facebook'],
            }, "source": "industry + cross-channel trends"},
            {"label": "Frequency half-saturation (posts/week)", "value": FREQ_HALF_SAT, "source": "benchmark"},
            {"label": "Posting bands (min/ideal/soft/hard)", "value": RECOMMENDED_FREQ, "source": "benchmark"},
            {"label": "Monthly growth caps", "value": PLATFORM_MONTHLY_CAP, "source": "realistic upper bounds"},
            {"label": "CPF range", "value": {"min": 3.0, "mid": 4.0, "max": 5.0}, "source": "industry"},
            {"label": "Oversaturation penalty", "value": "-40% effectiveness from soft to hard cap", "source": "model"},
            {"label": "Compounding growth", "value": "Platform baselines compounded weekly", "source": "model"},
        ]
        return {"assumptions": assumptions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/followers-history")
async def followers_history(sheet_path: str | None = None):
    """Return historical follower series parsed from the workbook or CSV.
    Prioritizes the CSV file with 2025 data if available.
    Extrapolates Oct-Dec 2025 if missing.
    """
    try:
        # First try CSV file with 2025 historical data
        csv_path = DATA_DIR / "followers_history_2025.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            data_rows = []
            labels = []
            platforms = ['Instagram', 'TikTok', 'Facebook', 'YouTube']

            for _, row in df.iterrows():
                month_str = row['Month']
                # Parse month and format as "Jan 2025"
                try:
                    dt = pd.to_datetime(month_str)
                    label = dt.strftime('%b %Y')
                except:
                    label = str(month_str)
                labels.append(label)
                data_rows.append({
                    "label": label,
                    "Instagram": float(row.get('Instagram', 0)),
                    "TikTok": float(row.get('TikTok', 0)),
                    "Facebook": float(row.get('Facebook', 0)),
                    "YouTube": float(row.get('YouTube', 0)),
                    "Total": float(row.get('Total', 0)),
                })

            # Extrapolate Oct-Dec 2025 if we only have through Sep
            if len(data_rows) >= 2 and labels[-1] == 'Sep 2025':
                # Calculate average monthly growth rate from last 3 months
                recent_growth = {}
                for p in platforms:
                    if len(data_rows) >= 3:
                        g1 = data_rows[-1][p] - data_rows[-2][p]
                        g2 = data_rows[-2][p] - data_rows[-3][p]
                        recent_growth[p] = (g1 + g2) / 2
                    else:
                        recent_growth[p] = data_rows[-1][p] - data_rows[-2][p]

                # Project Oct, Nov, Dec 2025
                last_row = data_rows[-1]
                for i, month_label in enumerate(['Oct 2025', 'Nov 2025', 'Dec 2025'], 1):
                    projected = {"label": month_label}
                    total = 0.0
                    for p in platforms:
                        val = last_row[p] + (recent_growth[p] * i)
                        projected[p] = float(val)
                        projected[f'{p}_interpolated'] = True
                        total += val
                    projected['Total'] = float(total)
                    projected['Total_interpolated'] = True
                    labels.append(month_label)
                    data_rows.append(projected)

            return {"labels": labels, "data": data_rows}

        # Fallback to Excel workbook
        wb = Path(sheet_path) if sheet_path else (Path(__file__).resolve().parents[2] / 'public' / 'Care Bears Audience Growth KPis .xlsx')
        if not wb.exists():
            return {"labels": [], "data": []}
        payload = load_follower_history_from_xlsx(wb)
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assumptions-calibrated")
async def get_assumptions_calibrated(use_sheet_calibration: bool = False, sheet_path: str | None = None):
    """Return effective assumptions after optional sheet calibration, with sources."""
    try:
        effective_bmr = BASE_MONTHLY_RATE.copy()
        effective_cap = PLATFORM_MONTHLY_CAP.copy()
        effective_ppg = PER_POST_GAIN_BASE.copy()
        effective_cmult = CONTENT_MULT.copy()
        effective_cpf_paid = CPF_DEFAULT.copy()
        effective_cpf_creator = CPF_DEFAULT.copy()
        seasonality = 0.0
        wb_used = None

        if use_sheet_calibration:
            wb = Path(sheet_path) if sheet_path else (Path(__file__).resolve().parents[2] / 'public' / 'Care Bears Audience Growth KPis .xlsx')
            if wb.exists():
                wb_used = str(wb)
                calib = load_calibration_from_xlsx(wb)
                if calib.get('base_monthly_rate'):
                    effective_bmr.update(calib['base_monthly_rate'])
                if calib.get('platform_monthly_cap'):
                    effective_cap.update(calib['platform_monthly_cap'])
                if calib.get('per_post_gain_base'):
                    effective_ppg.update(calib['per_post_gain_base'])
                if calib.get('cpf_paid'):
                    effective_cpf_paid = calib['cpf_paid']
                if calib.get('cpf_creator'):
                    effective_cpf_creator = calib['cpf_creator']
                seasonality = float(calib.get('month_decay_per_month') or 0.0)

        assumptions = [
            {"label": "Baseline monthly rate (BMR)", "value": effective_bmr, "source": "sheet+default" if use_sheet_calibration else "default"},
            {"label": "Monthly caps", "value": effective_cap, "source": "sheet+default" if use_sheet_calibration else "default"},
            {"label": "Per-post gain base", "value": effective_ppg, "source": "sheet+default" if use_sheet_calibration else "default"},
            {"label": "Content multipliers", "value": effective_cmult, "source": "default"},
            {"label": "Frequency half-saturation", "value": FREQ_HALF_SAT, "source": "default"},
            {"label": "Posting bands", "value": RECOMMENDED_FREQ, "source": "default"},
            {"label": "Paid funnel default", "value": PAID_FUNNEL_DEFAULT, "source": "default"},
            {"label": "CPF paid", "value": effective_cpf_paid, "source": "sheet or request override where set"},
            {"label": "CPF creator", "value": effective_cpf_creator, "source": "sheet or request override where set"},
            {"label": "Seasonality taper per month", "value": seasonality, "source": "sheet (fixed 0.02) or 0.0"},
        ]
        if wb_used:
            assumptions.append({"label": "Workbook path", "value": wb_used, "source": "sheet"})
        return {"assumptions": assumptions}
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

        # Load engagement index from cached historical data
        eng_index = get_engagement_index_cached(DATA_DIR)

        # Optional: sheet-driven calibration
        base_monthly_rate = None
        platform_monthly_cap = None
        per_post_gain_base = None
        paid_funnel = request.paid_funnel or None
        cpf_paid = request.cpf_paid or None
        cpf_creator = request.cpf_creator or None
        cpf_acquisition = request.cpf_acquisition or None
        month_decay_per_month = 0.0

        if request.use_sheet_calibration:
            wb_path = Path(request.sheet_path) if request.sheet_path else (Path(__file__).resolve().parents[2] / 'public' / 'Care Bears Audience Growth KPis .xlsx')
            if wb_path.exists():
                calib = load_calibration_from_xlsx(wb_path)
                base_monthly_rate = calib.get('base_monthly_rate') or None
                platform_monthly_cap = calib.get('platform_monthly_cap') or None
                per_post_gain_base = calib.get('per_post_gain_base') or None
                # Allow CPF overrides if not provided by request
                cpf_paid = cpf_paid or calib.get('cpf_paid') or None
                cpf_creator = cpf_creator or calib.get('cpf_creator') or None
                # Seasonality taper
                month_decay_per_month = float(calib.get('month_decay_per_month') or 0.0)

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
            paid_funnel=(paid_funnel or None),
            paid_budget_per_week_total=(request.paid_budget_per_week_total or 0.0),
            creator_budget_per_week_total=(request.creator_budget_per_week_total or 0.0),
            acquisition_budget_per_week_total=(request.acquisition_budget_per_week_total or 0.0),
            cpf_paid=(cpf_paid or None),
            cpf_creator=(cpf_creator or None),
            cpf_acquisition=(cpf_acquisition or None),
            base_monthly_rate=base_monthly_rate,
            platform_monthly_cap=platform_monthly_cap,
            per_post_gain_base=per_post_gain_base,
            month_decay_per_month=month_decay_per_month,
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


@router.get("/platform-metrics")
async def get_platform_metrics():
    """Get historical posts and engagement data by platform"""
    import json
    try:
        metrics_file = DATA_DIR / "platform_metrics.json"
        if not metrics_file.exists():
            raise HTTPException(status_code=404, detail="Platform metrics data not found")
        with open(metrics_file, "r") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

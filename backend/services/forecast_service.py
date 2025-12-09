import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List

# Constants
PLATFORMS = ["Instagram", "TikTok", "YouTube", "Facebook"]
POST_TYPES = ["Short Video", "Image", "Carousel", "Long Video", "Story/Live"]

BASE_MONTHLY_RATE = {
    "Instagram": 0.0045,
    "TikTok": 0.0040,
    "YouTube": 0.0035,
    "Facebook": 0.0025,
}

FREQ_HALF_SAT = {
    "Instagram": 6,
    "TikTok": 7,
    "YouTube": 3,
    "Facebook": 8,
}

RECOMMENDED_FREQ = {
    "Instagram": {"min": 2,  "max": 7,  "soft": 10, "hard": 14},
    "TikTok":   {"min": 3,  "max": 10, "soft": 15, "hard": 25},
    "YouTube":  {"min": 1,  "max":  3, "soft":  5, "hard":  8},
    "Facebook": {"min": 3,  "max": 10, "soft": 14, "hard": 20},
}

PLATFORM_MONTHLY_CAP = {
    "Instagram": 0.10,
    "TikTok": 0.12,
    "YouTube": 0.08,
    "Facebook": 0.06,
}

CONTENT_MULT = {
    "Instagram": {"Short Video": 1.10, "Image": 1.12, "Carousel": 1.25, "Long Video": 1.05, "Story/Live": 1.00},
    "TikTok":   {"Short Video": 1.30, "Image": 0.75, "Carousel": 0.85, "Long Video": 0.85, "Story/Live": 1.05},
    "YouTube":  {"Short Video": 0.85, "Image": 0.70, "Carousel": 0.80, "Long Video": 1.30, "Story/Live": 0.95},
    "Facebook": {"Short Video": 1.05, "Image": 1.00, "Carousel": 1.05, "Long Video": 1.10, "Story/Live": 1.00},
}

PER_POST_GAIN_BASE = {
    "Instagram": 640.0,
    "TikTok": 450.0,
    "YouTube": 500.0,
    "Facebook": 300.0,
}

PRESETS = {
    "Conservative": {"campaign_lift": 0.0,  "sensitivity": 0.35, "acq_scalar": 0.6},
    "Balanced":     {"campaign_lift": 0.15, "sensitivity": 0.50, "acq_scalar": 1.0},
    "Ambitious":    {"campaign_lift": 0.35, "sensitivity": 0.65, "acq_scalar": 1.5},
}

# Paid funnel default rates (industry-informed, adjustable)
# vtr: views per impression; er: engagements per view; fcr: follows per engagement
PAID_FUNNEL_DEFAULT = {
    "Instagram": {"vtr": 0.35, "er": 0.025, "fcr": 0.015},
    "TikTok":    {"vtr": 0.40, "er": 0.030, "fcr": 0.012},
    "YouTube":   {"vtr": 0.30, "er": 0.020, "fcr": 0.010},
    "Facebook":  {"vtr": 0.28, "er": 0.015, "fcr": 0.008},
}

# Cost-per-follower default ranges (USD)
CPF_DEFAULT = {"min": 0.10, "mid": 0.15, "max": 0.20}


def saturating_effect(freq_per_week: float, half_sat: float) -> float:
    if half_sat <= 0:
        return 0.0
    return float(freq_per_week / (freq_per_week + half_sat))


def blended_content_multiplier(platform: str, mix: dict, content_mult_override: dict | None = None) -> float:
    mults = (content_mult_override or CONTENT_MULT)[platform]
    s = sum(max(v, 0) for v in mix.values()) or 1.0
    return float(sum(mults[t] * max(mix.get(t, 0), 0) for t in POST_TYPES) / s)


def diversity_factor(mix: dict) -> float:
    vals = np.array([max(mix.get(t, 0.0), 0.0) for t in POST_TYPES], dtype=float)
    s = vals.sum() or 1.0
    fracs = vals / s
    hhi = float((fracs ** 2).sum())
    if hhi <= 0.5:
        return 1.0
    if hhi >= 0.9:
        return 0.85
    penalty = 1.0 - (hhi - 0.5) * (0.15 / 0.4)
    return float(max(0.85, min(1.0, penalty)))


def oversaturation_penalty(posts_per_week: float, soft: float, hard: float) -> float:
    if posts_per_week <= soft:
        return 1.0
    if posts_per_week >= hard:
        return 0.6
    ratio = (posts_per_week - soft) / max(hard - soft, 1e-6)
    return float(1.0 - 0.4 * ratio)


def consistency_boost(posts_per_week: float, min_ok: float, max_ok: float) -> float:
    if posts_per_week < min_ok:
        return 0.95
    if posts_per_week <= max_ok:
        return 1.08
    return 1.0


def compute_engagement_index(mentions_df: pd.DataFrame, sentiment_df: pd.DataFrame) -> pd.Series:
    """Compute engagement index from mentions and sentiment data"""
    df = mentions_df[["Time"]].copy()

    # Get mentions column
    mentions_col = 'Mentions' if 'Mentions' in mentions_df.columns else mentions_df.columns[1]
    m = pd.to_numeric(mentions_df[mentions_col], errors='coerce').fillna(0)
    df['mentions'] = m.values

    # Join sentiment
    if 'Time' in sentiment_df.columns:
        sent = sentiment_df.copy()
        for c in ['Positive','Neutral','Negative']:
            if c in sent.columns:
                sent[c] = pd.to_numeric(sent[c], errors='coerce').fillna(0)
            else:
                sent[c] = 0
        sent = sent[['Time','Positive','Neutral','Negative']]
        df = df.merge(sent, on='Time', how='left')
    else:
        df['Positive'] = 0
        df['Neutral'] = df['mentions']
        df['Negative'] = 0

    total = (df['Positive'] + df['Neutral'] + df['Negative']).replace(0, np.nan)
    sentiment_factor = ((df['Positive'] + 0.5*df['Neutral'] - 0.5*df['Negative']) / total).fillna(1.0)
    mentions_norm = (df['mentions'] / max(df['mentions'].max(), 1)).clip(lower=0)
    df['engagement_index'] = (mentions_norm * sentiment_factor).clip(lower=0)

    return df['engagement_index']


def forecast_growth(
    current_followers: Dict[str, int],
    posts_per_week_total: float,
    platform_allocation: Dict[str, float],
    content_mix_by_platform: Dict[str, Dict[str, float]],
    engagement_index_series: pd.Series,
    months: int = 12,
    campaign_lift: float = 0.0,
    sensitivity: float = 0.5,
    acq_scalar: float = 1.0,
    paid_impressions_per_week_total: float = 0.0,
    paid_allocation: Dict[str, float] | None = None,
    paid_funnel: Dict[str, Dict[str, float]] | None = None,
    # budget-based parameters
    paid_budget_per_week_total: float = 0.0,
    creator_budget_per_week_total: float = 0.0,
    acquisition_budget_per_week_total: float = 0.0,
    cpf_paid: Dict[str, float] | None = None,
    cpf_creator: Dict[str, float] | None = None,
    cpf_acquisition: Dict[str, float] | None = None,
    # overrides from calibration
    base_monthly_rate: Dict[str, float] | None = None,
    platform_monthly_cap: Dict[str, float] | None = None,
    content_mult: Dict[str, Dict[str, float]] | None = None,
    per_post_gain_base: Dict[str, float] | None = None,
    # seasonality/taper
    month_decay_per_month: float = 0.0,
) -> pd.DataFrame:
    """Run growth forecast simulation"""
    weeks = months * 4 + 4

    if len(engagement_index_series) == 0:
        engagement_index_series = pd.Series([0.5])

    baseline = float(engagement_index_series.tail(8).mean())
    weekly_engagement_forecast = np.full(weeks, max(baseline * (1 + campaign_lift), 0.0))

    # Convert allocation percentages to fractions
    alloc_frac = {p: max(platform_allocation.get(p, 0.0), 0.0) for p in PLATFORMS}
    total_alloc = sum(alloc_frac.values()) or 1.0
    alloc_frac = {p: v/total_alloc for p, v in alloc_frac.items()}
    posts_per_platform = {p: posts_per_week_total * alloc_frac[p] for p in PLATFORMS}

    # Paid allocation
    if paid_allocation is None:
        paid_alloc_frac = alloc_frac.copy()
    else:
        paid_alloc_frac = {p: max(paid_allocation.get(p, 0.0), 0.0) for p in PLATFORMS}
        total_paid_alloc = sum(paid_alloc_frac.values()) or 1.0
        paid_alloc_frac = {p: v/total_paid_alloc for p, v in paid_alloc_frac.items()}
    paid_funnel = paid_funnel or PAID_FUNNEL_DEFAULT

    # CPF configs
    cpf_paid = cpf_paid or CPF_DEFAULT
    cpf_creator = cpf_creator or CPF_DEFAULT
    cpf_acquisition = cpf_acquisition or CPF_DEFAULT

    # Normalize content mixes
    content_mix_norm = {}
    for p in PLATFORMS:
        mix = content_mix_by_platform.get(p, {})
        s = sum(max(mix.get(t, 0.0), 0.0) for t in POST_TYPES) or 1.0
        content_mix_norm[p] = {t: max(mix.get(t, 0.0), 0.0)/s for t in POST_TYPES}

    # Initialize
    weekly = []
    followers = {p: float(max(current_followers.get(p, 0), 0)) for p in PLATFORMS}

    # Apply overrides for constants
    BMR = base_monthly_rate or BASE_MONTHLY_RATE
    PMC = platform_monthly_cap or PLATFORM_MONTHLY_CAP
    PPG = per_post_gain_base or PER_POST_GAIN_BASE

    for w in range(weeks):
        ei = weekly_engagement_forecast[w]
        week_snapshot = {"Week": w}
        total_added_org = 0.0
        total_added_paid = 0.0

        for p in PLATFORMS:
            freq_eff = saturating_effect(posts_per_platform[p], FREQ_HALF_SAT[p])
            c_mult = blended_content_multiplier(p, content_mix_norm[p], content_mult_override=content_mult)
            div_factor = diversity_factor(content_mix_norm[p])

            freq_cfg = RECOMMENDED_FREQ[p]
            over_pen = oversaturation_penalty(posts_per_platform[p], freq_cfg["soft"], freq_cfg["hard"])
            consist = consistency_boost(posts_per_platform[p], freq_cfg["min"], freq_cfg["max"])

            base_rate = BMR[p] / 4.0
            plan_intensity = (1.0 + sensitivity * ei * freq_eff * c_mult * div_factor * over_pen * consist)
            weekly_rate = base_rate * plan_intensity
            # month-level taper (gentle seasonality/decay)
            if month_decay_per_month > 0:
                m_idx = min(w // 4, months - 1)
                weekly_rate *= max(0.5, 1.0 - month_decay_per_month * m_idx)

            cap_weekly = (1.0 + PMC[p]) ** (1/4.0) - 1.0
            weekly_rate = min(weekly_rate, cap_weekly)
            mult_add = followers[p] * weekly_rate

            quality = 0.5 + 0.5 * ei
            sat_quality = 0.5 + 0.5 * freq_eff
            per_post = PPG[p] * acq_scalar * quality * sat_quality * c_mult * div_factor * over_pen * consist
            add_posts = posts_per_platform[p] * per_post

            # Paid media additive followers this week
            paid_impr = paid_impressions_per_week_total * paid_alloc_frac[p]
            rates = paid_funnel.get(p, PAID_FUNNEL_DEFAULT[p])
            paid_follows = paid_impr * rates.get("vtr", 0.3) * rates.get("er", 0.02) * rates.get("fcr", 0.01)
            # modestly scale by content suitability
            paid_follows *= (0.8 + 0.2 * c_mult)

            # Budget-driven direct CPF followers (mid case); allocate by platform
            paid_budget_follows = 0.0
            creator_budget_follows = 0.0
            acq_budget_follows = 0.0
            if paid_budget_per_week_total > 0 and cpf_paid.get("mid", 4.0) > 0:
                paid_budget_follows = (paid_budget_per_week_total * paid_alloc_frac[p]) / cpf_paid.get("mid", 4.0)
            if creator_budget_per_week_total > 0 and cpf_creator.get("mid", 4.0) > 0:
                creator_budget_follows = (creator_budget_per_week_total * alloc_frac[p]) / cpf_creator.get("mid", 4.0)
            if acquisition_budget_per_week_total > 0 and cpf_acquisition.get("mid", 4.0) > 0:
                acq_budget_follows = (acquisition_budget_per_week_total * alloc_frac[p]) / cpf_acquisition.get("mid", 4.0)

            add_org = mult_add + add_posts
            add_paid = paid_follows + paid_budget_follows + creator_budget_follows + acq_budget_follows
            add = add_org + add_paid
            followers[p] += add
            week_snapshot[p] = followers[p]
            total_added_org += add_org
            total_added_paid += add_paid

        week_snapshot['Total'] = sum(followers.values())
        week_snapshot['Added_Organic'] = total_added_org
        week_snapshot['Added_Paid'] = total_added_paid
        weekly.append(week_snapshot)

    weekly_df = pd.DataFrame(weekly)

    # Aggregate into months
    monthly_rows = []
    start_total = sum(float(max(current_followers.get(p, 0), 0)) for p in PLATFORMS)

    for m in range(months):
        end_idx = min((m+1)*4 - 1, len(weekly_df)-1)
        row = {"Month": m+1}
        for p in PLATFORMS:
            row[p] = float(weekly_df.loc[end_idx, p])
        row["Total"] = float(weekly_df.loc[end_idx, 'Total'])
        # Sum weekly adds across this month
        start_idx = m*4
        month_slice = weekly_df.iloc[start_idx:end_idx+1]
        added_org = float(month_slice['Added_Organic'].sum()) if 'Added_Organic' in month_slice.columns else 0.0
        added_paid = float(month_slice['Added_Paid'].sum()) if 'Added_Paid' in month_slice.columns else 0.0
        row["Added"] = added_org + added_paid
        row["Added_Organic"] = added_org
        row["Added_Paid"] = added_paid
        monthly_rows.append(row)

    return pd.DataFrame(monthly_rows)


def load_historical_data(data_dir: Path):
    """Load historical CSV data"""
    def load_csv(path: Path, date_col: str = "Time") -> pd.DataFrame:
        try:
            df = pd.read_csv(path, encoding="utf-8-sig")
        except Exception:
            df = pd.read_csv(path)

        df.columns = [c.strip().strip('\ufeff').strip('"') for c in df.columns]

        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col].str.replace('"',''), errors='coerce', dayfirst=True)
            df = df.dropna(subset=[date_col])
            df = df.sort_values(by=date_col)

        df = df.loc[:, ~df.columns.duplicated()]
        return df

    mentions_df = load_csv(data_dir / "generaldynamics.csv")
    sentiment_df = load_csv(data_dir / "sentiment-dynamics.csv")
    tags_df = load_csv(data_dir / "tags-dynamics.csv")

    eng_index = compute_engagement_index(mentions_df, sentiment_df)

    # Convert timestamps to ISO format strings for JSON serialization
    for df in [mentions_df, sentiment_df, tags_df]:
        if 'Time' in df.columns:
            df['Time'] = df['Time'].astype(str)

    return {
        "mentions": mentions_df.to_dict('records'),
        "sentiment": sentiment_df.to_dict('records'),
        "tags": tags_df.to_dict('records'),
        "engagement_index": eng_index.to_list()
    }

# Lightweight in-memory cache for historical dataframes and engagement index
_HIST_CACHE: Dict[str, Any] = {
    "dir": None,
    "mtimes": {},
    "mentions_df": None,
    "sentiment_df": None,
    "tags_df": None,
    "engagement_index": None,
}


def _file_mtimes(data_dir: Path) -> Dict[str, float]:
    files = {
        "generaldynamics.csv": data_dir / "generaldynamics.csv",
        "sentiment-dynamics.csv": data_dir / "sentiment-dynamics.csv",
        "tags-dynamics.csv": data_dir / "tags-dynamics.csv",
    }
    out: Dict[str, float] = {}
    for key, p in files.items():
        try:
            out[key] = p.stat().st_mtime
        except Exception:
            out[key] = -1.0
    return out


def _load_csv_df(path: Path, date_col: str = "Time") -> pd.DataFrame:
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(path)
    df.columns = [c.strip().strip('\ufeff').strip('"') for c in df.columns]
    if date_col in df.columns:
        try:
            df[date_col] = pd.to_datetime(df[date_col].astype(str).str.replace('"',''), errors='coerce', dayfirst=True)
            df = df.dropna(subset=[date_col]).sort_values(by=date_col)
        except Exception:
            pass
    return df.loc[:, ~df.columns.duplicated()]


def get_historical_data_cached(data_dir: Path) -> Dict[str, Any]:
    global _HIST_CACHE
    mt = _file_mtimes(data_dir)
    if _HIST_CACHE["dir"] != str(data_dir) or mt != _HIST_CACHE.get("mtimes"):
        mentions_df = _load_csv_df(data_dir / "generaldynamics.csv")
        sentiment_df = _load_csv_df(data_dir / "sentiment-dynamics.csv")
        tags_df = _load_csv_df(data_dir / "tags-dynamics.csv")
        eng_index = compute_engagement_index(mentions_df, sentiment_df)

        _HIST_CACHE = {
            "dir": str(data_dir),
            "mtimes": mt,
            "mentions_df": mentions_df,
            "sentiment_df": sentiment_df,
            "tags_df": tags_df,
            "engagement_index": eng_index,
        }

    mentions_df = _HIST_CACHE["mentions_df"].copy()
    sentiment_df = _HIST_CACHE["sentiment_df"].copy()
    tags_df = _HIST_CACHE["tags_df"].copy()
    for df in (mentions_df, sentiment_df, tags_df):
        if 'Time' in df.columns:
            df['Time'] = df['Time'].astype(str)

    return {
        "mentions": mentions_df.to_dict('records'),
        "sentiment": sentiment_df.to_dict('records'),
        "tags": tags_df.to_dict('records'),
        "engagement_index": list(_HIST_CACHE["engagement_index"].values),
    }


def get_engagement_index_cached(data_dir: Path) -> pd.Series:
    _ = get_historical_data_cached(data_dir)
    return _HIST_CACHE["engagement_index"]

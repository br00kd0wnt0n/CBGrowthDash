import math
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta


@st.cache_data(show_spinner=False)
def load_csv(path: str, date_col: str = "Time") -> pd.DataFrame:
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(path)
    # Clean column names
    df.columns = [c.strip().strip('\ufeff').strip('"') for c in df.columns]
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col].str.replace('"',''), errors='coerce', dayfirst=True)
        df = df.dropna(subset=[date_col])
        df = df.sort_values(by=date_col)
    # Remove duplicate unnamed/empty columns if present
    df = df.loc[:, ~df.columns.duplicated()]
    return df


@st.cache_data(show_spinner=False)
def load_xlsx(path: str) -> dict:
    try:
        xls = pd.ExcelFile(path)
        sheets = {}
        for name in xls.sheet_names:
            df = xls.parse(name)
            df.columns = [str(c).strip() for c in df.columns]
            sheets[name] = df
        return sheets
    except Exception:
        return {}


def safe_first_numeric(df: pd.DataFrame, exclude_cols=("Time",)):
    for c in df.columns:
        if c in exclude_cols:
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            return c
        # try coerce
        try:
            coerced = pd.to_numeric(df[c], errors='coerce')
            if coerced.notna().any():
                return c
        except Exception:
            pass
    return None


def compute_engagement_index(mentions_df: pd.DataFrame, sentiment_df: pd.DataFrame) -> pd.DataFrame:
    df = mentions_df[["Time"]].copy()
    # Mentions column: prefer 'Mentions' if present else first numeric
    mentions_col = 'Mentions' if 'Mentions' in mentions_df.columns else safe_first_numeric(mentions_df)
    if mentions_col is None:
        mentions_col = mentions_df.columns[1]
    m = pd.to_numeric(mentions_df[mentions_col], errors='coerce').fillna(0)
    df['mentions'] = m.values

    # Join sentiment on Time if compatible
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
    return df


def saturating_effect(freq_per_week: float, half_sat: float) -> float:
    # Smoothly saturating curve: effect approaches 1 as frequency grows
    if half_sat <= 0:
        return 0.0
    return float(freq_per_week / (freq_per_week + half_sat))


PLATFORMS = ["Instagram", "TikTok", "YouTube", "Facebook"]
POST_TYPES = ["Short Video", "Image", "Carousel", "Long Video", "Story/Live"]

# Platform base monthly growth rate (organic baseline independent of campaign)
BASE_MONTHLY_RATE = {
    # Conservative organic baselines aligned to extracted trends
    "Instagram": 0.0045,
    "TikTok": 0.0040,
    "YouTube": 0.0035,
    "Facebook": 0.0025,
}

# Frequency half-saturation (posts/week to reach 50% of max effect)
FREQ_HALF_SAT = {
    # Earlier saturation to reflect quality-over-quantity guidance
    "Instagram": 6,
    "TikTok": 7,
    "YouTube": 3,
    "Facebook": 8,
}

# Recommended weekly posting bands and saturation thresholds (industry-informed defaults)
RECOMMENDED_FREQ = {
    # min, max describe the healthy band; soft/hard are oversaturation thresholds
    # Quality > quantity: tighten bands based on cross-channel trends
    "Instagram": {"min": 2,  "max": 7,  "soft": 10, "hard": 14},
    "TikTok":   {"min": 3,  "max": 10, "soft": 15, "hard": 25},
    "YouTube":  {"min": 1,  "max":  3, "soft":  5, "hard":  8},  # shorts+long combined
    "Facebook": {"min": 3,  "max": 10, "soft": 14, "hard": 20},
}

# Practical monthly growth caps to keep outcomes realistic
PLATFORM_MONTHLY_CAP = {
    # approximate organic+campaign upper bounds in kids/baby categories
    "Instagram": 0.10,
    "TikTok": 0.12,  # slowed follower growth despite engagement
    "YouTube": 0.08,
    "Facebook": 0.06,
}

# Content multipliers by platform and post type
CONTENT_MULT = {
    # Reflect extracted trends: IG Carousels lead reach+engagement; Reels solid; Images solid.
    # TikTok Short Video dominant; YouTube On-Demand (Long Video) leads reach; Shorts lower reach but engaging.
    "Instagram": {"Short Video": 1.10, "Image": 1.12, "Carousel": 1.25, "Long Video": 1.05, "Story/Live": 1.00},
    "TikTok":   {"Short Video": 1.30, "Image": 0.75, "Carousel": 0.85, "Long Video": 0.85, "Story/Live": 1.05},
    "YouTube":  {"Short Video": 0.85, "Image": 0.70, "Carousel": 0.80, "Long Video": 1.30, "Story/Live": 0.95},
    "Facebook": {"Short Video": 1.05, "Image": 1.00, "Carousel": 1.05, "Long Video": 1.10, "Story/Live": 1.00},
}

# Per-post acquisition baseline (followers per post at EI=1 and content_mult≈1)
PER_POST_GAIN_BASE = {
    # IG drives ~+42% more reach than TikTok on average; reflect in per-post acquisition
    "Instagram": 640.0,
    "TikTok": 450.0,
    "YouTube": 500.0,
    "Facebook": 300.0,
}

# Forecast presets to simplify assumptions
PRESETS = {
    "Conservative": {"campaign_lift": 0.0,  "sensitivity": 0.35, "acq_scalar": 0.6},
    "Balanced":     {"campaign_lift": 0.15, "sensitivity": 0.50, "acq_scalar": 1.0},
    "Ambitious":    {"campaign_lift": 0.35, "sensitivity": 0.65, "acq_scalar": 1.5},
}


def blended_content_multiplier(platform: str, mix: dict) -> float:
    mults = CONTENT_MULT[platform]
    s = sum(max(v, 0) for v in mix.values()) or 1.0
    return float(sum(mults[t] * max(mix.get(t, 0), 0) for t in POST_TYPES) / s)


def diversity_factor(mix: dict) -> float:
    # Penalize extreme concentration using HHI (sum of squares)
    vals = np.array([max(mix.get(t, 0.0), 0.0) for t in POST_TYPES], dtype=float)
    s = vals.sum() or 1.0
    fracs = vals / s
    hhi = float((fracs ** 2).sum())  # 0.2 (diverse) .. 1.0 (single format)
    if hhi <= 0.5:
        return 1.0
    if hhi >= 0.9:
        return 0.85
    # linear between 0.5 and 0.9
    penalty = 1.0 - (hhi - 0.5) * (0.15 / 0.4)
    return float(max(0.85, min(1.0, penalty)))


def oversaturation_penalty(posts_per_week: float, soft: float, hard: float) -> float:
    if posts_per_week <= soft:
        return 1.0
    if posts_per_week >= hard:
        return 0.6
    # linearly decrease from 1.0 at soft to 0.6 at hard
    ratio = (posts_per_week - soft) / max(hard - soft, 1e-6)
    return float(1.0 - 0.4 * ratio)


def consistency_boost(posts_per_week: float, min_ok: float, max_ok: float) -> float:
    if posts_per_week < min_ok:
        # small penalty for under-posting
        return 0.95
    if posts_per_week <= max_ok:
        return 1.08
    return 1.0


def generate_ai_insights(
    monthly: pd.DataFrame,
    cur_followers: dict,
    platform_alloc: dict,
    content_mix_by_platform: dict,
    posts_per_week_total: float,
    eng_df: pd.DataFrame,
    tags_df: pd.DataFrame,
) -> str:
    lines = []
    platforms = PLATFORMS
    start_total = sum(cur_followers.get(p, 0) for p in platforms)
    end_total = float(monthly['Total'].iloc[-1]) if len(monthly) else start_total
    added_total = end_total - start_total

    # 1) Goal trajectory
    target = start_total * 2
    hit_month = None
    for i in range(len(monthly)):
        if monthly['Total'].iloc[i] >= target:
            hit_month = int(monthly['Month'].iloc[i])
            break
    if hit_month:
        lines.append(f"On track to double total followers by month {hit_month}.")
    else:
        shortfall = max(0, target - end_total)
        progress = (end_total / target * 100) if target > 0 else 0
        lines.append(f"Projected to reach {progress:.1f}% of the doubling goal; shortfall ~{shortfall:,.0f}.")

    # 2) Platform contribution
    contrib = []
    for p in platforms:
        start_p = float(cur_followers.get(p, 0))
        end_p = float(monthly[p].iloc[-1]) if len(monthly) else start_p
        contrib.append((p, max(0.0, end_p - start_p)))
    contrib.sort(key=lambda x: x[1], reverse=True)
    top = ", ".join([f"{p} {int(v):,}" for p, v in contrib[:3]])
    lines.append(f"Top growth contributors: {top}.")

    # 3) Posting plan diagnostics (oversaturation / under-posting)
    alloc_frac = {p: max(platform_alloc.get(p, 0.0), 0.0) for p in platforms}
    total_alloc = sum(alloc_frac.values()) or 1.0
    alloc_frac = {p: v/total_alloc for p, v in alloc_frac.items()}
    posts_breakdown = {p: posts_per_week_total * alloc_frac[p] for p in platforms}
    issues = []
    freq_cfg_map = st.session_state.get("_local_freq_map", RECOMMENDED_FREQ)
    for p in platforms:
        cfg = freq_cfg_map[p]
        pw = posts_breakdown[p]
        if pw < cfg['min']:
            issues.append(f"{p}: below min ({pw:.1f}/wk < {cfg['min']}/wk)")
        elif pw > cfg['hard']:
            issues.append(f"{p}: over hard cap ({pw:.1f}/wk > {cfg['hard']}/wk)")
        elif pw > cfg['soft']:
            issues.append(f"{p}: over soft cap ({pw:.1f}/wk > {cfg['soft']}/wk)")
    if issues:
        lines.append("Posting cadence flags — " + "; ".join(issues) + ".")

    # 4) Content mix diversity
    def mix_hhi(mix: dict) -> float:
        vals = np.array([max(mix.get(t, 0.0), 0.0) for t in POST_TYPES], dtype=float)
        s = vals.sum() or 1.0
        f = vals / s
        return float((f**2).sum())
    conc = []
    for p in platforms:
        h = mix_hhi(content_mix_by_platform.get(p, {}))
        if h >= 0.85:
            conc.append(f"{p}")
    if conc:
        lines.append("High format concentration detected on: " + ", ".join(conc) + ". Consider diversifying 1–2 slots.")

    # 5) Engagement context and tags
    ei_last8 = float(eng_df['engagement_index'].tail(8).mean()) if 'engagement_index' in eng_df else 0.0
    if len(eng_df) >= 16:
        ei_prev8 = float(eng_df['engagement_index'].tail(16).head(8).mean())
        delta = ei_last8 - ei_prev8
        trend = "up" if delta > 0.02 else ("down" if delta < -0.02 else "flat")
        lines.append(f"Engagement trend: {trend} (last 8w avg {ei_last8:.2f}).")
    else:
        lines.append(f"Avg engagement index (last 8w): {ei_last8:.2f}.")
    if 'Time' in tags_df.columns and len(tags_df.columns) > 1:
        tag_cols = [c for c in tags_df.columns if c != 'Time']
        latest = tags_df.sort_values('Time').tail(4)
        sums = latest[tag_cols].apply(pd.to_numeric, errors='coerce').fillna(0).sum().sort_values(ascending=False)
        top_tags = ", ".join(list(sums.head(3).index))
        lines.append(f"Lean into recent tag pillars: {top_tags}.")

    # 6) Action nudge based on goal gap
    if not hit_month:
        # conservative nudge suggestions
        lines.append("Consider +15–25% posts/week and reweight toward high-yield formats (IG Carousels, TT Shorts, YT On‑Demand) while staying under soft caps.")

    return "\n".join(lines)


def forecast_growth(
    current_followers: dict,
    posts_per_week_total: float,
    platform_allocation: dict,        # percentages (0-100)
    content_mix_by_platform: dict,    # per platform dict of POST_TYPES percentages (0-100)
    engagement_index_series: pd.Series, # weekly values 0..~1
    months: int = 12,
    campaign_lift: float = 0.0,       # e.g., 0.2 = +20% engagement lift
    sensitivity: float = 0.5,         # scales how strongly engagement drives growth (multiplicative)
    acq_scalar: float = 1.0,          # scales additive per-post acquisition
) -> pd.DataFrame:
    # Build a weekly timeline for the next 12 months, using last index as baseline
    weeks = months * 4 + 4  # approx 4 weeks/month
    if len(engagement_index_series) == 0:
        engagement_index_series = pd.Series([0.5])
    baseline = float(engagement_index_series.tail(8).mean())
    # simple flat forecast with optional lift
    weekly_engagement_forecast = np.full(weeks, max(baseline * (1 + campaign_lift), 0.0))

    # Convert allocation percentages to fractions and compute posts per platform
    alloc_frac = {p: max(platform_allocation.get(p, 0.0), 0.0) for p in PLATFORMS}
    total_alloc = sum(alloc_frac.values()) or 1.0
    alloc_frac = {p: v/total_alloc for p, v in alloc_frac.items()}
    posts_per_platform = {p: posts_per_week_total * alloc_frac[p] for p in PLATFORMS}

    # Normalize content mixes per platform
    content_mix_norm = {}
    for p in PLATFORMS:
        mix = content_mix_by_platform.get(p, {})
        s = sum(max(mix.get(t, 0.0), 0.0) for t in POST_TYPES) or 1.0
        content_mix_norm[p] = {t: max(mix.get(t, 0.0), 0.0)/s for t in POST_TYPES}

    # Initialize weekly follower arrays per platform
    weekly = []
    followers = {p: float(max(current_followers.get(p, 0), 0)) for p in PLATFORMS}

    for w in range(weeks):
        ei = weekly_engagement_forecast[w]
        week_snapshot = {"Week": w}
        total_added = 0.0
        for p in PLATFORMS:
            freq_eff = saturating_effect(posts_per_platform[p], FREQ_HALF_SAT[p])
            content_mult = blended_content_multiplier(p, content_mix_norm[p])
            div_factor = diversity_factor(content_mix_norm[p])
            # Use dynamic benchmark maps if present in session state, else defaults
            freq_cfg_map = st.session_state.get("_local_freq_map", RECOMMENDED_FREQ)
            caps_map = st.session_state.get("_local_caps_map", PLATFORM_MONTHLY_CAP)
            freq_cfg = freq_cfg_map[p]
            over_pen = oversaturation_penalty(posts_per_platform[p], freq_cfg["soft"], freq_cfg["hard"])
            consist = consistency_boost(posts_per_platform[p], freq_cfg["min"], freq_cfg["max"])
            base_rate = BASE_MONTHLY_RATE[p] / 4.0  # per week baseline rate
            # multiplicative growth from existing base
            plan_intensity = (1.0 + sensitivity * ei * freq_eff * content_mult * div_factor * over_pen * consist)
            weekly_rate = base_rate * plan_intensity
            # cap multiplicative weekly rate to monthly cap translated to weekly
            cap_weekly = (1.0 + caps_map[p]) ** (1/4.0) - 1.0
            weekly_rate = min(weekly_rate, cap_weekly)
            mult_add = followers[p] * weekly_rate
            # additive per-post acquisition scaled by engagement and mild saturation
            quality = 0.5 + 0.5 * ei
            sat_quality = 0.5 + 0.5 * freq_eff
            per_post = PER_POST_GAIN_BASE[p] * acq_scalar * quality * sat_quality * content_mult * div_factor * over_pen * consist
            add_posts = posts_per_platform[p] * per_post
            add = mult_add + add_posts
            followers[p] += add
            week_snapshot[p] = followers[p]
            total_added += add
        week_snapshot['Total'] = sum(followers.values())
        weekly.append(week_snapshot)

    weekly_df = pd.DataFrame(weekly)

    # Aggregate into months (approx: 4 weeks per month)
    monthly_rows = []
    start_total = sum(float(max(current_followers.get(p, 0), 0)) for p in PLATFORMS)
    for m in range(months):
        end_idx = (m+1)*4 - 1
        end_idx = min(end_idx, len(weekly_df)-1)
        row = {"Month": m+1}
        for p in PLATFORMS:
            row[p] = float(weekly_df.loc[end_idx, p])
        row["Total"] = float(weekly_df.loc[end_idx, 'Total'])
        row["Added"] = row["Total"] - start_total
        monthly_rows.append(row)
    monthly_df = pd.DataFrame(monthly_rows)
    return monthly_df


def pct_dict_inputs(label: str, keys: list[str], defaults: dict[str, float], step=1.0, key_prefix: str = ""):
    cols = st.columns(len(keys))
    values = {}
    for i, k in enumerate(keys):
        with cols[i]:
            key = f"{key_prefix}-{label}-{k}" if key_prefix else f"{label}-{k}"
            values[k] = st.number_input(
                f"{label}: {k} %",
                min_value=0.0,
                max_value=100.0,
                value=float(defaults.get(k, 0.0)),
                step=step,
                key=key,
            )
    s = sum(values.values()) or 1.0
    normed = {k: (v / s) * 100.0 for k, v in values.items()}
    st.caption("Percentages auto-normalized to sum 100%.")
    return normed


def main():
    st.set_page_config(page_title="Care Bears Social Growth Planner", layout="wide")

    # --- Design: modern font + compact layout + subtle theming ---
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"], .stApp {font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif;}
        .stApp {background: #F1F5F9; color: #1F2937;}
        .block-container {max-width: 1200px; padding-top: 1rem;}
        header[data-testid="stHeader"] {background: transparent;}
        /* Global text colors */
        h1, h2, h3, h4, h5, h6, p, span, div, label {color: #1F2937 !important;}
        .stMarkdown, .stMarkdown p, .stMarkdown span {color: #1F2937 !important;}
        .stCaption {color: #6B7280 !important;}
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {gap: 8px;}
        .stTabs [data-baseweb="tab"] {background: #FFFFFF; border-radius: 10px; padding: 10px 14px; box-shadow: 0 1px 2px rgba(0,0,0,0.06); color: #1F2937;}
        .stTabs [aria-selected="true"] {background: #EEF2FF; color: #3730A3;}
        /* Sidebar */
        section[data-testid="stSidebar"] {background-color: #FFFFFF; border-right: 1px solid #E5E7EB;}
        section[data-testid="stSidebar"] * {color: #1F2937 !important;}
        section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label {color: #1F2937 !important;}
        /* Metrics */
        .stMetric {background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);}
        .stMetric > div {gap: 6px;}
        .stMetric label, .stMetric [data-testid="stMetricLabel"], .stMetric [data-testid="stMetricValue"] {color: #1F2937 !important;}
        /* Inputs */
        .stDownloadButton {margin-top: 0.5rem;}
        .stSlider, .stNumberInput {background: transparent;}
        .stSlider label, .stNumberInput label {color: #1F2937 !important;}
        .stSelectbox label, .stRadio label {color: #1F2937 !important;}
        /* Force light backgrounds and dark text on all inputs */
        input, select, textarea {
            background-color: #FFFFFF !important;
            color: #1F2937 !important;
            border: 1px solid #D1D5DB !important;
        }
        .stNumberInput input {
            background-color: #FFFFFF !important;
            color: #1F2937 !important;
        }
        /* Number input +/- buttons */
        .stNumberInput button {
            background-color: #FFFFFF !important;
            color: #1F2937 !important;
            border: 1px solid #D1D5DB !important;
        }
        .stNumberInput button:hover {
            background-color: #F3F4F6 !important;
        }
        .stNumberInput button svg {
            color: #1F2937 !important;
            fill: #1F2937 !important;
        }
        /* Selectbox and dropdown */
        .stSelectbox select, .stSelectbox div[data-baseweb="select"] {
            background-color: #FFFFFF !important;
            color: #1F2937 !important;
        }
        .stSelectbox div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            color: #1F2937 !important;
        }
        /* Make selectbox input non-editable */
        .stSelectbox input {
            pointer-events: none !important;
            cursor: pointer !important;
            caret-color: transparent !important;
        }
        .stSelectbox div[data-baseweb="select"] input {
            pointer-events: none !important;
            cursor: pointer !important;
            caret-color: transparent !important;
        }
        /* Dropdown menu options */
        ul[role="listbox"], li[role="option"] {
            background-color: #FFFFFF !important;
            color: #1F2937 !important;
        }
        li[role="option"]:hover {
            background-color: #F3F4F6 !important;
        }
        /* Radio buttons */
        .stRadio div[role="radiogroup"] label {
            color: #1F2937 !important;
        }
        /* Expanders - more specific selectors */
        .streamlit-expanderHeader, details summary {
            background-color: #FFFFFF !important;
            color: #1F2937 !important;
        }
        .streamlit-expanderContent, details[open] {
            background-color: #FAFAFA !important;
            color: #1F2937 !important;
        }
        details summary * {
            color: #1F2937 !important;
        }
        /* All buttons including download */
        button, .stButton button, .stDownloadButton button {
            background-color: #FFFFFF !important;
            color: #1F2937 !important;
            border: 1px solid #D1D5DB !important;
        }
        button:hover, .stButton button:hover, .stDownloadButton button:hover {
            background-color: #F3F4F6 !important;
            color: #1F2937 !important;
        }
        button *, .stButton button *, .stDownloadButton button * {
            color: #1F2937 !important;
        }
        /* Dataframes */
        .stDataFrame, .stDataFrame tbody tr, .stDataFrame td, .stDataFrame th {
            background-color: #FFFFFF !important;
            color: #1F2937 !important;
        }
        /* Columns */
        .stColumn {
            background: transparent !important;
        }
        /* Hide Streamlit footer/menu for cleaner look */
        #MainMenu {visibility: hidden;} footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Plotly defaults for a clean look
    px.defaults.template = "simple_white"
    px.defaults.color_discrete_sequence = ["#4F46E5", "#06B6D4", "#10B981", "#F59E0B", "#EF4444", "#64748B"]

    st.markdown("<h1 style='margin-bottom:0.25rem'>Care Bears Social Growth Planner</h1>", unsafe_allow_html=True)
    st.caption("Historical context + live scenario planning to inform strategy.")

    # --- Load data ---
    data_dir = "."
    mentions_df = load_csv(f"{data_dir}/generaldynamics.csv")
    sentiment_df = load_csv(f"{data_dir}/sentiment-dynamics.csv")
    tags_df = load_csv(f"{data_dir}/tags-dynamics.csv")
    authors_xlsx = load_xlsx(f"{data_dir}/YouScan_Authors_Care_Bears_02122024-02122025_ac903.xlsx")

    # Compute engagement index
    eng_df = compute_engagement_index(mentions_df, sentiment_df)

    with st.sidebar:
        st.header("Inputs")

        with st.expander("Live Data (optional)"):
            st.caption("Paste public CSV URLs to override local files. If your YouScan board is private, create a public export or Sheet and paste its link here.")
            use_remote = st.checkbox("Use remote CSVs", value=False, key="use-remote")
            rem_mentions = st.text_input("Mentions CSV URL", placeholder="https://.../generaldynamics.csv")
            rem_sent = st.text_input("Sentiment CSV URL", placeholder="https://.../sentiment-dynamics.csv")
            rem_tags = st.text_input("Tags CSV URL", placeholder="https://.../tags-dynamics.csv")
            refresh = st.button("Fetch remote data now")

            if use_remote and (refresh or (rem_mentions or rem_sent or rem_tags)):
                def _load_remote(label, url):
                    if not url:
                        return None
                    try:
                        df = pd.read_csv(url)
                        df.columns = [c.strip().strip('\ufeff').strip('"') for c in df.columns]
                        if 'Time' in df.columns:
                            df['Time'] = pd.to_datetime(df['Time'], errors='coerce', dayfirst=True)
                        st.success(f"Loaded {label} from remote URL")
                        return df
                    except Exception as e:
                        st.error(f"Failed to load {label}: {e}")
                        return None

                mdf = _load_remote('Mentions', rem_mentions)
                sdf = _load_remote('Sentiment', rem_sent)
                tdf = _load_remote('Tags', rem_tags)
                if mdf is not None:
                    mentions_df = mdf
                if sdf is not None:
                    sentiment_df = sdf
                if tdf is not None:
                    tags_df = tdf

        st.subheader("Current Followers")
        cur_followers = {}
        cols = st.columns(3)
        baseline_defaults = {
            "TikTok": 572_700,
            "Instagram": 384_000,
            "Facebook": 590_000,
            "YouTube": 381_000,
        }
        for i, p in enumerate(PLATFORMS):
            with cols[i % 3]:
                cur_followers[p] = st.number_input(
                    f"{p}",
                    min_value=0,
                    value=int(baseline_defaults.get(p, 0)),
                    step=500,
                    key=f"cur-followers-{p}",
                )
        total_current = sum(cur_followers.values())

        st.divider()
        st.subheader("Publishing Plan")
        total_posts_week = st.slider("Total posts per week (all platforms)", 0, 140, 35)

        platform_alloc_defaults = {"Instagram": 35.0, "TikTok": 35.0, "YouTube": 15.0, "Facebook": 15.0}
        platform_alloc = pct_dict_inputs("Platform Mix", PLATFORMS, platform_alloc_defaults, key_prefix="platform-alloc")

        st.subheader("Content Mix per Platform")
        content_mix_by_platform = {}
        for p in PLATFORMS:
            with st.expander(f"{p} content mix", expanded=(p in ("Instagram","TikTok"))):
                defaults = {
                    "Instagram":  {"Short Video": 25, "Image": 30, "Carousel": 35, "Long Video": 5,  "Story/Live": 5},
                    "TikTok":    {"Short Video": 90, "Image": 3,  "Carousel": 2,  "Long Video": 3,  "Story/Live": 2},
                    "YouTube":   {"Short Video": 30, "Image": 0,  "Carousel": 0,  "Long Video": 70, "Story/Live": 0},
                    "Facebook":  {"Short Video": 30, "Image": 40, "Carousel": 15, "Long Video": 10, "Story/Live": 5},
                }[p]
                content_mix_by_platform[p] = pct_dict_inputs("Mix", POST_TYPES, defaults, step=5.0, key_prefix=f"mix-{p}")

        st.divider()
        st.subheader("Forecast Settings")
        preset = st.selectbox(
            "Strategy preset",
            options=list(PRESETS.keys()),
            index=1,
            help="Locks forecast assumptions to realistic benchmark ranges.",
            key="preset-select",
        )
        months = st.slider("Projection horizon (months)", 3, 24, 12, key="months")
        # Locked parameters from preset
        preset_cfg = PRESETS[preset]
        campaign_lift = preset_cfg["campaign_lift"]
        sensitivity = preset_cfg["sensitivity"]
        acq_scalar = preset_cfg["acq_scalar"]
        st.caption(
            f"Using preset assumptions — Campaign lift: {campaign_lift:.2f}, "
            f"Sensitivity: {sensitivity:.2f}, Per‑post acquisition: {acq_scalar:.2f}"
        )

        # Optional benchmark overrides (kept hidden by default)
        with st.expander("Benchmarks (optional)"):
            st.caption("Override posting bands and growth caps, if you have industry numbers.")
            use_override = st.checkbox("Use custom benchmark overrides", value=False, key="bench-override")
            local_freq = {**RECOMMENDED_FREQ}
            local_caps = {**PLATFORM_MONTHLY_CAP}
            if use_override:
                for p in PLATFORMS:
                    st.markdown(f"**{p}**")
                    c1, c2, c3, c4, c5 = st.columns(5)
                    with c1:
                        local_freq[p]["min"] = st.number_input(f"{p} min/wk", 0, 84, int(RECOMMENDED_FREQ[p]["min"]), key=f"{p}-min")
                    with c2:
                        local_freq[p]["max"] = st.number_input(f"{p} ideal max/wk", 0, 84, int(RECOMMENDED_FREQ[p]["max"]), key=f"{p}-max")
                    with c3:
                        local_freq[p]["soft"] = st.number_input(f"{p} soft cap/wk", 0, 140, int(RECOMMENDED_FREQ[p]["soft"]), key=f"{p}-soft")
                    with c4:
                        local_freq[p]["hard"] = st.number_input(f"{p} hard cap/wk", 0, 200, int(RECOMMENDED_FREQ[p]["hard"]), key=f"{p}-hard")
                    with c5:
                        local_caps[p] = st.number_input(f"{p} monthly cap", 0.0, 0.5, float(PLATFORM_MONTHLY_CAP[p]), 0.01, key=f"{p}-cap")
            else:
                local_freq = RECOMMENDED_FREQ
                local_caps = PLATFORM_MONTHLY_CAP

    # --- Historical charts (tabs for clarity) ---
    st.subheader("Historical Overview")
    t1, t2, t3 = st.tabs(["Mentions", "Sentiment", "Tags"])
    with t1:
        if "Time" in mentions_df.columns:
            mcol = 'Mentions' if 'Mentions' in mentions_df.columns else safe_first_numeric(mentions_df)
            m_plot = mentions_df[['Time', mcol]].rename(columns={mcol: 'Mentions'})
            fig_m = px.line(m_plot, x='Time', y='Mentions', title=None)
            fig_m.update_layout(
                font_family="Inter",
                font_color="#1F2937",
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FAFAFA",
                legend_title_text="",
                legend=dict(font=dict(color="#1F2937")),
            )
            fig_m.update_xaxes(tickfont=dict(color="#1F2937"), title_font=dict(color="#1F2937"))
            fig_m.update_yaxes(tickfont=dict(color="#1F2937"), title_font=dict(color="#1F2937"))
            st.plotly_chart(fig_m, use_container_width=True)
    with t2:
        if 'Time' in sentiment_df.columns:
            sent_plot = sentiment_df.copy()
            for c in ['Positive','Neutral','Negative']:
                if c in sent_plot.columns:
                    sent_plot[c] = pd.to_numeric(sent_plot[c], errors='coerce').fillna(0).clip(lower=0)
                else:
                    sent_plot[c] = 0
            sent_plot['Total'] = (sent_plot.get('Positive', 0) + sent_plot.get('Neutral', 0) + sent_plot.get('Negative', 0)).replace(0, np.nan)

            view = st.radio("View", ["Counts", "Percent"], horizontal=True, key="sent-view")
            color_map = {"Positive": "#2ca02c", "Neutral": "#7f7f7f", "Negative": "#d62728"}
            if view == "Counts":
                fig_s = px.area(
                    sent_plot,
                    x='Time',
                    y=['Positive','Neutral','Negative'],
                    title=None,
                    color_discrete_map=color_map,
                )
                fig_s.update_layout(
                    font_family="Inter",
                    font_color="#1F2937",
                    paper_bgcolor="#FFFFFF",
                    plot_bgcolor="#FAFAFA",
                    legend_title_text="Sentiment",
                    legend=dict(font=dict(color="#1F2937")),
                )
                fig_s.update_xaxes(tickfont=dict(color="#1F2937"), title_font=dict(color="#1F2937"))
                fig_s.update_yaxes(tickfont=dict(color="#1F2937"), title_font=dict(color="#1F2937"))
                # Update traces to ensure proper rendering with sparse data
                fig_s.update_traces(line_shape='linear', connectgaps=True)
                st.plotly_chart(fig_s, use_container_width=True)
            else:
                sp = sent_plot.copy()
                for c in ['Positive','Neutral','Negative']:
                    sp[c] = (sp[c] / sp['Total'] * 100).fillna(0)
                fig_sp = px.area(
                    sp,
                    x='Time',
                    y=['Positive','Neutral','Negative'],
                    title=None,
                    color_discrete_map=color_map,
                )
                fig_sp.update_layout(
                    font_family="Inter",
                    font_color="#1F2937",
                    paper_bgcolor="#FFFFFF",
                    plot_bgcolor="#FAFAFA",
                    legend_title_text="Sentiment",
                    legend=dict(font=dict(color="#1F2937")),
                )
                fig_sp.update_yaxes(title_text='Share %', tickfont=dict(color="#1F2937"), title_font=dict(color="#1F2937"))
                fig_sp.update_xaxes(tickfont=dict(color="#1F2937"), title_font=dict(color="#1F2937"))
                # Update traces to ensure proper rendering with sparse data
                fig_sp.update_traces(line_shape='linear', connectgaps=True)
                st.plotly_chart(fig_sp, use_container_width=True)

            st.caption(f"Avg Engagement Index (last 8w): {eng_df['engagement_index'].tail(8).mean():.2f}")
            with st.expander("Show last 6 rows (sentiment)"):
                st.dataframe(sent_plot.tail(6).drop(columns=['Total']), use_container_width=True)
    with t3:
        if 'Time' in tags_df.columns and len(tags_df.columns) > 1:
            tag_cols = [c for c in tags_df.columns if c != 'Time']
            latest = tags_df.sort_values('Time').tail(4)
            sums = latest[tag_cols].apply(pd.to_numeric, errors='coerce').fillna(0).sum().sort_values(ascending=False)
            top = sums.head(5)
            fig_tags = px.bar(top, title=None)
            st.plotly_chart(fig_tags, use_container_width=True)

    st.divider()

    # At-a-glance summary (no duplicates of per-platform follower inputs)
    mcol1, mcol2, mcol3 = st.columns(3)
    with mcol1:
        st.metric("Current Total Followers", f"{total_current:,}")
    with mcol2:
        st.metric("Horizon (months)", months)
    with mcol3:
        st.metric("Avg Engagement Index (8w)", f"{eng_df['engagement_index'].tail(8).mean():.2f}")

    # Plan breakdown: posts/week by platform (for transparency)
    st.subheader("Plan Breakdown")
    # Normalize platform allocation to fractions
    alloc_frac = {p: max(platform_alloc.get(p, 0.0), 0.0) for p in PLATFORMS}
    total_alloc = sum(alloc_frac.values()) or 1.0
    alloc_frac = {p: v/total_alloc for p, v in alloc_frac.items()}
    posts_breakdown = {p: total_posts_week * alloc_frac[p] for p in PLATFORMS}
    br_cols = st.columns(len(PLATFORMS))
    for i, p in enumerate(PLATFORMS):
        with br_cols[i]:
            st.metric(f"{p} posts/week", f"{posts_breakdown[p]:.1f}")
            # Pull benchmark maps from state (set below), fallback to defaults
            cfg_map = st.session_state.get("_local_freq_map", RECOMMENDED_FREQ)
            cfg = cfg_map[p]
            warn = ''
            if posts_breakdown[p] < cfg['min']:
                warn = f"Under min ({cfg['min']}/wk)"
            elif posts_breakdown[p] > cfg['hard']:
                warn = f"Over hard cap ({cfg['hard']}/wk)"
            elif posts_breakdown[p] > cfg['soft']:
                warn = f"Over soft cap ({cfg['soft']}/wk)"
            elif posts_breakdown[p] > cfg['max']:
                warn = f"Above ideal ({cfg['max']}/wk)"
            if warn:
                st.caption(f"⚠ {warn}")

    # Stash benchmark overrides for forecast if changed
    if 'bench-override' in st.session_state and st.session_state['bench-override']:
        st.session_state['_local_freq_map'] = local_freq
        st.session_state['_local_caps_map'] = local_caps
    else:
        st.session_state['_local_freq_map'] = RECOMMENDED_FREQ
        st.session_state['_local_caps_map'] = PLATFORM_MONTHLY_CAP

    # --- Forecast ---
    monthly = forecast_growth(
        current_followers=cur_followers,
        posts_per_week_total=total_posts_week,
        platform_allocation=platform_alloc,
        content_mix_by_platform=content_mix_by_platform,
        engagement_index_series=eng_df['engagement_index'],
        months=months,
        campaign_lift=campaign_lift,
        sensitivity=sensitivity,
        acq_scalar=acq_scalar,
    )

    st.subheader("Projection")
    cproj1, cproj2 = st.columns(2)
    with cproj1:
        fig_stack = go.Figure()
        for p in PLATFORMS:
            fig_stack.add_trace(go.Scatter(x=monthly['Month'], y=monthly[p], mode='lines', name=p, stackgroup='one'))
        fig_stack.update_layout(
            title="By Platform (stacked)",
            title_font=dict(color="#1F2937"),
            xaxis_title="Month",
            yaxis_title="Followers",
            font_family="Inter",
            font_color="#1F2937",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FAFAFA",
            legend=dict(font=dict(color="#1F2937"))
        )
        fig_stack.update_xaxes(tickfont=dict(color="#1F2937"), title_font=dict(color="#1F2937"))
        fig_stack.update_yaxes(tickfont=dict(color="#1F2937"), title_font=dict(color="#1F2937"))
        st.plotly_chart(fig_stack, use_container_width=True)
    with cproj2:
        fig_total = px.line(monthly, x='Month', y='Total', title='Total Followers')
        fig_total.update_layout(
            font_family="Inter",
            font_color="#1F2937",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FAFAFA",
            title_font=dict(color="#1F2937"),
            legend=dict(font=dict(color="#1F2937"))
        )
        fig_total.update_xaxes(tickfont=dict(color="#1F2937"), title_font=dict(color="#1F2937"))
        fig_total.update_yaxes(tickfont=dict(color="#1F2937"), title_font=dict(color="#1F2937"))
        st.plotly_chart(fig_total, use_container_width=True)

    goal = total_current * 2
    last_total = float(monthly['Total'].iloc[-1])
    pct_to_goal = (last_total / goal * 100) if goal > 0 else 0
    g1, g2, g3 = st.columns(3)
    with g1:
        st.metric("Projected Total (end)", f"{last_total:,.0f}")
    with g2:
        st.metric("Doubling Goal", f"{goal:,.0f}")
    with g3:
        st.metric("Progress to Goal", f"{pct_to_goal:.1f}%")

    st.dataframe(monthly.style.format({**{p: '{:,.0f}' for p in PLATFORMS}, 'Total': '{:,.0f}', 'Added': '{:,.0f}'}), use_container_width=True)

    # AI Insights — generate on first load and allow manual regenerate
    st.subheader("AI Insights")
    regen = st.button("Regenerate insights", help="Recompute insights based on current plan and data")
    if regen or 'insights_text' not in st.session_state:
        st.session_state['insights_text'] = generate_ai_insights(
            monthly=monthly,
            cur_followers=cur_followers,
            platform_alloc=platform_alloc,
            content_mix_by_platform=content_mix_by_platform,
            posts_per_week_total=total_posts_week,
            eng_df=eng_df,
            tags_df=tags_df,
        )
        st.session_state['insights_updated'] = pd.Timestamp.utcnow()
    st.write(st.session_state.get('insights_text', ''))
    ts = st.session_state.get('insights_updated')
    if ts is not None:
        st.caption(f"Last updated: {ts.tz_localize('UTC').tz_convert('US/Pacific').strftime('%Y-%m-%d %H:%M %Z')}")

    # Export
    csv = monthly.to_csv(index=False).encode('utf-8')
    st.download_button("Download projection CSV", csv, file_name="projection.csv", mime="text/csv")


if __name__ == "__main__":
    main()

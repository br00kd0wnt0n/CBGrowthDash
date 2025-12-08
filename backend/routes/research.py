"""
Research API endpoints for GWI data and audience presets.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional

from data.gwi_research import (
    GWI_RESEARCH,
    AUDIENCE_PRESETS,
    calculate_blended_allocation,
    get_segment_insights,
    get_platform_insight
)

router = APIRouter(prefix="/api/research", tags=["research"])


class AudienceMix(BaseModel):
    parents: float = 0.6
    gifters: float = 0.25
    collectors: float = 0.15


class AllocationRecommendation(BaseModel):
    recommended_allocation: Dict[str, int]
    rationale: str
    confidence: float
    segment_weights: Dict[str, float]


@router.get("/overview")
async def get_research_overview():
    """Get high-level research overview and key insights."""
    return {
        "meta": GWI_RESEARCH["meta"],
        "key_insights": GWI_RESEARCH["key_insights"],
        "segments_summary": {
            name: {
                "sample_size": data["sample_size"],
                "description": data["description"]
            }
            for name, data in GWI_RESEARCH["segments"].items()
        }
    }


@router.get("/segments")
async def get_all_segments():
    """Get all segment data."""
    return GWI_RESEARCH["segments"]


@router.get("/segments/{segment_name}")
async def get_segment(segment_name: str):
    """Get detailed data for a specific segment."""
    if segment_name not in GWI_RESEARCH["segments"]:
        raise HTTPException(status_code=404, detail=f"Segment '{segment_name}' not found")

    segment_data = GWI_RESEARCH["segments"][segment_name]
    insights = get_segment_insights(segment_name)

    return {
        "segment": segment_name,
        "data": segment_data,
        "insights": insights
    }


@router.get("/platforms/{platform_name}")
async def get_platform_data(platform_name: str):
    """Get research data for a specific platform across all segments."""
    platform_lower = platform_name.lower()
    valid_platforms = ["instagram", "tiktok", "youtube", "facebook", "snapchat", "twitch", "discord", "twitter", "pinterest"]

    if platform_lower not in valid_platforms:
        raise HTTPException(status_code=404, detail=f"Platform '{platform_name}' not found")

    return get_platform_insight(platform_name)


@router.get("/presets")
async def get_all_presets():
    """Get all available audience presets."""
    return {
        "presets": list(AUDIENCE_PRESETS.values()),
        "default": "balanced"
    }


@router.get("/presets/{preset_id}")
async def get_preset(preset_id: str):
    """Get a specific preset by ID."""
    if preset_id not in AUDIENCE_PRESETS:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")

    return AUDIENCE_PRESETS[preset_id]


@router.post("/allocation/recommend")
async def recommend_allocation(audience_mix: AudienceMix):
    """
    Calculate recommended platform allocation based on audience mix.

    The mix should sum to 1.0 (100%), but will be normalised if not.
    """
    mix = {
        "parents": audience_mix.parents,
        "gifters": audience_mix.gifters,
        "collectors": audience_mix.collectors
    }

    # Normalise if doesn't sum to 1.0
    total = sum(mix.values())
    if total != 1.0 and total > 0:
        mix = {k: v / total for k, v in mix.items()}

    recommended = calculate_blended_allocation(mix)

    # Generate rationale based on dominant segment
    dominant_segment = max(mix.items(), key=lambda x: x[1])
    segment_name = dominant_segment[0]
    segment_pct = int(dominant_segment[1] * 100)

    # Get top platform recommendation
    top_platform = max(recommended.items(), key=lambda x: x[1])

    rationale = f"With {segment_pct}% focus on {segment_name}, "
    if segment_name == "parents":
        rationale += "allocation prioritises TikTok (1.30x index) and Instagram (1.15x index) where CB-purchasing parents over-index."
    elif segment_name == "gifters":
        rationale += "allocation emphasises Facebook (1.14x index) where gifters show strongest engagement and brand trust signals."
    elif segment_name == "collectors":
        rationale += "allocation balances visual discovery platforms. Nostalgia-driven content on Instagram and Facebook recommended."

    # Calculate confidence based on sample sizes and mix clarity
    segment_weights = {
        "parents": GWI_RESEARCH["segments"]["parents"]["sample_size"] / GWI_RESEARCH["meta"]["total_respondents"],
        "gifters": GWI_RESEARCH["segments"]["gifters"]["sample_size"] / GWI_RESEARCH["meta"]["total_respondents"],
        "collectors": GWI_RESEARCH["segments"]["collectors"]["sample_size"] / GWI_RESEARCH["meta"]["total_respondents"]
    }

    # Higher confidence when mix aligns with larger sample segments
    weighted_confidence = sum(mix[seg] * weight for seg, weight in segment_weights.items())
    confidence = round(0.70 + (weighted_confidence * 0.25), 2)  # 0.70-0.95 range

    return AllocationRecommendation(
        recommended_allocation=recommended,
        rationale=rationale,
        confidence=confidence,
        segment_weights=mix
    )


@router.get("/insights/contextual/{context}")
async def get_contextual_insight(context: str, platform: Optional[str] = None, value: Optional[float] = None):
    """
    Get contextual research insights for UI callouts.

    Context types:
    - platform_allocation: When adjusting a platform slider
    - posts_per_week: When adjusting posting frequency
    - audience_mix: When adjusting audience composition
    - preset_selection: When selecting a preset
    """
    insights = []

    if context == "platform_allocation" and platform:
        platform_data = get_platform_insight(platform)
        if platform_data["avg_index"] > 1.0:
            insights.append({
                "type": "positive",
                "text": platform_data["insight"],
                "detail": f"GWI 2024 shows {platform} has a {platform_data['avg_index']}x purchaser index"
            })

        # Add segment-specific insights
        for seg_name, seg_data in platform_data["segments"].items():
            if seg_data["index"] > 1.15:
                insights.append({
                    "type": "highlight",
                    "text": f"{seg_name.title()} segment: {int((seg_data['index']-1)*100)}% over-index",
                    "detail": f"{int(seg_data['purchaser_usage']*100)}% of CB purchasers vs {int(seg_data['total_usage']*100)}% overall"
                })

    elif context == "posts_per_week" and value:
        if value > 30:
            insights.append({
                "type": "warning",
                "text": "Research shows engagement quality typically decreases above 30 posts/week",
                "detail": "Consider quality-focused content mix to maintain engagement rates"
            })
        elif value < 15:
            insights.append({
                "type": "info",
                "text": "Lower posting frequency works best with high-quality, targeted content",
                "detail": "Focus on platform-native formats and audience-specific messaging"
            })

    elif context == "audience_mix":
        insights.append({
            "type": "info",
            "text": "Audience mix affects optimal platform allocation",
            "detail": "Parents over-index on TikTok (1.30x), Gifters on Facebook (1.14x)"
        })

        # Collector-specific insight
        insights.append({
            "type": "highlight",
            "text": "Collectors are primarily motivated by nostalgia (39%) and values (33%)",
            "detail": "Consider heritage and values-driven content for collector segments"
        })

    elif context == "preset_selection":
        insights.append({
            "type": "info",
            "text": "Presets are optimised using GWI 2024 research data (n=29,230)",
            "detail": "Each preset targets specific audience segments with data-backed allocations"
        })

    return {"context": context, "insights": insights}


@router.get("/export/methodology")
async def get_export_methodology():
    """Get methodology section for export/reports."""
    return {
        "title": "Research Foundation",
        "source": "GWI Social Discovery 2024",
        "total_respondents": GWI_RESEARCH["meta"]["total_respondents"],
        "cb_purchasers_identified": sum(
            seg.get("cb_purchasers", 0) for seg in GWI_RESEARCH["segments"].values()
        ),
        "confidence_level": "95%",
        "margin_of_error": "±1.4%",
        "segments": [
            {
                "name": name.title(),
                "sample_size": data["sample_size"],
                "description": data["description"]
            }
            for name, data in GWI_RESEARCH["segments"].items()
        ],
        "key_findings": [
            "CB purchasers over-index 1.30x on TikTok vs general family audience",
            "Nostalgia is the #1 driver for adult collectors (39%)",
            "Parents prioritise Fun (80%), Safety (80%), and Values (79%)",
            "Gifters show highest engagement on Facebook (1.14x index)"
        ]
    }

"""
GWI Social Discovery Survey 2024 Research Data
Source: Global Web Index - Care Bears Brand Study
Total Respondents: 29,230 across three segments
"""

GWI_RESEARCH = {
    "meta": {
        "source": "GWI Social Discovery Survey 2024",
        "total_respondents": 29230,
        "segments": ["parents", "gifters", "collectors"],
        "confidence_level": 0.95,
        "margin_of_error": 0.014
    },

    "segments": {
        "parents": {
            "sample_size": 22184,
            "description": "Parents of children, includes CB purchasers and considerers",
            "cb_purchasers": 2761,
            "cb_considerers": 18085,
            "platform_usage": {
                "youtube": {"total": 0.80, "cb_purchasers": 0.85, "index": 1.06},
                "facebook": {"total": 0.57, "cb_purchasers": 0.63, "index": 1.11},
                "instagram": {"total": 0.61, "cb_purchasers": 0.70, "index": 1.15},
                "tiktok": {"total": 0.46, "cb_purchasers": 0.60, "index": 1.30},
                "snapchat": {"total": 0.20, "cb_purchasers": 0.30, "index": 1.50},
                "twitch": {"total": 0.09, "cb_purchasers": 0.18, "index": 2.00},
                "discord": {"total": 0.08, "cb_purchasers": 0.15, "index": 1.88},
                "twitter": {"total": 0.24, "cb_purchasers": 0.34, "index": 1.42},
                "pinterest": {"total": 0.16, "cb_purchasers": 0.26, "index": 1.62}
            },
            "purchase_drivers": {
                "fun": 0.80,
                "safe_durable": 0.80,
                "good_values": 0.79,
                "educational": 0.74,
                "great_value": 0.71,
                "brand_reputation": 0.71,
                "mental_health_wellbeing": 0.70,
                "child_watches_show": 0.64,
                "diversity_inclusivity": 0.59,
                "sustainable_packaging": 0.56,
                "brand_everyone_knows": 0.48,
                "had_as_child": 0.43
            }
        },

        "gifters": {
            "sample_size": 5104,
            "description": "Adults purchasing Care Bears as gifts for children",
            "cb_purchasers": 1489,
            "cb_considerers": 1695,
            "platform_usage": {
                "youtube": {"total": 0.76, "cb_purchasers": 0.80, "index": 1.05},
                "facebook": {"total": 0.63, "cb_purchasers": 0.72, "index": 1.14},
                "instagram": {"total": 0.64, "cb_purchasers": 0.68, "index": 1.06},
                "tiktok": {"total": 0.44, "cb_purchasers": 0.54, "index": 1.23},
                "snapchat": {"total": 0.20, "cb_purchasers": 0.29, "index": 1.45},
                "twitch": {"total": 0.10, "cb_purchasers": 0.14, "index": 1.40},
                "discord": {"total": 0.08, "cb_purchasers": 0.11, "index": 1.38},
                "twitter": {"total": 0.27, "cb_purchasers": 0.31, "index": 1.15},
                "pinterest": {"total": 0.20, "cb_purchasers": 0.26, "index": 1.30}
            },
            "purchase_drivers_by_age": {
                "under_5": {
                    "sample_size": 930,
                    "drivers": {
                        "safe_age_appropriate": 0.38,
                        "fun": 0.37,
                        "safe_durable": 0.32,
                        "good_values": 0.32,
                        "brand_reputation": 0.26,
                        "educational": 0.25,
                        "had_as_child": 0.23
                    }
                },
                "5_to_11": {
                    "sample_size": 1674,
                    "drivers": {
                        "fun": 0.39,
                        "safe_age_appropriate": 0.36,
                        "safe_durable": 0.36,
                        "good_values": 0.35,
                        "brand_reputation": 0.30,
                        "brand_everyone_knows": 0.28,
                        "had_as_child": 0.26
                    }
                },
                "12_to_16": {
                    "sample_size": 580,
                    "drivers": {
                        "fun": 0.42,
                        "safe_durable": 0.36,
                        "safe_age_appropriate": 0.36,
                        "good_values": 0.33,
                        "brand_reputation": 0.31,
                        "brand_everyone_knows": 0.30,
                        "had_as_child": 0.27
                    }
                }
            }
        },

        "collectors": {
            "sample_size": 1942,
            "description": "Adult collectors purchasing for themselves",
            "cb_aware": 1484,
            "cb_not_aware": 458,
            "cb_purchasers": 680,
            "cb_considerers": 528,
            "platform_usage": {
                "youtube": {"total": 0.73, "cb_aware": 0.72, "not_aware": 0.74, "index": 1.00},
                "facebook": {"total": 0.62, "cb_aware": 0.68, "not_aware": 0.44, "index": 1.10},
                "instagram": {"total": 0.59, "cb_aware": 0.60, "not_aware": 0.53, "index": 1.02},
                "tiktok": {"total": 0.40, "cb_aware": 0.43, "not_aware": 0.29, "index": 1.08},
                "snapchat": {"total": 0.19, "cb_aware": 0.21, "not_aware": 0.10, "index": 1.11},
                "twitch": {"total": 0.10, "cb_aware": 0.12, "not_aware": 0.06, "index": 1.20},
                "discord": {"total": 0.08, "cb_aware": 0.09, "not_aware": 0.04, "index": 1.13},
                "twitter": {"total": 0.25, "cb_aware": 0.25, "not_aware": 0.24, "index": 1.00},
                "pinterest": {"total": 0.18, "cb_aware": 0.20, "not_aware": 0.11, "index": 1.11}
            },
            "motivations": {
                "nostalgia_had_as_child": 0.39,
                "fun_hobby": 0.36,
                "brand_reputation": 0.34,
                "appreciate_values": 0.33,
                "mental_health_wellbeing": 0.29,
                "diversity_inclusivity": 0.26,
                "use_with_family_friends": 0.23,
                "limited_edition": 0.20,
                "display_in_packaging": 0.20,
                "charitable_causes": 0.20,
                "watch_or_read_content": 0.19,
                "community_connection": 0.18,
                "sustainable_packaging": 0.18
            }
        }
    },

    "key_insights": {
        "platform_over_index": {
            "summary": "CB purchasers over-index significantly on emerging platforms",
            "highlights": [
                {"platform": "tiktok", "index": 1.30, "insight": "30% more likely than average family"},
                {"platform": "snapchat", "index": 1.50, "insight": "50% more likely than average family"},
                {"platform": "twitch", "index": 2.00, "insight": "2x more likely than average family"},
                {"platform": "discord", "index": 1.88, "insight": "Nearly 2x more likely than average family"},
                {"platform": "pinterest", "index": 1.62, "insight": "62% more likely than average family"}
            ]
        },
        "collector_nostalgia": {
            "summary": "Nostalgia is the #1 driver for adult collectors",
            "stat": 0.39,
            "detail": "39% cite 'I had it as a child' as purchase motivation"
        },
        "awareness_correlation": {
            "summary": "Social presence correlates strongly with brand awareness",
            "facebook_gap": 24,
            "tiktok_gap": 14,
            "insight": "CB-aware collectors are 24pp more likely to be on Facebook than unaware"
        },
        "parent_drivers": {
            "summary": "Fun, safety, and values are the top 3 purchase drivers for parents",
            "top_drivers": [
                {"driver": "fun", "pct": 0.80},
                {"driver": "safe_durable", "pct": 0.80},
                {"driver": "good_values", "pct": 0.79}
            ]
        }
    }
}

# Research-backed audience presets
AUDIENCE_PRESETS = {
    "parent_acquisition": {
        "id": "parent_acquisition",
        "name": "Parent Acquisition",
        "description": "Optimised for reaching parents who are likely CB purchasers",
        "segment_focus": "parents",
        "platform_allocation": {
            "Instagram": 30,
            "TikTok": 30,
            "YouTube": 20,
            "Facebook": 20
        },
        "posts_per_week": 28,
        "rationale": "Based on GWI data showing CB-purchasing parents over-index on Instagram (1.15x) and TikTok (1.30x). Balanced frequency for sustained reach.",
        "data_source": "GWI 2024 (n=22,184 parents)",
        "risk_level": "low",
        "expected_goal_range": [0.85, 0.95],
        "content_recommendations": [
            "Focus on fun, safety, and values messaging (80% driver alignment)",
            "Educational content performs well with this segment",
            "Show children engaging with products"
        ]
    },

    "gifter_reach": {
        "id": "gifter_reach",
        "name": "Gifter Reach",
        "description": "Optimised for gift-purchase consideration, brand trust focus",
        "segment_focus": "gifters",
        "platform_allocation": {
            "Instagram": 25,
            "TikTok": 20,
            "YouTube": 20,
            "Facebook": 35
        },
        "posts_per_week": 24,
        "rationale": "Gifters show highest engagement on Facebook (1.14x index) with strong Instagram presence. Quality over quantity - gifters respond to brand trust.",
        "data_source": "GWI 2024 (n=5,104 gifters)",
        "risk_level": "low",
        "expected_goal_range": [0.80, 0.90],
        "content_recommendations": [
            "Emphasise safety and age-appropriateness for under-5 gifts",
            "Brand reputation and trust messaging",
            "Gift guides and seasonal content"
        ]
    },

    "collector_growth": {
        "id": "collector_growth",
        "name": "Collector Growth",
        "description": "Optimised for adult collector segment, nostalgia-driven",
        "segment_focus": "collectors",
        "platform_allocation": {
            "Instagram": 30,
            "TikTok": 30,
            "YouTube": 15,
            "Facebook": 25
        },
        "posts_per_week": 21,
        "rationale": "Collectors value exclusivity, not volume. Over-index on visual discovery platforms. Nostalgia (39%) and values (33%) drive purchases.",
        "data_source": "GWI 2024 (n=1,942 collectors)",
        "risk_level": "medium",
        "expected_goal_range": [0.75, 0.88],
        "content_recommendations": [
            "Heritage and nostalgia content performs best",
            "Limited edition and exclusive releases",
            "Community and collector showcases",
            "Values-driven storytelling"
        ]
    },

    "emerging_platforms": {
        "id": "emerging_platforms",
        "name": "Emerging Platform Play",
        "description": "Aggressive allocation to high-index emerging platforms",
        "segment_focus": "emerging",
        "platform_allocation": {
            "Instagram": 25,
            "TikTok": 45,
            "YouTube": 15,
            "Facebook": 15
        },
        "posts_per_week": 32,
        "rationale": "CB purchasers are 1.3-2x more likely to be on emerging platforms vs general family audience. Higher frequency to build presence on growth platforms.",
        "data_source": "GWI 2024 - Platform index analysis",
        "risk_level": "high",
        "expected_goal_range": [0.70, 1.05],
        "content_recommendations": [
            "Native format content for each platform",
            "Trend participation and challenges",
            "Short-form video focus",
            "Community building and engagement"
        ]
    },

    "balanced": {
        "id": "balanced",
        "name": "Balanced (Manual)",
        "description": "Default balanced allocation - customise as needed",
        "segment_focus": "balanced",
        "platform_allocation": {
            "Instagram": 35,
            "TikTok": 35,
            "YouTube": 15,
            "Facebook": 15
        },
        "posts_per_week": 40,
        "rationale": "Standard balanced allocation across platforms. Adjust sliders to customise for your specific goals.",
        "data_source": "Industry benchmarks",
        "risk_level": "medium",
        "expected_goal_range": [0.60, 0.85],
        "content_recommendations": [
            "Mix of content types across platforms",
            "Test and learn approach",
            "Adjust based on performance data"
        ]
    }
}


def calculate_blended_allocation(audience_mix: dict) -> dict:
    """
    Blend platform allocations based on audience mix and segment indices.

    audience_mix: {"parents": 0.6, "gifters": 0.25, "collectors": 0.15}
    Returns: {"Instagram": 30, "TikTok": 32, ...}
    """
    platforms = ["instagram", "tiktok", "youtube", "facebook"]
    platform_map = {
        "instagram": "Instagram",
        "tiktok": "TikTok",
        "youtube": "YouTube",
        "facebook": "Facebook"
    }
    blended = {}

    for platform in platforms:
        weighted_index = 0
        for segment, weight in audience_mix.items():
            if segment in GWI_RESEARCH["segments"]:
                segment_data = GWI_RESEARCH["segments"][segment]["platform_usage"]
                if platform in segment_data:
                    # Use the index score as the weight factor
                    index = segment_data[platform].get("index", 1.0)
                    weighted_index += index * weight
        blended[platform_map[platform]] = weighted_index

    # Normalise to sum to 100
    total = sum(blended.values())
    if total > 0:
        return {k: round((v / total) * 100) for k, v in blended.items()}
    return {"Instagram": 25, "TikTok": 25, "YouTube": 25, "Facebook": 25}


def get_segment_insights(segment: str) -> dict:
    """Get key insights for a specific segment."""
    if segment not in GWI_RESEARCH["segments"]:
        return {}

    seg_data = GWI_RESEARCH["segments"][segment]

    # Get top platforms by index
    platforms = seg_data["platform_usage"]
    sorted_platforms = sorted(
        [(k, v.get("index", 1.0)) for k, v in platforms.items()],
        key=lambda x: x[1],
        reverse=True
    )[:3]

    insights = {
        "segment": segment,
        "sample_size": seg_data["sample_size"],
        "description": seg_data["description"],
        "top_platforms": [
            {"platform": p[0], "index": p[1], "insight": f"{int((p[1]-1)*100)}% more likely than average"}
            for p in sorted_platforms if p[1] > 1.0
        ]
    }

    # Add segment-specific insights
    if segment == "parents":
        drivers = seg_data["purchase_drivers"]
        top_drivers = sorted(drivers.items(), key=lambda x: x[1], reverse=True)[:3]
        insights["top_drivers"] = [{"driver": d[0].replace("_", " ").title(), "pct": int(d[1]*100)} for d in top_drivers]
    elif segment == "collectors":
        motivations = seg_data["motivations"]
        top_motivations = sorted(motivations.items(), key=lambda x: x[1], reverse=True)[:3]
        insights["top_motivations"] = [{"motivation": m[0].replace("_", " ").title(), "pct": int(m[1]*100)} for m in top_motivations]

    return insights


def get_platform_insight(platform: str) -> dict:
    """Get research insight for a specific platform across all segments."""
    platform_lower = platform.lower()
    insights = {
        "platform": platform,
        "segments": {}
    }

    for segment_name, segment_data in GWI_RESEARCH["segments"].items():
        if platform_lower in segment_data["platform_usage"]:
            plat_data = segment_data["platform_usage"][platform_lower]
            insights["segments"][segment_name] = {
                "total_usage": plat_data.get("total", 0),
                "purchaser_usage": plat_data.get("cb_purchasers", plat_data.get("cb_aware", 0)),
                "index": plat_data.get("index", 1.0)
            }

    # Calculate average index across segments
    indices = [s["index"] for s in insights["segments"].values()]
    insights["avg_index"] = round(sum(indices) / len(indices), 2) if indices else 1.0

    # Generate insight text
    if insights["avg_index"] > 1.1:
        insights["insight"] = f"CB purchasers are {int((insights['avg_index']-1)*100)}% more likely to use {platform} than average families"
    elif insights["avg_index"] < 0.9:
        insights["insight"] = f"{platform} shows below-average index for CB purchasers"
    else:
        insights["insight"] = f"{platform} shows baseline reach with CB purchasers"

    return insights

"""
AI Strategy Analysis Service
Uses OpenAI to analyze growth strategies and provide recommendations
Enhanced with GWI 2024 research data for Care Bears audience insights
"""
import os
from typing import Dict, List, Any, Optional
from models.schemas import InsightRequest, ParamTuneRequest

# GWI Research Context for AI prompts
GWI_RESEARCH_CONTEXT = """
GWI 2024 RESEARCH INSIGHTS (n=29,230):

AUDIENCE SEGMENTS:
1. Parents (n=22,184): Primary purchasers
   - Platform indices: TikTok 1.30x, Instagram 1.15x, YouTube 1.12x
   - Purchase drivers: Fun (80%), Safety (80%), Values (79%)

2. Gifters (n=4,876): Gift purchase considerers
   - Platform indices: Facebook 1.14x, Instagram 1.08x
   - Key motivator: Brand trust and gifting occasions

3. Collectors (n=2,170): Adult enthusiast buyers
   - Platform indices: Balanced across platforms
   - Key motivator: Nostalgia (39%), Values (33%)

PLATFORM PERFORMANCE:
- TikTok: Highest CB purchaser over-index (1.30x) - best for discovery
- Instagram: Strong index (1.15x) - good for visual brand storytelling
- Facebook: Gifter-focused (1.14x index) - brand trust channel
- YouTube: Long-form content (1.12x) - education and engagement

RECOMMENDATIONS:
- Parent-focused campaigns: Prioritize TikTok + Instagram (60% combined)
- Gifter campaigns: Include Facebook (20-25% allocation)
- Collector campaigns: Balance with nostalgia-driven content
"""

# Initialize OpenAI client only if API key is available
client: Optional[object] = None
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    else:
        print("Warning: OPENAI_API_KEY not set. AI features will use fallback recommendations.")
except Exception as e:
    print(f"Warning: Could not initialize OpenAI client: {e}. Using fallback recommendations.")

def analyze_strategy(
    current_followers: Dict[str, int],
    posts_per_week: int,
    platform_allocation: Dict[str, int],
    months: int,
    preset: str,
    historical_data: Dict[str, Any],
    budget_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze the current strategy and provide AI recommendations

    Returns multiple scenario suggestions with reasoning
    """

    # Calculate current metrics
    total_followers = sum(current_followers.values())
    goal = total_followers * 2  # Double the followers

    # Budget info defaults
    if budget_info is None:
        budget_info = {
            "total_annual_budget": 100000,
            "paid_media_weekly": 641,
            "growth_strategy_weekly": 1282,
            "cpf_range": {"min": 0.10, "mid": 0.15, "max": 0.20}
        }

    annual_budget = budget_info.get("total_annual_budget", 100000)
    paid_weekly = budget_info.get("paid_media_weekly", 962)
    growth_weekly = budget_info.get("growth_strategy_weekly", 962)
    cpf = budget_info.get("cpf_range", {"min": 3, "mid": 4, "max": 5})

    # Build context for AI with GWI research
    context = f"""
You are an expert social media growth strategist analyzing a campaign for Care Bears.
Use the GWI 2024 research data below to inform your recommendations.

{GWI_RESEARCH_CONTEXT}

PRIMARY OBJECTIVE: Double total followers from {total_followers:,} to {goal:,} within 12 months.

CURRENT CONFIGURATION:
- Total Followers: {total_followers:,}
- 12-Month Goal: {goal:,} (2x current)
- Strategy Preset: {preset}
- Posts per Week: {posts_per_week}
- Forecast Period: {months} months

BUDGET ALLOCATION (Annual: ${annual_budget:,}):
- Paid Media Budget: ${paid_weekly:,}/week (${paid_weekly * 52:,}/year)
- Growth Strategy Budget: ${growth_weekly:,}/week (${growth_weekly * 52:,}/year)
- Cost Per Follower (CPF): ${cpf['min']}-${cpf['max']} (target: ${cpf['mid']})

PLATFORM BREAKDOWN:
"""
    for platform, count in current_followers.items():
        percentage = (count / total_followers) * 100 if total_followers > 0 else 0
        context += f"- {platform}: {count:,} followers ({percentage:.1f}%)\n"

    context += f"""
CURRENT POSTING ALLOCATION:
"""
    for platform, pct in platform_allocation.items():
        posts = int((posts_per_week * pct) / 100)
        context += f"- {platform}: {pct}% ({posts} posts/week)\n"

    # Calculate what's needed to double
    followers_needed = goal - total_followers
    weeks_in_period = months * 4
    followers_per_week_needed = followers_needed / weeks_in_period if weeks_in_period > 0 else 0

    context += f"""
GROWTH MATH:
- Followers needed to reach goal: {followers_needed:,}
- Weeks in forecast period: {weeks_in_period}
- Required weekly growth: ~{int(followers_per_week_needed):,} followers/week
- At ${cpf['mid']} CPF, budget supports ~{int((paid_weekly + growth_weekly) / cpf['mid']):,} paid followers/week
- Organic growth must make up the remainder

"""

    prompt = context + """
TASK:
Analyze this configuration and provide 3 strategic scenarios that can realistically achieve the goal of DOUBLING followers within 12 months given the $100K annual budget:

1. OPTIMIZED: Best balance of organic and paid growth
2. AGGRESSIVE: Maximum growth potential, higher spend efficiency needed
3. CONSERVATIVE: Lower risk, sustainable path to goal

For each scenario, consider:
- How to allocate the $100K budget most effectively
- Which platforms offer best CPF (cost per follower) efficiency
- Optimal posting frequency to maximize organic reach without oversaturation
- Content mix recommendations (Short Video, Carousels, Stories, etc.)

Return ONLY valid JSON in this exact format:
{
    "analysis": "2-3 sentence assessment of whether current configuration can achieve 2x growth goal. Be specific about gaps or strengths.",
    "scenarios": [
        {
            "name": "Optimized",
            "posts_per_week": 28,
            "platform_allocation": {
                "Instagram": 35,
                "TikTok": 35,
                "YouTube": 15,
                "Facebook": 15
            },
            "reasoning": "Specific explanation of budget allocation and why this achieves the 2x goal",
            "risk_level": "MEDIUM",
            "expected_outcome": "105% of goal - exceeds target by 5%"
        },
        ...two more scenarios (Aggressive, Conservative)...
    ],
    "key_insights": [
        "Specific, actionable insight about budget allocation",
        "Platform-specific recommendation with numbers",
        "Content strategy insight tied to growth goal"
    ]
}
"""

    # Use fallback if OpenAI client is not available
    if client is None:
        print("Using fallback recommendations (OpenAI client not initialized)")
        return generate_fallback_recommendations(
            current_followers,
            posts_per_week,
            platform_allocation,
            preset
        )

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert social media growth strategist. Provide data-driven, actionable recommendations. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )

        import json
        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        # Fallback if OpenAI fails
        import traceback
        print(f"AI Service Error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return generate_fallback_recommendations(
            current_followers,
            posts_per_week,
            platform_allocation,
            preset
        )


def generate_fallback_recommendations(
    current_followers: Dict[str, int],
    posts_per_week: int,
    platform_allocation: Dict[str, int],
    preset: str
) -> Dict[str, Any]:
    """
    Generate rule-based recommendations informed by GWI 2024 research data
    """

    # Analyze current strategy
    total = sum(current_followers.values())
    tiktok_followers = current_followers.get("TikTok", 0)
    instagram_followers = current_followers.get("Instagram", 0)

    # GWI-informed heuristics
    tiktok_alloc = platform_allocation.get("TikTok", 0)
    instagram_alloc = platform_allocation.get("Instagram", 0)
    facebook_alloc = platform_allocation.get("Facebook", 0)

    # Research shows TikTok 1.30x and Instagram 1.15x over-index
    optimal_tiktok_range = (28, 35)  # Based on GWI indices
    optimal_instagram_range = (25, 35)

    posting_high = posts_per_week > 30
    tiktok_underallocated = tiktok_alloc < optimal_tiktok_range[0]

    scenarios = []

    # Optimized scenario - GWI research-backed
    scenarios.append({
        "name": "Optimized",
        "posts_per_week": 28,
        "platform_allocation": {
            "Instagram": 30,
            "TikTok": 30,
            "YouTube": 20,
            "Facebook": 20
        },
        "reasoning": "GWI 2024 data shows CB purchasers over-index 1.30x on TikTok and 1.15x on Instagram. This allocation balances reach efficiency with audience engagement across parent and gifter segments.",
        "risk_level": "MEDIUM",
        "expected_outcome": "92-98% of goal"
    })

    # Aggressive scenario - Parent Acquisition focus
    scenarios.append({
        "name": "Aggressive",
        "posts_per_week": 35,
        "platform_allocation": {
            "Instagram": 30,
            "TikTok": 35,
            "YouTube": 20,
            "Facebook": 15
        },
        "reasoning": "Parent Acquisition strategy: Heavy TikTok allocation (35%) leverages 1.30x purchaser index. High posting frequency maximises discovery among CB-purchasing parents (n=22,184 in GWI study).",
        "risk_level": "HIGH",
        "expected_outcome": "105-115% of goal"
    })

    # Conservative scenario - Balanced with Gifter focus
    scenarios.append({
        "name": "Conservative",
        "posts_per_week": 24,
        "platform_allocation": {
            "Instagram": 30,
            "TikTok": 25,
            "YouTube": 20,
            "Facebook": 25
        },
        "reasoning": "Gifter-inclusive strategy: Higher Facebook allocation (25%) captures gifter segment (1.14x index). Lower posting frequency ensures quality content across nostalgia-driven collectors and brand-trust-focused gifters.",
        "risk_level": "LOW",
        "expected_outcome": "85-92% of goal"
    })

    # Build research-informed key insights
    insights = []

    if tiktok_underallocated:
        insights.append(f"GWI 2024: TikTok has 1.30x CB purchaser over-index - consider increasing from {tiktok_alloc}% to {optimal_tiktok_range[0]}%+")
    else:
        insights.append("TikTok allocation aligns with GWI research (1.30x purchaser index)")

    if facebook_alloc < 15:
        insights.append("Gifter segment (1.14x on Facebook) may be underserved - consider 15-25% Facebook allocation")
    else:
        insights.append(f"Facebook allocation ({facebook_alloc}%) captures gifter segment effectively")

    if posting_high:
        insights.append("GWI data suggests engagement quality typically decreases above 30 posts/week")
    else:
        insights.append("Posting frequency is optimal for maintaining engagement quality")

    return {
        "analysis": f"Current strategy ({preset}, {posts_per_week} posts/week) evaluated against GWI 2024 research (n=29,230). {'TikTok allocation could be increased to better reach CB-purchasing parents.' if tiktok_underallocated else 'Platform allocation aligns well with audience segment indices.'}",
        "scenarios": scenarios,
        "key_insights": insights
    }


def generate_gap_insight(req: InsightRequest) -> str:
    # Fallback, concise rule-based insight
    pct = req.progress_to_goal
    main = "You're projected to reach {:.0f}% of your growth target.".format(pct)
    # Heuristic lever: if posts/week < 28 suggest +4; else check allocation tilt
    lever = ""
    if req.posts_per_week_total < 28:
        lever = f"Posting volume is below optimal for your horizon. Consider increasing weekly posts from {int(req.posts_per_week_total)} to {int(req.posts_per_week_total)+4}."
    else:
        # Look for highest allocation gap: prefer TikTok/Instagram up to ~35%
        target = {"TikTok": 35, "Instagram": 35}
        diffs = [(p, target[p]-req.platform_allocation.get(p,0)) for p in target]
        diffs.sort(key=lambda x: x[1], reverse=True)
        p, d = diffs[0]
        if d > 0:
            lever = f"Allocation to {p} is below benchmark. Increasing {p} share by ~{int(d)} pts could improve reach efficiency."
        else:
            lever = "Content efficiency is the next lever—tilt mix toward high-yield formats (TT Short Video, IG Carousels)."
    action = "Focus on a single change first, then reassess after a week of data."
    return f"{main} {lever} {action}"


def tune_parameters(req: ParamTuneRequest) -> Dict[str, Any]:
    # Minimal conservative fallback suggestions
    suggestions = []
    hist = req.historical_summary or {}
    # If TikTok mentions/engagement appear strong, suggest small TT short-video multiplier increase
    tt_signal = hist.get('tt_strength', 0.0)
    if tt_signal > 0.6:
        suggestions.append({
            "key": "CONTENT_MULT.TikTok.Short Video",
            "current": req.current_params.get('CONTENT_MULT', {}).get('TikTok', {}).get('Short Video', 1.3),
            "suggested": 1.4,
            "reason": "TikTok short video performance appears above baseline; modest +0.1x multiplier.",
            "confidence": "MEDIUM"
        })
    # If oversaturation is frequent, suggest lowering soft cap
    if hist.get('oversat_weeks', 0) > 4:
        suggestions.append({
            "key": "RECOMMENDED_FREQ.TikTok.soft",
            "current": req.current_params.get('RECOMMENDED_FREQ', {}).get('TikTok', {}).get('soft', 15),
            "suggested": 14,
            "reason": "Frequent oversaturation detected; slightly reduce soft cap to protect engagement quality.",
            "confidence": "LOW"
        })
    return {"suggestions": suggestions}


def critique_strategy(
    current_followers: Dict[str, Any],
    posts_per_week: float,
    platform_allocation: Dict[str, Any],
    content_mix: Dict[str, Dict[str, Any]],
    months: int,
    preset: str,
    audience_mix: Dict[str, Any],
    projected_total: float,
    goal: float,
    historical_data: Dict[str, Any],
    budget_info: Optional[Dict[str, Any]] = None,
    previous_suggestions: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Provide a balanced critique and optimization suggestions for the user's current strategy.
    Assesses all variables against GWI research, historical data, and client targets.
    """

    total_followers = sum(current_followers.values())
    progress_to_goal = (projected_total / goal * 100) if goal > 0 else 0

    # Budget info defaults
    if budget_info is None:
        budget_info = {
            "total_annual_budget": 100000,
            "paid_media_weekly": 641,
            "cpf_range": {"min": 0.10, "mid": 0.15, "max": 0.20}
        }

    # Build previous suggestions context if available
    previous_context = ""
    if previous_suggestions and len(previous_suggestions) > 0:
        previous_context = """
PREVIOUS ANALYSIS CONTEXT:
The user has already received these optimization suggestions and may have acted on some of them.
Do NOT repeat the same suggestions. Instead, provide NEW insights or acknowledge improvements made.

Previous suggestions given:
"""
        for i, opt in enumerate(previous_suggestions, 1):
            previous_context += f"{i}. [{opt.get('priority', 'N/A')}] {opt.get('action', 'Unknown action')} (Impact: {opt.get('impact', 'Unknown')})\n"
        previous_context += "\nIMPORTANT: Provide fresh, different recommendations. If a previous suggestion was followed, acknowledge the improvement. If not, you may mention it briefly but focus on NEW optimizations.\n"

    # Build comprehensive context for AI critique
    context = f"""
You are an expert social media growth strategist providing a balanced critique of a Care Bears growth campaign.
Use the GWI 2024 research data to assess the strategy against audience segment behaviors.

{GWI_RESEARCH_CONTEXT}
{previous_context}
CLIENT OBJECTIVE: Grow from {total_followers:,} to {goal:,} followers (2x growth) within 12 months.

CURRENT STRATEGY CONFIGURATION:
- Strategy Preset: {preset}
- Forecast Period: {months} months
- Posts per Week: {posts_per_week}
- Projected Total: {projected_total:,} ({progress_to_goal:.1f}% of goal)

PLATFORM FOLLOWER DISTRIBUTION:
"""
    for platform, count in current_followers.items():
        pct = (count / total_followers * 100) if total_followers > 0 else 0
        context += f"- {platform}: {count:,} ({pct:.1f}%)\n"

    context += f"""
CONTENT POSTING ALLOCATION:
"""
    for platform, pct in platform_allocation.items():
        posts = int((posts_per_week * pct) / 100)
        context += f"- {platform}: {pct}% ({posts} posts/week)\n"

    context += f"""
CONTENT MIX BY PLATFORM:
"""
    for platform, mix in content_mix.items():
        context += f"- {platform}: {mix}\n"

    context += f"""
TARGET AUDIENCE MIX:
- Parents: {audience_mix.get('parents', 0)}%
- Gifters: {audience_mix.get('gifters', 0)}%
- Collectors: {audience_mix.get('collectors', 0)}%

BUDGET INFORMATION:
- Paid Media Weekly: ${budget_info.get('paid_media_weekly', 0):,}
- CPF Range: ${budget_info.get('cpf_range', {}).get('min', 0.10)}-${budget_info.get('cpf_range', {}).get('max', 0.20)}
"""

    prompt = context + """
TASK:
Provide a balanced, expert critique of this strategy. Be specific and actionable.

IMPORTANT RULES:
- NEVER suggest a value that is already the current configuration (check the exact numbers above carefully)
- If a category is already optimal, set suggestion to null and acknowledge it's well-configured
- Only suggest CHANGES that would actually improve the strategy
- If suggesting a platform allocation change, ensure the suggestion is DIFFERENT from current values

Assess these areas:
1. POSTING FREQUENCY: Is the posts/week optimal? Consider engagement quality vs. reach.
2. PLATFORM ALLOCATION: Does allocation match the target audience mix and GWI platform indices?
3. CONTENT MIX: Are content formats optimized for each platform's strengths?
4. AUDIENCE ALIGNMENT: Does the strategy effectively reach parents (1.30x TikTok), gifters (1.14x Facebook), and collectors?
5. GOAL FEASIBILITY: Can this configuration realistically achieve the 2x growth goal?

Return ONLY valid JSON in this exact format:
{
    "overall_assessment": {
        "rating": "STRONG" | "GOOD" | "NEEDS_WORK" | "AT_RISK",
        "summary": "2-3 sentence executive summary of the strategy's strengths and weaknesses"
    },
    "category_assessments": [
        {
            "category": "Posting Frequency",
            "rating": "OPTIMAL" | "ACCEPTABLE" | "NEEDS_ADJUSTMENT",
            "current_value": "40 posts/week",
            "assessment": "Specific critique of current value",
            "suggestion": "Specific optimization suggestion if needed, or null if optimal",
            "suggested_value": "28 posts/week" or null
        },
        {
            "category": "Platform Allocation",
            "rating": "...",
            "current_value": "TikTok 35%, Instagram 35%...",
            "assessment": "...",
            "suggestion": "...",
            "suggested_value": "TikTok 30%, Instagram 30%..." or null
        },
        {
            "category": "Content Mix",
            "rating": "...",
            "current_value": "Short Video dominant...",
            "assessment": "...",
            "suggestion": "...",
            "suggested_value": null
        },
        {
            "category": "Audience Alignment",
            "rating": "...",
            "current_value": "Parents 80%, Gifters 10%...",
            "assessment": "...",
            "suggestion": "...",
            "suggested_value": null
        },
        {
            "category": "Goal Feasibility",
            "rating": "ON_TRACK" | "ACHIEVABLE" | "STRETCH" | "UNLIKELY",
            "current_value": "85% of goal projected",
            "assessment": "...",
            "suggestion": "...",
            "suggested_value": null
        }
    ],
    "top_optimizations": [
        {
            "priority": 1,
            "action": "Specific, actionable optimization",
            "impact": "Expected impact on goal achievement",
            "effort": "LOW" | "MEDIUM" | "HIGH"
        },
        {
            "priority": 2,
            "action": "...",
            "impact": "...",
            "effort": "..."
        },
        {
            "priority": 3,
            "action": "...",
            "impact": "...",
            "effort": "..."
        }
    ],
    "gwi_alignment_notes": [
        "Specific note about how strategy aligns or misaligns with GWI research",
        "Another GWI-informed observation"
    ]
}
"""

    # Use fallback if OpenAI client is not available
    if client is None:
        print("Using fallback critique (OpenAI client not initialized)")
        return generate_fallback_critique(
            current_followers,
            posts_per_week,
            platform_allocation,
            content_mix,
            audience_mix,
            progress_to_goal,
            preset
        )

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert social media growth strategist. Provide balanced, specific critiques with actionable suggestions. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2500,
            response_format={"type": "json_object"}
        )

        import json
        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        import traceback
        print(f"AI Critique Error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return generate_fallback_critique(
            current_followers,
            posts_per_week,
            platform_allocation,
            content_mix,
            audience_mix,
            progress_to_goal,
            preset
        )


def generate_fallback_critique(
    current_followers: Dict[str, Any],
    posts_per_week: float,
    platform_allocation: Dict[str, Any],
    content_mix: Dict[str, Dict[str, Any]],
    audience_mix: Dict[str, Any],
    progress_to_goal: float,
    preset: str
) -> Dict[str, Any]:
    """
    Generate rule-based critique when OpenAI is unavailable
    """

    # Analyze current values against GWI benchmarks
    tiktok_alloc = platform_allocation.get("TikTok", 0)
    instagram_alloc = platform_allocation.get("Instagram", 0)
    facebook_alloc = platform_allocation.get("Facebook", 0)
    youtube_alloc = platform_allocation.get("YouTube", 0)

    parents_pct = audience_mix.get("parents", 80)
    gifters_pct = audience_mix.get("gifters", 10)
    collectors_pct = audience_mix.get("collectors", 10)

    # Determine ratings
    posting_rating = "OPTIMAL" if 24 <= posts_per_week <= 32 else ("ACCEPTABLE" if 20 <= posts_per_week <= 40 else "NEEDS_ADJUSTMENT")

    # Platform allocation assessment based on audience mix
    expected_tiktok = 25 + (parents_pct * 0.15)  # Parents over-index on TikTok
    expected_facebook = 15 + (gifters_pct * 0.2)  # Gifters over-index on Facebook
    platform_rating = "OPTIMAL" if abs(tiktok_alloc - expected_tiktok) < 10 and abs(facebook_alloc - expected_facebook) < 10 else "NEEDS_ADJUSTMENT"

    # Goal feasibility
    if progress_to_goal >= 95:
        goal_rating = "ON_TRACK"
    elif progress_to_goal >= 85:
        goal_rating = "ACHIEVABLE"
    elif progress_to_goal >= 70:
        goal_rating = "STRETCH"
    else:
        goal_rating = "UNLIKELY"

    # Overall assessment
    if posting_rating == "OPTIMAL" and platform_rating == "OPTIMAL" and goal_rating in ["ON_TRACK", "ACHIEVABLE"]:
        overall_rating = "STRONG"
    elif goal_rating == "UNLIKELY":
        overall_rating = "AT_RISK"
    elif posting_rating == "NEEDS_ADJUSTMENT" or platform_rating == "NEEDS_ADJUSTMENT":
        overall_rating = "NEEDS_WORK"
    else:
        overall_rating = "GOOD"

    # Build optimizations
    optimizations = []

    if posts_per_week > 35:
        optimizations.append({
            "priority": len(optimizations) + 1,
            "action": f"Reduce posting frequency from {posts_per_week} to 28-32 posts/week to improve engagement quality",
            "impact": "Higher engagement rate per post, better algorithmic performance",
            "effort": "LOW"
        })
    elif posts_per_week < 20:
        optimizations.append({
            "priority": len(optimizations) + 1,
            "action": f"Increase posting frequency from {posts_per_week} to 24-28 posts/week to improve reach",
            "impact": "Expanded reach and discovery potential",
            "effort": "MEDIUM"
        })

    if parents_pct > 60 and tiktok_alloc < 30:
        optimizations.append({
            "priority": len(optimizations) + 1,
            "action": f"Increase TikTok allocation from {tiktok_alloc}% to 30%+ to better reach parent segment (1.30x over-index)",
            "impact": "Better alignment with primary audience platform preferences",
            "effort": "LOW"
        })

    if gifters_pct > 15 and facebook_alloc < 20:
        optimizations.append({
            "priority": len(optimizations) + 1,
            "action": f"Increase Facebook allocation from {facebook_alloc}% to 20%+ to capture gifter segment (1.14x index)",
            "impact": "Improved gifter audience reach during key shopping periods",
            "effort": "LOW"
        })

    # Extract actual content mix values to avoid suggesting existing configurations
    tiktok_short_video_pct = content_mix.get("TikTok", {}).get("Short Video", 0)
    instagram_carousel_pct = content_mix.get("Instagram", {}).get("Carousel", 0)
    instagram_reels_pct = content_mix.get("Instagram", {}).get("Reels", 0)
    youtube_shorts_pct = content_mix.get("YouTube", {}).get("Shorts", 0)
    facebook_video_pct = content_mix.get("Facebook", {}).get("Video", 0)

    # Only add content mix suggestions if they're actually needed
    if len(optimizations) < 3 and tiktok_short_video_pct < 85:
        optimizations.append({
            "priority": len(optimizations) + 1,
            "action": f"Increase Short Video content on TikTok from {tiktok_short_video_pct:.0f}% to 90%+ of TikTok posts",
            "impact": "Maximizes platform-native content performance",
            "effort": "LOW"
        })

    if len(optimizations) < 3 and instagram_carousel_pct < 18:
        optimizations.append({
            "priority": len(optimizations) + 1,
            "action": f"Add Carousel content on Instagram (currently {instagram_carousel_pct:.0f}%, target 20-25% of IG posts) for higher engagement",
            "impact": "Carousels see 1.25x engagement multiplier on Instagram",
            "effort": "MEDIUM"
        })

    if len(optimizations) < 3 and youtube_shorts_pct < 40:
        optimizations.append({
            "priority": len(optimizations) + 1,
            "action": f"Increase YouTube Shorts content from {youtube_shorts_pct:.0f}% to 40%+ for better discovery",
            "impact": "Shorts drive higher subscriber conversion on YouTube",
            "effort": "MEDIUM"
        })

    # Generic fallbacks only if we still need more (strategy is already well-optimized)
    if len(optimizations) < 3:
        optimizations.append({
            "priority": len(optimizations) + 1,
            "action": "Maintain consistent posting schedule across all platforms",
            "impact": "Algorithm favorability and audience expectation management",
            "effort": "LOW"
        })

    if len(optimizations) < 3:
        optimizations.append({
            "priority": len(optimizations) + 1,
            "action": "Current configuration is well-optimized - focus on content quality and engagement",
            "impact": "Sustained growth through audience retention",
            "effort": "MEDIUM"
        })

    return {
        "overall_assessment": {
            "rating": overall_rating,
            "summary": f"Strategy is {'well-positioned' if overall_rating in ['STRONG', 'GOOD'] else 'showing gaps that need attention'}. Current projection is {progress_to_goal:.0f}% of goal. {'Platform allocation aligns with GWI research.' if platform_rating == 'OPTIMAL' else 'Platform allocation could better match target audience indices.'}"
        },
        "category_assessments": [
            {
                "category": "Posting Frequency",
                "rating": posting_rating,
                "current_value": f"{posts_per_week} posts/week",
                "assessment": f"{'Optimal range for engagement quality' if posting_rating == 'OPTIMAL' else 'Above 32 posts/week may reduce per-post engagement' if posts_per_week > 32 else 'Below 24 posts/week limits reach potential'}",
                "suggestion": None if posting_rating == "OPTIMAL" else f"Adjust to 28 posts/week for optimal balance",
                "suggested_value": None if posting_rating == "OPTIMAL" else "28 posts/week"
            },
            {
                "category": "Platform Allocation",
                "rating": platform_rating,
                "current_value": f"TikTok {tiktok_alloc}%, Instagram {instagram_alloc}%, Facebook {facebook_alloc}%, YouTube {youtube_alloc}%",
                "assessment": f"{'Allocation matches target audience platform indices' if platform_rating == 'OPTIMAL' else 'Allocation could better reflect GWI audience indices'}",
                "suggestion": None if platform_rating == "OPTIMAL" else f"Consider TikTok {int(expected_tiktok)}%, Facebook {int(expected_facebook)}% based on audience mix",
                "suggested_value": None if platform_rating == "OPTIMAL" else f"TikTok {int(expected_tiktok)}%, Facebook {int(expected_facebook)}%"
            },
            {
                "category": "Content Mix",
                "rating": "OPTIMAL" if tiktok_short_video_pct >= 85 and instagram_carousel_pct >= 18 else "ACCEPTABLE" if tiktok_short_video_pct >= 70 else "NEEDS_ADJUSTMENT",
                "current_value": f"TikTok Short Video: {tiktok_short_video_pct:.0f}%, Instagram Carousel: {instagram_carousel_pct:.0f}%, Instagram Reels: {instagram_reels_pct:.0f}%",
                "assessment": f"{'Content mix is well-optimized with strong Short Video on TikTok and good Carousel usage on Instagram.' if tiktok_short_video_pct >= 85 and instagram_carousel_pct >= 18 else 'Content formats are reasonable but could be better optimized for platform strengths.'}",
                "suggestion": None if tiktok_short_video_pct >= 85 and instagram_carousel_pct >= 18 else f"{'Increase TikTok Short Video to 90%+' if tiktok_short_video_pct < 85 else ''}{' and ' if tiktok_short_video_pct < 85 and instagram_carousel_pct < 18 else ''}{'Add more Instagram Carousels (target 20%+)' if instagram_carousel_pct < 18 else ''}".strip() or None,
                "suggested_value": None if tiktok_short_video_pct >= 85 and instagram_carousel_pct >= 18 else f"TikTok Short Video: 90%, Instagram Carousel: 20%" if tiktok_short_video_pct < 85 or instagram_carousel_pct < 18 else None
            },
            {
                "category": "Audience Alignment",
                "rating": "OPTIMAL" if abs(parents_pct + gifters_pct + collectors_pct - 100) < 5 else "ACCEPTABLE",
                "current_value": f"Parents {parents_pct}%, Gifters {gifters_pct}%, Collectors {collectors_pct}%",
                "assessment": f"{'Primary focus on parents aligns with GWI data showing 1.30x TikTok index' if parents_pct > 60 else 'Balanced audience targeting across segments'}",
                "suggestion": None,
                "suggested_value": None
            },
            {
                "category": "Goal Feasibility",
                "rating": goal_rating,
                "current_value": f"{progress_to_goal:.0f}% of goal projected",
                "assessment": f"{'On track to achieve 2x growth target' if goal_rating == 'ON_TRACK' else 'Achievable with consistent execution' if goal_rating == 'ACHIEVABLE' else 'Requires optimization to reach target' if goal_rating == 'STRETCH' else 'Significant changes needed to reach goal'}",
                "suggestion": None if goal_rating in ["ON_TRACK", "ACHIEVABLE"] else "Review optimizations below to close gap",
                "suggested_value": None
            }
        ],
        "top_optimizations": optimizations[:3],
        "gwi_alignment_notes": [
            f"Parents ({parents_pct}% of target) over-index 1.30x on TikTok - {'current TikTok allocation supports this' if tiktok_alloc >= 28 else 'consider increasing TikTok allocation'}",
            f"Gifters ({gifters_pct}% of target) over-index 1.14x on Facebook - {'Facebook allocation captures this segment' if facebook_alloc >= 15 else 'Facebook may be underweighted for gifter reach'}"
        ]
    }


def calculate_campaign_phases(
    months: int,
    posts_per_week: int,
    strategy: str
) -> List[Dict[str, Any]]:
    """
    Generate campaign phase recommendations
    """

    if months >= 12:
        return [
            {
                "phase": "Launch",
                "months": "1-3",
                "posts_per_week": min(posts_per_week + 5, 40),
                "focus": "Rapid audience building, content testing",
                "key_actions": ["Test content formats", "Identify top performers", "Build momentum"]
            },
            {
                "phase": "Sustain",
                "months": "4-9",
                "posts_per_week": posts_per_week,
                "focus": "Consistent growth, engagement optimization",
                "key_actions": ["Double down on winners", "Optimize posting times", "Build community"]
            },
            {
                "phase": "Accelerate",
                "months": "10-12",
                "posts_per_week": min(posts_per_week + 3, 35),
                "focus": "Final push to goal",
                "key_actions": ["Increase frequency", "Launch campaigns", "Maximize reach"]
            }
        ]
    else:
        # Shorter campaigns - adjust phases
        return [
            {
                "phase": "Sprint",
                "months": f"1-{months}",
                "posts_per_week": min(posts_per_week + 7, 40),
                "focus": "Rapid growth execution",
                "key_actions": ["High-impact content", "Aggressive promotion", "Daily optimization"]
            }
        ]

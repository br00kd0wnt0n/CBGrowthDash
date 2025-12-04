"""
AI Strategy Analysis Service
Uses OpenAI to analyze growth strategies and provide recommendations
"""
import os
from typing import Dict, List, Any, Optional
from models.schemas import InsightRequest, ParamTuneRequest

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
    historical_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze the current strategy and provide AI recommendations

    Returns multiple scenario suggestions with reasoning
    """

    # Calculate current metrics
    total_followers = sum(current_followers.values())
    goal = total_followers * 2

    # Build context for AI
    context = f"""
You are a social media growth strategist analyzing a campaign for Care Bears.

CURRENT SITUATION:
- Total Followers: {total_followers:,}
- 12-Month Goal: {goal:,} (double current)
- Current Strategy: {preset}
- Posts per Week: {posts_per_week}
- Platform Distribution: {platform_allocation}

PLATFORM BREAKDOWN:
"""
    for platform, count in current_followers.items():
        percentage = (count / total_followers) * 100
        context += f"- {platform}: {count:,} followers ({percentage:.1f}% of total)\n"

    context += f"""
CURRENT POSTING ALLOCATION:
"""
    for platform, pct in platform_allocation.items():
        posts = int((posts_per_week * pct) / 100)
        context += f"- {platform}: {pct}% ({posts} posts/week)\n"

    prompt = context + """
TASK:
Analyze this strategy and provide 3 alternative scenarios:
1. OPTIMIZED: Balanced approach for steady growth
2. AGGRESSIVE: Higher risk, faster growth potential
3. CONSERVATIVE: Lower risk, sustainable growth

For each scenario, provide:
- Recommended posts per week (14-50 range)
- Platform allocation percentages (must sum to 100%)
- Brief reasoning (2-3 sentences)
- Risk level (LOW/MEDIUM/HIGH)
- Expected outcome vs goal

IMPORTANT:
- Consider that oversaturation (>35 posts/week) can reduce engagement quality
- Different platforms have different optimal posting frequencies
- Account for audience overlap between platforms
- Balance reach expansion with engagement quality

Return ONLY valid JSON in this exact format:
{
    "analysis": "Overall assessment of current strategy in 2-3 sentences",
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
            "reasoning": "Brief explanation of why this works",
            "risk_level": "MEDIUM",
            "expected_outcome": "95% of goal"
        },
        ...two more scenarios...
    ],
    "key_insights": [
        "Insight 1",
        "Insight 2",
        "Insight 3"
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
    Generate rule-based recommendations if AI is unavailable
    """

    # Analyze current strategy
    total = sum(current_followers.values())
    tiktok_followers = current_followers.get("TikTok", 0)
    instagram_followers = current_followers.get("Instagram", 0)

    # Simple heuristics
    tiktok_strong = tiktok_followers > instagram_followers
    posting_high = posts_per_week > 30

    scenarios = []

    # Optimized scenario
    optimized_allocation = platform_allocation.copy()
    if tiktok_strong:
        optimized_allocation["TikTok"] = min(optimized_allocation.get("TikTok", 35) + 5, 45)
        optimized_allocation["Instagram"] = max(optimized_allocation.get("Instagram", 35) - 5, 25)

    scenarios.append({
        "name": "Optimized",
        "posts_per_week": 28,
        "platform_allocation": optimized_allocation,
        "reasoning": "Balanced approach focusing on high-performing platforms while maintaining presence across all channels.",
        "risk_level": "MEDIUM",
        "expected_outcome": "92-98% of goal"
    })

    # Aggressive scenario
    aggressive_allocation = {
        "Instagram": 30,
        "TikTok": 40,
        "YouTube": 20,
        "Facebook": 10
    }
    scenarios.append({
        "name": "Aggressive",
        "posts_per_week": 35,
        "platform_allocation": aggressive_allocation,
        "reasoning": "High-volume approach prioritizing video-first platforms for maximum reach expansion.",
        "risk_level": "HIGH",
        "expected_outcome": "105-115% of goal"
    })

    # Conservative scenario
    conservative_allocation = {
        "Instagram": 35,
        "TikTok": 30,
        "YouTube": 20,
        "Facebook": 15
    }
    scenarios.append({
        "name": "Conservative",
        "posts_per_week": 24,
        "platform_allocation": conservative_allocation,
        "reasoning": "Sustainable growth strategy focusing on engagement quality over volume.",
        "risk_level": "LOW",
        "expected_outcome": "85-92% of goal"
    })

    return {
        "analysis": f"Current strategy ({preset}, {posts_per_week} posts/week) provides a solid foundation. Consider testing alternative allocations to optimize growth.",
        "scenarios": scenarios,
        "key_insights": [
            "TikTok shows strong follower base - consider increasing allocation" if tiktok_strong else "Instagram is your primary platform - maintain focus there",
            "Current posting volume is sustainable" if not posting_high else "High posting frequency may risk oversaturation",
            "Diversified platform presence reduces dependency risk"
        ]
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

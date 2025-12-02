"""
AI Strategy Analysis Service
Uses OpenAI to analyze growth strategies and provide recommendations
"""
import os
from typing import Dict, List, Any
import openai

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

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

    try:
        response = openai.chat.completions.create(
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
        print(f"AI Service Error: {e}")
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

import httpx
import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.core.config import settings


async def generate_insights_with_ai(
    aggregates: Dict[str, Any],
    sample_transactions: List[Dict[str, Any]],
    filters: Dict[str, Any]
) -> List[str]:
    """
    Generate financial insights using AI based on aggregated data.

    Returns a list of 3-5 insight strings.
    """
    if not settings.OPENROUTER_API_KEY:
        return _get_stub_insights(aggregates)

    try:
        return await _call_openrouter_for_insights(aggregates, sample_transactions, filters)
    except Exception as e:
        print(f"Error calling OpenRouter for insights: {e}")
        return _get_stub_insights(aggregates)


async def _call_openrouter_for_insights(
    aggregates: Dict[str, Any],
    sample_transactions: List[Dict[str, Any]],
    filters: Dict[str, Any]
) -> List[str]:
    """Call OpenRouter API for insights generation."""

    # Build context
    context = {
        "filters": filters,
        "aggregates": aggregates,
        "sample_transactions": sample_transactions[:5]  # First 5 transactions
    }

    prompt = f"""You are a personal finance assistant generating concise insights for a user.

Based on the following structured data about their spending over a period:

{json.dumps(context, indent=2, default=str)}

Generate 3-5 bullet points with friendly, non-judgmental insights about:
- Overall spending patterns
- Notable categories
- Potential areas of concern or optimization
- Any unusual patterns

Return ONLY valid JSON with key "insights" containing an array of insight strings.
Example: {{"insights": ["Your total spending was $1234.56.", "Transport costs were lower than usual."]}}
"""

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": settings.OPENROUTER_MODEL,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
        )
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Parse JSON from response
        parsed = json.loads(content)

        return parsed.get("insights", [])


def _get_stub_insights(aggregates: Dict[str, Any]) -> List[str]:
    """Return stub insights when API key is not available."""
    total_spent = abs(aggregates.get("total_spent", 0))
    total_income = aggregates.get("total_income", 0)
    by_category = aggregates.get("by_category", {})

    insights = [
        f"Your total spending for this period was ${total_spent:.2f}.",
        f"Your total income was ${total_income:.2f}."
    ]

    if by_category:
        top_category = max(by_category.items(), key=lambda x: abs(x[1]))
        insights.append(f"Your largest spending category was {top_category[0]} at ${abs(top_category[1]):.2f}.")

    insights.append("Connect an OpenRouter API key to get AI-powered insights.")

    return insights

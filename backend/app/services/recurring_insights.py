"""
AI-powered recurring payment insights service.

This service generates insights about recurring payments including:
- Cost analysis and summaries
- Optimization suggestions
- Anomaly detection
- Upcoming payment predictions
"""

import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func
from openai import OpenAI

from app.core.config import settings
from app.models.transaction import Transaction
from app.models.recurring_cache import RecurringCache
from app.models.recurring_insights import RecurringInsights
from app.prompts.recurring_insights import (
    get_recurring_insights_prompt,
    get_simple_insights_prompt
)

logger = logging.getLogger("categorization")

# Cache validity period in days
INSIGHTS_CACHE_DAYS = 30


def get_cached_insights(user_id: int, db: Session) -> Optional[Dict]:
    """
    Get cached insights if they exist and are less than 30 days old.

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Cached insights dict or None if not found/stale
    """
    cached = db.query(RecurringInsights).filter(
        RecurringInsights.user_id == user_id
    ).first()

    if not cached:
        return None

    # Check if stale (> 30 days)
    days_since = (datetime.utcnow() - cached.analyzed_at).days
    if days_since > INSIGHTS_CACHE_DAYS:
        logger.info(f"Cached insights are stale ({days_since} days old)")
        return None

    logger.info(f"Returning cached insights ({days_since} days old)")
    return {
        "summary": cached.summary,
        "insights": cached.insights,
        "upcoming": cached.upcoming,
        "generated_at": cached.analyzed_at.isoformat()
    }


def save_insights(user_id: int, db: Session, insights: Dict) -> None:
    """
    Save or update insights in database.

    Args:
        user_id: User ID
        db: Database session
        insights: Insights dict to save
    """
    existing = db.query(RecurringInsights).filter(
        RecurringInsights.user_id == user_id
    ).first()

    if existing:
        existing.summary = insights.get("summary", {})
        existing.insights = insights.get("insights", [])
        existing.upcoming = insights.get("upcoming", [])
        existing.analyzed_at = datetime.utcnow()
        logger.info(f"Updated cached insights for user {user_id}")
    else:
        new_insights = RecurringInsights(
            user_id=user_id,
            summary=insights.get("summary", {}),
            insights=insights.get("insights", []),
            upcoming=insights.get("upcoming", []),
            analyzed_at=datetime.utcnow()
        )
        db.add(new_insights)
        logger.info(f"Created new cached insights for user {user_id}")

    db.commit()


def get_openai_client() -> Optional[OpenAI]:
    """Get OpenAI client configured for OpenRouter."""
    if not settings.OPENROUTER_API_KEY:
        return None

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
    )


def calculate_monthly_amount(amount: float, frequency: str) -> float:
    """
    Convert amount to monthly equivalent.

    Args:
        amount: Payment amount
        frequency: Payment frequency

    Returns:
        Monthly equivalent amount
    """
    multipliers = {
        "weekly": 4.33,
        "bi-weekly": 2.17,
        "monthly": 1,
        "quarterly": 1/3,
        "yearly": 1/12
    }
    return amount * multipliers.get(frequency, 1)


async def generate_recurring_insights(
    user_id: int,
    db: Session,
    recurring_payments: Optional[List[Dict]] = None
) -> Dict:
    """
    Generate AI insights about recurring payments.

    Args:
        user_id: User ID
        db: Database session
        recurring_payments: Optional pre-fetched recurring payments

    Returns:
        Dict with summary, insights, and upcoming payments
    """
    logger.info(f"Generating recurring insights for user {user_id}")

    # Get recurring payments if not provided (expenses only, exclude Income category)
    if recurring_payments is None:
        cached = db.query(RecurringCache).filter(
            RecurringCache.user_id == user_id,
            RecurringCache.is_recurring == True,
            RecurringCache.category != "Income"  # Exclude income entries
        ).all()

        recurring_payments = [
            {
                "merchant_key": c.merchant_key,
                "merchant_name": c.merchant_name or c.merchant_key,
                "category": c.category or "Other",
                "frequency": c.frequency or "monthly",
                "typical_amount": c.typical_amount or 0,
                "amount_variance": c.amount_variance or "variable",
                "next_expected_date": c.next_expected_date.isoformat() if c.next_expected_date else None
            }
            for c in cached
        ]

    if not recurring_payments:
        logger.info("No recurring payments found")
        return _empty_insights()

    # Calculate basic stats
    total_monthly = sum(
        calculate_monthly_amount(p["typical_amount"], p["frequency"])
        for p in recurring_payments
    )
    total_yearly = total_monthly * 12

    # Get total expenses and income for context
    thirty_days_ago = datetime.utcnow().date() - timedelta(days=30)

    expenses_result = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.date >= thirty_days_ago,
        Transaction.amount < 0
    ).scalar()
    total_monthly_expenses = abs(expenses_result) if expenses_result else 0

    income_result = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.date >= thirty_days_ago,
        Transaction.amount > 0
    ).scalar()
    total_monthly_income = income_result if income_result else 0

    # Try AI insights
    client = get_openai_client()
    if client:
        try:
            return await _get_ai_insights(
                client,
                recurring_payments,
                total_monthly_expenses,
                total_monthly_income
            )
        except Exception as e:
            logger.error(f"AI insights failed: {e}", exc_info=True)

    # Fallback to basic insights
    return _generate_basic_insights(
        recurring_payments,
        total_monthly,
        total_yearly,
        total_monthly_expenses
    )


async def _get_ai_insights(
    client: OpenAI,
    recurring_payments: List[Dict],
    total_monthly_expenses: float,
    total_monthly_income: float
) -> Dict:
    """
    Get AI-generated insights.

    Args:
        client: OpenAI client
        recurring_payments: List of recurring payments
        total_monthly_expenses: Total monthly expenses
        total_monthly_income: Total monthly income

    Returns:
        Dict with insights
    """
    logger.info(f"Calling AI for insights on {len(recurring_payments)} recurring payments...")

    prompt = get_recurring_insights_prompt(
        recurring_payments,
        total_monthly_expenses,
        total_monthly_income
    )

    response = client.chat.completions.create(
        model=settings.OPENROUTER_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        extra_body={"reasoning": {"enabled": True}}
    )

    content = response.choices[0].message.content

    # Parse JSON response
    try:
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1

        if start_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx:end_idx]
            result = json.loads(json_str)

            # Add generated_at timestamp
            result["generated_at"] = datetime.utcnow().isoformat()

            logger.info("AI insights generated successfully")
            return result
        else:
            logger.error("No JSON object found in AI response")
            raise ValueError("No JSON in response")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response: {e}")
        logger.error(f"Response content: {content[:500]}")
        raise


def _generate_basic_insights(
    recurring_payments: List[Dict],
    total_monthly: float,
    total_yearly: float,
    total_monthly_expenses: float
) -> Dict:
    """
    Generate basic insights without AI.

    Args:
        recurring_payments: List of recurring payments
        total_monthly: Total monthly recurring cost
        total_yearly: Total yearly recurring cost
        total_monthly_expenses: Total monthly expenses

    Returns:
        Dict with basic insights
    """
    logger.info("Generating basic insights (no AI)")

    # Calculate by category
    by_category = defaultdict(float)
    for p in recurring_payments:
        monthly = calculate_monthly_amount(p["typical_amount"], p["frequency"])
        by_category[p["category"]] += monthly

    # Calculate percentage
    percentage = (total_monthly / total_monthly_expenses * 100) if total_monthly_expenses > 0 else 0

    # Build insights
    insights = [
        {
            "type": "cost_analysis",
            "title": "Monthly Recurring Costs",
            "message": f"You spend ${total_monthly:.2f}/month (${total_yearly:.2f}/year) on {len(recurring_payments)} recurring payments",
            "priority": "info"
        }
    ]

    # Add category breakdown if multiple categories
    if len(by_category) > 1:
        top_category = max(by_category.items(), key=lambda x: x[1])
        insights.append({
            "type": "cost_analysis",
            "title": f"Largest Category: {top_category[0]}",
            "message": f"${top_category[1]:.2f}/month goes to {top_category[0]}",
            "priority": "info"
        })

    # Add percentage insight if significant
    if percentage >= 5:
        insights.append({
            "type": "cost_analysis",
            "title": "Expense Proportion",
            "message": f"Recurring payments make up {percentage:.1f}% of your monthly expenses",
            "priority": "info" if percentage < 20 else "warning"
        })

    # Get upcoming payments
    today = datetime.utcnow().date()
    upcoming = []
    for p in recurring_payments:
        if p.get("next_expected_date"):
            try:
                next_date = datetime.strptime(p["next_expected_date"], "%Y-%m-%d").date()
                days_until = (next_date - today).days
                if 0 <= days_until <= 14:
                    upcoming.append({
                        "merchant": p["merchant_name"],
                        "amount": p["typical_amount"],
                        "date": p["next_expected_date"],
                        "days_until": days_until
                    })
            except ValueError:
                pass

    upcoming.sort(key=lambda x: x["days_until"])

    return {
        "summary": {
            "total_monthly": round(total_monthly, 2),
            "total_yearly": round(total_yearly, 2),
            "count": len(recurring_payments),
            "percentage_of_expenses": round(percentage, 1),
            "by_category": {k: round(v, 2) for k, v in by_category.items()}
        },
        "insights": insights,
        "upcoming": upcoming[:5],  # Top 5 upcoming
        "generated_at": datetime.utcnow().isoformat()
    }


def _empty_insights() -> Dict:
    """Return empty insights structure."""
    return {
        "summary": {
            "total_monthly": 0,
            "total_yearly": 0,
            "count": 0,
            "percentage_of_expenses": 0,
            "by_category": {}
        },
        "insights": [
            {
                "type": "info",
                "title": "No Recurring Payments",
                "message": "No recurring payments detected yet. Add more transactions or run analysis.",
                "priority": "info"
            }
        ],
        "upcoming": [],
        "generated_at": datetime.utcnow().isoformat()
    }

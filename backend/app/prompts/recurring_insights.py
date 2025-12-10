"""
Prompt templates for AI-powered recurring payment insights.

This module generates prompts for AI to analyze recurring payments
and generate actionable insights like cost summaries, optimization
suggestions, anomaly detection, and predictions.
"""

from typing import List, Dict
from datetime import date


def get_recurring_insights_prompt(
    recurring_payments: List[Dict],
    total_monthly_expenses: float,
    total_monthly_income: float
) -> str:
    """
    Generate a prompt for analyzing recurring payments and generating insights.

    Args:
        recurring_payments: List of recurring payment dicts with:
            - merchant_name: Human-readable name
            - category: Payment category
            - frequency: weekly/bi-weekly/monthly/quarterly/yearly
            - typical_amount: Typical payment amount (positive number)
            - amount_variance: fixed/variable
            - next_expected_date: Expected next payment date (optional)
        total_monthly_expenses: Total monthly expenses for context
        total_monthly_income: Total monthly income for context

    Returns:
        Formatted prompt string
    """
    # Build payment list
    payment_lines = []
    for i, payment in enumerate(recurring_payments, 1):
        freq = payment.get("frequency", "monthly")
        amount = abs(payment.get("typical_amount", 0))
        variance = payment.get("amount_variance", "fixed")
        next_date = payment.get("next_expected_date", "unknown")
        category = payment.get("category", "Other")

        payment_lines.append(
            f"{i}. {payment['merchant_name']}: ${amount:.2f}/{freq} ({variance}) - {category}"
            f" - Next: {next_date}"
        )

    payments_text = "\n".join(payment_lines)

    prompt = f"""Analyze these recurring payments and generate insights:

**Recurring Payments:**
{payments_text}

**Financial Context:**
- Total Monthly Expenses: ${total_monthly_expenses:.2f}
- Total Monthly Income: ${total_monthly_income:.2f}

**Generate insights in these categories:**

1. **Cost Analysis**: Summarize total recurring costs (monthly/yearly)
2. **Optimization**: Suggest ways to save money (bundles, unused services, etc.)
3. **Anomaly Detection**: Flag any unusual patterns or concerns
4. **Predictions**: Upcoming payment reminders and cash flow predictions

**Response Format (JSON only):**
{{
  "summary": {{
    "total_monthly": 150.00,
    "total_yearly": 1800.00,
    "count": 5,
    "percentage_of_expenses": 6.0,
    "by_category": {{
      "Subscription": 50.00,
      "Utilities": 100.00
    }}
  }},
  "insights": [
    {{
      "type": "cost_analysis",
      "title": "Monthly Recurring Costs",
      "message": "You spend $150/month on recurring payments",
      "priority": "info"
    }},
    {{
      "type": "optimization",
      "title": "Streaming Services",
      "message": "Consider bundling Netflix + Disney+ for savings",
      "priority": "suggestion"
    }},
    {{
      "type": "anomaly",
      "title": "Unusual Charge",
      "message": "Your gym membership increased by 20%",
      "priority": "warning"
    }},
    {{
      "type": "prediction",
      "title": "High Expense Week",
      "message": "3 payments due next week totaling $85",
      "priority": "info"
    }}
  ],
  "upcoming": [
    {{
      "merchant": "Netflix",
      "amount": 15.99,
      "date": "2025-12-15",
      "days_until": 9
    }}
  ]
}}

**Important:**
- Be concise but informative
- Prioritize actionable insights
- Use "info" for neutral observations, "suggestion" for recommendations, "warning" for concerns
- Include at least one insight from each category if relevant
- List upcoming payments within the next 14 days

**CRITICAL:** Return ONLY the JSON object. No additional text."""

    return prompt


def get_simple_insights_prompt(
    recurring_payments: List[Dict]
) -> str:
    """
    Generate a simpler prompt when we don't have full financial context.

    Args:
        recurring_payments: List of recurring payment dicts

    Returns:
        Formatted prompt string
    """
    # Build payment list
    payment_lines = []
    total = 0
    for payment in recurring_payments:
        amount = abs(payment.get("typical_amount", 0))
        freq = payment.get("frequency", "monthly")
        total += amount if freq == "monthly" else amount / 12

        payment_lines.append(
            f"- {payment['merchant_name']}: ${amount:.2f}/{freq} ({payment.get('category', 'Other')})"
        )

    payments_text = "\n".join(payment_lines)

    prompt = f"""Analyze these recurring payments:

{payments_text}

**Generate a brief summary with:**
1. Total monthly cost
2. Total yearly cost
3. 1-2 optimization suggestions if any stand out
4. Any unusual patterns

Return JSON:
{{
  "summary": {{
    "total_monthly": {total:.2f},
    "total_yearly": {total * 12:.2f},
    "count": {len(recurring_payments)}
  }},
  "insights": [
    {{
      "type": "cost_analysis",
      "title": "Summary",
      "message": "Brief summary here",
      "priority": "info"
    }}
  ]
}}

**CRITICAL:** Return ONLY the JSON object."""

    return prompt

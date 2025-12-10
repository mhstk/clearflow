"""
Prompt templates for AI-powered recurring payment detection.

This module generates prompts for AI to verify if a set of transactions
from the same merchant represent a recurring payment pattern.
"""

from typing import List, Dict
from datetime import date


def get_recurring_detection_prompt(
    merchant_key: str,
    merchant_name: str,
    category: str,
    transactions: List[Dict],
    stats: Dict
) -> str:
    """
    Generate a prompt for detecting recurring payment patterns.

    Args:
        merchant_key: Normalized merchant identifier
        merchant_name: Human-readable merchant name (description_raw)
        category: Current category of transactions
        transactions: List of transaction dicts with date, amount, note
        stats: Pre-calculated statistics (count, avg_interval, amount_min/max, variance_pct)

    Returns:
        Formatted prompt string
    """
    # Build transaction list
    transaction_lines = []
    for i, txn in enumerate(transactions, 1):
        amount_str = f"${abs(txn['amount']):.2f}"
        note_str = f' (note: "{txn["note"]}")' if txn.get("note") else ""
        transaction_lines.append(
            f"{i}. {txn['date']}: -{amount_str}{note_str}"
        )
    transactions_text = "\n".join(transaction_lines)

    # Amount description
    if stats["amount_variance_pct"] == 0:
        amount_desc = f"Fixed at ${stats['amount_min']:.2f} (0% variance)"
    else:
        amount_desc = f"${stats['amount_min']:.2f} - ${stats['amount_max']:.2f} ({stats['amount_variance_pct']:.1f}% variance)"

    prompt = f"""Analyze these transactions from "{merchant_name}":

Transactions:
{transactions_text}

Stats:
- Count: {stats['count']} transactions
- Average interval: {stats['avg_interval_days']:.0f} days
- Amount: {amount_desc}
- Category: {category}

Questions:
1. Is this a recurring payment? (yes/no)
2. Are these the SAME recurring transaction based on the notes and amounts? (yes/no)
3. Frequency? (weekly/bi-weekly/monthly/quarterly/yearly/none)
4. Is amount fixed or variable?
5. When is next payment expected? (YYYY-MM-DD format)
6. Confidence? (high/medium/low)

Return JSON only:
{{
  "is_recurring": true,
  "same_transaction": true,
  "frequency": "monthly",
  "typical_amount": 2.26,
  "amount_variance": "fixed",
  "confidence": "high",
  "next_expected_date": "2025-12-27",
  "notes": "Description of the recurring pattern"
}}

**CRITICAL:** Return ONLY the JSON object. No additional text."""

    return prompt


def get_batch_recurring_detection_prompt(
    merchants: List[Dict]
) -> str:
    """
    Generate a prompt for batch detection of multiple merchants.

    Args:
        merchants: List of merchant dicts, each containing:
            - merchant_key: Normalized identifier
            - merchant_name: Human-readable name
            - category: Current category
            - transactions: List of transaction dicts
            - stats: Pre-calculated statistics

    Returns:
        Formatted prompt string
    """
    merchant_sections = []

    for idx, merchant in enumerate(merchants, 1):
        # Build transaction list
        transaction_lines = []
        for i, txn in enumerate(merchant["transactions"], 1):
            amount_str = f"${abs(txn['amount']):.2f}"
            note_str = f' (note: "{txn["note"]}")' if txn.get("note") else ""
            transaction_lines.append(
                f"   {i}. {txn['date']}: -{amount_str}{note_str}"
            )
        transactions_text = "\n".join(transaction_lines)

        stats = merchant["stats"]
        if stats["amount_variance_pct"] == 0:
            amount_desc = f"Fixed at ${stats['amount_min']:.2f}"
        else:
            amount_desc = f"${stats['amount_min']:.2f}-${stats['amount_max']:.2f} ({stats['amount_variance_pct']:.0f}% variance)"

        merchant_sections.append(f"""
Merchant {idx}: "{merchant['merchant_name']}" (key: {merchant['merchant_key']})
Category: {merchant['category']}
Transactions:
{transactions_text}
Stats: {stats['count']} transactions, avg interval {stats['avg_interval_days']:.0f} days, {amount_desc}
""")

    merchants_text = "\n".join(merchant_sections)

    prompt = f"""Analyze these merchants for recurring payment patterns:
{merchants_text}

For EACH merchant, determine:
1. Is this a recurring payment?
2. Are transactions the SAME recurring bill (based on notes/amounts)?
3. Frequency (weekly/bi-weekly/monthly/quarterly/yearly/none)
4. Is amount fixed or variable?
5. Next expected payment date
6. Confidence level

Return a JSON array with one object per merchant in order:
[
  {{
    "merchant_key": "MERCHANTKEY1",
    "is_recurring": true,
    "same_transaction": true,
    "frequency": "monthly",
    "typical_amount": 10.00,
    "amount_variance": "fixed",
    "confidence": "high",
    "next_expected_date": "2025-12-15",
    "notes": "Monthly subscription"
  }},
  ...
]

**CRITICAL:** Return ONLY the JSON array. No additional text."""

    return prompt

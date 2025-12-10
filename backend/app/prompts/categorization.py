"""
Prompt templates for AI-powered transaction categorization.

Modify these templates to adjust how the AI categorizes transactions.
"""

from typing import List, Dict


def get_batch_categorization_prompt(
    transactions: List[Dict],
    available_categories: List[str]
) -> str:
    """
    Generate a prompt for batch transaction categorization.

    Args:
        transactions: List of transaction dicts with id, description_raw, merchant_key, amount, date
        available_categories: List of valid category names

    Returns:
        Formatted prompt string
    """
    categories_list = ", ".join(available_categories)

    # Build transaction list for the prompt
    transaction_lines = []
    for txn in transactions:
        amount_str = f"${abs(txn['amount']):.2f}"
        txn_type = "expense" if txn['amount'] < 0 else "income"
        description = txn.get('description_raw', txn.get('merchant', 'Unknown'))
        merchant_key = txn.get('merchant_key', '')

        # Include both description_raw and merchant_key for better context
        merchant_info = f"\"{description}\""
        if merchant_key and merchant_key != description:
            merchant_info += f" (normalized: {merchant_key})"

        transaction_lines.append(
            f"  - ID: {txn['id']}, Merchant: {merchant_info}, "
            f"Amount: {amount_str} ({txn_type}), Date: {txn['date']}"
        )

    transactions_text = "\n".join(transaction_lines)

    prompt = f"""You are a financial transaction categorization expert. Your task is to categorize transactions into appropriate spending categories.

**Available Categories:**
{categories_list}

**Important Rules:**
1. Choose ONLY from the available categories above
2. Consider both the merchant name AND the transaction amount
3. Use "Income" for positive amounts (deposits, paychecks, refunds)
4. Use "Other" if you're uncertain about the category
5. For each transaction, provide:
   - category: One of the available categories
   - note: A short, user-friendly description (max 40 characters)
   - confidence: "high", "medium", or "low"

**Transactions to Categorize:**
{transactions_text}

**Guidelines for Common Merchants:**
- Grocery stores (Loblaws, Metro, Walmart, Costco) → Groceries
- Fast food/restaurants (McDonald's, Tim Hortons, Starbucks) → Eating Out
- Gas stations (Shell, Esso, Petro-Canada) → Transport
- Streaming services (Netflix, Spotify, Disney+) → Subscription
- Transit (Presto, TTC, GO Transit) → Transport
- Pharmacies (Shoppers Drug Mart, Rexall) → Shopping
- Utilities (Hydro, Gas, Water, Internet, Phone) → Utilities
- Rent payments → Rent
- Income deposits, paychecks → Income

**Response Format:**
Return a JSON array with one object per transaction in the EXACT same order as provided above.

Example:
[
  {{
    "transaction_id": 123,
    "category": "Groceries",
    "note": "Weekly shopping",
    "confidence": "high"
  }},
  {{
    "transaction_id": 456,
    "category": "Eating Out",
    "note": "Fast food lunch",
    "confidence": "high"
  }}
]

**CRITICAL:** Return ONLY the JSON array. No additional text before or after."""

    return prompt


def get_single_categorization_prompt(
    transaction: Dict,
    available_categories: List[str]
) -> str:
    """
    Generate a prompt for single transaction categorization.

    Args:
        transaction: Dict with id, description_raw, merchant_key, amount, date
        available_categories: List of valid category names

    Returns:
        Formatted prompt string
    """
    categories_list = ", ".join(available_categories)

    amount_str = f"${abs(transaction['amount']):.2f}"
    txn_type = "expense" if transaction['amount'] < 0 else "income"

    description = transaction.get('description_raw', transaction.get('merchant', 'Unknown'))
    merchant_key = transaction.get('merchant_key', '')

    # Include both description_raw and merchant_key for better context
    merchant_info = f"\"{description}\""
    if merchant_key and merchant_key != description:
        merchant_info += f" (normalized: {merchant_key})"

    prompt = f"""You are a financial transaction categorization expert. Categorize this transaction into the most appropriate category.

**Available Categories:**
{categories_list}

**Transaction:**
- Merchant: {merchant_info}
- Amount: {amount_str} ({txn_type})
- Date: {transaction['date']}

**Important Rules:**
1. Choose ONLY from the available categories above
2. Consider both the merchant name AND the transaction amount
3. Use "Income" for positive amounts
4. Use "Other" if you're uncertain

**Response Format:**
Return a JSON object with:

{{
  "category": "chosen_category",
  "note": "short user-friendly description (max 40 chars)",
  "confidence": "high|medium|low"
}}

**CRITICAL:** Return ONLY the JSON object. No additional text."""

    return prompt

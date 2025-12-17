import httpx
import json
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.config import settings
from app.models.merchant_cache import MerchantCache
from app.models.transaction import Transaction
from app.models.user_category import UserCategory, DEFAULT_USER_CATEGORIES


def get_user_categories(db: Session, user_id: int) -> List[str]:
    """
    Get list of category names for a user.
    If user has no categories, returns default category names.
    """
    categories = db.query(UserCategory).filter(
        UserCategory.user_id == user_id
    ).order_by(UserCategory.sort_order).all()

    if categories:
        return [cat.name for cat in categories]

    # Return default names if user has no categories yet
    return [cat["name"] for cat in DEFAULT_USER_CATEGORIES]


async def categorize_merchant_with_ai(
    merchant_key: str,
    sample_descriptions: list[str],
    db: Session,
    user_id: int
) -> Dict[str, str]:
    """
    Categorize a merchant using AI (OpenRouter).

    Returns cached result if available, otherwise calls LLM.
    Uses user's custom categories for categorization.
    """
    # Get user's categories
    user_categories = get_user_categories(db, user_id)

    # Check cache first
    cache_entry = db.query(MerchantCache).filter(
        MerchantCache.user_id == user_id,
        MerchantCache.merchant_key == merchant_key
    ).first()

    if cache_entry:
        # Update last_used_at
        cache_entry.last_used_at = datetime.utcnow()
        db.commit()

        return {
            "merchant_key": merchant_key,
            "category": cache_entry.suggested_category,
            "note": cache_entry.suggested_note,
            "explanation": cache_entry.suggested_explanation
        }

    # Call LLM
    if not settings.OPENROUTER_API_KEY:
        # Return stub if no API key
        return _get_stub_categorization(merchant_key)

    try:
        result = await _call_openrouter(merchant_key, sample_descriptions, user_categories)

        # Save to cache
        cache_entry = MerchantCache(
            user_id=user_id,
            merchant_key=merchant_key,
            suggested_category=result["category"],
            suggested_note=result["note"],
            suggested_explanation=result["explanation"]
        )
        db.add(cache_entry)

        # Update transactions with this merchant_key
        db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.merchant_key == merchant_key,
            Transaction.category_source == "uncategorized"
        ).update({
            "category": result["category"],
            "category_source": "ai"
        })

        db.commit()

        return {
            "merchant_key": merchant_key,
            **result
        }

    except Exception as e:
        print(f"Error calling OpenRouter: {e}")
        return _get_stub_categorization(merchant_key)


async def _call_openrouter(
    merchant_key: str,
    sample_descriptions: list[str],
    categories: List[str]
) -> Dict[str, str]:
    """Call OpenRouter API for categorization using user's custom categories."""

    prompt = f"""You are helping categorize financial transactions.
You will receive several raw transaction descriptions from a bank statement.

Choose one high-level category from this list:
{', '.join(categories)}

Sample descriptions for merchant "{merchant_key}":
{chr(10).join(f"- {desc}" for desc in sample_descriptions)}

Generate:
1. A category from the list above
2. A short user-friendly label (max 30 characters) summarizing typical transactions for this merchant
3. A one-sentence explanation of what this merchant likely is

Return ONLY valid JSON with keys: category, note, explanation.
Example: {{"category": "Eating Out", "note": "Lunch - McDonald's", "explanation": "McDonald's is a fast food restaurant."}}
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
                "temperature": 0.3
            }
        )
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Parse JSON from response
        parsed = json.loads(content)

        # Validate category against user's categories
        if parsed["category"] not in categories:
            parsed["category"] = "Other"

        return parsed


def _get_stub_categorization(merchant_key: str) -> Dict[str, str]:
    """Return stub data when API key is not available."""
    return {
        "merchant_key": merchant_key,
        "category": "Other",
        "note": f"Transaction at {merchant_key}",
        "explanation": f"Merchant categorized as {merchant_key} (stub - no API key)"
    }

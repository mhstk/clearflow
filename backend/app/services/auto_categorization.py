"""
AI-powered auto-categorization service using OpenAI client with OpenRouter.
"""

import json
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from openai import OpenAI

from app.core.config import settings
from app.models.transaction import Transaction
from app.models.merchant_cache import MerchantCache
from app.prompts.categorization import (
    get_batch_categorization_prompt,
    get_single_categorization_prompt
)
from app.services.categorization import get_user_categories

logger = logging.getLogger(__name__)


def get_openai_client() -> Optional[OpenAI]:
    """Get OpenAI client configured for OpenRouter."""
    if not settings.OPENROUTER_API_KEY:
        return None

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
    )
    return client


async def categorize_transactions_batch(
    transaction_ids: List[int],
    db: Session,
    user_id: int,
    auto_apply: bool = True
) -> Dict:
    """
    Categorize multiple transactions using AI.

    Args:
        transaction_ids: List of transaction IDs to categorize
        db: Database session
        user_id: User ID
        auto_apply: Whether to automatically apply categories to database

    Returns:
        Dict with results for each transaction
    """
    # Get user's custom categories
    valid_categories = get_user_categories(db, user_id)

    # Get transactions
    transactions = db.query(Transaction).filter(
        Transaction.id.in_(transaction_ids),
        Transaction.user_id == user_id
    ).all()

    if not transactions:
        return {
            "results": [],
            "total_processed": 0,
            "successful": 0,
            "failed": 0
        }

    # Check which transactions can use merchant cache
    cached_results = []
    uncached_transactions = []

    for txn in transactions:
        cache_entry = db.query(MerchantCache).filter(
            MerchantCache.user_id == user_id,
            MerchantCache.merchant_key == txn.merchant_key
        ).first()

        if cache_entry:
            # Use cached categorization
            if auto_apply:
                txn.category = cache_entry.suggested_category
                txn.category_source = "ai"
                txn.note_user = cache_entry.suggested_note if not txn.note_user else txn.note_user

            cached_results.append({
                "transaction_id": txn.id,
                "category": cache_entry.suggested_category,
                "note": cache_entry.suggested_note,
                "confidence": "high",
                "applied": auto_apply,
                "error": None
            })

            # Update cache last_used_at
            cache_entry.last_used_at = datetime.utcnow()
        else:
            uncached_transactions.append(txn)

    # Commit cached updates
    if auto_apply and cached_results:
        db.commit()

    # If all transactions were cached, return early
    if not uncached_transactions:
        return {
            "results": cached_results,
            "total_processed": len(cached_results),
            "successful": len(cached_results),
            "failed": 0
        }

    # Categorize uncached transactions with AI
    client = get_openai_client()
    if not client:
        # No API key - return stub results
        stub_results = []
        for txn in uncached_transactions:
            stub_results.append({
                "transaction_id": txn.id,
                "category": "Uncategorized",
                "note": "AI categorization unavailable",
                "confidence": "low",
                "applied": False,
                "error": "No API key configured"
            })

        return {
            "results": cached_results + stub_results,
            "total_processed": len(transactions),
            "successful": len(cached_results),
            "failed": len(stub_results)
        }

    # Prepare transaction data for AI
    txn_data = []
    for txn in uncached_transactions:
        txn_data.append({
            "id": txn.id,
            "description_raw": txn.description_raw,
            "merchant_key": txn.merchant_key,
            "amount": txn.amount,
            "date": txn.date.isoformat()
        })

    # Get AI categorization
    try:
        ai_results = await _call_ai_for_categorization(client, txn_data, valid_categories)

        # Process AI results
        ai_categorization_results = []
        # Track which merchants we've already cached in this batch to avoid duplicates
        cached_in_batch = set()

        for ai_result in ai_results:
            txn_id = ai_result.get("transaction_id")
            category = ai_result.get("category", "Uncategorized")
            note = ai_result.get("note", "")
            confidence = ai_result.get("confidence", "medium")

            # Validate category against user's categories
            if category not in valid_categories:
                category = "Other"

            # Find transaction
            txn = next((t for t in uncached_transactions if t.id == txn_id), None)
            if not txn:
                continue

            # Apply to database if auto_apply
            applied = False
            if auto_apply:
                txn.category = category
                txn.category_source = "ai"
                if not txn.note_user:  # Don't overwrite existing notes
                    txn.note_user = note
                applied = True

                # Cache this result - check if exists first OR if we've already cached it in this batch
                if txn.merchant_key not in cached_in_batch:
                    existing_cache = db.query(MerchantCache).filter(
                        MerchantCache.user_id == user_id,
                        MerchantCache.merchant_key == txn.merchant_key
                    ).first()

                    if existing_cache:
                        # Update existing cache
                        existing_cache.suggested_category = category
                        existing_cache.suggested_note = note
                        existing_cache.suggested_explanation = f"Auto-categorized as {category}"
                        existing_cache.last_used_at = datetime.utcnow()
                    else:
                        # Create new cache entry
                        cache_entry = MerchantCache(
                            user_id=user_id,
                            merchant_key=txn.merchant_key,
                            suggested_category=category,
                            suggested_note=note,
                            suggested_explanation=f"Auto-categorized as {category}",
                            last_used_at=datetime.utcnow()
                        )
                        db.add(cache_entry)

                    # Mark this merchant as cached in this batch
                    cached_in_batch.add(txn.merchant_key)

            ai_categorization_results.append({
                "transaction_id": txn_id,
                "category": category,
                "note": note,
                "confidence": confidence,
                "applied": applied,
                "error": None
            })

        # Commit all changes
        if auto_apply:
            try:
                db.commit()
            except Exception as commit_error:
                db.rollback()
                logger.error(f"Error committing AI categorization: {commit_error}", exc_info=True)
                # Mark results as failed
                for result in ai_categorization_results:
                    result["applied"] = False
                    result["error"] = f"Database error: {str(commit_error)}"

        # Combine cached and AI results
        all_results = cached_results + ai_categorization_results
        successful = len([r for r in all_results if not r.get("error")])
        failed = len(all_results) - successful

        return {
            "results": all_results,
            "total_processed": len(all_results),
            "successful": successful,
            "failed": failed
        }

    except Exception as e:
        # Return error results
        error_results = []
        for txn in uncached_transactions:
            error_results.append({
                "transaction_id": txn.id,
                "category": "Uncategorized",
                "note": "",
                "confidence": "low",
                "applied": False,
                "error": str(e)
            })

        return {
            "results": cached_results + error_results,
            "total_processed": len(transactions),
            "successful": len(cached_results),
            "failed": len(error_results)
        }


async def _call_ai_for_categorization(
    client: OpenAI,
    transactions: List[Dict],
    categories: List[str]
) -> List[Dict]:
    """
    Call OpenRouter API to categorize transactions.

    Args:
        client: OpenAI client
        transactions: List of transaction dicts
        categories: List of valid category names for the user

    Returns:
        List of categorization results
    """
    # Generate prompt with user's categories
    prompt = get_batch_categorization_prompt(transactions, categories)

    # Call API
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

    # Extract response
    content = response.choices[0].message.content

    # Parse JSON response
    try:
        # Try to extract JSON from response
        # Sometimes the model includes extra text, so we need to find the JSON
        start_idx = content.find('[')
        end_idx = content.rfind(']') + 1

        if start_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx:end_idx]
            results = json.loads(json_str)
            return results
        else:
            # Couldn't find JSON array
            raise ValueError("No JSON array found in response")

    except json.JSONDecodeError as e:
        # If JSON parsing fails, return empty results
        logger.error(f"Failed to parse AI response: {e}")
        logger.error(f"Response content: {content}")
        return []


async def categorize_single_transaction(
    transaction_id: int,
    db: Session,
    user_id: int,
    auto_apply: bool = True
) -> Dict:
    """
    Categorize a single transaction using AI.

    Args:
        transaction_id: Transaction ID
        db: Database session
        user_id: User ID
        auto_apply: Whether to automatically apply category to database

    Returns:
        Categorization result
    """
    # Use batch function with single transaction
    result = await categorize_transactions_batch(
        [transaction_id],
        db,
        user_id,
        auto_apply
    )

    if result["results"]:
        return result["results"][0]
    else:
        return {
            "transaction_id": transaction_id,
            "category": "Uncategorized",
            "note": "",
            "confidence": "low",
            "applied": False,
            "error": "Transaction not found"
        }


def get_valid_categories(db: Session, user_id: int) -> List[str]:
    """Get list of valid categories for a user."""
    return get_user_categories(db, user_id)

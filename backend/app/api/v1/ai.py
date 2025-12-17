import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_user_id
from app.db.session import SessionLocal
from app.schemas.merchant_cache import (
    CategorizeMerchantRequest,
    CategorizeMerchantResponse,
    InsightsRequest,
    InsightsResponse,
    BatchCategorizationRequest,
    BatchCategorizationResponse
)
from app.services.categorization import categorize_merchant_with_ai
from app.services.insights import generate_insights_with_ai
from app.services.auto_categorization import categorize_transactions_batch, get_valid_categories
from app.models.transaction import Transaction
from datetime import date

logger = logging.getLogger("categorization")
router = APIRouter()

# Thread pool for AI operations - prevents blocking the event loop
ai_executor = ThreadPoolExecutor(max_workers=3)


def _run_categorize_merchant_sync(merchant_key: str, sample_descriptions: List[str], user_id: int):
    """Run merchant categorization in a background thread."""
    db = SessionLocal()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                categorize_merchant_with_ai(
                    merchant_key=merchant_key,
                    sample_descriptions=sample_descriptions,
                    db=db,
                    user_id=user_id
                )
            )
            return result
        finally:
            loop.close()
    finally:
        db.close()


def _run_insights_sync(aggregates: dict, sample_transactions: list, filters: dict):
    """Run insights generation in a background thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            generate_insights_with_ai(
                aggregates=aggregates,
                sample_transactions=sample_transactions,
                filters=filters
            )
        )
        return result
    finally:
        loop.close()


def _run_batch_categorize_sync(transaction_ids: List[int], user_id: int, auto_apply: bool):
    """Run batch categorization in a background thread."""
    db = SessionLocal()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                categorize_transactions_batch(
                    transaction_ids=transaction_ids,
                    db=db,
                    user_id=user_id,
                    auto_apply=auto_apply
                )
            )
            return result
        finally:
            loop.close()
    finally:
        db.close()


@router.post("/categorize_merchant", response_model=CategorizeMerchantResponse)
async def categorize_merchant(
    request: CategorizeMerchantRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    Categorize a merchant using AI.

    Returns cached result if available, otherwise calls LLM and caches the result.
    Also updates all uncategorized transactions for this merchant.
    Runs in background thread to avoid blocking other requests.
    """
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            ai_executor,
            _run_categorize_merchant_sync,
            request.merchant_key,
            request.sample_descriptions,
            user_id
        )

        return CategorizeMerchantResponse(**result)

    except Exception as e:
        logger.error(f"Error categorizing merchant: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to categorize merchant. Please try again.")


@router.post("/insights", response_model=InsightsResponse)
async def get_insights(
    request: InsightsRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Generate AI-powered insights based on filtered transactions.

    Uses the same filtering logic as /transactions/view to compute aggregates,
    then generates narrative insights using AI.
    """
    try:
        # Build query with same filters as transactions/view
        query = db.query(Transaction).filter(Transaction.user_id == user_id)

        if request.account_id is not None:
            query = query.filter(Transaction.account_id == request.account_id)

        if request.start_date is not None:
            start = date.fromisoformat(request.start_date)
            query = query.filter(Transaction.date >= start)

        if request.end_date is not None:
            end = date.fromisoformat(request.end_date)
            query = query.filter(Transaction.date <= end)

        if request.category is not None:
            query = query.filter(Transaction.category.in_(request.category))

        if request.merchant_query is not None:
            search_pattern = f"%{request.merchant_query}%"
            query = query.filter(
                Transaction.description_raw.ilike(search_pattern)
                | Transaction.note_user.ilike(search_pattern)
                | Transaction.merchant_key.ilike(search_pattern)
            )

        if request.min_amount is not None:
            query = query.filter(Transaction.amount >= request.min_amount)

        if request.max_amount is not None:
            query = query.filter(Transaction.amount <= request.max_amount)

        # Get all filtered transactions
        transactions = query.all()

        # Compute aggregates
        total_spent = sum(t.amount for t in transactions if t.amount < 0)
        total_income = sum(t.amount for t in transactions if t.amount > 0)

        by_category = {}
        for t in transactions:
            by_category[t.category] = by_category.get(t.category, 0) + t.amount

        aggregates = {
            "total_spent": total_spent,
            "total_income": total_income,
            "by_category": by_category
        }

        # Sample transactions for context
        sample_transactions = [
            {
                "date": t.date.isoformat(),
                "description": t.description_raw,
                "amount": t.amount,
                "category": t.category
            }
            for t in transactions[:10]
        ]

        # Generate insights with AI in background thread
        loop = asyncio.get_event_loop()
        insights = await loop.run_in_executor(
            ai_executor,
            _run_insights_sync,
            aggregates,
            sample_transactions,
            request.model_dump()
        )

        return InsightsResponse(insights=insights)

    except Exception as e:
        logger.error(f"Error generating insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate insights. Please try again.")


@router.get("/categories")
def get_available_categories(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get list of valid categories that can be assigned to transactions.

    Returns the user's custom categories that:
    - Can be manually assigned by users
    - Are recognized by the AI categorization system
    - Are validated when transactions are categorized

    Use this endpoint to:
    - Populate category selection dropdowns
    - Validate user input
    - Show available options in the UI

    Note: Each user has their own custom category list.
    New users get default categories automatically.
    """
    return get_valid_categories(db, user_id)


@router.post("/categorize_batch", response_model=BatchCategorizationResponse)
async def categorize_batch(
    request: BatchCategorizationRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    Batch categorize transactions using AI.

    Categorizes multiple transactions at once using AI analysis of merchant names and amounts.
    Uses cached results when available to minimize API calls.
    Runs in background thread to avoid blocking other requests.

    Parameters:
    - transaction_ids: List of transaction IDs to categorize
    - auto_apply: Whether to automatically apply categories to database (default: True)

    Returns categorization results with:
    - category: Assigned category
    - note: User-friendly description
    - confidence: AI confidence level (high/medium/low)
    - applied: Whether category was applied to database

    Features:
    - Uses merchant cache to avoid redundant API calls
    - Validates categories against allowed list
    - Provides confidence scores
    - Handles errors gracefully per transaction

    Example:
    ```json
    {
      "transaction_ids": [1, 2, 3, 4, 5],
      "auto_apply": true
    }
    ```
    """
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            ai_executor,
            _run_batch_categorize_sync,
            request.transaction_ids,
            user_id,
            request.auto_apply
        )

        return BatchCategorizationResponse(**result)

    except Exception as e:
        logger.error(f"Error categorizing transactions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to categorize transactions. Please try again."
        )

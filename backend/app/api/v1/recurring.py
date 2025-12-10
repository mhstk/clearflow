"""
Recurring payments API endpoints.

Provides endpoints for:
- Detecting recurring payments
- Getting AI insights
- Viewing upcoming payments
- Triggering background analysis
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.api.deps import get_db, get_current_user_id
from app.db.session import SessionLocal
from app.schemas.recurring import (
    RecurringPayment,
    RecurringPaymentsResponse,
    RecurringInsight,
    UpcomingPayment,
    RecurringInsightsResponse,
    AnalyzeResponse
)
from app.services.recurring_detection import (
    detect_recurring_payments,
    get_cached_recurring_payments,
    get_upcoming_payments,
    calculate_monthly_amount
)
from app.services.recurring_insights import (
    generate_recurring_insights,
    get_cached_insights,
    save_insights
)

logger = logging.getLogger("categorization")
router = APIRouter()

# Thread pool for background tasks
executor = ThreadPoolExecutor(max_workers=2)


def _run_detection_in_background(user_id: int):
    """
    Run recurring detection in a background thread.
    Creates its own database session and event loop.
    """
    db = SessionLocal()
    try:
        logger.info(f"Background recurring detection started for user {user_id}")

        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                detect_recurring_payments(
                    user_id=user_id,
                    db=db,
                    force_refresh=True
                )
            )
            logger.info(f"Background detection complete: {len(result)} recurring payments found")
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Background detection failed: {e}", exc_info=True)
    finally:
        db.close()


@router.get("/", response_model=RecurringPaymentsResponse)
async def get_recurring_payments(
    force_refresh: bool = Query(False, description="Force re-analysis ignoring cache"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get all detected recurring payments.

    Uses cached results unless force_refresh=True, which triggers
    a full re-analysis including AI verification.

    Returns:
    - List of recurring payments with details
    - Total monthly and yearly costs
    """
    try:
        if force_refresh:
            # Run detection with force refresh
            recurring_payments = await detect_recurring_payments(
                user_id=user_id,
                db=db,
                force_refresh=True
            )
        else:
            # Get cached results
            recurring_payments = get_cached_recurring_payments(user_id, db)

            # If no cache, run detection
            if not recurring_payments:
                recurring_payments = await detect_recurring_payments(
                    user_id=user_id,
                    db=db,
                    force_refresh=False
                )

        # Calculate totals
        total_monthly = sum(
            calculate_monthly_amount(p["typical_amount"], p["frequency"])
            for p in recurring_payments
        )
        total_yearly = total_monthly * 12

        return RecurringPaymentsResponse(
            recurring_payments=[
                RecurringPayment(
                    merchant_key=p["merchant_key"],
                    merchant_name=p["merchant_name"],
                    category=p["category"],
                    frequency=p["frequency"],
                    typical_amount=p["typical_amount"],
                    amount_variance=p["amount_variance"],
                    confidence=p["confidence"],
                    transaction_count=p["transaction_count"],
                    last_transaction_date=datetime.strptime(
                        p["last_transaction_date"], "%Y-%m-%d"
                    ).date() if p["last_transaction_date"] else None,
                    next_expected_date=datetime.strptime(
                        p["next_expected_date"], "%Y-%m-%d"
                    ).date() if p["next_expected_date"] else None,
                    ai_notes=p.get("ai_notes")
                )
                for p in recurring_payments
            ],
            total_count=len(recurring_payments),
            total_monthly=round(total_monthly, 2),
            total_yearly=round(total_yearly, 2)
        )

    except Exception as e:
        logger.error(f"Error getting recurring payments: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get recurring payments. Please try again."
        )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_recurring_payments(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Trigger full recurring payment analysis in background.

    This runs the complete detection pipeline:
    1. Groups transactions by merchant
    2. Calculates interval and amount patterns
    3. Verifies with AI
    4. Caches results

    Returns immediately with status. Use GET /recurring to fetch results.
    """
    try:
        # Count merchants to analyze
        from app.models.transaction import Transaction
        from sqlalchemy import func
        from datetime import timedelta

        cutoff_date = datetime.utcnow().date() - timedelta(days=180)

        # Count merchants with 2+ expense transactions (only expenses, not income)
        merchant_counts = db.query(
            Transaction.merchant_key,
            func.count(Transaction.id).label("count")
        ).filter(
            Transaction.user_id == user_id,
            Transaction.date >= cutoff_date,
            Transaction.amount < 0  # Only expenses (negative amounts)
        ).group_by(Transaction.merchant_key).having(
            func.count(Transaction.id) >= 2
        ).all()

        merchants_to_analyze = len(merchant_counts)

        if merchants_to_analyze == 0:
            return AnalyzeResponse(
                message="No merchants with enough transactions to analyze",
                status="completed",
                merchants_to_analyze=0
            )

        # Run detection in background thread
        executor.submit(_run_detection_in_background, user_id)

        return AnalyzeResponse(
            message=f"Analysis started for {merchants_to_analyze} merchants",
            status="started",
            merchants_to_analyze=merchants_to_analyze
        )

    except Exception as e:
        logger.error(f"Error starting analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to start analysis. Please try again."
        )


@router.get("/insights", response_model=RecurringInsightsResponse)
async def get_insights(
    force_refresh: bool = Query(False, description="Force regeneration of insights"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get AI-generated insights about recurring payments.

    Returns cached insights unless:
    - force_refresh=True (user clicked Analyze)
    - Cache is empty
    - Cache is older than 30 days

    Provides:
    - Cost summary (monthly, yearly, by category)
    - Optimization suggestions
    - Anomaly alerts
    - Upcoming payment predictions
    """
    try:
        # Try cached first (unless force refresh)
        if not force_refresh:
            cached = get_cached_insights(user_id, db)
            if cached:
                result = cached
            else:
                # No cache, generate fresh
                result = await generate_recurring_insights(user_id=user_id, db=db)
                # Save to DB
                save_insights(user_id, db, result)
        else:
            # Force refresh - generate new insights
            result = await generate_recurring_insights(user_id=user_id, db=db)
            # Save to DB
            save_insights(user_id, db, result)

        return RecurringInsightsResponse(
            summary=result.get("summary", {}),
            insights=[
                RecurringInsight(
                    type=i["type"],
                    title=i["title"],
                    message=i["message"],
                    priority=i["priority"]
                )
                for i in result.get("insights", [])
            ],
            upcoming=[
                UpcomingPayment(
                    merchant_key=u.get("merchant_key", u.get("merchant", "")),
                    merchant_name=u.get("merchant_name", u.get("merchant", "")),
                    amount=u["amount"],
                    expected_date=datetime.strptime(
                        u["date"], "%Y-%m-%d"
                    ).date() if isinstance(u["date"], str) else u["date"],
                    days_until=u["days_until"]
                )
                for u in result.get("upcoming", [])
            ],
            generated_at=datetime.fromisoformat(
                result["generated_at"]
            ) if isinstance(result.get("generated_at"), str) else result.get("generated_at", datetime.utcnow())
        )

    except Exception as e:
        logger.error(f"Error getting insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get insights. Please try again."
        )


@router.get("/upcoming", response_model=List[UpcomingPayment])
async def get_upcoming(
    days: int = Query(7, ge=1, le=30, description="Days to look ahead"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get upcoming recurring payments.

    Returns payments expected within the specified number of days,
    sorted by expected date.

    Parameters:
    - days: Number of days to look ahead (1-30, default: 7)
    """
    try:
        upcoming = get_upcoming_payments(
            user_id=user_id,
            db=db,
            days=days
        )

        return [
            UpcomingPayment(
                merchant_key=u["merchant_key"],
                merchant_name=u["merchant_name"],
                amount=u["amount"],
                expected_date=datetime.strptime(
                    u["expected_date"], "%Y-%m-%d"
                ).date() if isinstance(u["expected_date"], str) else u["expected_date"],
                days_until=u["days_until"]
            )
            for u in upcoming
        ]

    except Exception as e:
        logger.error(f"Error getting upcoming payments: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get upcoming payments. Please try again."
        )

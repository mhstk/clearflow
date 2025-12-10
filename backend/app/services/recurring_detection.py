"""
AI-powered recurring payment detection service.

This service detects recurring payment patterns by:
1. Grouping transactions by merchant_key
2. Calculating interval and amount statistics
3. Verifying patterns with AI
4. Caching results for performance
"""

import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta, date
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func
from openai import OpenAI

from app.core.config import settings
from app.models.transaction import Transaction
from app.models.recurring_cache import RecurringCache
from app.prompts.recurring_detection import (
    get_recurring_detection_prompt,
    get_batch_recurring_detection_prompt
)

logger = logging.getLogger("categorization")  # Use same log file


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


def get_openai_client() -> Optional[OpenAI]:
    """Get OpenAI client configured for OpenRouter."""
    if not settings.OPENROUTER_API_KEY:
        return None

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
    )


def calculate_transaction_stats(transactions: List[Dict]) -> Dict:
    """
    Calculate statistics for a group of transactions.

    Args:
        transactions: List of transaction dicts with date and amount

    Returns:
        Dict with count, avg_interval_days, amount_min, amount_max, amount_variance_pct
    """
    if not transactions:
        return {
            "count": 0,
            "avg_interval_days": 0,
            "amount_min": 0,
            "amount_max": 0,
            "amount_variance_pct": 0
        }

    # Sort by date
    sorted_txns = sorted(transactions, key=lambda x: x["date"])

    # Calculate intervals between transactions
    intervals = []
    for i in range(1, len(sorted_txns)):
        date1 = sorted_txns[i-1]["date"]
        date2 = sorted_txns[i]["date"]

        if isinstance(date1, str):
            date1 = datetime.strptime(date1, "%Y-%m-%d").date()
        if isinstance(date2, str):
            date2 = datetime.strptime(date2, "%Y-%m-%d").date()

        interval = (date2 - date1).days
        if interval > 0:  # Ignore same-day transactions
            intervals.append(interval)

    avg_interval = sum(intervals) / len(intervals) if intervals else 0

    # Calculate amount statistics
    amounts = [abs(txn["amount"]) for txn in transactions]
    amount_min = min(amounts)
    amount_max = max(amounts)

    # Variance as percentage of mean
    if amount_min > 0:
        variance_pct = ((amount_max - amount_min) / amount_min) * 100
    else:
        variance_pct = 0

    return {
        "count": len(transactions),
        "avg_interval_days": avg_interval,
        "amount_min": amount_min,
        "amount_max": amount_max,
        "amount_variance_pct": variance_pct
    }


def detect_frequency_from_interval(avg_interval: float) -> Optional[str]:
    """
    Detect payment frequency from average interval.

    Args:
        avg_interval: Average days between transactions

    Returns:
        Frequency string or None if unclear
    """
    if avg_interval <= 0:
        return None

    # Tolerances for each frequency
    if 5 <= avg_interval <= 9:
        return "weekly"
    elif 12 <= avg_interval <= 17:
        return "bi-weekly"
    elif 26 <= avg_interval <= 35:
        return "monthly"
    elif 85 <= avg_interval <= 100:
        return "quarterly"
    elif 350 <= avg_interval <= 380:
        return "yearly"

    return None


def calculate_next_expected_date(
    last_date: date,
    frequency: str
) -> Optional[date]:
    """
    Calculate next expected payment date.

    Args:
        last_date: Last transaction date
        frequency: Payment frequency

    Returns:
        Expected next date or None
    """
    if isinstance(last_date, str):
        last_date = datetime.strptime(last_date, "%Y-%m-%d").date()

    intervals = {
        "weekly": 7,
        "bi-weekly": 14,
        "monthly": 30,
        "quarterly": 90,
        "yearly": 365
    }

    days = intervals.get(frequency)
    if days:
        return last_date + timedelta(days=days)
    return None


async def detect_recurring_payments(
    user_id: int,
    db: Session,
    min_occurrences: int = 2,
    lookback_days: int = 180,
    force_refresh: bool = False
) -> List[Dict]:
    """
    Detect recurring payments for a user.

    Args:
        user_id: User ID
        db: Database session
        min_occurrences: Minimum transactions to consider recurring
        lookback_days: How far back to look for patterns
        force_refresh: If True, re-analyze even if cached

    Returns:
        List of recurring payment dicts
    """
    logger.info("=" * 80)
    logger.info(f"Starting recurring payment detection for user {user_id}")
    logger.info(f"   Min occurrences: {min_occurrences}")
    logger.info(f"   Lookback days: {lookback_days}")
    logger.info(f"   Force refresh: {force_refresh}")
    logger.info("=" * 80)

    # If not force refresh, return cached results (expenses only)
    if not force_refresh:
        cached = db.query(RecurringCache).filter(
            RecurringCache.user_id == user_id,
            RecurringCache.is_recurring == True,
            RecurringCache.category != "Income"  # Exclude income entries
        ).all()

        if cached:
            logger.info(f"Returning {len(cached)} cached recurring payments")
            return [_cache_to_dict(c) for c in cached]

    # Get expense transactions within lookback period (expenses only - negative amounts)
    cutoff_date = datetime.utcnow().date() - timedelta(days=lookback_days)

    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.date >= cutoff_date,
        Transaction.amount < 0  # Only expenses (negative amounts), not income
    ).order_by(Transaction.date.desc()).all()

    logger.info(f"Found {len(transactions)} expense transactions in lookback period")

    # Group by merchant_key
    merchant_groups = defaultdict(list)
    for txn in transactions:
        merchant_groups[txn.merchant_key].append({
            "id": txn.id,
            "date": txn.date.isoformat() if hasattr(txn.date, 'isoformat') else str(txn.date),
            "amount": txn.amount,
            "note": txn.note_user or "",
            "description_raw": txn.description_raw,
            "category": txn.category
        })

    # Filter to merchants with enough occurrences
    candidates = {
        key: txns for key, txns in merchant_groups.items()
        if len(txns) >= min_occurrences
    }

    logger.info(f"Found {len(candidates)} merchants with {min_occurrences}+ transactions")

    if not candidates:
        return []

    # Prepare data for AI analysis
    merchants_to_analyze = []
    for merchant_key, txns in candidates.items():
        stats = calculate_transaction_stats(txns)

        # Get merchant name from first transaction
        merchant_name = txns[0].get("description_raw", merchant_key)
        category = txns[0].get("category", "Other")

        merchants_to_analyze.append({
            "merchant_key": merchant_key,
            "merchant_name": merchant_name,
            "category": category,
            "transactions": txns,
            "stats": stats
        })

    # Call AI for verification
    client = get_openai_client()
    if not client:
        logger.warning("No OpenRouter API key - using algorithm-only detection")
        return _algorithm_only_detection(merchants_to_analyze, user_id, db)

    try:
        ai_results = await _call_ai_for_detection(client, merchants_to_analyze)
        return _process_ai_results(ai_results, merchants_to_analyze, user_id, db)
    except Exception as e:
        logger.error(f"AI detection failed: {e}", exc_info=True)
        return _algorithm_only_detection(merchants_to_analyze, user_id, db)


async def _call_ai_for_detection(
    client: OpenAI,
    merchants: List[Dict]
) -> List[Dict]:
    """
    Call OpenRouter API to detect recurring patterns.

    Args:
        client: OpenAI client
        merchants: List of merchant data with transactions

    Returns:
        List of AI detection results
    """
    logger.info(f"Calling AI to analyze {len(merchants)} merchants...")

    # Use batch prompt for efficiency
    prompt = get_batch_recurring_detection_prompt(merchants)

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
        start_idx = content.find('[')
        end_idx = content.rfind(']') + 1

        if start_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx:end_idx]
            results = json.loads(json_str)
            logger.info(f"AI returned {len(results)} results")
            return results
        else:
            logger.error("No JSON array found in AI response")
            return []

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response: {e}")
        logger.error(f"Response content: {content[:500]}")
        return []


def _process_ai_results(
    ai_results: List[Dict],
    merchants: List[Dict],
    user_id: int,
    db: Session
) -> List[Dict]:
    """
    Process AI results and update cache.

    Args:
        ai_results: Results from AI
        merchants: Original merchant data
        user_id: User ID
        db: Database session

    Returns:
        List of recurring payment dicts
    """
    recurring_payments = []

    # Create lookup for merchant data
    merchant_data = {m["merchant_key"]: m for m in merchants}

    for result in ai_results:
        merchant_key = result.get("merchant_key")
        if not merchant_key or merchant_key not in merchant_data:
            continue

        merchant = merchant_data[merchant_key]
        is_recurring = result.get("is_recurring", False)
        same_transaction = result.get("same_transaction", True)

        # Only consider it recurring if both conditions are true
        if not (is_recurring and same_transaction):
            is_recurring = False

        # Update or create cache entry
        cache_entry = db.query(RecurringCache).filter(
            RecurringCache.user_id == user_id,
            RecurringCache.merchant_key == merchant_key
        ).first()

        if cache_entry:
            # Update existing
            cache_entry.is_recurring = is_recurring
            cache_entry.frequency = result.get("frequency")
            cache_entry.typical_amount = abs(result.get("typical_amount") or 0)
            cache_entry.amount_variance = result.get("amount_variance", "variable")
            cache_entry.confidence = result.get("confidence", "low")
            cache_entry.ai_verified = True
            cache_entry.ai_notes = result.get("notes", "")
            cache_entry.last_analyzed_at = datetime.utcnow()

            # Update pattern data from merchant info
            stats = merchant["stats"]
            txns = merchant["transactions"]
            cache_entry.transaction_count = stats["count"]
            cache_entry.category = merchant["category"]
            cache_entry.merchant_name = merchant["merchant_name"]

            if txns:
                sorted_txns = sorted(txns, key=lambda x: x["date"])
                cache_entry.first_transaction_date = datetime.strptime(
                    sorted_txns[0]["date"], "%Y-%m-%d"
                ).date() if isinstance(sorted_txns[0]["date"], str) else sorted_txns[0]["date"]
                cache_entry.last_transaction_date = datetime.strptime(
                    sorted_txns[-1]["date"], "%Y-%m-%d"
                ).date() if isinstance(sorted_txns[-1]["date"], str) else sorted_txns[-1]["date"]

            # Parse next expected date
            next_date_str = result.get("next_expected_date")
            if next_date_str:
                try:
                    cache_entry.next_expected_date = datetime.strptime(
                        next_date_str, "%Y-%m-%d"
                    ).date()
                except ValueError:
                    cache_entry.next_expected_date = None
        else:
            # Create new entry
            stats = merchant["stats"]
            txns = merchant["transactions"]

            first_date = None
            last_date = None
            if txns:
                sorted_txns = sorted(txns, key=lambda x: x["date"])
                first_date = datetime.strptime(
                    sorted_txns[0]["date"], "%Y-%m-%d"
                ).date() if isinstance(sorted_txns[0]["date"], str) else sorted_txns[0]["date"]
                last_date = datetime.strptime(
                    sorted_txns[-1]["date"], "%Y-%m-%d"
                ).date() if isinstance(sorted_txns[-1]["date"], str) else sorted_txns[-1]["date"]

            next_date = None
            next_date_str = result.get("next_expected_date")
            if next_date_str:
                try:
                    next_date = datetime.strptime(next_date_str, "%Y-%m-%d").date()
                except ValueError:
                    pass

            cache_entry = RecurringCache(
                user_id=user_id,
                merchant_key=merchant_key,
                merchant_name=merchant["merchant_name"],
                is_recurring=is_recurring,
                frequency=result.get("frequency"),
                typical_amount=abs(result.get("typical_amount") or 0),
                amount_variance=result.get("amount_variance", "variable"),
                confidence=result.get("confidence", "low"),
                category=merchant["category"],
                transaction_count=stats["count"],
                first_transaction_date=first_date,
                last_transaction_date=last_date,
                next_expected_date=next_date,
                ai_verified=True,
                ai_notes=result.get("notes", ""),
                last_analyzed_at=datetime.utcnow()
            )
            db.add(cache_entry)

        if is_recurring:
            recurring_payments.append(_cache_to_dict(cache_entry))

    # Commit changes
    try:
        db.commit()
        logger.info(f"Cached {len(ai_results)} analysis results, {len(recurring_payments)} are recurring")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to commit cache: {e}", exc_info=True)

    return recurring_payments


def _algorithm_only_detection(
    merchants: List[Dict],
    user_id: int,
    db: Session
) -> List[Dict]:
    """
    Fallback detection using algorithm only (no AI).

    Args:
        merchants: Merchant data with transactions
        user_id: User ID
        db: Database session

    Returns:
        List of recurring payment dicts
    """
    logger.info("Using algorithm-only detection (no AI)")
    recurring_payments = []

    for merchant in merchants:
        stats = merchant["stats"]
        frequency = detect_frequency_from_interval(stats["avg_interval_days"])

        # Consider recurring if:
        # 1. Has detectable frequency
        # 2. Low amount variance (< 20%)
        # 3. At least 2 transactions
        is_recurring = (
            frequency is not None and
            stats["amount_variance_pct"] < 20 and
            stats["count"] >= 2
        )

        if is_recurring:
            txns = merchant["transactions"]
            sorted_txns = sorted(txns, key=lambda x: x["date"])

            last_date = datetime.strptime(
                sorted_txns[-1]["date"], "%Y-%m-%d"
            ).date() if isinstance(sorted_txns[-1]["date"], str) else sorted_txns[-1]["date"]

            next_date = calculate_next_expected_date(last_date, frequency)

            first_date = datetime.strptime(
                sorted_txns[0]["date"], "%Y-%m-%d"
            ).date() if isinstance(sorted_txns[0]["date"], str) else sorted_txns[0]["date"]

            # Update or create cache
            cache_entry = db.query(RecurringCache).filter(
                RecurringCache.user_id == user_id,
                RecurringCache.merchant_key == merchant["merchant_key"]
            ).first()

            if cache_entry:
                cache_entry.is_recurring = True
                cache_entry.frequency = frequency
                cache_entry.typical_amount = stats["amount_min"]
                cache_entry.amount_variance = "fixed" if stats["amount_variance_pct"] < 5 else "variable"
                cache_entry.confidence = "medium"
                cache_entry.ai_verified = False
                cache_entry.transaction_count = stats["count"]
                cache_entry.first_transaction_date = first_date
                cache_entry.last_transaction_date = last_date
                cache_entry.next_expected_date = next_date
                cache_entry.last_analyzed_at = datetime.utcnow()
            else:
                cache_entry = RecurringCache(
                    user_id=user_id,
                    merchant_key=merchant["merchant_key"],
                    merchant_name=merchant["merchant_name"],
                    is_recurring=True,
                    frequency=frequency,
                    typical_amount=stats["amount_min"],
                    amount_variance="fixed" if stats["amount_variance_pct"] < 5 else "variable",
                    confidence="medium",
                    category=merchant["category"],
                    transaction_count=stats["count"],
                    first_transaction_date=first_date,
                    last_transaction_date=last_date,
                    next_expected_date=next_date,
                    ai_verified=False,
                    ai_notes="Detected by algorithm",
                    last_analyzed_at=datetime.utcnow()
                )
                db.add(cache_entry)

            recurring_payments.append(_cache_to_dict(cache_entry))

    try:
        db.commit()
        logger.info(f"Algorithm detected {len(recurring_payments)} recurring payments")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to commit: {e}", exc_info=True)

    return recurring_payments


def _cache_to_dict(cache: RecurringCache) -> Dict:
    """Convert cache entry to dict."""
    return {
        "merchant_key": cache.merchant_key,
        "merchant_name": cache.merchant_name or cache.merchant_key,
        "category": cache.category or "Other",
        "frequency": cache.frequency or "monthly",
        "typical_amount": cache.typical_amount or 0,
        "amount_variance": cache.amount_variance or "variable",
        "confidence": cache.confidence or "low",
        "transaction_count": cache.transaction_count or 0,
        "last_transaction_date": cache.last_transaction_date.isoformat() if cache.last_transaction_date else None,
        "next_expected_date": cache.next_expected_date.isoformat() if cache.next_expected_date else None,
        "ai_notes": cache.ai_notes
    }


def get_cached_recurring_payments(user_id: int, db: Session) -> List[Dict]:
    """
    Get cached recurring payments for a user (expenses only).

    Args:
        user_id: User ID
        db: Database session

    Returns:
        List of recurring payment dicts
    """
    cached = db.query(RecurringCache).filter(
        RecurringCache.user_id == user_id,
        RecurringCache.is_recurring == True,
        RecurringCache.category != "Income"  # Exclude income entries
    ).all()

    return [_cache_to_dict(c) for c in cached]


def get_upcoming_payments(
    user_id: int,
    db: Session,
    days: int = 7
) -> List[Dict]:
    """
    Get upcoming recurring payments (expenses only).

    Args:
        user_id: User ID
        db: Database session
        days: Look ahead days

    Returns:
        List of upcoming payment dicts
    """
    today = datetime.utcnow().date()
    future = today + timedelta(days=days)

    upcoming = db.query(RecurringCache).filter(
        RecurringCache.user_id == user_id,
        RecurringCache.is_recurring == True,
        RecurringCache.category != "Income",  # Exclude income entries
        RecurringCache.next_expected_date != None,
        RecurringCache.next_expected_date >= today,
        RecurringCache.next_expected_date <= future
    ).order_by(RecurringCache.next_expected_date).all()

    result = []
    for cache in upcoming:
        days_until = (cache.next_expected_date - today).days
        result.append({
            "merchant_key": cache.merchant_key,
            "merchant_name": cache.merchant_name or cache.merchant_key,
            "amount": cache.typical_amount or 0,
            "expected_date": cache.next_expected_date.isoformat(),
            "days_until": days_until
        })

    return result

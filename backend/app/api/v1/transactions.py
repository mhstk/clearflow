from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional, List
from datetime import date, datetime, timedelta
from collections import defaultdict
from dateutil.relativedelta import relativedelta
import asyncio
import time
import logging

from app.api.deps import get_db, get_current_user_id
from app.models.transaction import Transaction
from app.models.account import Account
from app.db.session import SessionLocal
from app.schemas.transaction import (
    TransactionResponse,
    TransactionViewResponse,
    TransactionUpdateNote,
    TransactionUpdateCategory,
    TransactionUpdate,
    TransactionManualCreate,
    CSVUploadResponse,
    TransactionAggregates,
    DayAggregate,
    DateRangeEnum,
    CategoryResponse,
    DashboardStats,
    RecurringTransaction,
    RecurringTransactionsResponse
)
from app.services.csv_import import parse_rbc_csv
from app.services.auto_categorization import categorize_transactions_batch
from app.core.logging_config import get_categorization_logger

router = APIRouter()
logger = get_categorization_logger()


def _categorize_transactions_in_background(
    transaction_ids: List[int],
    user_id: int,
    batch_size: int = 10,
    max_retries: int = 2
):
    """
    Background task to categorize transactions in batches with automatic retry.

    This runs in a thread pool to avoid blocking the FastAPI event loop,
    allowing the server to continue handling other requests.

    If a batch has failures, failed transactions will be automatically retried
    up to max_retries times.

    Args:
        transaction_ids: List of transaction IDs to categorize
        user_id: User ID
        batch_size: Number of transactions to process per batch (default: 10)
        max_retries: Maximum number of retry attempts for failed transactions (default: 2)
    """
    logger.info("=" * 80)
    logger.info(f"🤖 Starting background categorization for {len(transaction_ids)} transactions")
    logger.info(f"   Batch size: {batch_size}")
    logger.info(f"   Total batches: {(len(transaction_ids) + batch_size - 1) // batch_size}")
    logger.info(f"   Max retries: {max_retries}")
    logger.info("=" * 80)

    # Create a new database session for background task
    db = SessionLocal()

    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Process in batches
        for i in range(0, len(transaction_ids), batch_size):
            batch = transaction_ids[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(transaction_ids) + batch_size - 1) // batch_size

            logger.info(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} transactions)...")

            # Track which transactions need to be retried
            current_batch = batch
            retry_count = 0

            while retry_count <= max_retries:
                try:
                    # Categorize this batch (run async function in this thread's event loop)
                    result = loop.run_until_complete(
                        categorize_transactions_batch(
                            transaction_ids=current_batch,
                            db=db,
                            user_id=user_id,
                            auto_apply=True
                        )
                    )

                    successful = result['successful']
                    total = result['total_processed']
                    failed = result['failed']

                    if retry_count == 0:
                        logger.info(f"   ✅ Batch {batch_num} complete: {successful}/{total} successful")
                    else:
                        logger.info(f"   🔄 Retry {retry_count} complete: {successful}/{total} successful")

                    # Check if we need to retry
                    if failed == 0 or successful == total:
                        # All successful, move to next batch
                        break
                    elif retry_count < max_retries:
                        # Get failed transaction IDs for retry
                        failed_txn_ids = [
                            r['transaction_id']
                            for r in result['results']
                            if r.get('error') is not None
                        ]

                        if failed_txn_ids:
                            retry_count += 1
                            current_batch = failed_txn_ids
                            logger.warning(f"   ⚠️  {failed} failed, retrying {len(failed_txn_ids)} transactions (attempt {retry_count}/{max_retries})...")
                            time.sleep(2)  # Longer delay before retry
                        else:
                            break
                    else:
                        # Max retries reached
                        logger.error(f"   ❌ Max retries reached. {failed} transactions still failed.")
                        break

                except Exception as e:
                    if retry_count < max_retries:
                        retry_count += 1
                        logger.error(f"   ❌ Batch {batch_num} error: {e}")
                        logger.info(f"   🔄 Retrying batch (attempt {retry_count}/{max_retries})...")
                        time.sleep(2)
                    else:
                        logger.error(f"   ❌ Batch {batch_num} failed after {max_retries} retries: {e}")
                        break

            # Delay between batches to avoid rate limiting
            if i + batch_size < len(transaction_ids):
                time.sleep(1)

        logger.info("=" * 80)
        logger.info("✅ Background categorization complete!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ Background categorization error: {e}", exc_info=True)
        logger.error("=" * 80)
    finally:
        db.close()
        loop.close()


@router.post("/upload_csv", response_model=CSVUploadResponse)
async def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    account_id: Optional[int] = Form(None),
    auto_categorize: bool = Form(False),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Upload and parse CSV file containing transactions.

    Parameters:
    - file: CSV file to upload
    - account_id: Optional account ID to associate transactions with
    - auto_categorize: Whether to automatically categorize transactions with AI (default: False)

    If auto_categorize is True, transactions will be categorized in the BACKGROUND.
    - The API responds immediately after uploading
    - Categorization happens in batches of 10
    - Refresh the transactions page to see progress
    - Check server logs for categorization status
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    # Read file content
    content = await file.read()

    # Parse CSV
    try:
        inserted, skipped, final_account_id = parse_rbc_csv(
            content, db, user_id, account_id
        )

        # Auto-categorize if requested (in background)
        if auto_categorize and inserted > 0:
            # Get the IDs of newly inserted transactions
            new_transactions = db.query(Transaction).filter(
                Transaction.account_id == final_account_id,
                Transaction.user_id == user_id,
                Transaction.category == "Uncategorized"
            ).order_by(Transaction.created_at.desc()).limit(inserted).all()

            if new_transactions:
                transaction_ids = [t.id for t in new_transactions]

                # Add background task for categorization
                background_tasks.add_task(
                    _categorize_transactions_in_background,
                    transaction_ids,
                    user_id,
                    batch_size=10  # Process 10 at a time
                )

                logger.info(f"📤 CSV uploaded: {inserted} transactions")
                logger.info(f"🤖 Queued {len(transaction_ids)} transactions for background categorization")

        return CSVUploadResponse(
            inserted_count=inserted,
            skipped_count=skipped,
            account_id=final_account_id
        )
    except Exception as e:
        logger.error(f"Error parsing CSV: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Failed to parse CSV file. Please check the format and try again.")


@router.post("/", response_model=TransactionResponse)
def create_transaction(
    transaction: TransactionManualCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Manually create a new transaction.

    Parameters:
    - date: Transaction date
    - amount: Positive for income, negative for expense
    - description: Merchant/description
    - category: Category name (default: Uncategorized)
    - note: Optional user note
    - account_id: Optional account ID (uses default if not provided)
    """
    # Get or create a default account for the user if not provided
    account_id = transaction.account_id
    if not account_id:
        # Try to get existing account
        account = db.query(Account).filter(Account.user_id == user_id).first()
        if not account:
            # Create a default account
            account = Account(
                user_id=user_id,
                name="Default Account",
                institution="Manual",
                account_type="checking",
                currency="CAD"
            )
            db.add(account)
            db.commit()
            db.refresh(account)
        account_id = account.id

    # Generate merchant_key from description (lowercase, no special chars)
    merchant_key = ''.join(c.lower() for c in transaction.description if c.isalnum() or c.isspace()).strip()
    merchant_key = '_'.join(merchant_key.split())[:50]  # Max 50 chars

    # Create the transaction
    new_transaction = Transaction(
        user_id=user_id,
        account_id=account_id,
        date=transaction.date,
        description_raw=transaction.description,
        merchant_key=merchant_key,
        amount=transaction.amount,
        currency="CAD",
        category=transaction.category,
        category_source="user",  # Mark as user-created
        note_user=transaction.note
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return new_transaction


@router.get("/view", response_model=TransactionViewResponse)
def get_transactions_view(
    account_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    date_range: Optional[DateRangeEnum] = None,
    category: Optional[List[str]] = Query(None),
    merchant_query: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get filtered transactions with aggregates.

    This endpoint returns both paginated transaction rows and aggregated statistics
    computed on the filtered dataset (Excel-style behavior).

    Date filtering options:
    - Use date_range for preset ranges: "this_month", "last_month", "last_3_months", etc.
    - Or use start_date and end_date for custom ranges
    - date_range takes precedence over start_date/end_date
    """
    # Apply date_range if provided
    if date_range:
        start_date, end_date = _get_date_range(date_range)

    # Build base query
    query = db.query(Transaction).filter(Transaction.user_id == user_id)

    # Apply filters
    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)

    if start_date is not None:
        query = query.filter(Transaction.date >= start_date)

    if end_date is not None:
        query = query.filter(Transaction.date <= end_date)

    if category is not None and len(category) > 0:
        query = query.filter(Transaction.category.in_(category))

    if merchant_query is not None:
        search_pattern = f"%{merchant_query}%"
        query = query.filter(
            or_(
                Transaction.description_raw.ilike(search_pattern),
                Transaction.note_user.ilike(search_pattern),
                Transaction.merchant_key.ilike(search_pattern)
            )
        )

    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)

    if max_amount is not None:
        query = query.filter(Transaction.amount <= max_amount)

    # Get total count for pagination
    total_count = query.count()

    # Get filtered transactions for aggregates (before pagination)
    all_filtered = query.all()

    # Apply pagination
    offset = (page - 1) * page_size
    paginated_query = query.order_by(Transaction.date.desc()).offset(offset).limit(page_size)
    rows = paginated_query.all()

    # Compute aggregates on ALL filtered data
    aggregates = _compute_aggregates(all_filtered)

    # Build response
    return TransactionViewResponse(
        filters={
            "account_id": account_id,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "date_range": date_range.value if date_range else None,
            "category": category,
            "merchant_query": merchant_query,
            "min_amount": min_amount,
            "max_amount": max_amount
        },
        pagination={
            "page": page,
            "page_size": page_size,
            "total_count": total_count
        },
        rows=[TransactionResponse.model_validate(row) for row in rows],
        aggregates=aggregates
    )


def _compute_aggregates(transactions: List[Transaction]) -> TransactionAggregates:
    """Compute aggregate statistics on a list of transactions"""
    total_spent = 0.0
    total_income = 0.0
    by_category = defaultdict(float)
    by_day = defaultdict(float)

    for txn in transactions:
        if txn.amount < 0:
            total_spent += txn.amount
        else:
            total_income += txn.amount

        by_category[txn.category] += txn.amount
        by_day[txn.date.isoformat()] += txn.amount

    # Convert by_day to list of DayAggregate (descending order)
    day_list = [
        DayAggregate(date=day, net=net)
        for day, net in sorted(by_day.items(), reverse=True)
    ]

    return TransactionAggregates(
        total_spent=total_spent,
        total_income=total_income,
        by_category=dict(by_category),
        by_day=day_list
    )


def _get_date_range(date_range: DateRangeEnum) -> tuple[date, date]:
    """Convert date_range enum to start_date and end_date"""
    today = date.today()

    if date_range == DateRangeEnum.last_7_days:
        start = today - timedelta(days=7)
        end = today
    elif date_range == DateRangeEnum.last_30_days:
        start = today - timedelta(days=30)
        end = today
    elif date_range == DateRangeEnum.this_month:
        start = date(today.year, today.month, 1)
        end = today
    elif date_range == DateRangeEnum.last_month:
        first_of_month = date(today.year, today.month, 1)
        end = first_of_month - timedelta(days=1)
        start = date(end.year, end.month, 1)
    elif date_range == DateRangeEnum.last_3_months:
        start = today - relativedelta(months=3)
        end = today
    elif date_range == DateRangeEnum.last_6_months:
        start = today - relativedelta(months=6)
        end = today
    elif date_range == DateRangeEnum.this_year:
        start = date(today.year, 1, 1)
        end = today
    else:  # all_time
        start = date(2000, 1, 1)
        end = today

    return start, end


@router.patch("/{transaction_id}/note", response_model=TransactionResponse)
def update_transaction_note(
    transaction_id: int,
    update: TransactionUpdateNote,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Update user note for a transaction"""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    transaction.note_user = update.note_user
    db.commit()
    db.refresh(transaction)

    return transaction


@router.patch("/{transaction_id}/category", response_model=TransactionResponse)
def update_transaction_category(
    transaction_id: int,
    update: TransactionUpdateCategory,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Update category for a transaction"""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    transaction.category = update.category
    transaction.category_source = "user"
    db.commit()
    db.refresh(transaction)

    return transaction


@router.patch("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    update: TransactionUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Update transaction date and/or amount"""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if update.date is not None:
        transaction.date = update.date

    if update.amount is not None:
        transaction.amount = update.amount

    db.commit()
    db.refresh(transaction)

    return transaction


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get a single transaction by ID.

    Returns 404 if transaction not found or doesn't belong to user.
    """
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return transaction


@router.delete("/batch")
def delete_transactions_batch(
    transaction_ids: List[int],
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Delete multiple transactions by IDs.

    Only deletes transactions that belong to the authenticated user.
    Returns count of deleted transactions.
    """
    if not transaction_ids:
        raise HTTPException(status_code=400, detail="No transaction IDs provided")

    # Delete only transactions belonging to this user
    deleted_count = db.query(Transaction).filter(
        Transaction.id.in_(transaction_ids),
        Transaction.user_id == user_id
    ).delete(synchronize_session=False)

    db.commit()

    return {"deleted_count": deleted_count}


@router.get("/categories/list", response_model=List[CategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get all categories used in user's transactions with counts and totals.

    Returns a list of categories sorted by total amount (descending).
    """
    # Query to get category stats
    results = db.query(
        Transaction.category,
        func.count(Transaction.id).label('count'),
        func.sum(Transaction.amount).label('total_amount')
    ).filter(
        Transaction.user_id == user_id
    ).group_by(
        Transaction.category
    ).order_by(
        func.sum(Transaction.amount).desc()
    ).all()

    return [
        CategoryResponse(
            category=row.category,
            count=row.count,
            total_amount=row.total_amount
        )
        for row in results
    ]


@router.get("/recurring/detect", response_model=RecurringTransactionsResponse)
def detect_recurring_transactions(
    min_occurrences: int = 3,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Detect recurring transactions based on merchant patterns.

    A transaction is considered recurring if:
    - Same merchant_key appears multiple times (>= min_occurrences)
    - Amounts are relatively consistent
    - Time intervals are relatively regular

    Parameters:
    - min_occurrences: Minimum number of transactions to consider as recurring (default: 3)
    """
    # Get all transactions grouped by merchant
    merchant_groups = db.query(
        Transaction.merchant_key,
        func.count(Transaction.id).label('count'),
        func.avg(Transaction.amount).label('avg_amount'),
        func.max(Transaction.date).label('last_date')
    ).filter(
        Transaction.user_id == user_id
    ).group_by(
        Transaction.merchant_key
    ).having(
        func.count(Transaction.id) >= min_occurrences
    ).all()

    recurring_list = []

    for group in merchant_groups:
        # Get sample transactions for this merchant
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.merchant_key == group.merchant_key
        ).order_by(Transaction.date.desc()).limit(10).all()

        if not transactions:
            continue

        # Calculate frequency
        if len(transactions) >= 2:
            dates = sorted([t.date for t in transactions])
            intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
            avg_interval = sum(intervals) / len(intervals) if intervals else 0

            if avg_interval <= 7:
                frequency = "weekly"
            elif avg_interval <= 35:
                frequency = "monthly"
            elif avg_interval <= 100:
                frequency = "quarterly"
            else:
                frequency = "irregular"
        else:
            frequency = "unknown"

        # Get merchant name from most recent transaction
        merchant_name = transactions[0].description_raw if transactions else group.merchant_key
        category = transactions[0].category if transactions else "Uncategorized"

        # Estimate next expected date
        next_expected = None
        if frequency in ["weekly", "monthly", "quarterly"] and transactions:
            last_date = transactions[0].date
            if frequency == "weekly":
                next_expected = last_date + timedelta(days=7)
            elif frequency == "monthly":
                next_expected = last_date + relativedelta(months=1)
            elif frequency == "quarterly":
                next_expected = last_date + relativedelta(months=3)

        recurring_list.append(
            RecurringTransaction(
                merchant_key=group.merchant_key,
                merchant_name=merchant_name[:50],  # Truncate to 50 chars
                category=category,
                average_amount=float(group.avg_amount),
                frequency=frequency,
                transaction_count=group.count,
                last_transaction_date=group.last_date,
                next_expected_date=next_expected,
                sample_transactions=[t.id for t in transactions[:5]]
            )
        )

    # Sort by transaction count (descending)
    recurring_list.sort(key=lambda x: x.transaction_count, reverse=True)

    return RecurringTransactionsResponse(
        recurring=recurring_list,
        total_count=len(recurring_list)
    )

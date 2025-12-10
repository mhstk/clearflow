from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from dateutil.relativedelta import relativedelta

from app.api.deps import get_db, get_current_user_id
from app.models.transaction import Transaction
from app.models.account import Account
from app.schemas.transaction import DashboardStats, DateRangeEnum
from app.api.v1.transactions import _get_date_range

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    date_range: DateRangeEnum = DateRangeEnum.last_30_days,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get dashboard statistics for the current user.

    Parameters:
    - date_range: Time period for stats (default: last_30_days)

    Returns:
    - total_balance: Net balance (income - expenses)
    - total_expenses: Total spending (negative amounts)
    - total_income: Total income (positive amounts)
    - savings: Same as total_balance
    - savings_rate: Percentage of income saved
    - transaction_count: Total number of transactions
    - account_count: Number of accounts
    - top_category: Category with most spending
    - top_category_amount: Amount spent in top category
    """
    # Get date range
    start_date, end_date = _get_date_range(date_range)

    # Get all transactions for the selected period
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).all()

    # Calculate totals
    total_expenses = sum(t.amount for t in transactions if t.amount < 0)
    total_income = sum(t.amount for t in transactions if t.amount > 0)
    total_balance = total_income + total_expenses  # expenses are negative
    savings = total_balance

    # Calculate savings rate
    savings_rate = (savings / total_income * 100) if total_income > 0 else 0.0

    # Get transaction count
    transaction_count = len(transactions)

    # Get account count
    account_count = db.query(func.count(Account.id)).filter(
        Account.user_id == user_id
    ).scalar() or 0

    # Get top spending category
    category_totals = {}
    for t in transactions:
        if t.amount < 0:  # Only count expenses
            category_totals[t.category] = category_totals.get(t.category, 0) + t.amount

    top_category = None
    top_category_amount = 0.0

    if category_totals:
        # Get category with most spending (most negative)
        top_category = min(category_totals.items(), key=lambda x: x[1])[0]
        top_category_amount = abs(category_totals[top_category])

    return DashboardStats(
        total_balance=total_balance,
        total_expenses=abs(total_expenses),
        total_income=total_income,
        savings=savings,
        savings_rate=round(savings_rate, 2),
        transaction_count=transaction_count,
        account_count=account_count,
        top_category=top_category,
        top_category_amount=top_category_amount
    )


@router.get("/stats/period", response_model=DashboardStats)
def get_dashboard_stats_period(
    months: int = 1,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get dashboard statistics for a specific period.

    Parameters:
    - months: Number of months to look back (default: 1)

    Returns the same stats as /stats but for the specified period.
    """
    # Calculate date range
    today = date.today()
    start_date = today - relativedelta(months=months)

    # Get all transactions for the period
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.date >= start_date
    ).all()

    # Calculate totals
    total_expenses = sum(t.amount for t in transactions if t.amount < 0)
    total_income = sum(t.amount for t in transactions if t.amount > 0)
    total_balance = total_income + total_expenses
    savings = total_balance

    # Calculate savings rate
    savings_rate = (savings / total_income * 100) if total_income > 0 else 0.0

    # Get transaction count
    transaction_count = len(transactions)

    # Get account count
    account_count = db.query(func.count(Account.id)).filter(
        Account.user_id == user_id
    ).scalar() or 0

    # Get top spending category
    category_totals = {}
    for t in transactions:
        if t.amount < 0:
            category_totals[t.category] = category_totals.get(t.category, 0) + t.amount

    top_category = None
    top_category_amount = 0.0

    if category_totals:
        top_category = min(category_totals.items(), key=lambda x: x[1])[0]
        top_category_amount = abs(category_totals[top_category])

    return DashboardStats(
        total_balance=total_balance,
        total_expenses=abs(total_expenses),
        total_income=total_income,
        savings=savings,
        savings_rate=round(savings_rate, 2),
        transaction_count=transaction_count,
        account_count=account_count,
        top_category=top_category,
        top_category_amount=top_category_amount
    )

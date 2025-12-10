from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List, Dict
from enum import Enum


class TransactionBase(BaseModel):
    date: date
    description_raw: str
    merchant_key: str
    amount: float
    currency: str = "CAD"
    category: str = "Uncategorized"
    category_source: str = "uncategorized"
    note_user: Optional[str] = None


class TransactionCreate(TransactionBase):
    account_id: int
    user_id: int


class TransactionManualCreate(BaseModel):
    """Schema for manually creating a transaction via the UI"""
    date: date
    amount: float  # positive for income, negative for expense
    description: str  # merchant/description entered by user
    category: str = "Uncategorized"
    note: Optional[str] = None
    account_id: Optional[int] = None  # optional, will use default if not provided


class TransactionResponse(TransactionBase):
    id: int
    account_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionUpdateNote(BaseModel):
    note_user: str


class TransactionUpdateCategory(BaseModel):
    category: str


class TransactionUpdate(BaseModel):
    date: Optional[date] = None
    amount: Optional[float] = None


class DateRangeEnum(str, Enum):
    last_7_days = "last_7_days"
    last_30_days = "last_30_days"
    this_month = "this_month"
    last_month = "last_month"
    last_3_months = "last_3_months"
    last_6_months = "last_6_months"
    this_year = "this_year"
    all_time = "all_time"


class TransactionFilters(BaseModel):
    account_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    date_range: Optional[DateRangeEnum] = None
    category: Optional[List[str]] = None
    merchant_query: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    page: int = 1
    page_size: int = 50


class DayAggregate(BaseModel):
    date: str
    net: float


class TransactionAggregates(BaseModel):
    total_spent: float
    total_income: float
    by_category: Dict[str, float]
    by_day: List[DayAggregate]


class TransactionViewResponse(BaseModel):
    filters: dict
    pagination: dict
    rows: List[TransactionResponse]
    aggregates: TransactionAggregates


class CSVUploadResponse(BaseModel):
    inserted_count: int
    skipped_count: int
    account_id: int


class CategoryResponse(BaseModel):
    category: str
    count: int
    total_amount: float


class DashboardStats(BaseModel):
    total_balance: float
    total_expenses: float
    total_income: float
    savings: float
    savings_rate: float
    transaction_count: int
    account_count: int
    top_category: Optional[str] = None
    top_category_amount: float = 0.0


class RecurringTransaction(BaseModel):
    merchant_key: str
    merchant_name: str
    category: str
    average_amount: float
    frequency: str
    transaction_count: int
    last_transaction_date: date
    next_expected_date: Optional[date] = None
    sample_transactions: List[int]


class RecurringTransactionsResponse(BaseModel):
    recurring: List[RecurringTransaction]
    total_count: int

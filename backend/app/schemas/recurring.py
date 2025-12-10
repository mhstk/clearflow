"""
Pydantic schemas for recurring payments API.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date, datetime


class RecurringPayment(BaseModel):
    """Individual recurring payment details."""
    merchant_key: str
    merchant_name: str
    category: str
    frequency: str  # weekly, bi-weekly, monthly, quarterly, yearly
    typical_amount: float
    amount_variance: str  # fixed, variable
    confidence: str  # high, medium, low
    transaction_count: int
    last_transaction_date: date
    next_expected_date: Optional[date] = None
    ai_notes: Optional[str] = None

    class Config:
        from_attributes = True


class RecurringPaymentsResponse(BaseModel):
    """Response for listing recurring payments."""
    recurring_payments: List[RecurringPayment]
    total_count: int
    total_monthly: float
    total_yearly: float


class RecurringInsight(BaseModel):
    """AI-generated insight about recurring payments."""
    type: str  # cost_analysis, optimization, anomaly, prediction
    title: str
    message: str
    priority: str  # info, suggestion, warning


class UpcomingPayment(BaseModel):
    """Upcoming payment prediction."""
    merchant_key: str
    merchant_name: str
    amount: float
    expected_date: date
    days_until: int


class RecurringInsightsResponse(BaseModel):
    """Response for recurring insights endpoint."""
    summary: Dict[str, Any]
    insights: List[RecurringInsight]
    upcoming: List[UpcomingPayment]
    generated_at: datetime


class AnalyzeResponse(BaseModel):
    """Response for triggering analysis."""
    message: str
    status: str  # started, already_running, completed
    merchants_to_analyze: int

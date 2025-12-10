"""
Recurring insights cache model for storing AI-generated insights.
"""

from sqlalchemy import Column, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class RecurringInsights(Base):
    __tablename__ = "recurring_insights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # Stored insights (JSON)
    summary = Column(JSON, nullable=False)  # {total_monthly, total_yearly, count, percentage_of_expenses, by_category}
    insights = Column(JSON, nullable=False)  # [{type, title, message, priority}, ...]
    upcoming = Column(JSON, nullable=False)  # [{merchant, amount, date, days_until}, ...]

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    analyzed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    user = relationship("User", back_populates="recurring_insights")

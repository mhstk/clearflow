"""
Recurring payments cache model for storing AI-detected recurring payment patterns.
"""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class RecurringCache(Base):
    __tablename__ = "recurring_cache"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    merchant_key = Column(String, nullable=False, index=True)
    merchant_name = Column(String)  # Human-readable name (description_raw)

    # Detection results
    is_recurring = Column(Boolean, default=False)
    frequency = Column(String)  # weekly, bi-weekly, monthly, quarterly, yearly
    typical_amount = Column(Float)
    amount_variance = Column(String)  # fixed, variable
    confidence = Column(String)  # high, medium, low
    category = Column(String)

    # Pattern data
    transaction_count = Column(Integer)
    first_transaction_date = Column(Date)
    last_transaction_date = Column(Date)
    next_expected_date = Column(Date)

    # AI enrichment
    ai_verified = Column(Boolean, default=False)
    ai_notes = Column(String)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_analyzed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    user = relationship("User", back_populates="recurring_caches")

    __table_args__ = (
        UniqueConstraint("user_id", "merchant_key", name="uq_user_merchant_recurring"),
    )

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Enum as SQLEnum, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base
import enum


class CategorySource(str, enum.Enum):
    rule = "rule"
    ai = "ai"
    user = "user"
    uncategorized = "uncategorized"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    description_raw = Column(String, nullable=False)
    merchant_key = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="CAD", nullable=False)
    category = Column(String, default="Uncategorized", nullable=False, index=True)
    category_source = Column(
        SQLEnum(CategorySource),
        default=CategorySource.uncategorized,
        nullable=False
    )
    note_user = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # Expense flag for fast filtering (True = expense/negative, False = income/positive)
    is_expense = Column(Boolean, default=True, nullable=False, index=True)

    # Composite index for recurring detection queries
    __table_args__ = (
        Index('ix_transactions_user_expense_date', 'user_id', 'is_expense', 'date'),
    )

    # Relationships
    account = relationship("Account", back_populates="transactions")
    user = relationship("User", back_populates="transactions")

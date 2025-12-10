from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=True, index=True)  # Required for new users via schemas
    hashed_password = Column(String, nullable=True)  # Null for OAuth-only users

    # Profile
    name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)

    # OAuth
    google_id = Column(String, unique=True, nullable=True, index=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_demo = Column(Boolean, default=False, nullable=False)  # True for demo account

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    merchant_caches = relationship("MerchantCache", back_populates="user", cascade="all, delete-orphan")
    recurring_caches = relationship("RecurringCache", back_populates="user", cascade="all, delete-orphan")
    recurring_insights = relationship("RecurringInsights", back_populates="user", cascade="all, delete-orphan", uselist=False)

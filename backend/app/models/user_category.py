"""
User-defined categories model.

Each user can have their own set of categories for transactions.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.session import Base


# Default categories created for new users
DEFAULT_USER_CATEGORIES = [
    {"name": "Groceries", "color": "#22c55e", "sort_order": 1, "is_system": False},
    {"name": "Rent", "color": "#ef4444", "sort_order": 2, "is_system": False},
    {"name": "Transport", "color": "#f59e0b", "sort_order": 3, "is_system": False},
    {"name": "Eating Out", "color": "#3b82f6", "sort_order": 4, "is_system": False},
    {"name": "Shopping", "color": "#8b5cf6", "sort_order": 5, "is_system": False},
    {"name": "Subscription", "color": "#ec4899", "sort_order": 6, "is_system": False},
    {"name": "Utilities", "color": "#6366f1", "sort_order": 7, "is_system": False},
    {"name": "Income", "color": "#10b981", "sort_order": 8, "is_system": False},
    {"name": "Other", "color": "#6b7280", "sort_order": 99, "is_system": True},
]


class UserCategory(Base):
    """
    User-defined category for transactions.

    Each user has their own set of categories. The "Other" category is a system
    category that cannot be edited or deleted. "Uncategorized" is NOT stored here
    - it's just a default value for transactions that haven't been categorized yet.
    """
    __tablename__ = "user_categories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    color = Column(String(7), nullable=True)  # Hex color like #RRGGBB
    icon = Column(String(50), nullable=True)  # Icon name (for future use)
    sort_order = Column(Integer, default=0)
    is_system = Column(Boolean, default=False)  # True for "Other" (uneditable)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to user
    user = relationship("User", back_populates="categories")

    # Unique constraint: user can't have duplicate category names
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_user_category_name'),
    )

    def __repr__(self):
        return f"<UserCategory(id={self.id}, user_id={self.user_id}, name='{self.name}')>"

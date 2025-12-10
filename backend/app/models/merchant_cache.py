from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class MerchantCache(Base):
    __tablename__ = "merchant_caches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    merchant_key = Column(String, nullable=False, index=True)
    suggested_category = Column(String, nullable=False)
    suggested_note = Column(String, nullable=False)
    suggested_explanation = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="merchant_caches")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint("user_id", "merchant_key", name="uq_user_merchant"),
    )

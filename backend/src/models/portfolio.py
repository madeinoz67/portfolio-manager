"""
Portfolio model for investment collections.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import relationship

from src.database import Base

if TYPE_CHECKING:
    from .holding import Holding
    from .transaction import Transaction
    from .user import User


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    owner_id = Column(Uuid, ForeignKey("users.id"), nullable=False)
    total_value = Column(Numeric(15, 2), default=Decimal("0.00"))
    daily_change = Column(Numeric(10, 2), default=Decimal("0.00"))
    daily_change_percent = Column(Numeric(5, 2), default=Decimal("0.00"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    owner: "User" = relationship("User", back_populates="portfolios")
    holdings: list["Holding"] = relationship(
        "Holding", back_populates="portfolio", cascade="all, delete-orphan"
    )
    transactions: list["Transaction"] = relationship(
        "Transaction", back_populates="portfolio", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Portfolio(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"
"""
Holding model for current stock positions in portfolios.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, Uuid
from sqlalchemy.orm import relationship

from src.database import Base

if TYPE_CHECKING:
    from .portfolio import Portfolio
    from .stock import Stock


class Holding(Base):
    __tablename__ = "holdings"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(Uuid, ForeignKey("portfolios.id"), nullable=False)
    stock_id = Column(Uuid, ForeignKey("stocks.id"), nullable=False)
    quantity = Column(Numeric(12, 4), nullable=False)
    average_cost = Column(Numeric(10, 4), default=Decimal("0.0000"))
    current_value = Column(Numeric(15, 2), default=Decimal("0.00"))
    unrealized_gain_loss = Column(Numeric(15, 2), default=Decimal("0.00"))
    unrealized_gain_loss_percent = Column(Numeric(5, 2), default=Decimal("0.00"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    portfolio: "Portfolio" = relationship("Portfolio", back_populates="holdings")
    stock: "Stock" = relationship("Stock", back_populates="holdings")

    # Composite unique constraint
    __table_args__ = (
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return f"<Holding(id={self.id}, portfolio_id={self.portfolio_id}, stock_id={self.stock_id}, quantity={self.quantity})>"
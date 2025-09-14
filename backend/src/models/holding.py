"""
Holding model for current stock positions in portfolios.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from src.utils.datetime_utils import now

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, Uuid
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

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
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)

    # Relationships
    portfolio: "Portfolio" = relationship("Portfolio", back_populates="holdings")
    stock: "Stock" = relationship("Stock", back_populates="holdings")

    @hybrid_property
    def current_value(self) -> Decimal:
        """Calculate current market value based on live stock price."""
        if self.stock and self.stock.current_price:
            return self.quantity * self.stock.current_price
        return self.quantity * self.average_cost  # Fallback to cost basis if no current price

    @hybrid_property
    def cost_basis(self) -> Decimal:
        """Total cost basis for this holding."""
        return self.quantity * self.average_cost

    @hybrid_property
    def unrealized_gain_loss(self) -> Decimal:
        """Calculate unrealized gain/loss based on current price."""
        return self.current_value - self.cost_basis

    @hybrid_property
    def unrealized_gain_loss_percent(self) -> Decimal:
        """Calculate unrealized gain/loss percentage."""
        if self.cost_basis > 0:
            return (self.unrealized_gain_loss / self.cost_basis) * 100
        return Decimal("0.00")

    # Composite unique constraint
    __table_args__ = (
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return f"<Holding(id={self.id}, portfolio_id={self.portfolio_id}, stock_id={self.stock_id}, quantity={self.quantity})>"
"""
Database model for cached portfolio valuations.

Stores pre-calculated portfolio values with TTL for performance optimization.
"""

from datetime import datetime, timedelta
from typing import Optional
import uuid

from src.utils.datetime_utils import now

from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base


class PortfolioValuation(Base):
    """Model for cached portfolio valuations."""

    __tablename__ = "portfolio_valuations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False, index=True)
    total_value = Column(Numeric(precision=15, scale=4), nullable=False)
    total_cost_basis = Column(Numeric(precision=15, scale=4), nullable=False)
    total_gain_loss = Column(Numeric(precision=15, scale=4), nullable=False)
    total_gain_loss_percent = Column(Numeric(precision=10, scale=4), nullable=False)
    day_change = Column(Numeric(precision=15, scale=4), nullable=True)
    day_change_percent = Column(Numeric(precision=10, scale=4), nullable=True)
    holdings_count = Column(Integer, nullable=False)
    breakdown = Column(JSON, nullable=True)  # Per-holding breakdown
    calculated_at = Column(DateTime, default=now, nullable=False)
    expires_at = Column(DateTime, nullable=False)  # TTL timestamp
    is_stale = Column(Boolean, default=False, nullable=False)  # Mark as stale when prices are old
    created_at = Column(DateTime, default=now, nullable=False)

    # Relationships
    portfolio = relationship("Portfolio", lazy="select")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.expires_at is None:
            # Default TTL of 20 minutes
            self.expires_at = now() + timedelta(minutes=20)

    @property
    def is_expired(self) -> bool:
        """Check if the valuation has expired."""
        return now() > self.expires_at

    def __repr__(self) -> str:
        return f"<PortfolioValuation(portfolio_id={self.portfolio_id}, value={self.total_value}, calculated_at={self.calculated_at})>"
"""
Database model for realtime symbols master table.

Single source of truth for current stock prices, eliminating dual-table synchronization.
Implements Option C (Hybrid Master + History Reference) architecture.
"""

from datetime import datetime
from typing import Optional
import uuid

from src.utils.datetime_utils import now

from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base


class RealtimeSymbol(Base):
    """
    Master table for realtime symbol pricing - single source of truth.

    This table serves as the authoritative source for current stock prices,
    eliminating the dual-table synchronization complexity that caused timestamp bugs.
    """

    __tablename__ = "realtime_symbols"

    # Primary key is symbol for fast lookups
    symbol = Column(String(20), primary_key=True, nullable=False)

    # Core pricing information
    current_price = Column(Numeric(precision=10, scale=4), nullable=False)
    company_name = Column(String(255), nullable=True)
    last_updated = Column(DateTime, nullable=False)

    # Market data
    volume = Column(Integer, nullable=True)
    market_cap = Column(Numeric(precision=20, scale=2), nullable=True)

    # Provider information
    provider_id = Column(UUID(as_uuid=True), ForeignKey("market_data_providers.id"), nullable=False)

    # Reference to latest history record for time-series access
    latest_history_id = Column(UUID(as_uuid=True), ForeignKey("realtime_price_history.id"), nullable=True)

    # System fields
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, nullable=False)

    # Relationships
    provider = relationship("MarketDataProvider", lazy="select")
    latest_history = relationship("RealtimePriceHistory", foreign_keys=[latest_history_id], lazy="select")

    def update_timestamp(self):
        """Update the updated_at timestamp. Call this before committing changes."""
        self.updated_at = now()

    def __repr__(self) -> str:
        return f"<RealtimeSymbol(symbol={self.symbol}, price={self.current_price}, last_updated={self.last_updated})>"
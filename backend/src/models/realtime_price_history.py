"""
Database model for real-time price history tracking.

Stores time-series price data with source tracking for market data.
"""

from datetime import datetime
from typing import Optional
import uuid

from src.utils.datetime_utils import now

from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base


class RealtimePriceHistory(Base):
    """Model for storing real-time price history."""

    __tablename__ = "realtime_price_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False, index=True)
    price = Column(Numeric(precision=10, scale=4), nullable=False)
    volume = Column(Integer, nullable=True)
    market_cap = Column(Numeric(precision=20, scale=2), nullable=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("market_data_providers.id"), nullable=False)
    source_timestamp = Column(DateTime, nullable=False)  # Timestamp from the data provider
    fetched_at = Column(DateTime, default=now, nullable=False)  # When we fetched it
    created_at = Column(DateTime, default=now, nullable=False)

    # Relationships
    provider = relationship("MarketDataProvider", lazy="select")

    # Indexes for performance
    __table_args__ = (
        Index('idx_symbol_fetched_at', 'symbol', 'fetched_at'),
        Index('idx_symbol_source_timestamp', 'symbol', 'source_timestamp'),
        Index('idx_provider_fetched_at', 'provider_id', 'fetched_at'),
    )

    def __repr__(self) -> str:
        return f"<RealtimePriceHistory(symbol={self.symbol}, price={self.price}, fetched_at={self.fetched_at})>"
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

    # Extended price information for trend calculations
    opening_price = Column(Numeric(precision=10, scale=4), nullable=True)  # Day's opening price
    high_price = Column(Numeric(precision=10, scale=4), nullable=True)     # Day's high
    low_price = Column(Numeric(precision=10, scale=4), nullable=True)      # Day's low
    previous_close = Column(Numeric(precision=10, scale=4), nullable=True) # Previous day's close

    # Volume and market data
    volume = Column(Integer, nullable=True)
    market_cap = Column(Numeric(precision=20, scale=2), nullable=True)

    # Extended market information
    fifty_two_week_high = Column(Numeric(precision=10, scale=4), nullable=True)  # 52-week high
    fifty_two_week_low = Column(Numeric(precision=10, scale=4), nullable=True)   # 52-week low
    dividend_yield = Column(Numeric(precision=5, scale=2), nullable=True)        # Dividend yield %
    pe_ratio = Column(Numeric(precision=8, scale=2), nullable=True)              # Price-to-earnings ratio
    beta = Column(Numeric(precision=5, scale=2), nullable=True)                  # Beta coefficient

    # Metadata
    currency = Column(String(3), nullable=True, default='USD')                   # Currency code
    company_name = Column(String(255), nullable=True)                            # Company name

    # System fields
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
        Index('idx_symbol_opening_price', 'symbol', 'opening_price'),  # For trend calculations
    )

    def __repr__(self) -> str:
        return f"<RealtimePriceHistory(symbol={self.symbol}, price={self.price}, fetched_at={self.fetched_at})>"
"""
Database model for market data provider configurations.

Manages different data sources like Alpha Vantage, yfinance, etc.
"""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID

from src.database import Base


class MarketDataProvider(Base):
    """Model for market data provider configurations."""

    __tablename__ = "market_data_providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)  # 'alpha_vantage', 'yfinance'
    display_name = Column(String(100), nullable=False)  # 'Alpha Vantage', 'Yahoo Finance'
    is_enabled = Column(Boolean, default=True, nullable=False)
    api_key = Column(String(255), nullable=True)  # Encrypted API key
    base_url = Column(String(255), nullable=True)
    rate_limit_per_minute = Column(Integer, default=5, nullable=False)
    rate_limit_per_day = Column(Integer, default=500, nullable=False)
    priority = Column(Integer, default=1, nullable=False)  # 1 = highest priority
    config = Column(JSON, nullable=True)  # Provider-specific configuration
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<MarketDataProvider(name={self.name}, enabled={self.is_enabled}, priority={self.priority})>"
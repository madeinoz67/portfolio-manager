"""
Database model for market data provider configurations.

Manages different data sources like Alpha Vantage, yfinance, etc.
"""

from datetime import datetime
from typing import Optional
import uuid

from src.utils.datetime_utils import now

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.types import DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

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
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)

    # Relationships
    recent_activities = relationship("ProviderActivity", back_populates="provider", order_by="desc(ProviderActivity.timestamp)")

    def __repr__(self) -> str:
        return f"<MarketDataProvider(name={self.name}, enabled={self.is_enabled}, priority={self.priority})>"


class ProviderActivity(Base):
    """Model for tracking market data provider activity logs."""

    __tablename__ = "provider_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(String(50), ForeignKey("market_data_providers.name"), nullable=False)
    activity_type = Column(String(50), nullable=False)  # 'API_CALL', 'RATE_LIMIT', 'API_ERROR', etc.
    description = Column(Text, nullable=False)
    status = Column(String(20), nullable=False)  # 'success', 'error', 'warning'
    timestamp = Column(DateTime, default=now, nullable=False)
    activity_metadata = Column(JSON, nullable=True)  # Additional context data

    # Relationships
    provider = relationship("MarketDataProvider", back_populates="recent_activities")

    def __repr__(self) -> str:
        return f"<ProviderActivity(provider={self.provider_id}, type={self.activity_type}, status={self.status})>"



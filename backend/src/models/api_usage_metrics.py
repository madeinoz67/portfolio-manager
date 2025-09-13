"""
Database model for API usage metrics tracking.

Tracks market data provider API calls for rate limiting and monitoring.
"""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID

from src.database import Base


class ApiUsageMetrics(Base):
    """Model for tracking API usage metrics."""

    __tablename__ = "api_usage_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_name = Column(String(50), nullable=False)  # 'alpha_vantage', 'yfinance'
    symbol = Column(String(20), nullable=True)  # Stock symbol requested
    endpoint = Column(String(100), nullable=False)  # API endpoint called
    request_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    response_status = Column(Integer, nullable=False)  # HTTP status code
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    rate_limit_remaining = Column(Integer, nullable=True)
    rate_limit_total = Column(Integer, nullable=True)
    created_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<ApiUsageMetrics(provider={self.provider_name}, symbol={self.symbol}, success={self.success})>"
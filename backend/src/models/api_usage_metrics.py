"""
Database model for API usage metrics tracking.

Tracks market data provider API calls for rate limiting and monitoring.
"""

from datetime import datetime
from src.utils.datetime_utils import now
from typing import Optional
import uuid

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, DECIMAL
from sqlalchemy.dialects.postgresql import UUID

from src.database import Base


class ApiUsageMetrics(Base):
    """Model for tracking API usage metrics."""

    __tablename__ = "api_usage_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_id = Column(String(100), nullable=False)
    provider_id = Column(String(50), nullable=False)  # 'alpha_vantage', 'yfinance'
    user_id = Column(UUID(as_uuid=True), nullable=True)
    portfolio_id = Column(UUID(as_uuid=True), nullable=True)
    request_type = Column(String(50), nullable=False)
    requests_count = Column(Integer, nullable=True)
    data_points_fetched = Column(Integer, nullable=True)
    cost_estimate = Column(DECIMAL(8, 4), nullable=True)
    recorded_at = Column(DateTime, default=now, nullable=False)
    time_bucket = Column(String(20), nullable=False)  # 'hourly', 'daily', or 'monthly'
    rate_limit_hit = Column(Boolean, nullable=True)
    error_count = Column(Integer, nullable=True)
    avg_response_time_ms = Column(Integer, nullable=True)  # Average response time in milliseconds

    def __repr__(self) -> str:
        return f"<ApiUsageMetrics(provider={self.provider_id}, requests={self.requests_count}, errors={self.error_count})>"
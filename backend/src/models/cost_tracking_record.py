"""
Database model for market data provider cost tracking.

Tracks API usage costs and spending per provider with support for
daily cost aggregation, budget monitoring, and rate limit tracking.
"""

from datetime import datetime, date
from decimal import Decimal
import uuid

from sqlalchemy import Column, String, DateTime, Date, ForeignKey
from sqlalchemy.types import DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base
from src.utils.datetime_utils import now


class CostTrackingRecord(Base):
    """Model for tracking daily API usage costs per provider."""

    __tablename__ = "cost_tracking_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_config_id = Column(UUID(as_uuid=True), ForeignKey("provider_configurations.id"), nullable=False)
    date = Column(Date, nullable=False)  # Daily cost aggregation
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)

    # Cost tracking (use DECIMAL for financial precision)
    api_calls_count = Column(DECIMAL(10, 0), default=0, nullable=False)
    total_cost_usd = Column(DECIMAL(10, 4), default=0, nullable=False)  # 4 decimal places for sub-cent precision

    # Rate limiting tracking
    rate_limit_hits = Column(DECIMAL(10, 0), default=0, nullable=False)
    quota_usage_percent = Column(DECIMAL(5, 2), default=0, nullable=False)  # 0-100.00%

    # Provider-specific cost metadata
    cost_breakdown = Column(String(1000), nullable=True)  # JSON string for provider-specific cost details

    # Relationships
    provider_config = relationship("ProviderConfiguration", back_populates="cost_records")

    def __repr__(self) -> str:
        return f"<CostTrackingRecord(provider={self.provider_config_id}, date={self.date}, cost=${self.total_cost_usd})>"

    @property
    def cost_per_call(self) -> Decimal:
        """Calculate average cost per API call."""
        if self.api_calls_count == 0:
            return Decimal('0.0000')
        return self.total_cost_usd / self.api_calls_count

    @property
    def quota_remaining_percent(self) -> Decimal:
        """Calculate remaining quota percentage."""
        return Decimal('100.00') - self.quota_usage_percent

    def add_api_call_cost(self, cost_usd: Decimal, hit_rate_limit: bool = False) -> None:
        """Add cost for a single API call."""
        self.api_calls_count += 1
        self.total_cost_usd += cost_usd

        if hit_rate_limit:
            self.rate_limit_hits += 1

    def update_quota_usage(self, usage_percent: Decimal) -> None:
        """Update the quota usage percentage."""
        if 0 <= usage_percent <= 100:
            self.quota_usage_percent = usage_percent
        else:
            raise ValueError(f"Quota usage must be between 0-100%, got {usage_percent}")

    def is_approaching_quota_limit(self, threshold_percent: Decimal = Decimal('80.00')) -> bool:
        """Check if quota usage is approaching the limit."""
        return self.quota_usage_percent >= threshold_percent

    def is_over_budget(self, daily_budget_usd: Decimal) -> bool:
        """Check if daily costs exceed the budget."""
        return self.total_cost_usd > daily_budget_usd

    @classmethod
    def create_daily_record(cls, provider_config_id: str, record_date: date) -> "CostTrackingRecord":
        """Create a new daily cost tracking record for a provider."""
        return cls(
            provider_config_id=provider_config_id,
            date=record_date,
            api_calls_count=0,
            total_cost_usd=Decimal('0.0000'),
            rate_limit_hits=0,
            quota_usage_percent=Decimal('0.00')
        )
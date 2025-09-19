"""
Database model for market data provider adapter configurations.

Part of the new adapter system architecture supporting multiple providers
with standardized interface and metrics tracking.
"""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base
from src.utils.datetime_utils import now


class ProviderConfiguration(Base):
    """Model for market data provider adapter configurations."""

    __tablename__ = "provider_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_name = Column(String(50), nullable=False)  # Reference to adapter type
    display_name = Column(String(100), nullable=False)  # Human-readable name for admin UI
    config_data = Column(JSON, nullable=False)  # Provider-specific settings (encrypted credentials)
    is_active = Column(Boolean, default=False, nullable=False)  # Enable/disable provider
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    created_by = relationship("User")
    metrics = relationship(
        "ProviderMetrics",
        back_populates="provider_config",
        cascade="all, delete-orphan"
    )
    cost_records = relationship(
        "CostTrackingRecord",
        back_populates="provider_config",
        cascade="all, delete-orphan"
    )
    health_checks = relationship(
        "AdapterHealthCheck",
        back_populates="provider_config",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ProviderConfiguration(provider_name={self.provider_name}, display_name={self.display_name}, active={self.is_active})>"

    @property
    def is_healthy(self) -> bool:
        """Check if the most recent health check was successful."""
        if not self.health_checks:
            return False
        latest_check = max(self.health_checks, key=lambda x: x.check_timestamp)
        return latest_check.status == "healthy"

    def get_latest_metrics(self) -> Optional["ProviderMetrics"]:
        """Get the most recent metrics record."""
        if not self.metrics:
            return None
        return max(self.metrics, key=lambda x: x.timestamp)

    def get_daily_cost(self, date: datetime.date) -> Optional["CostTrackingRecord"]:
        """Get cost tracking record for a specific date."""
        for record in self.cost_records:
            if record.date == date:
                return record
        return None
"""
Database model for real-time provider metrics tracking.

Stores performance data for market data provider adapters including
latency, success rates, error counts, and circuit breaker state.
"""

from datetime import datetime
import uuid

from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.types import DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base
from src.utils.datetime_utils import now


class ProviderMetrics(Base):
    """Model for real-time performance data for each provider."""

    __tablename__ = "provider_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_config_id = Column(UUID(as_uuid=True), ForeignKey("provider_configurations.id"), nullable=False)
    timestamp = Column(DateTime, default=now, nullable=False)

    # Request metrics
    request_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)

    # Performance metrics
    total_latency_ms = Column(DECIMAL(10, 2), default=0, nullable=False)  # Sum for average calculation
    avg_latency_ms = Column(DECIMAL(8, 2), default=0, nullable=False)    # Pre-calculated average

    # Rate limiting and circuit breaker
    rate_limit_hits = Column(Integer, default=0, nullable=False)
    circuit_breaker_state = Column(String(20), default="closed", nullable=False)  # closed/open/half_open

    # Provider-specific metadata
    provider_metadata = Column(JSON, nullable=True)

    # Relationships
    provider_config = relationship("ProviderConfiguration", back_populates="metrics")

    def __repr__(self) -> str:
        return f"<ProviderMetrics(provider={self.provider_config_id}, requests={self.request_count}, success_rate={self.success_rate:.2%})>"

    @property
    def success_rate(self) -> float:
        """Calculate success rate as a decimal (0-1)."""
        if self.request_count == 0:
            return 0.0
        return self.success_count / self.request_count

    @property
    def error_rate(self) -> float:
        """Calculate error rate as a decimal (0-1)."""
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count

    def update_metrics(self, latency_ms: float, success: bool) -> None:
        """Update metrics with a new request result."""
        self.request_count += 1

        if success:
            self.success_count += 1
            self.total_latency_ms += latency_ms
            # Recalculate average latency
            if self.success_count > 0:
                self.avg_latency_ms = self.total_latency_ms / self.success_count
        else:
            self.error_count += 1

    def record_rate_limit_hit(self) -> None:
        """Record a rate limit violation."""
        self.rate_limit_hits += 1

    def set_circuit_breaker_state(self, state: str) -> None:
        """Update circuit breaker state."""
        if state in ["closed", "open", "half_open"]:
            self.circuit_breaker_state = state
        else:
            raise ValueError(f"Invalid circuit breaker state: {state}")

    @classmethod
    def create_empty_metrics(cls, provider_config_id: str) -> "ProviderMetrics":
        """Create a new empty metrics record for a provider."""
        return cls(
            provider_config_id=provider_config_id,
            request_count=0,
            success_count=0,
            error_count=0,
            total_latency_ms=0,
            avg_latency_ms=0,
            rate_limit_hits=0,
            circuit_breaker_state="closed"
        )
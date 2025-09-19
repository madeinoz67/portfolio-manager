"""
Database model for adapter health check tracking.

Stores health check results for market data provider adapters including
response times, status, error details, and connectivity monitoring.
"""

from datetime import datetime
from decimal import Decimal
import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.types import DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base
from src.utils.datetime_utils import now


class AdapterHealthCheck(Base):
    """Model for tracking adapter health check results."""

    __tablename__ = "adapter_health_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_config_id = Column(UUID(as_uuid=True), ForeignKey("provider_configurations.id"), nullable=False)
    check_timestamp = Column(DateTime, default=now, nullable=False)

    # Health status
    status = Column(String(20), nullable=False)  # healthy, degraded, unhealthy, timeout, error
    response_time_ms = Column(DECIMAL(8, 2), nullable=True)  # Response time in milliseconds

    # Check details
    status_code = Column(String(10), nullable=True)  # HTTP status code or error code
    error_message = Column(Text, nullable=True)  # Detailed error message
    error_type = Column(String(50), nullable=True)  # connection, authentication, rate_limit, etc.

    # Connectivity details
    endpoint_tested = Column(String(200), nullable=True)  # Which endpoint was tested
    test_symbol = Column(String(20), nullable=True)  # Symbol used for testing (e.g., "AAPL")

    # Relationships
    provider_config = relationship("ProviderConfiguration", back_populates="health_checks")

    def __repr__(self) -> str:
        return f"<AdapterHealthCheck(provider={self.provider_config_id}, status={self.status}, time={self.check_timestamp})>"

    @property
    def is_healthy(self) -> bool:
        """Check if the health check indicates healthy status."""
        return self.status == "healthy"

    @property
    def is_degraded(self) -> bool:
        """Check if the health check indicates degraded performance."""
        return self.status == "degraded"

    @property
    def has_error(self) -> bool:
        """Check if the health check indicates an error."""
        return self.status in ["unhealthy", "timeout", "error"]

    @property
    def response_time_seconds(self) -> Decimal:
        """Get response time in seconds."""
        if self.response_time_ms is None:
            return Decimal('0.0')
        return self.response_time_ms / Decimal('1000.0')

    def is_slow_response(self, threshold_ms: Decimal = Decimal('5000.0')) -> bool:
        """Check if response time exceeds threshold (default 5 seconds)."""
        if self.response_time_ms is None:
            return False
        return self.response_time_ms > threshold_ms

    def get_status_summary(self) -> dict:
        """Get summary of health check status."""
        return {
            "status": self.status,
            "is_healthy": self.is_healthy,
            "is_degraded": self.is_degraded,
            "has_error": self.has_error,
            "response_time_ms": float(self.response_time_ms) if self.response_time_ms else None,
            "check_time": self.check_timestamp.isoformat()
        }

    def get_error_details(self) -> dict:
        """Get error details if check failed."""
        if not self.has_error:
            return {}

        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "status_code": self.status_code,
            "endpoint_tested": self.endpoint_tested,
            "test_symbol": self.test_symbol
        }

    @classmethod
    def create_healthy_check(
        cls,
        provider_config_id: str,
        response_time_ms: Decimal,
        endpoint_tested: str,
        test_symbol: str = None
    ) -> "AdapterHealthCheck":
        """Create a healthy health check record."""
        return cls(
            provider_config_id=provider_config_id,
            status="healthy",
            response_time_ms=response_time_ms,
            endpoint_tested=endpoint_tested,
            test_symbol=test_symbol,
            status_code="200"
        )

    @classmethod
    def create_error_check(
        cls,
        provider_config_id: str,
        error_type: str,
        error_message: str,
        status_code: str = None,
        endpoint_tested: str = None,
        test_symbol: str = None
    ) -> "AdapterHealthCheck":
        """Create an error health check record."""
        status = "unhealthy"
        if error_type == "timeout":
            status = "timeout"
        elif error_type == "rate_limit":
            status = "degraded"

        return cls(
            provider_config_id=provider_config_id,
            status=status,
            error_type=error_type,
            error_message=error_message,
            status_code=status_code,
            endpoint_tested=endpoint_tested,
            test_symbol=test_symbol
        )

    @classmethod
    def create_degraded_check(
        cls,
        provider_config_id: str,
        response_time_ms: Decimal,
        reason: str,
        endpoint_tested: str,
        test_symbol: str = None
    ) -> "AdapterHealthCheck":
        """Create a degraded performance health check record."""
        return cls(
            provider_config_id=provider_config_id,
            status="degraded",
            response_time_ms=response_time_ms,
            error_message=reason,
            error_type="performance",
            endpoint_tested=endpoint_tested,
            test_symbol=test_symbol,
            status_code="200"
        )
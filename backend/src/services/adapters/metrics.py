"""
Provider metrics collection and Prometheus integration.

Provides comprehensive metrics collection for market data provider adapters
with Prometheus-compatible metrics and database persistence for historical analysis.
"""

import time
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime, timedelta, timezone
import logging
from dataclasses import dataclass, asdict

from aioprometheus import Counter, Histogram, Gauge, Summary
from sqlalchemy.orm import Session

from src.models.provider_metrics import ProviderMetrics
from src.models.provider_configuration import ProviderConfiguration
from src.models.adapter_health_check import AdapterHealthCheck
from src.models.cost_tracking_record import CostTrackingRecord
from src.database import get_db
from .base_adapter import AdapterResponse

logger = logging.getLogger(__name__)


@dataclass
class AdapterMetrics:
    """Basic adapter metrics tracking for testing and monitoring."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    last_request_at: Optional[datetime] = None
    error_counts: Dict[str, int] = None

    def __post_init__(self):
        if self.error_counts is None:
            self.error_counts = {}

    def record_success(self, response_time: float):
        """Record a successful request."""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_response_time += response_time
        self.last_request_at = datetime.now(timezone.utc)

    def record_failure(self, error_type: str, response_time: float = 0.0):
        """Record a failed request."""
        self.total_requests += 1
        self.failed_requests += 1
        self.total_response_time += response_time
        self.last_request_at = datetime.now(timezone.utc)
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

    def record_request(self, success: bool, response_time: float, error_type: str = None):
        """Record a request with success/failure status."""
        if success:
            self.record_success(response_time)
        else:
            self.record_failure(error_type or "Unknown", response_time)

    @property
    def average_response_time(self) -> float:
        """Calculate average response time."""
        if self.total_requests == 0:
            return 0.0
        return self.total_response_time / self.total_requests

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests

    def reset(self):
        """Reset all metrics to initial state."""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_response_time = 0.0
        self.last_request_at = None
        self.error_counts = {}


@dataclass
class PerformanceMetrics:
    """Performance tracking metrics."""

    response_time_p50: float = 0.0
    response_time_p95: float = 0.0
    response_time_p99: float = 0.0
    throughput_per_second: float = 0.0
    concurrent_requests: int = 0


@dataclass
class CostMetrics:
    """Cost tracking metrics."""

    requests_this_period: int = 0
    cost_this_period: Decimal = Decimal('0.00')
    cost_per_request: Decimal = Decimal('0.00')
    billing_period_start: Optional[datetime] = None
    billing_period_end: Optional[datetime] = None


@dataclass
class HealthMetrics:
    """Health monitoring metrics."""

    is_healthy: bool = True
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    circuit_breaker_state: str = "CLOSED"
    service_availability: float = 1.0


@dataclass
class MetricsSnapshot:
    """Snapshot of provider metrics at a point in time."""

    provider_name: str
    timestamp: datetime
    request_count: int
    success_count: int
    error_count: int
    avg_latency_ms: float
    success_rate: float
    error_rate: float
    rate_limit_hits: int
    circuit_breaker_state: str
    response_time_p50: Optional[float] = None
    response_time_p90: Optional[float] = None
    response_time_p99: Optional[float] = None


class ProviderMetricsCollector:
    """
    Comprehensive metrics collection for market data provider adapters.

    Integrates with Prometheus for real-time monitoring and persists
    metrics to database for historical analysis and reporting.
    """

    def __init__(self):
        """Initialize metrics collector with Prometheus metrics."""

        # Prometheus metrics
        self.request_counter = Counter(
            "adapter_requests_total",
            "Total number of adapter requests",
            const_labels={}
        )

        self.response_time_histogram = Histogram(
            "adapter_response_time_seconds",
            "Response time histogram for adapter requests",
            const_labels={},
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )

        self.active_requests_gauge = Gauge(
            "adapter_active_requests",
            "Number of active adapter requests",
            const_labels={}
        )

        self.circuit_breaker_state_gauge = Gauge(
            "adapter_circuit_breaker_state",
            "Circuit breaker state (0=closed, 1=half_open, 2=open)",
            const_labels={}
        )

        self.rate_limit_counter = Counter(
            "adapter_rate_limits_total",
            "Total number of rate limit hits",
            const_labels={}
        )

        self.success_rate_gauge = Gauge(
            "adapter_success_rate",
            "Success rate for adapter requests",
            const_labels={}
        )

        # Internal tracking
        self._provider_metrics: Dict[str, Dict[str, Any]] = {}
        self._active_requests: Dict[str, int] = {}

        self.logger = logging.getLogger("adapter.metrics")

    def record_request_start(self, provider_name: str, operation: str) -> str:
        """
        Record the start of a request.

        Args:
            provider_name: Name of the provider
            operation: Operation being performed

        Returns:
            Request ID for tracking
        """
        request_id = f"{provider_name}:{operation}:{time.time()}"

        # Update active requests
        if provider_name not in self._active_requests:
            self._active_requests[provider_name] = 0
        self._active_requests[provider_name] += 1

        # Update Prometheus gauge
        self.active_requests_gauge.labels(provider=provider_name).set(
            self._active_requests[provider_name]
        )

        return request_id

    def record_request_end(
        self,
        request_id: str,
        provider_name: str,
        operation: str,
        response: AdapterResponse,
        cost_usd: Optional[Decimal] = None
    ) -> None:
        """
        Record the completion of a request.

        Args:
            request_id: Request ID from record_request_start
            provider_name: Name of the provider
            operation: Operation that was performed
            response: Response from the adapter
            cost_usd: Optional cost of the request
        """
        # Extract timing from request_id
        start_time = float(request_id.split(':')[-1])
        duration_seconds = time.time() - start_time
        duration_ms = duration_seconds * 1000

        # Determine status
        status = "success" if response.success else "error"
        hit_rate_limit = response.error_code == "RATE_LIMIT_EXCEEDED"

        # Update Prometheus metrics
        self.request_counter.labels(
            provider=provider_name,
            operation=operation,
            status=status
        ).inc()

        self.response_time_histogram.labels(
            provider=provider_name,
            operation=operation
        ).observe(duration_seconds)

        if hit_rate_limit:
            self.rate_limit_counter.labels(provider=provider_name).inc()

        # Update active requests
        if provider_name in self._active_requests:
            self._active_requests[provider_name] = max(0, self._active_requests[provider_name] - 1)
            self.active_requests_gauge.labels(provider=provider_name).set(
                self._active_requests[provider_name]
            )

        # Update internal metrics
        self._update_internal_metrics(
            provider_name=provider_name,
            success=response.success,
            latency_ms=duration_ms,
            hit_rate_limit=hit_rate_limit,
            cost_usd=cost_usd
        )

    def _update_internal_metrics(
        self,
        provider_name: str,
        success: bool,
        latency_ms: float,
        hit_rate_limit: bool = False,
        cost_usd: Optional[Decimal] = None
    ) -> None:
        """Update internal metrics tracking."""
        if provider_name not in self._provider_metrics:
            self._provider_metrics[provider_name] = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_latency_ms": 0.0,
                "rate_limit_hits": 0,
                "total_cost_usd": Decimal('0.0'),
                "response_times": [],  # Last 100 for percentiles
                "last_updated": datetime.utcnow()
            }

        metrics = self._provider_metrics[provider_name]
        metrics["total_requests"] += 1
        metrics["total_latency_ms"] += latency_ms
        metrics["last_updated"] = datetime.utcnow()

        if success:
            metrics["successful_requests"] += 1
        else:
            metrics["failed_requests"] += 1

        if hit_rate_limit:
            metrics["rate_limit_hits"] += 1

        if cost_usd:
            metrics["total_cost_usd"] += cost_usd

        # Track response times for percentiles
        metrics["response_times"].append(latency_ms)
        if len(metrics["response_times"]) > 100:
            metrics["response_times"].pop(0)

        # Update Prometheus success rate gauge
        if metrics["total_requests"] > 0:
            success_rate = metrics["successful_requests"] / metrics["total_requests"]
            self.success_rate_gauge.labels(provider=provider_name).set(success_rate)

    def record_circuit_breaker_state(self, provider_name: str, state: str) -> None:
        """
        Record circuit breaker state change.

        Args:
            provider_name: Name of the provider
            state: Circuit breaker state (closed, half_open, open)
        """
        state_mapping = {"closed": 0, "half_open": 1, "open": 2}
        state_value = state_mapping.get(state, 0)

        self.circuit_breaker_state_gauge.labels(provider=provider_name).set(state_value)

        self.logger.info(f"Circuit breaker state changed for {provider_name}: {state}")

    def get_provider_metrics_snapshot(self, provider_name: str) -> Optional[MetricsSnapshot]:
        """
        Get current metrics snapshot for a provider.

        Args:
            provider_name: Name of the provider

        Returns:
            MetricsSnapshot or None if no metrics available
        """
        if provider_name not in self._provider_metrics:
            return None

        metrics = self._provider_metrics[provider_name]
        total_requests = metrics["total_requests"]

        if total_requests == 0:
            return MetricsSnapshot(
                provider_name=provider_name,
                timestamp=datetime.utcnow(),
                request_count=0,
                success_count=0,
                error_count=0,
                avg_latency_ms=0.0,
                success_rate=0.0,
                error_rate=0.0,
                rate_limit_hits=0,
                circuit_breaker_state="unknown"
            )

        # Calculate percentiles
        response_times = sorted(metrics["response_times"])
        p50 = p90 = p99 = None
        if len(response_times) >= 10:
            p50 = response_times[len(response_times) // 2]
            p90 = response_times[int(len(response_times) * 0.9)]
            p99 = response_times[int(len(response_times) * 0.99)]

        return MetricsSnapshot(
            provider_name=provider_name,
            timestamp=metrics["last_updated"],
            request_count=total_requests,
            success_count=metrics["successful_requests"],
            error_count=metrics["failed_requests"],
            avg_latency_ms=metrics["total_latency_ms"] / total_requests,
            success_rate=metrics["successful_requests"] / total_requests,
            error_rate=metrics["failed_requests"] / total_requests,
            rate_limit_hits=metrics["rate_limit_hits"],
            circuit_breaker_state="unknown",  # Would need circuit breaker reference
            response_time_p50=p50,
            response_time_p90=p90,
            response_time_p99=p99
        )

    def get_all_providers_metrics(self) -> List[MetricsSnapshot]:
        """Get metrics snapshots for all providers."""
        snapshots = []
        for provider_name in self._provider_metrics.keys():
            snapshot = self.get_provider_metrics_snapshot(provider_name)
            if snapshot:
                snapshots.append(snapshot)
        return snapshots

    async def persist_metrics_to_database(self, db_session: Session) -> None:
        """
        Persist current metrics to database.

        Args:
            db_session: Database session for persistence
        """
        try:
            for provider_name in self._provider_metrics.keys():
                snapshot = self.get_provider_metrics_snapshot(provider_name)
                if not snapshot or snapshot.request_count == 0:
                    continue

                # Find provider configuration
                provider_config = db_session.query(ProviderConfiguration).filter(
                    ProviderConfiguration.provider_name == provider_name,
                    ProviderConfiguration.is_active == True
                ).first()

                if not provider_config:
                    self.logger.warning(f"No active configuration found for provider {provider_name}")
                    continue

                # Create or update metrics record
                metrics_record = ProviderMetrics(
                    provider_config_id=provider_config.id,
                    request_count=snapshot.request_count,
                    success_count=snapshot.success_count,
                    error_count=snapshot.error_count,
                    total_latency_ms=Decimal(str(snapshot.avg_latency_ms * snapshot.request_count)),
                    avg_latency_ms=Decimal(str(snapshot.avg_latency_ms)),
                    rate_limit_hits=snapshot.rate_limit_hits,
                    circuit_breaker_state=snapshot.circuit_breaker_state,
                    provider_metadata={
                        "response_time_p50": snapshot.response_time_p50,
                        "response_time_p90": snapshot.response_time_p90,
                        "response_time_p99": snapshot.response_time_p99
                    }
                )

                db_session.add(metrics_record)

            db_session.commit()
            self.logger.info("Metrics persisted to database successfully")

        except Exception as e:
            db_session.rollback()
            self.logger.error(f"Error persisting metrics to database: {e}")

    async def record_health_check(
        self,
        provider_name: str,
        response: AdapterResponse,
        test_symbol: str = "AAPL"
    ) -> None:
        """
        Record health check result to database.

        Args:
            provider_name: Name of the provider
            response: Health check response
            test_symbol: Symbol used for testing
        """
        try:
            # Get database session
            db = next(get_db())

            # Find provider configuration
            provider_config = db.query(ProviderConfiguration).filter(
                ProviderConfiguration.provider_name == provider_name,
                ProviderConfiguration.is_active == True
            ).first()

            if not provider_config:
                self.logger.warning(f"No active configuration found for provider {provider_name}")
                return

            # Determine status and create health check record
            if response.success:
                health_check = AdapterHealthCheck.create_healthy_check(
                    provider_config_id=str(provider_config.id),
                    response_time_ms=Decimal(str(response.response_time_ms)),
                    endpoint_tested="health_check",
                    test_symbol=test_symbol
                )
            else:
                health_check = AdapterHealthCheck.create_error_check(
                    provider_config_id=str(provider_config.id),
                    error_type=response.error_code or "unknown",
                    error_message=response.error_message or "Unknown error",
                    endpoint_tested="health_check",
                    test_symbol=test_symbol
                )

            db.add(health_check)
            db.commit()

        except Exception as e:
            self.logger.error(f"Error recording health check for {provider_name}: {e}")
        finally:
            db.close()

    def reset_provider_metrics(self, provider_name: str) -> None:
        """Reset metrics for a specific provider."""
        if provider_name in self._provider_metrics:
            del self._provider_metrics[provider_name]

        if provider_name in self._active_requests:
            del self._active_requests[provider_name]

        self.logger.info(f"Metrics reset for provider {provider_name}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get overall metrics summary across all providers.

        Returns:
            Dict with aggregated metrics information
        """
        total_providers = len(self._provider_metrics)
        total_requests = sum(m["total_requests"] for m in self._provider_metrics.values())
        total_success = sum(m["successful_requests"] for m in self._provider_metrics.values())
        total_errors = sum(m["failed_requests"] for m in self._provider_metrics.values())
        total_rate_limits = sum(m["rate_limit_hits"] for m in self._provider_metrics.values())

        overall_success_rate = (total_success / total_requests) if total_requests > 0 else 0.0

        return {
            "total_providers": total_providers,
            "total_requests": total_requests,
            "total_successful_requests": total_success,
            "total_failed_requests": total_errors,
            "overall_success_rate": overall_success_rate,
            "total_rate_limit_hits": total_rate_limits,
            "active_providers": list(self._provider_metrics.keys()),
            "last_updated": max(
                (m["last_updated"] for m in self._provider_metrics.values()),
                default=None
            )
        }


# Global metrics collector instance
_global_metrics_collector = ProviderMetricsCollector()


def get_metrics_collector() -> ProviderMetricsCollector:
    """Get the global metrics collector instance."""
    return _global_metrics_collector
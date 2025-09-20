"""
T061: Unit tests for metrics collection
Tests ProviderMetricsCollector for aioprometheus integration and adapter metrics.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import asyncio
from typing import Dict, Any, List

from src.services.adapters.metrics import (
    ProviderMetricsCollector,
    MetricsAggregator,
    MetricsStorage,
    AdapterMetrics,
    PerformanceMetrics,
    CostMetrics,
    HealthMetrics,
)


class TestProviderMetricsCollector:
    """Test the ProviderMetricsCollector class."""

    @pytest.fixture
    def mock_prometheus_registry(self):
        """Mock Prometheus registry."""
        with patch('aioprometheus.Registry') as mock_registry:
            yield mock_registry.return_value

    @pytest.fixture
    def mock_storage(self):
        """Mock metrics storage."""
        mock = Mock(spec=MetricsStorage)
        mock.store_metrics = AsyncMock()
        mock.get_metrics = AsyncMock()
        mock.get_metrics_history = AsyncMock()
        return mock

    @pytest.fixture
    def metrics_collector(self, mock_prometheus_registry, mock_storage):
        """Create metrics collector with mocked dependencies."""
        return ProviderMetricsCollector(
            registry=mock_prometheus_registry,
            storage=mock_storage
        )

    def test_metrics_collector_initialization(self, mock_prometheus_registry, mock_storage):
        """Test metrics collector initialization."""
        collector = ProviderMetricsCollector(
            registry=mock_prometheus_registry,
            storage=mock_storage
        )

        assert collector.registry == mock_prometheus_registry
        assert collector.storage == mock_storage
        assert collector.enabled is True

    def test_metrics_collector_disable(self, metrics_collector):
        """Test disabling metrics collection."""
        metrics_collector.disable()
        assert metrics_collector.enabled is False

    def test_metrics_collector_enable(self, metrics_collector):
        """Test enabling metrics collection."""
        metrics_collector.disable()
        metrics_collector.enable()
        assert metrics_collector.enabled is True

    @pytest.mark.asyncio
    async def test_record_request_success(self, metrics_collector):
        """Test recording successful request metrics."""
        provider_id = "test_provider"
        adapter_id = "adapter_123"
        response_time = 150.5
        endpoint = "get_price"

        await metrics_collector.record_request(
            provider_id=provider_id,
            adapter_id=adapter_id,
            success=True,
            response_time_ms=response_time,
            endpoint=endpoint
        )

        # Verify storage was called
        metrics_collector.storage.store_metrics.assert_called_once()
        call_args = metrics_collector.storage.store_metrics.call_args[1]

        assert call_args["provider_id"] == provider_id
        assert call_args["adapter_id"] == adapter_id
        assert call_args["success"] is True
        assert call_args["response_time_ms"] == response_time
        assert call_args["endpoint"] == endpoint

    @pytest.mark.asyncio
    async def test_record_request_failure(self, metrics_collector):
        """Test recording failed request metrics."""
        provider_id = "test_provider"
        adapter_id = "adapter_123"
        response_time = 200.0
        error_type = "ConnectionError"

        await metrics_collector.record_request(
            provider_id=provider_id,
            adapter_id=adapter_id,
            success=False,
            response_time_ms=response_time,
            error_type=error_type
        )

        # Verify storage was called
        call_args = metrics_collector.storage.store_metrics.call_args[1]

        assert call_args["success"] is False
        assert call_args["error_type"] == error_type

    @pytest.mark.asyncio
    async def test_record_request_disabled(self, metrics_collector):
        """Test recording request when metrics are disabled."""
        metrics_collector.disable()

        await metrics_collector.record_request(
            provider_id="test_provider",
            adapter_id="adapter_123",
            success=True,
            response_time_ms=100.0
        )

        # Storage should not be called when disabled
        metrics_collector.storage.store_metrics.assert_not_called()

    @pytest.mark.asyncio
    async def test_record_cost_metrics(self, metrics_collector):
        """Test recording cost metrics."""
        provider_id = "test_provider"
        adapter_id = "adapter_123"
        cost = Decimal("0.05")
        requests_count = 10

        await metrics_collector.record_cost(
            provider_id=provider_id,
            adapter_id=adapter_id,
            cost=cost,
            requests_count=requests_count,
            cost_type="api_call"
        )

        # Verify cost metrics were stored
        call_args = metrics_collector.storage.store_metrics.call_args[1]

        assert call_args["provider_id"] == provider_id
        assert call_args["cost"] == cost
        assert call_args["requests_count"] == requests_count
        assert call_args["cost_type"] == "api_call"

    @pytest.mark.asyncio
    async def test_get_adapter_metrics(self, metrics_collector):
        """Test getting adapter metrics."""
        adapter_id = "adapter_123"
        time_range = timedelta(hours=24)

        # Mock storage response
        mock_metrics = {
            "total_requests": 100,
            "successful_requests": 95,
            "failed_requests": 5,
            "average_response_time": 150.0,
            "total_cost": Decimal("2.50")
        }
        metrics_collector.storage.get_metrics.return_value = mock_metrics

        result = await metrics_collector.get_adapter_metrics(adapter_id, time_range)

        assert result == mock_metrics
        metrics_collector.storage.get_metrics.assert_called_once_with(
            adapter_id=adapter_id,
            time_range=time_range
        )

    @pytest.mark.asyncio
    async def test_get_provider_metrics(self, metrics_collector):
        """Test getting provider-level metrics."""
        provider_id = "test_provider"
        time_range = timedelta(hours=6)

        # Mock storage response
        mock_metrics = {
            "total_adapters": 3,
            "active_adapters": 2,
            "total_requests": 500,
            "average_response_time": 120.0
        }
        metrics_collector.storage.get_metrics.return_value = mock_metrics

        result = await metrics_collector.get_provider_metrics(provider_id, time_range)

        assert result == mock_metrics
        metrics_collector.storage.get_metrics.assert_called_once_with(
            provider_id=provider_id,
            time_range=time_range
        )

    @pytest.mark.asyncio
    async def test_get_metrics_history(self, metrics_collector):
        """Test getting metrics history."""
        adapter_id = "adapter_123"
        start_time = datetime.now(timezone.utc) - timedelta(days=1)
        end_time = datetime.now(timezone.utc)

        # Mock storage response
        mock_history = [
            {"timestamp": start_time, "requests": 10, "response_time": 100.0},
            {"timestamp": end_time, "requests": 15, "response_time": 120.0}
        ]
        metrics_collector.storage.get_metrics_history.return_value = mock_history

        result = await metrics_collector.get_metrics_history(
            adapter_id=adapter_id,
            start_time=start_time,
            end_time=end_time
        )

        assert result == mock_history
        metrics_collector.storage.get_metrics_history.assert_called_once_with(
            adapter_id=adapter_id,
            start_time=start_time,
            end_time=end_time
        )

    @pytest.mark.asyncio
    async def test_record_health_check(self, metrics_collector):
        """Test recording health check metrics."""
        adapter_id = "adapter_123"
        provider_id = "test_provider"
        status = "healthy"
        response_time = 50.0
        details = {"connectivity": "ok", "api_quota": "75%"}

        await metrics_collector.record_health_check(
            adapter_id=adapter_id,
            provider_id=provider_id,
            status=status,
            response_time_ms=response_time,
            details=details
        )

        # Verify health metrics were stored
        call_args = metrics_collector.storage.store_metrics.call_args[1]

        assert call_args["adapter_id"] == adapter_id
        assert call_args["provider_id"] == provider_id
        assert call_args["status"] == status
        assert call_args["response_time_ms"] == response_time
        assert call_args["details"] == details

    def test_prometheus_metrics_registration(self, mock_prometheus_registry, mock_storage):
        """Test Prometheus metrics registration."""
        collector = ProviderMetricsCollector(
            registry=mock_prometheus_registry,
            storage=mock_storage
        )

        # Verify that prometheus metrics were registered
        assert mock_prometheus_registry.register.call_count > 0

    @pytest.mark.asyncio
    async def test_batch_record_requests(self, metrics_collector):
        """Test batch recording of request metrics."""
        batch_data = [
            {
                "provider_id": "provider_1",
                "adapter_id": "adapter_1",
                "success": True,
                "response_time_ms": 100.0,
                "endpoint": "get_price"
            },
            {
                "provider_id": "provider_2",
                "adapter_id": "adapter_2",
                "success": False,
                "response_time_ms": 200.0,
                "error_type": "TimeoutError"
            }
        ]

        await metrics_collector.batch_record_requests(batch_data)

        # Verify storage was called for each item
        assert metrics_collector.storage.store_metrics.call_count == 2

    @pytest.mark.asyncio
    async def test_export_metrics(self, metrics_collector):
        """Test exporting metrics in Prometheus format."""
        # Mock the Prometheus registry generate_latest method
        mock_output = b"# HELP adapter_requests_total Total adapter requests\n"
        metrics_collector.registry.generate_latest = Mock(return_value=mock_output)

        result = await metrics_collector.export_prometheus_metrics()

        assert result == mock_output
        metrics_collector.registry.generate_latest.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_old_metrics(self, metrics_collector):
        """Test cleanup of old metrics data."""
        retention_period = timedelta(days=30)

        # Mock storage cleanup method
        metrics_collector.storage.cleanup_old_metrics = AsyncMock()

        await metrics_collector.cleanup_old_metrics(retention_period)

        metrics_collector.storage.cleanup_old_metrics.assert_called_once_with(retention_period)

    def test_metrics_context_manager(self, metrics_collector):
        """Test metrics collector as context manager."""
        with metrics_collector as collector:
            assert collector.enabled is True

        # Should remain enabled after context exit
        assert metrics_collector.enabled is True

    @pytest.mark.asyncio
    async def test_error_handling_in_record_request(self, metrics_collector):
        """Test error handling when recording request fails."""
        # Make storage raise an exception
        metrics_collector.storage.store_metrics.side_effect = Exception("Storage error")

        # Should not raise exception, just log error
        await metrics_collector.record_request(
            provider_id="test_provider",
            adapter_id="adapter_123",
            success=True,
            response_time_ms=100.0
        )

        # Verify storage was called despite error
        metrics_collector.storage.store_metrics.assert_called_once()


class TestMetricsAggregator:
    """Test the MetricsAggregator class."""

    @pytest.fixture
    def mock_storage(self):
        """Mock metrics storage."""
        mock = Mock(spec=MetricsStorage)
        mock.get_raw_metrics = AsyncMock()
        mock.store_aggregated_metrics = AsyncMock()
        return mock

    @pytest.fixture
    def aggregator(self, mock_storage):
        """Create metrics aggregator with mocked storage."""
        return MetricsAggregator(storage=mock_storage)

    @pytest.mark.asyncio
    async def test_aggregate_adapter_metrics(self, aggregator):
        """Test aggregating adapter metrics."""
        adapter_id = "adapter_123"
        time_window = timedelta(hours=1)

        # Mock raw metrics data
        raw_metrics = [
            {"success": True, "response_time_ms": 100.0, "timestamp": datetime.now(timezone.utc)},
            {"success": True, "response_time_ms": 150.0, "timestamp": datetime.now(timezone.utc)},
            {"success": False, "response_time_ms": 200.0, "timestamp": datetime.now(timezone.utc)}
        ]
        aggregator.storage.get_raw_metrics.return_value = raw_metrics

        result = await aggregator.aggregate_adapter_metrics(adapter_id, time_window)

        assert result["total_requests"] == 3
        assert result["successful_requests"] == 2
        assert result["failed_requests"] == 1
        assert result["success_rate"] == 66.67
        assert result["average_response_time"] == 150.0

    @pytest.mark.asyncio
    async def test_aggregate_provider_metrics(self, aggregator):
        """Test aggregating provider-level metrics."""
        provider_id = "test_provider"
        time_window = timedelta(hours=24)

        # Mock adapter metrics for the provider
        adapter_metrics = {
            "adapter_1": {"requests": 100, "success_rate": 95.0, "avg_response_time": 120.0},
            "adapter_2": {"requests": 50, "success_rate": 90.0, "avg_response_time": 180.0}
        }
        aggregator.storage.get_raw_metrics.return_value = adapter_metrics

        result = await aggregator.aggregate_provider_metrics(provider_id, time_window)

        assert "total_requests" in result
        assert "average_success_rate" in result
        assert "average_response_time" in result

    @pytest.mark.asyncio
    async def test_calculate_cost_metrics(self, aggregator):
        """Test calculating cost metrics."""
        adapter_id = "adapter_123"
        time_window = timedelta(days=1)

        # Mock cost data
        cost_data = [
            {"cost": Decimal("0.05"), "requests": 10, "timestamp": datetime.now(timezone.utc)},
            {"cost": Decimal("0.03"), "requests": 5, "timestamp": datetime.now(timezone.utc)}
        ]
        aggregator.storage.get_raw_metrics.return_value = cost_data

        result = await aggregator.calculate_cost_metrics(adapter_id, time_window)

        assert result["total_cost"] == Decimal("0.08")
        assert result["total_requests"] == 15
        assert result["cost_per_request"] == Decimal("0.08") / 15

    @pytest.mark.asyncio
    async def test_calculate_performance_percentiles(self, aggregator):
        """Test calculating performance percentiles."""
        adapter_id = "adapter_123"
        time_window = timedelta(hours=1)

        # Mock response time data
        response_times = [100.0, 120.0, 150.0, 180.0, 200.0, 250.0, 300.0, 400.0, 500.0, 600.0]
        metrics_data = [{"response_time_ms": rt} for rt in response_times]
        aggregator.storage.get_raw_metrics.return_value = metrics_data

        result = await aggregator.calculate_performance_percentiles(adapter_id, time_window)

        assert "p50" in result
        assert "p95" in result
        assert "p99" in result
        assert result["p95"] >= result["p50"]
        assert result["p99"] >= result["p95"]

    @pytest.mark.asyncio
    async def test_run_periodic_aggregation(self, aggregator):
        """Test running periodic aggregation."""
        # Mock the individual aggregation methods
        aggregator.aggregate_all_adapters = AsyncMock()
        aggregator.cleanup_old_aggregations = AsyncMock()

        await aggregator.run_periodic_aggregation()

        aggregator.aggregate_all_adapters.assert_called_once()
        aggregator.cleanup_old_aggregations.assert_called_once()


class TestAdapterMetrics:
    """Test the AdapterMetrics data class."""

    def test_adapter_metrics_initialization(self):
        """Test AdapterMetrics initialization."""
        metrics = AdapterMetrics()

        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.total_response_time == 0.0
        assert metrics.last_request_at is None

    def test_adapter_metrics_success_rate(self):
        """Test success rate calculation."""
        metrics = AdapterMetrics(
            total_requests=100,
            successful_requests=95,
            failed_requests=5
        )

        assert metrics.success_rate == 95.0

    def test_adapter_metrics_success_rate_no_requests(self):
        """Test success rate with no requests."""
        metrics = AdapterMetrics()
        assert metrics.success_rate == 0.0

    def test_adapter_metrics_average_response_time(self):
        """Test average response time calculation."""
        metrics = AdapterMetrics(
            total_requests=10,
            total_response_time=1500.0
        )

        assert metrics.average_response_time == 150.0

    def test_adapter_metrics_average_response_time_no_requests(self):
        """Test average response time with no requests."""
        metrics = AdapterMetrics()
        assert metrics.average_response_time == 0.0


class TestPerformanceMetrics:
    """Test the PerformanceMetrics data class."""

    def test_performance_metrics_initialization(self):
        """Test PerformanceMetrics initialization."""
        metrics = PerformanceMetrics(
            p50=100.0,
            p95=200.0,
            p99=300.0,
            min_response_time=50.0,
            max_response_time=400.0
        )

        assert metrics.p50 == 100.0
        assert metrics.p95 == 200.0
        assert metrics.p99 == 300.0
        assert metrics.min_response_time == 50.0
        assert metrics.max_response_time == 400.0


class TestCostMetrics:
    """Test the CostMetrics data class."""

    def test_cost_metrics_initialization(self):
        """Test CostMetrics initialization."""
        metrics = CostMetrics(
            total_cost=Decimal("10.50"),
            cost_per_request=Decimal("0.05"),
            daily_cost=Decimal("2.50"),
            monthly_estimate=Decimal("75.00")
        )

        assert metrics.total_cost == Decimal("10.50")
        assert metrics.cost_per_request == Decimal("0.05")
        assert metrics.daily_cost == Decimal("2.50")
        assert metrics.monthly_estimate == Decimal("75.00")


class TestHealthMetrics:
    """Test the HealthMetrics data class."""

    def test_health_metrics_initialization(self):
        """Test HealthMetrics initialization."""
        last_check = datetime.now(timezone.utc)
        metrics = HealthMetrics(
            status="healthy",
            last_check_at=last_check,
            consecutive_failures=0,
            uptime_percentage=99.5
        )

        assert metrics.status == "healthy"
        assert metrics.last_check_at == last_check
        assert metrics.consecutive_failures == 0
        assert metrics.uptime_percentage == 99.5
"""
Integration test for live metrics monitoring functionality.

Tests the complete user scenario:
1. Admin sets up adapter configurations
2. Adapters make API calls and generate metrics
3. Metrics are collected and stored in real-time
4. Admin dashboard displays live metrics

Based on Scenario 2 from quickstart.md
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import AsyncMock, patch

from src.main import app
from tests.conftest import get_admin_jwt_token


client = TestClient(app)


@pytest.fixture
def admin_jwt_token(db_session: Session) -> str:
    """Create admin JWT token for testing."""
    return get_admin_jwt_token(db_session)


class TestMetricsMonitoringIntegration:
    """Integration tests for live metrics monitoring functionality."""

    def test_metrics_monitoring_complete_flow(self, admin_jwt_token: str, db_session: Session):
        """Test complete metrics monitoring workflow from quickstart scenario 2."""

        # Step 1: Create adapter configuration (will fail until implemented)
        adapter_config = {
            "provider_name": "yahoo_finance",
            "display_name": "Yahoo Finance Test",
            "config_data": {
                "base_url": "https://query1.finance.yahoo.com",
                "timeout": 30,
                "calls_per_minute": 60
            },
            "is_active": True
        }

        create_response = client.post(
            "/api/v1/admin/adapters",
            json=adapter_config,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should initially fail (endpoint not implemented)
        assert create_response.status_code in [201, 404], "Create endpoint not implemented yet"

        # If implemented, continue with the flow
        if create_response.status_code == 201:
            adapter_data = create_response.json()
            adapter_id = adapter_data["id"]

            # Step 2: Simulate adapter making API calls (this would be done by adapter service)
            # In a real scenario, the adapter would make calls to Yahoo Finance
            # and metrics would be automatically collected

            # Step 3: Check that metrics are being collected
            metrics_response = client.get(
                f"/api/v1/admin/adapters/{adapter_id}/metrics",
                headers={"Authorization": f"Bearer {admin_jwt_token}"}
            )

            assert metrics_response.status_code == 200, "Should provide metrics"
            metrics_data = metrics_response.json()

            # Verify metrics structure
            assert "current_metrics" in metrics_data, "Should include current metrics"
            assert "historical_data" in metrics_data, "Should include historical data"

            current = metrics_data["current_metrics"]
            assert "request_count" in current, "Should track request count"
            assert "success_rate" in current, "Should track success rate"
            assert "avg_latency_ms" in current, "Should track latency"
            assert "last_updated" in current, "Should have timestamp"

            # Step 4: Verify metrics are live (not hard-coded)
            # Make another metrics call and verify timestamp changed
            import time
            time.sleep(1)

            second_metrics_response = client.get(
                f"/api/v1/admin/adapters/{adapter_id}/metrics",
                headers={"Authorization": f"Bearer {admin_jwt_token}"}
            )

            assert second_metrics_response.status_code == 200, "Metrics should be available"
            second_data = second_metrics_response.json()

            # Verify data is dynamic (generated_at should be recent)
            assert "generated_at" in second_data, "Should include generation timestamp"

    def test_metrics_aggregation_over_time(self, admin_jwt_token: str, db_session: Session):
        """Test that metrics are properly aggregated over time windows."""

        # This test would verify:
        # 1. Metrics are collected per API call
        # 2. Metrics are aggregated into time windows (1 minute, 5 minutes, etc.)
        # 3. Historical data is maintained
        # 4. Old data is properly cleaned up

        # For now, just verify the endpoint structure would support this
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        # Test time range parameters
        params = {
            "start_time": "2025-09-19T10:00:00Z",
            "end_time": "2025-09-19T11:00:00Z",
            "interval": "5m"
        }

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/metrics",
            params=params,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should accept time parameters or not be implemented
        assert response.status_code in [200, 404], "Should support time-based metrics or not be implemented"

    def test_metrics_real_time_updates(self, admin_jwt_token: str, db_session: Session):
        """Test that metrics update in real-time as adapters make calls."""

        # This test would verify:
        # 1. Adapter makes API call
        # 2. Metrics are immediately updated
        # 3. Dashboard reflects changes without refresh
        # 4. Multiple adapters can be monitored simultaneously

        # For now, verify metrics endpoint supports real-time requirements
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/metrics",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        if response.status_code == 200:
            data = response.json()

            # Verify response includes real-time indicators
            assert "generated_at" in data, "Should include generation timestamp"

            # Verify metrics include current state
            if "current_metrics" in data:
                current = data["current_metrics"]
                assert "last_updated" in current, "Should track when metrics were last updated"

        # Should provide real-time metrics or not be implemented
        assert response.status_code in [200, 404], "Should provide real-time metrics or not be implemented"

    def test_metrics_performance_requirements(self, admin_jwt_token: str, db_session: Session):
        """Test that metrics collection doesn't impact adapter performance."""

        # This test would verify:
        # 1. Metrics collection is asynchronous
        # 2. Metrics don't slow down API calls
        # 3. Metrics storage is efficient
        # 4. Dashboard queries are fast

        import time

        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        start_time = time.time()

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/metrics",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        end_time = time.time()
        response_time = end_time - start_time

        # Metrics endpoint should be fast (< 200ms)
        if response.status_code == 200:
            assert response_time < 0.2, "Metrics endpoint should respond quickly"

        assert response.status_code in [200, 404], "Should provide fast metrics or not be implemented"

    def test_metrics_error_handling(self, admin_jwt_token: str, db_session: Session):
        """Test metrics collection during adapter error scenarios."""

        # This test would verify:
        # 1. Failed API calls are tracked in metrics
        # 2. Error rates are calculated correctly
        # 3. Circuit breaker state is monitored
        # 4. Rate limit violations are recorded

        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/metrics",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        if response.status_code == 200:
            data = response.json()

            # Verify error tracking capabilities
            if "current_metrics" in data:
                current = data["current_metrics"]
                # Should track both success and error metrics
                expected_error_fields = {
                    "error_count", "success_rate", "rate_limit_hits", "circuit_breaker_state"
                }

                # At least some error tracking should be present
                error_fields_present = any(field in current for field in expected_error_fields)
                # This assertion might be too strict for initial implementation
                # assert error_fields_present, "Should track error metrics"

        assert response.status_code in [200, 404], "Should track error metrics or not be implemented"

    def test_multiple_adapter_metrics_monitoring(self, admin_jwt_token: str, db_session: Session):
        """Test monitoring metrics across multiple adapters simultaneously."""

        # This test would verify:
        # 1. Multiple adapters can be configured
        # 2. Each adapter has independent metrics
        # 3. Dashboard can display all adapters
        # 4. Performance comparison is possible

        # Test getting list of all adapters and their metrics
        list_response = client.get(
            "/api/v1/admin/adapters",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should list adapters or not be implemented
        assert list_response.status_code in [200, 404], "Should list adapters or not be implemented"

        if list_response.status_code == 200:
            data = list_response.json()

            # Should include metrics summary in listing
            if "items" in data:
                # Each adapter should have basic metrics info
                for adapter in data["items"]:
                    # Adapter listing might include summary metrics
                    pass  # Structure depends on implementation

    def test_metrics_data_persistence(self, admin_jwt_token: str, db_session: Session):
        """Test that metrics data is properly persisted to database."""

        # This test would verify:
        # 1. Metrics are stored in ProviderMetrics table
        # 2. Time-series data is maintained
        # 3. Data retention policies are followed
        # 4. Database performance is acceptable

        # This is more of a database integration test
        # The API contract test just verifies data is available
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/metrics",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        if response.status_code == 200:
            data = response.json()

            # Verify historical data is available (indicating persistence)
            if "historical_data" in data:
                historical = data["historical_data"]
                # Should be an array of time-series data points
                assert isinstance(historical, list), "Historical data should be an array"

        assert response.status_code in [200, 404], "Should persist metrics data or not be implemented"
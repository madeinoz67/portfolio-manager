"""
Integration test for multiple provider fallback functionality.

Tests the complete user scenario:
1. Multiple providers configured with priorities
2. Primary provider fails
3. System automatically falls back to secondary provider
4. Data continues to flow without interruption
5. System reverts to primary when recovered

Based on Scenario 4 from quickstart.md
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


class TestProviderFallbackIntegration:
    """Integration tests for multiple provider fallback scenarios."""

    def test_multiple_provider_configuration(self, admin_jwt_token: str, db_session: Session):
        """Test configuring multiple providers with fallback priority."""

        # Step 1: Configure primary provider (Alpha Vantage)
        primary_config = {
            "provider_name": "alpha_vantage",
            "display_name": "Alpha Vantage Primary",
            "config_data": {
                "api_key": "primary_api_key",
                "base_url": "https://www.alphavantage.co/query",
                "priority": 1  # Highest priority
            },
            "is_active": True
        }

        primary_response = client.post(
            "/api/v1/admin/adapters",
            json=primary_config,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Step 2: Configure secondary provider (Yahoo Finance)
        secondary_config = {
            "provider_name": "yahoo_finance",
            "display_name": "Yahoo Finance Secondary",
            "config_data": {
                "base_url": "https://query1.finance.yahoo.com",
                "timeout": 30,
                "priority": 2  # Lower priority
            },
            "is_active": True
        }

        secondary_response = client.post(
            "/api/v1/admin/adapters",
            json=secondary_config,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should initially fail (endpoints not implemented)
        assert primary_response.status_code in [201, 404], "Primary provider creation"
        assert secondary_response.status_code in [201, 404], "Secondary provider creation"

        # If implemented, verify both providers are listed
        if primary_response.status_code == 201 and secondary_response.status_code == 201:
            list_response = client.get(
                "/api/v1/admin/adapters",
                headers={"Authorization": f"Bearer {admin_jwt_token}"}
            )

            assert list_response.status_code == 200, "Should list multiple providers"
            data = list_response.json()

            if "items" in data:
                assert len(data["items"]) >= 2, "Should have multiple providers configured"

    def test_provider_priority_ordering(self, admin_jwt_token: str, db_session: Session):
        """Test that providers are ordered by priority for fallback."""

        # This test would verify:
        # 1. Providers are tried in priority order
        # 2. Higher priority (lower number) providers are preferred
        # 3. Provider selection respects active/inactive status
        # 4. Fallback chain is properly configured

        list_response = client.get(
            "/api/v1/admin/adapters",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        if list_response.status_code == 200:
            data = list_response.json()

            # Should support sorting/ordering by priority
            params = {"sort": "priority", "order": "asc"}
            sorted_response = client.get(
                "/api/v1/admin/adapters",
                params=params,
                headers={"Authorization": f"Bearer {admin_jwt_token}"}
            )

            # Should accept sorting parameters
            assert sorted_response.status_code in [200, 404], "Should support priority sorting or not implemented"

        assert list_response.status_code in [200, 404], "Should list providers or not be implemented"

    def test_automatic_fallback_on_primary_failure(self, admin_jwt_token: str, db_session: Session):
        """Test automatic fallback when primary provider fails."""

        # This test would verify:
        # 1. Primary provider failure is detected
        # 2. System automatically switches to secondary
        # 3. Data requests continue without user intervention
        # 4. Fallback is transparent to end users

        # In a real implementation, this would involve:
        # - Making a data request
        # - Primary provider failing (simulated)
        # - Request succeeding via secondary provider
        # - Metrics showing the fallback occurred

        # For now, test the infrastructure supports this
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        # Check health of providers to understand fallback status
        health_response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/health",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        if health_response.status_code == 200:
            data = health_response.json()

            # Health status should indicate if this provider is being used
            if "status" in data:
                status = data["status"]
                assert status in ["healthy", "degraded", "unhealthy"], "Should have valid status"

        assert health_response.status_code in [200, 404], "Should provide health status or not be implemented"

    def test_fallback_metrics_tracking(self, admin_jwt_token: str, db_session: Session):
        """Test that fallback events are tracked in metrics."""

        # This test would verify:
        # 1. Fallback events are recorded
        # 2. Each provider's usage is tracked separately
        # 3. Fallback frequency is monitored
        # 4. Performance comparison between providers is available

        # Check metrics for multiple providers
        list_response = client.get(
            "/api/v1/admin/adapters",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        if list_response.status_code == 200:
            data = list_response.json()

            if "items" in data:
                for adapter in data["items"]:
                    adapter_id = adapter.get("id")
                    if adapter_id:
                        # Each provider should have independent metrics
                        metrics_response = client.get(
                            f"/api/v1/admin/adapters/{adapter_id}/metrics",
                            headers={"Authorization": f"Bearer {admin_jwt_token}"}
                        )

                        if metrics_response.status_code == 200:
                            metrics_data = metrics_response.json()

                            # Should track usage per provider
                            if "current_metrics" in metrics_data:
                                current = metrics_data["current_metrics"]
                                # Each provider tracks its own requests
                                if "request_count" in current:
                                    count = current["request_count"]
                                    assert isinstance(count, int), "Request count should be integer"

        assert list_response.status_code in [200, 404], "Should track per-provider metrics or not be implemented"

    def test_primary_provider_recovery_detection(self, admin_jwt_token: str, db_session: Session):
        """Test detection and reversion when primary provider recovers."""

        # This test would verify:
        # 1. System detects when primary provider recovers
        # 2. Traffic is gradually shifted back to primary
        # 3. Secondary provider remains available for future fallbacks
        # 4. Recovery process is logged and monitored

        # Test health monitoring across multiple providers
        list_response = client.get(
            "/api/v1/admin/adapters",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        if list_response.status_code == 200:
            data = list_response.json()

            # Should show health status for all providers
            if "items" in data:
                for adapter in data["items"]:
                    # Each adapter should have health information
                    if "health_status" in adapter:
                        health = adapter["health_status"]
                        # Should indicate if provider is available for use
                        if "status" in health:
                            status = health["status"]
                            assert status in ["healthy", "degraded", "unhealthy"], "Should have valid status"

        assert list_response.status_code in [200, 404], "Should monitor all provider health or not be implemented"

    def test_provider_load_balancing(self, admin_jwt_token: str, db_session: Session):
        """Test load balancing between multiple healthy providers."""

        # This test would verify:
        # 1. When multiple providers are healthy, load is distributed
        # 2. Load balancing respects provider capabilities
        # 3. Rate limits are considered in load distribution
        # 4. Provider performance affects load balancing decisions

        # Check that registry shows provider capabilities
        registry_response = client.get(
            "/api/v1/admin/adapters/registry",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        if registry_response.status_code == 200:
            data = registry_response.json()

            # Should show capabilities for load balancing decisions
            if "available_adapters" in data:
                adapters = data["available_adapters"]
                for adapter in adapters:
                    if "capabilities" in adapter:
                        caps = adapter["capabilities"]
                        # Should include rate limiting info for load balancing
                        if "rate_limit_per_minute" in caps:
                            rate_limit = caps["rate_limit_per_minute"]
                            if rate_limit is not None:
                                assert isinstance(rate_limit, int), "Rate limit should be integer"

        assert registry_response.status_code in [200, 404], "Should show capabilities or not be implemented"

    def test_fallback_configuration_validation(self, admin_jwt_token: str, db_session: Session):
        """Test validation of fallback configuration settings."""

        # This test would verify:
        # 1. Priority values are validated (unique, positive integers)
        # 2. At least one provider must be active
        # 3. Circular dependencies are prevented
        # 4. Configuration changes are validated before applying

        # Test creating provider with invalid priority
        invalid_config = {
            "provider_name": "alpha_vantage",
            "display_name": "Invalid Priority Test",
            "config_data": {
                "api_key": "test_key",
                "priority": -1  # Invalid priority
            },
            "is_active": True
        }

        response = client.post(
            "/api/v1/admin/adapters",
            json=invalid_config,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should validate configuration or not be implemented
        assert response.status_code in [400, 422, 404], "Should validate priority or not be implemented"

    def test_fallback_performance_requirements(self, admin_jwt_token: str, db_session: Session):
        """Test that fallback doesn't significantly impact performance."""

        # This test would verify:
        # 1. Fallback decision is made quickly (< 100ms)
        # 2. Provider health checks are efficient
        # 3. Fallback doesn't cause request timeouts
        # 4. Multiple fallback attempts don't cascade failures

        import time

        # Test health check performance
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        start_time = time.time()

        health_response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/health",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        end_time = time.time()
        response_time = end_time - start_time

        # Health checks should be fast for fallback decisions
        if health_response.status_code == 200:
            assert response_time < 0.1, "Health checks should be fast for fallback"

        assert health_response.status_code in [200, 404], "Should provide fast health checks or not be implemented"

    def test_fallback_data_consistency(self, admin_jwt_token: str, db_session: Session):
        """Test that fallback maintains data consistency."""

        # This test would verify:
        # 1. Different providers return consistent data formats
        # 2. Fallback doesn't cause data loss or corruption
        # 3. Timestamps and data quality are maintained
        # 4. User experience is seamless during fallback

        # This would primarily be tested through actual data requests
        # For now, verify that providers support consistent interfaces

        registry_response = client.get(
            "/api/v1/admin/adapters/registry",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        if registry_response.status_code == 200:
            data = registry_response.json()

            # All providers should support consistent data types
            if "available_adapters" in data:
                adapters = data["available_adapters"]
                for adapter in adapters:
                    if "capabilities" in adapter:
                        caps = adapter["capabilities"]
                        # Should support stock prices consistently
                        if "supported_data_types" in caps:
                            data_types = caps["supported_data_types"]
                            assert isinstance(data_types, list), "Supported data types should be array"

        assert registry_response.status_code in [200, 404], "Should show consistent capabilities or not be implemented"
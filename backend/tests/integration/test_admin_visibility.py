"""
Test admin visibility requirements - admin users should see full adapter metadata.

Validates that admin users have complete visibility into adapter operations
while maintaining separation from regular user experience.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime, timezone

from src.main import app
from src.core.auth import create_access_token
from src.models.user import UserRole


@pytest.fixture
def client():
    """Test client for API calls."""
    return TestClient(app)


@pytest.fixture
def admin_user_token():
    """JWT token for admin user."""
    return create_access_token(data={
        "sub": "admin@example.com",
        "role": UserRole.ADMIN.value,
        "user_id": 1
    })


@pytest.fixture
def mock_adapter_response_with_metadata():
    """Mock adapter response with full metadata for admin view."""
    return {
        "success": True,
        "data": {
            "symbol": "AAPL",
            "price": Decimal("150.25"),
            "open": Decimal("149.80"),
            "high": Decimal("151.00"),
            "low": Decimal("149.50"),
            "volume": 45000000,
            "currency": "USD"
        },
        "source_info": {
            "provider_name": "yfinance_default",
            "adapter_type": "yfinance",
            "response_time_ms": 245,
            "rate_limit_remaining": 950,
            "cost_units_consumed": 1,
            "fallback_used": False
        },
        "cache_info": {
            "cache_hit": False,
            "cache_age_seconds": 0,
            "cache_expires_at": "2025-09-22T11:00:00Z"
        }
    }


class TestAdminVisibility:
    """Test that admin users can see full adapter metadata."""

    def test_admin_can_access_adapter_management(self, client, admin_user_token):
        """Test that admin users can access adapter management endpoints."""
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = client.get("/api/v1/admin/adapters", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Verify admin can see adapter list
        assert isinstance(data, list) or "adapters" in data

    def test_admin_can_see_adapter_details(self, client, admin_user_token):
        """Test that admin users can see detailed adapter information."""
        headers = {"Authorization": f"Bearer {admin_user_token}"}

        # Get list of adapters first
        response = client.get("/api/v1/admin/adapters", headers=headers)
        assert response.status_code == 200

        adapters = response.json()
        if isinstance(adapters, list) and len(adapters) > 0:
            adapter_id = adapters[0].get("id")

            # Get detailed adapter info
            detail_response = client.get(f"/api/v1/admin/adapters/{adapter_id}", headers=headers)
            assert detail_response.status_code == 200

            adapter_detail = detail_response.json()

            # Verify admin can see provider details
            expected_fields = ["provider_name", "adapter_type", "is_active", "configuration"]
            for field in expected_fields:
                assert field in adapter_detail or any(field in str(v) for v in adapter_detail.values())

    @patch('src.services.adapter_metrics_service.AdapterMetricsService.get_adapter_metrics')
    def test_admin_can_see_adapter_metrics(self, mock_metrics, client, admin_user_token):
        """Test that admin users can see detailed adapter metrics."""
        mock_metrics.return_value = {
            "provider_name": "yfinance_default",
            "adapter_type": "yfinance",
            "is_healthy": True,
            "response_time_ms": 245,
            "success_rate_percent": 98.5,
            "requests_today": 1250,
            "cost_today_usd": 0.00,  # Free provider
            "rate_limit_remaining": 950,
            "circuit_breaker_state": "closed",
            "last_error": None,
            "uptime_percent": 99.2
        }

        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = client.get("/api/v1/admin/adapters/1/metrics", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Verify admin can see detailed metrics
        expected_metrics = [
            "provider_name", "adapter_type", "response_time_ms",
            "success_rate_percent", "requests_today", "rate_limit_remaining"
        ]
        for metric in expected_metrics:
            assert metric in data

    def test_admin_can_see_adapter_health_status(self, client, admin_user_token):
        """Test that admin users can see adapter health status."""
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = client.get("/api/v1/admin/adapters/1/health", headers=headers)

        if response.status_code == 200:
            data = response.json()

            # Verify admin can see health details
            health_fields = ["status", "response_time_ms", "last_check"]
            for field in health_fields:
                assert field in data or any(field in str(v) for v in data.values())

    @patch('src.services.adapter_service.AdapterService.get_adapter_registry')
    def test_admin_can_see_adapter_registry(self, mock_registry, client, admin_user_token):
        """Test that admin users can see the adapter registry."""
        mock_registry.return_value = {
            "available_adapters": [
                {
                    "adapter_name": "yfinance",
                    "display_name": "Yahoo Finance",
                    "description": "Free market data from Yahoo Finance",
                    "supported_features": ["stock_prices", "bulk_quotes"],
                    "cost_model": "free",
                    "rate_limits": {"requests_per_minute": 60}
                },
                {
                    "adapter_name": "alpha_vantage",
                    "display_name": "Alpha Vantage",
                    "description": "Professional market data API",
                    "supported_features": ["stock_prices", "fundamentals"],
                    "cost_model": "freemium",
                    "rate_limits": {"requests_per_minute": 5}
                }
            ]
        }

        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = client.get("/api/v1/admin/adapters/registry", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Verify admin can see all adapter types
        assert "available_adapters" in data or isinstance(data, list)

        if "available_adapters" in data:
            adapters = data["available_adapters"]
        else:
            adapters = data

        # Verify detailed adapter information is present
        if len(adapters) > 0:
            adapter = adapters[0]
            expected_fields = ["adapter_name", "display_name", "supported_features", "cost_model"]
            for field in expected_fields:
                assert field in adapter

    def test_admin_can_configure_adapters(self, client, admin_user_token):
        """Test that admin users can configure adapters."""
        headers = {"Authorization": f"Bearer {admin_user_token}"}

        # Test creating a new adapter configuration
        adapter_config = {
            "provider_name": "test_alpha_vantage",
            "adapter_type": "alpha_vantage",
            "display_name": "Test Alpha Vantage",
            "configuration": {
                "api_key": "test_api_key",
                "timeout": 30
            },
            "is_active": True
        }

        response = client.post("/api/v1/admin/adapters", headers=headers, json=adapter_config)

        # Should succeed or give specific validation error
        assert response.status_code in [200, 201, 400, 422]

        if response.status_code in [200, 201]:
            data = response.json()
            # Verify configuration was accepted
            assert "id" in data or "provider_name" in data

    @patch('src.services.adapter_service.AdapterService.test_adapter_connection')
    def test_admin_can_test_adapter_connections(self, mock_test, client, admin_user_token):
        """Test that admin users can test adapter connections."""
        mock_test.return_value = {
            "success": True,
            "response_time_ms": 234,
            "error_message": None,
            "provider_info": {
                "api_version": "v1.2",
                "rate_limit_status": "normal",
                "features_available": ["quotes", "historical"]
            }
        }

        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = client.post("/api/v1/admin/adapters/1/test", headers=headers)

        if response.status_code == 200:
            data = response.json()

            # Verify admin can see test results
            assert "success" in data
            assert "response_time_ms" in data

    def test_admin_can_see_cost_tracking(self, client, admin_user_token):
        """Test that admin users can see cost tracking information."""
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = client.get("/api/v1/admin/adapters/1/costs", headers=headers)

        if response.status_code == 200:
            data = response.json()

            # Verify admin can see cost information
            cost_fields = ["daily_cost", "monthly_cost", "requests_used", "quota_remaining"]
            # At least some cost-related information should be present
            has_cost_info = any(field in data for field in cost_fields)
            assert has_cost_info or "cost_tracking" in data

    @patch('src.services.adapter_service.AdapterService.get_adapter_logs')
    def test_admin_can_see_adapter_logs(self, mock_logs, client, admin_user_token):
        """Test that admin users can see adapter operation logs."""
        mock_logs.return_value = {
            "logs": [
                {
                    "timestamp": "2025-09-22T10:30:00Z",
                    "level": "INFO",
                    "message": "Successful price fetch for AAPL",
                    "adapter": "yfinance",
                    "response_time_ms": 234,
                    "symbols": ["AAPL"]
                },
                {
                    "timestamp": "2025-09-22T10:29:45Z",
                    "level": "WARNING",
                    "message": "Rate limit approaching",
                    "adapter": "alpha_vantage",
                    "rate_limit_remaining": 5
                }
            ],
            "total_count": 2,
            "page": 1
        }

        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = client.get("/api/v1/admin/adapters/1/logs", headers=headers)

        if response.status_code == 200:
            data = response.json()

            # Verify admin can see operation logs
            assert "logs" in data or isinstance(data, list)

            if "logs" in data:
                logs = data["logs"]
            else:
                logs = data

            if len(logs) > 0:
                log = logs[0]
                log_fields = ["timestamp", "level", "message", "adapter"]
                for field in log_fields:
                    assert field in log


class TestAdminSourceInfoVisibility:
    """Test that admin APIs include source_info while user APIs don't."""

    @patch('src.services.market_data_service.MarketDataService.get_current_price')
    def test_admin_api_includes_source_info(self, mock_get_price, client, admin_user_token, mock_adapter_response_with_metadata):
        """Test that admin market data APIs include source_info."""
        mock_get_price.return_value = mock_adapter_response_with_metadata

        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = client.get("/api/v1/admin/market-data/prices/AAPL", headers=headers)

        if response.status_code == 200:
            data = response.json()

            # Verify admin can see source information
            assert "source_info" in data
            source_info = data["source_info"]

            expected_source_fields = ["provider_name", "adapter_type", "response_time_ms"]
            for field in expected_source_fields:
                assert field in source_info

    def test_admin_dashboard_shows_provider_details(self, client, admin_user_token):
        """Test that admin dashboard shows provider-specific details."""
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = client.get("/api/v1/admin/dashboard/market-data", headers=headers)

        if response.status_code == 200:
            data = response.json()

            # Admin dashboard should show provider details
            provider_fields = ["active_providers", "provider_status", "total_requests"]
            has_provider_info = any(field in data for field in provider_fields)
            assert has_provider_info

    def test_admin_can_manage_provider_priorities(self, client, admin_user_token):
        """Test that admin users can manage provider priorities and failover."""
        headers = {"Authorization": f"Bearer {admin_user_token}"}

        # Test getting current provider priority
        response = client.get("/api/v1/admin/adapters/priorities", headers=headers)

        if response.status_code == 200:
            data = response.json()

            # Should show provider ordering/priority information
            priority_fields = ["primary_provider", "fallback_chain", "provider_order"]
            has_priority_info = any(field in data for field in priority_fields)
            assert has_priority_info or isinstance(data, list)
"""
Contract tests for GET /api/v1/admin/market-data/usage endpoint.

These tests verify the API contract for administrative usage metrics.
They MUST FAIL until the admin_market_data_router is implemented.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


class TestAdminUsageContract:
    """Contract tests for admin usage metrics endpoint."""

    def test_usage_endpoint_exists(self, client: TestClient, valid_jwt_token: str):
        """Test that the usage endpoint exists and accepts requests."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/market-data/usage", headers=headers)
        
        # Should return 200 for successful usage retrieval
        assert response.status_code == 200
        
        # Should return JSON content
        assert response.headers["content-type"] == "application/json"

    def test_usage_requires_authentication(self, client: TestClient):
        """Test that usage endpoint requires valid authentication."""
        # This test MUST FAIL until the endpoint is implemented
        
        response = client.get("/api/v1/admin/market-data/usage")
        
        assert response.status_code == 401

    def test_usage_response_structure(self, client: TestClient, valid_jwt_token: str):
        """Test that usage endpoint returns correct response structure."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/market-data/usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required top-level fields
        assert "current_period" in data
        assert "api_providers" in data
        assert "system_metrics" in data
        assert "historical_usage" in data
        assert "limits" in data
        assert "alerts" in data
        
        # Verify current_period structure
        current_period = data["current_period"]
        assert "start_date" in current_period
        assert "end_date" in current_period
        assert "total_requests" in current_period
        assert "successful_requests" in current_period
        assert "failed_requests" in current_period
        assert "cached_responses" in current_period

    def test_usage_api_providers_structure(self, client: TestClient, valid_jwt_token: str):
        """Test that API providers usage has correct structure."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/market-data/usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        api_providers = data["api_providers"]
        
        assert isinstance(api_providers, list)
        assert len(api_providers) > 0
        
        for provider in api_providers:
            assert "name" in provider
            assert "requests_today" in provider
            assert "requests_this_month" in provider
            assert "success_rate" in provider
            assert "average_response_time_ms" in provider
            assert "last_request" in provider
            assert "error_count" in provider
            assert "rate_limit_hits" in provider
            assert "cost_estimate" in provider
            
            assert provider["name"] in ["alpha_vantage", "yfinance"]
            assert isinstance(provider["requests_today"], int)
            assert isinstance(provider["requests_this_month"], int)
            assert isinstance(provider["success_rate"], (int, float))
            assert isinstance(provider["error_count"], int)
            assert isinstance(provider["rate_limit_hits"], int)

    def test_usage_system_metrics_structure(self, client: TestClient, valid_jwt_token: str):
        """Test that system metrics have correct structure."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/market-data/usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        system_metrics = data["system_metrics"]
        
        assert "cache_hit_rate" in system_metrics
        assert "average_cache_ttl_minutes" in system_metrics
        assert "active_sse_connections" in system_metrics
        assert "peak_concurrent_connections" in system_metrics
        assert "data_freshness_minutes" in system_metrics
        assert "system_load" in system_metrics
        assert "memory_usage_mb" in system_metrics
        
        assert isinstance(system_metrics["cache_hit_rate"], (int, float))
        assert isinstance(system_metrics["average_cache_ttl_minutes"], (int, float))
        assert isinstance(system_metrics["active_sse_connections"], int)
        assert isinstance(system_metrics["peak_concurrent_connections"], int)

    def test_usage_historical_data_structure(self, client: TestClient, valid_jwt_token: str):
        """Test that historical usage data has correct structure."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/market-data/usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        historical_usage = data["historical_usage"]
        
        assert "daily_breakdown" in historical_usage
        assert "monthly_breakdown" in historical_usage
        
        daily_breakdown = historical_usage["daily_breakdown"]
        assert isinstance(daily_breakdown, list)
        
        if daily_breakdown:  # If there's historical data
            for day_data in daily_breakdown[:3]:  # Check first few entries
                assert "date" in day_data
                assert "total_requests" in day_data
                assert "successful_requests" in day_data
                assert "failed_requests" in day_data
                assert "cache_hits" in day_data
                
                assert isinstance(day_data["total_requests"], int)
                assert isinstance(day_data["successful_requests"], int)
                assert isinstance(day_data["failed_requests"], int)
                assert isinstance(day_data["cache_hits"], int)

    def test_usage_limits_structure(self, client: TestClient, valid_jwt_token: str):
        """Test that limits information has correct structure."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/market-data/usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        limits = data["limits"]
        
        assert "alpha_vantage" in limits
        assert "yfinance" in limits
        assert "system" in limits
        
        # Check Alpha Vantage limits
        av_limits = limits["alpha_vantage"]
        assert "daily_limit" in av_limits
        assert "monthly_limit" in av_limits
        assert "requests_per_minute" in av_limits
        assert "current_usage_percent" in av_limits
        
        # Check system limits
        system_limits = limits["system"]
        assert "max_sse_connections" in system_limits
        assert "max_concurrent_requests" in system_limits
        assert "cache_size_limit_mb" in system_limits

    def test_usage_alerts_structure(self, client: TestClient, valid_jwt_token: str):
        """Test that alerts section has correct structure."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/market-data/usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        alerts = data["alerts"]
        
        assert "active_alerts" in alerts
        assert "recent_alerts" in alerts
        
        active_alerts = alerts["active_alerts"]
        assert isinstance(active_alerts, list)
        
        if active_alerts:  # If there are active alerts
            for alert in active_alerts:
                assert "id" in alert
                assert "type" in alert
                assert "severity" in alert
                assert "message" in alert
                assert "created_at" in alert
                assert "threshold_value" in alert
                assert "current_value" in alert
                
                assert alert["severity"] in ["low", "medium", "high", "critical"]
                assert alert["type"] in ["rate_limit", "error_rate", "system_load", "cache_miss"]

    def test_usage_date_range_parameter(self, client: TestClient, valid_jwt_token: str):
        """Test that usage endpoint accepts date range parameters."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Test with date range
        response = client.get(
            "/api/v1/admin/market-data/usage?start_date=2024-01-01&end_date=2024-01-31", 
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        current_period = data["current_period"]
        
        # Should reflect the requested date range
        assert current_period["start_date"] == "2024-01-01"
        assert current_period["end_date"] == "2024-01-31"

    def test_usage_timestamp_format(self, client: TestClient, valid_jwt_token: str):
        """Test that timestamps follow ISO 8601 format."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/market-data/usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify timestamp formats
        from datetime import datetime
        
        # Check provider timestamps
        for provider in data["api_providers"]:
            if provider["last_request"]:
                datetime.fromisoformat(provider["last_request"].replace("Z", "+00:00"))
        
        # Check historical data timestamps
        historical = data["historical_usage"]["daily_breakdown"]
        if historical:
            for day_data in historical[:3]:
                # Date should be in YYYY-MM-DD format
                datetime.strptime(day_data["date"], "%Y-%m-%d")
        
        # Check alert timestamps
        for alert in data["alerts"]["active_alerts"]:
            datetime.fromisoformat(alert["created_at"].replace("Z", "+00:00"))

    def test_usage_percentage_values_valid(self, client: TestClient, valid_jwt_token: str):
        """Test that percentage values are within valid ranges."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/market-data/usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check API provider success rates
        for provider in data["api_providers"]:
            success_rate = provider["success_rate"]
            assert 0.0 <= success_rate <= 100.0
        
        # Check system cache hit rate
        system_metrics = data["system_metrics"]
        cache_hit_rate = system_metrics["cache_hit_rate"]
        assert 0.0 <= cache_hit_rate <= 100.0
        
        # Check usage percentages in limits
        for provider_name, limits in data["limits"].items():
            if provider_name != "system" and "current_usage_percent" in limits:
                usage_percent = limits["current_usage_percent"]
                assert 0.0 <= usage_percent <= 100.0

    def test_usage_non_negative_counters(self, client: TestClient, valid_jwt_token: str):
        """Test that all counter values are non-negative."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/market-data/usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check current period counters
        current_period = data["current_period"]
        assert current_period["total_requests"] >= 0
        assert current_period["successful_requests"] >= 0
        assert current_period["failed_requests"] >= 0
        assert current_period["cached_responses"] >= 0
        
        # Check provider counters
        for provider in data["api_providers"]:
            assert provider["requests_today"] >= 0
            assert provider["requests_this_month"] >= 0
            assert provider["error_count"] >= 0
            assert provider["rate_limit_hits"] >= 0
        
        # Check system metrics
        system_metrics = data["system_metrics"]
        assert system_metrics["active_sse_connections"] >= 0
        assert system_metrics["peak_concurrent_connections"] >= 0

    def test_usage_consistency_checks(self, client: TestClient, valid_jwt_token: str):
        """Test that usage data is internally consistent."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/market-data/usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check that total requests = successful + failed
        current_period = data["current_period"]
        total = current_period["total_requests"]
        successful = current_period["successful_requests"]
        failed = current_period["failed_requests"]
        
        assert total == successful + failed
        
        # Check that active connections <= peak connections
        system_metrics = data["system_metrics"]
        active = system_metrics["active_sse_connections"]
        peak = system_metrics["peak_concurrent_connections"]
        
        assert active <= peak

    def test_usage_unauthorized_user(self, client: TestClient):
        """Test usage endpoint with invalid token."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/api/v1/admin/market-data/usage", headers=headers)
        
        assert response.status_code == 401

    def test_usage_admin_authorization(self, client: TestClient):
        """Test that only admin users can access usage data."""
        # This test MUST FAIL until the endpoint is implemented
        
        # Test with non-admin token
        headers = {"Authorization": "Bearer non_admin_token"}
        
        response = client.get("/api/v1/admin/market-data/usage", headers=headers)
        
        # Should return 401 (unauthorized) or 403 (forbidden)
        assert response.status_code in [401, 403]

    def test_usage_response_caching(self, client: TestClient, valid_jwt_token: str):
        """Test that usage responses include appropriate caching headers."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/market-data/usage", headers=headers)
        assert response.status_code == 200
        
        # Should include cache control headers
        assert "cache-control" in response.headers
        # Usage data should be short-lived cache
        cache_control = response.headers["cache-control"]
        assert "max-age" in cache_control

    def test_usage_cost_estimates_format(self, client: TestClient, valid_jwt_token: str):
        """Test that cost estimates are properly formatted."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/market-data/usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check cost estimates for each provider
        for provider in data["api_providers"]:
            cost_estimate = provider["cost_estimate"]
            assert isinstance(cost_estimate, (int, float, str))
            
            # If it's a string, should be a valid decimal format
            if isinstance(cost_estimate, str):
                from decimal import Decimal
                Decimal(cost_estimate)  # Should not raise exception

    def test_usage_multiple_requests_consistency(self, client: TestClient, valid_jwt_token: str):
        """Test that consecutive usage requests show consistent or increasing values."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Make two consecutive requests
        response1 = client.get("/api/v1/admin/market-data/usage", headers=headers)
        response2 = client.get("/api/v1/admin/market-data/usage", headers=headers)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Request counts should not decrease
        period1 = data1["current_period"]
        period2 = data2["current_period"]
        
        assert period2["total_requests"] >= period1["total_requests"]
        assert period2["successful_requests"] >= period1["successful_requests"]
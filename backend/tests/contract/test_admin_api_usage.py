"""
Contract tests for GET /api/v1/admin/api-usage endpoint.

These tests verify the API contract for retrieving API usage metrics.
They MUST FAIL until the admin_market_data_router is implemented.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


class TestAdminApiUsageContract:
    """Contract tests for admin API usage endpoint."""

    def test_api_usage_endpoint_exists(self, client: TestClient, valid_jwt_token: str):
        """Test that the API usage endpoint exists and accepts requests."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/api-usage", headers=headers)
        
        # Should return 200 for successful retrieval
        assert response.status_code == 200
        
        # Should return JSON content
        assert response.headers["content-type"] == "application/json"

    def test_api_usage_requires_authentication(self, client: TestClient):
        """Test that API usage endpoint requires valid authentication."""
        # This test MUST FAIL until the endpoint is implemented
        
        response = client.get("/api/v1/admin/api-usage")
        
        assert response.status_code == 401

    def test_api_usage_response_structure(self, client: TestClient, valid_jwt_token: str):
        """Test that API usage endpoint returns correct response structure."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/api-usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required top-level fields
        assert "summary" in data
        assert "by_provider" in data
        assert "by_date" in data
        assert "rate_limits" in data
        assert "last_updated" in data
        
        # Verify summary structure
        summary = data["summary"]
        assert "total_requests_today" in summary
        assert "total_requests_this_month" in summary
        assert "errors_today" in summary
        assert "success_rate_today" in summary
        
        # Verify data types
        assert isinstance(summary["total_requests_today"], int)
        assert isinstance(summary["total_requests_this_month"], int)
        assert isinstance(summary["errors_today"], int)
        assert isinstance(summary["success_rate_today"], (int, float))

    def test_api_usage_by_provider_structure(self, client: TestClient, valid_jwt_token: str):
        """Test that by_provider section has correct structure."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/api-usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        by_provider = data["by_provider"]
        
        assert isinstance(by_provider, list)
        
        # If there are providers, verify structure
        for provider in by_provider:
            assert "provider_name" in provider
            assert "requests_today" in provider
            assert "requests_this_month" in provider
            assert "errors_today" in provider
            assert "rate_limit_remaining" in provider
            assert "rate_limit_total" in provider
            assert "last_request_at" in provider
            
            # Verify data types
            assert isinstance(provider["provider_name"], str)
            assert isinstance(provider["requests_today"], int)
            assert isinstance(provider["requests_this_month"], int)
            assert isinstance(provider["errors_today"], int)
            assert isinstance(provider["rate_limit_remaining"], int)
            assert isinstance(provider["rate_limit_total"], int)
            
            # Verify provider names are valid
            assert provider["provider_name"] in ["alpha_vantage", "yfinance"]

    def test_api_usage_by_date_structure(self, client: TestClient, valid_jwt_token: str):
        """Test that by_date section has correct structure."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/api-usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        by_date = data["by_date"]
        
        assert isinstance(by_date, list)
        
        # If there are date entries, verify structure
        for date_entry in by_date:
            assert "date" in date_entry
            assert "total_requests" in date_entry
            assert "successful_requests" in date_entry
            assert "failed_requests" in date_entry
            assert "unique_symbols" in date_entry
            
            # Verify data types
            assert isinstance(date_entry["date"], str)
            assert isinstance(date_entry["total_requests"], int)
            assert isinstance(date_entry["successful_requests"], int)
            assert isinstance(date_entry["failed_requests"], int)
            assert isinstance(date_entry["unique_symbols"], int)
            
            # Verify date format (YYYY-MM-DD)
            import re
            assert re.match(r'^\d{4}-\d{2}-\d{2}$', date_entry["date"])

    def test_api_usage_rate_limits_structure(self, client: TestClient, valid_jwt_token: str):
        """Test that rate_limits section has correct structure."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/api-usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        rate_limits = data["rate_limits"]
        
        assert "daily_limit" in rate_limits
        assert "hourly_limit" in rate_limits
        assert "minute_limit" in rate_limits
        assert "current_usage" in rate_limits
        
        # Verify data types
        assert isinstance(rate_limits["daily_limit"], int)
        assert isinstance(rate_limits["hourly_limit"], int)
        assert isinstance(rate_limits["minute_limit"], int)
        
        current_usage = rate_limits["current_usage"]
        assert "daily" in current_usage
        assert "hourly" in current_usage
        assert "minute" in current_usage
        
        assert isinstance(current_usage["daily"], int)
        assert isinstance(current_usage["hourly"], int)
        assert isinstance(current_usage["minute"], int)

    def test_api_usage_timestamp_format(self, client: TestClient, valid_jwt_token: str):
        """Test that timestamps follow ISO 8601 format."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/api-usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify main timestamp format
        from datetime import datetime
        datetime.fromisoformat(data["last_updated"].replace("Z", "+00:00"))
        
        # Verify provider timestamps
        for provider in data["by_provider"]:
            if provider["last_request_at"]:
                datetime.fromisoformat(provider["last_request_at"].replace("Z", "+00:00"))

    def test_api_usage_numeric_constraints(self, client: TestClient, valid_jwt_token: str):
        """Test that numeric values follow logical constraints."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/api-usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        summary = data["summary"]
        
        # All counts should be non-negative
        assert summary["total_requests_today"] >= 0
        assert summary["total_requests_this_month"] >= 0
        assert summary["errors_today"] >= 0
        
        # Success rate should be between 0 and 100
        assert 0 <= summary["success_rate_today"] <= 100
        
        # Monthly requests should be >= daily requests
        assert summary["total_requests_this_month"] >= summary["total_requests_today"]
        
        # Errors should not exceed total requests
        assert summary["errors_today"] <= summary["total_requests_today"]

    def test_api_usage_date_filtering(self, client: TestClient, valid_jwt_token: str):
        """Test that endpoint supports date range filtering."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Test with date range parameters
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        response = client.get(
            f"/api/v1/admin/api-usage?start_date={start_date}&end_date={end_date}",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Should still return proper structure
        assert "by_date" in data
        
        # Date entries should be within the requested range
        for date_entry in data["by_date"]:
            entry_date = date_entry["date"]
            assert start_date <= entry_date <= end_date

    def test_api_usage_provider_filtering(self, client: TestClient, valid_jwt_token: str):
        """Test that endpoint supports provider filtering."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Test filtering by specific provider
        response = client.get("/api/v1/admin/api-usage?provider=alpha_vantage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Should filter by_provider to only include requested provider
        for provider in data["by_provider"]:
            assert provider["provider_name"] == "alpha_vantage"

    def test_api_usage_unauthorized_user(self, client: TestClient):
        """Test API usage endpoint with invalid token."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/api/v1/admin/api-usage", headers=headers)
        
        assert response.status_code == 401

    def test_api_usage_pagination_support(self, client: TestClient, valid_jwt_token: str):
        """Test that endpoint supports pagination for date entries."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Test with limit parameter
        response = client.get("/api/v1/admin/api-usage?limit=5", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Should respect limit for by_date entries
        assert len(data["by_date"]) <= 5
        
        # Test with offset parameter
        response_offset = client.get("/api/v1/admin/api-usage?offset=0&limit=3", headers=headers)
        assert response_offset.status_code == 200

    def test_api_usage_response_caching(self, client: TestClient, valid_jwt_token: str):
        """Test that API usage responses include appropriate caching headers."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/api-usage", headers=headers)
        assert response.status_code == 200
        
        # Should include cache control headers
        assert "cache-control" in response.headers
        # Usage data should be short-lived cache
        cache_control = response.headers["cache-control"]
        assert "max-age" in cache_control or "no-cache" in cache_control

    def test_api_usage_aggregation_consistency(self, client: TestClient, valid_jwt_token: str):
        """Test that aggregated data is mathematically consistent."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/api-usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        summary = data["summary"]
        
        # Calculate totals from by_provider data
        provider_total_today = sum(p["requests_today"] for p in data["by_provider"])
        provider_errors_today = sum(p["errors_today"] for p in data["by_provider"])
        
        # Summary totals should match provider totals (if providers exist)
        if data["by_provider"]:
            assert summary["total_requests_today"] == provider_total_today
            assert summary["errors_today"] == provider_errors_today

    def test_api_usage_rate_limit_consistency(self, client: TestClient, valid_jwt_token: str):
        """Test that rate limit data is logically consistent."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/api-usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        rate_limits = data["rate_limits"]
        current_usage = rate_limits["current_usage"]
        
        # Current usage should not exceed limits
        assert current_usage["daily"] <= rate_limits["daily_limit"]
        assert current_usage["hourly"] <= rate_limits["hourly_limit"]
        assert current_usage["minute"] <= rate_limits["minute_limit"]
        
        # Hourly usage should not exceed daily usage
        assert current_usage["hourly"] <= current_usage["daily"]
        
        # Minute usage should not exceed hourly usage
        assert current_usage["minute"] <= current_usage["hourly"]

    def test_api_usage_provider_rate_limits(self, client: TestClient, valid_jwt_token: str):
        """Test that provider rate limits are within expected ranges."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/api-usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        for provider in data["by_provider"]:
            # Rate limit remaining should not exceed total
            assert provider["rate_limit_remaining"] <= provider["rate_limit_total"]
            
            # Rate limit remaining should be non-negative
            assert provider["rate_limit_remaining"] >= 0
            
            # Requests today should not exceed rate limit total (unless multi-day)
            # This is a soft check as limits might reset
            assert provider["requests_today"] >= 0

    def test_api_usage_error_response_format(self, client: TestClient, valid_jwt_token: str):
        """Test error responses for invalid query parameters."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Test with invalid date format
        response = client.get("/api/v1/admin/api-usage?start_date=invalid-date", headers=headers)
        
        # Should return appropriate error status
        assert response.status_code in [400, 422]
        
        if response.status_code != 404:  # 404 might not have JSON body
            data = response.json()
            # Should follow FastAPI error format
            assert "detail" in data or "error" in data

    def test_api_usage_empty_data_handling(self, client: TestClient, valid_jwt_token: str):
        """Test endpoint behavior when no usage data exists."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/api-usage", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Should return proper structure even with no data
        assert isinstance(data["by_provider"], list)
        assert isinstance(data["by_date"], list)
        assert isinstance(data["summary"]["total_requests_today"], int)
        
        # Totals should be zero if no data
        if not data["by_provider"] and not data["by_date"]:
            assert data["summary"]["total_requests_today"] == 0
            assert data["summary"]["errors_today"] == 0
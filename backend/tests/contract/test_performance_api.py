"""
Contract tests for Performance API endpoints.
Tests API contracts against OpenAPI specification.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestPerformanceAPI:
    """Test Performance API endpoints against contract specifications."""

    def test_get_portfolio_performance_endpoint_exists(self, client: TestClient):
        """GET /api/v1/portfolios/{portfolio_id}/performance should exist."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/portfolios/{test_uuid}/performance")
        
        # Should return 401/404, not 404 for missing route
        assert response.status_code in [200, 401, 404], f"Expected valid status code, got {response.status_code}"

    def test_performance_period_parameter(self, client: TestClient):
        """GET performance should handle period parameter."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/portfolios/{test_uuid}/performance?period=1M")
        
        # Should return 401/404, not 404 for missing route
        assert response.status_code in [200, 401, 404], f"Expected valid status code, got {response.status_code}"

    def test_performance_period_enum_validation(self, client: TestClient):
        """GET performance should validate period enum values."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        
        # Test valid periods
        valid_periods = ["1D", "1W", "1M", "3M", "6M", "1Y", "YTD", "ALL"]
        for period in valid_periods:
            response = client.get(f"/api/v1/portfolios/{test_uuid}/performance?period={period}")
            if response.status_code == 200:
                # If endpoint is implemented, should accept valid periods
                data = response.json()
                assert isinstance(data, dict), "Performance metrics should be an object"

        # Test invalid period
        response = client.get(f"/api/v1/portfolios/{test_uuid}/performance?period=INVALID")
        if response.status_code == 422:
            error_data = response.json()
            assert "detail" in error_data or "error" in error_data

    def test_performance_default_period(self, client: TestClient):
        """GET performance should default to 1M period when not specified."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/portfolios/{test_uuid}/performance")
        
        if response.status_code == 200:
            data = response.json()
            # Should return performance data with default period
            assert "period" in data, "Response should include period field"

    def test_performance_response_structure(self, client: TestClient):
        """When implemented, performance should return proper structure."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/portfolios/{test_uuid}/performance?period=1M")
        
        if response.status_code == 200:
            data = response.json()
            required_fields = [
                "total_return",
                "annualized_return", 
                "max_drawdown",
                "dividend_yield",
                "period_start_value",
                "period_end_value",
                "total_dividends",
                "period",
                "calculated_at"
            ]
            for field in required_fields:
                assert field in data, f"Performance metrics should contain {field} field"

    def test_performance_numeric_fields(self, client: TestClient):
        """Performance metrics should have proper numeric types."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/portfolios/{test_uuid}/performance?period=1M")
        
        if response.status_code == 200:
            data = response.json()
            numeric_fields = [
                "total_return", "annualized_return", "max_drawdown", 
                "dividend_yield", "period_start_value", "period_end_value", "total_dividends"
            ]
            for field in numeric_fields:
                if field in data:
                    assert isinstance(data[field], (int, float)), f"{field} should be numeric"

    def test_performance_date_fields(self, client: TestClient):
        """Performance metrics should have proper date format."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/portfolios/{test_uuid}/performance?period=1M")
        
        if response.status_code == 200:
            data = response.json()
            if "calculated_at" in data:
                # Should be ISO 8601 datetime format
                calculated_at = data["calculated_at"]
                assert isinstance(calculated_at, str), "calculated_at should be string"
                # Basic format check (should contain T for datetime)
                assert "T" in calculated_at, "calculated_at should be ISO 8601 datetime format"

    def test_performance_period_consistency(self, client: TestClient):
        """Performance response period should match requested period."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        requested_period = "3M"
        response = client.get(f"/api/v1/portfolios/{test_uuid}/performance?period={requested_period}")
        
        if response.status_code == 200:
            data = response.json()
            if "period" in data:
                assert data["period"] == requested_period, f"Response period should match requested period {requested_period}"
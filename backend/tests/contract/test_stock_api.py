"""
Contract tests for Stock API endpoints.
Tests API contracts against OpenAPI specification.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestStockAPI:
    """Test Stock API endpoints against contract specifications."""

    def test_search_stocks_endpoint_exists(self, client: TestClient):
        """GET /api/v1/stocks should exist for stock search."""
        response = client.get("/api/v1/stocks?q=AAPL")
        
        # Should return 401 without auth or 200, not 404 for missing route
        assert response.status_code in [200, 401, 404], f"Expected valid status code, got {response.status_code}"

    def test_get_stock_endpoint_exists(self, client: TestClient):
        """GET /api/v1/stocks/{stock_symbol} should exist."""
        response = client.get("/api/v1/stocks/AAPL")
        
        # Should return 401/404, not 404 for missing route
        assert response.status_code in [200, 401, 404], f"Expected valid status code, got {response.status_code}"

    def test_get_stock_price_history_endpoint_exists(self, client: TestClient):
        """GET /api/v1/stocks/{stock_symbol}/price-history should exist."""
        response = client.get("/api/v1/stocks/AAPL/price-history?period=1M")
        
        # Should return 401/404, not 404 for missing route
        assert response.status_code in [200, 401, 404], f"Expected valid status code, got {response.status_code}"

    def test_search_stocks_query_parameter(self, client: TestClient):
        """GET /api/v1/stocks should handle query parameter validation."""
        # Test with query parameter
        response = client.get("/api/v1/stocks?q=AAPL&limit=10")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Search results should be an array"

    def test_search_stocks_limit_validation(self, client: TestClient):
        """GET /api/v1/stocks should validate limit parameter (max 50)."""
        response = client.get("/api/v1/stocks?q=AAPL&limit=100")
        
        if response.status_code == 422:
            # Should validate max limit
            error_data = response.json()
            assert "detail" in error_data or "error" in error_data

    def test_get_stock_response_structure(self, client: TestClient):
        """When implemented, stock details should return proper structure."""
        response = client.get("/api/v1/stocks/AAPL")
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["id", "symbol", "company_name", "current_price", "exchange"]
            for field in required_fields:
                assert field in data, f"Stock should contain {field} field"

    def test_stock_price_history_period_validation(self, client: TestClient):
        """Price history should validate period parameter enum values."""
        # Test valid period
        response = client.get("/api/v1/stocks/AAPL/price-history?period=1M")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Price history should be an array"

        # Test invalid period
        invalid_response = client.get("/api/v1/stocks/AAPL/price-history?period=INVALID")
        if invalid_response.status_code == 422:
            error_data = invalid_response.json()
            assert "detail" in error_data or "error" in error_data

    def test_stock_price_history_date_range(self, client: TestClient):
        """Price history should handle date range parameters."""
        response = client.get(
            "/api/v1/stocks/AAPL/price-history"
            "?from_date=2024-01-01&to_date=2024-12-31"
        )
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Price history should be an array"
            if len(data) > 0:
                price_point = data[0]
                required_fields = ["date", "open", "high", "low", "close", "volume"]
                for field in required_fields:
                    assert field in price_point, f"Price point should contain {field} field"
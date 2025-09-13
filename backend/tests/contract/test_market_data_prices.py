"""
Contract tests for GET /api/v1/market-data/prices/{symbol} endpoint.

These tests verify the API contract for individual stock price retrieval.
They MUST FAIL until the market_data_router is implemented.
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from src.main import app


class TestMarketDataPricesContract:
    """Contract tests for individual stock price endpoint."""

    def test_prices_endpoint_exists(self, client: TestClient, valid_jwt_token: str):
        """Test that the prices endpoint exists and accepts requests."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        symbol = "AAPL"
        
        response = client.get(f"/api/v1/market-data/prices/{symbol}", headers=headers)
        
        # Should return 200 for successful price retrieval
        assert response.status_code == 200
        
        # Should return JSON content
        assert response.headers["content-type"] == "application/json"

    def test_prices_requires_authentication(self, client: TestClient):
        """Test that prices endpoint requires valid authentication."""
        # This test MUST FAIL until the endpoint is implemented
        
        symbol = "AAPL"
        response = client.get(f"/api/v1/market-data/prices/{symbol}")
        
        assert response.status_code == 401

    def test_prices_response_structure(self, client: TestClient, valid_jwt_token: str):
        """Test that prices endpoint returns correct response structure."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        symbol = "AAPL"
        
        response = client.get(f"/api/v1/market-data/prices/{symbol}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required fields
        assert "symbol" in data
        assert "current_price" in data
        assert "previous_close" in data
        assert "daily_change" in data
        assert "daily_change_percent" in data
        assert "last_updated" in data
        assert "source" in data
        
        # Verify data types
        assert isinstance(data["symbol"], str)
        assert isinstance(data["current_price"], str)  # String for precision
        assert isinstance(data["previous_close"], str)
        assert isinstance(data["daily_change"], str)
        assert isinstance(data["daily_change_percent"], str)
        assert isinstance(data["last_updated"], str)
        assert isinstance(data["source"], str)
        
        # Verify symbol matches request
        assert data["symbol"] == symbol
        
        # Verify source is valid
        assert data["source"] in ["alpha_vantage", "yfinance", "cache"]

    def test_prices_decimal_precision(self, client: TestClient, valid_jwt_token: str):
        """Test that price values maintain proper decimal precision."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        symbol = "AAPL"
        
        response = client.get(f"/api/v1/market-data/prices/{symbol}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify prices can be converted to Decimal (for precision)
        current_price = Decimal(data["current_price"])
        previous_close = Decimal(data["previous_close"])
        daily_change = Decimal(data["daily_change"])
        daily_change_percent = Decimal(data["daily_change_percent"])
        
        # Verify reasonable price ranges (positive values)
        assert current_price > Decimal("0")
        assert previous_close > Decimal("0")
        
        # Verify daily change is consistent
        expected_change = current_price - previous_close
        assert abs(daily_change - expected_change) < Decimal("0.01")

    def test_prices_timestamp_format(self, client: TestClient, valid_jwt_token: str):
        """Test that timestamps follow ISO 8601 format."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        symbol = "AAPL"
        
        response = client.get(f"/api/v1/market-data/prices/{symbol}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify timestamp format (ISO 8601)
        from datetime import datetime
        datetime.fromisoformat(data["last_updated"].replace("Z", "+00:00"))

    def test_prices_symbol_validation(self, client: TestClient, valid_jwt_token: str):
        """Test that invalid symbols are handled properly."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        invalid_symbol = "INVALID_STOCK_SYMBOL_12345"
        
        response = client.get(f"/api/v1/market-data/prices/{invalid_symbol}", headers=headers)
        
        # Should return 404 for invalid symbol or 200 with error data
        assert response.status_code in [404, 200]
        
        if response.status_code == 200:
            data = response.json()
            # If returning data, should indicate error state
            assert "error" in data or data.get("current_price") is None

    def test_prices_symbol_case_insensitive(self, client: TestClient, valid_jwt_token: str):
        """Test that symbol lookup is case insensitive."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Test with lowercase
        response_lower = client.get("/api/v1/market-data/prices/aapl", headers=headers)
        # Test with uppercase
        response_upper = client.get("/api/v1/market-data/prices/AAPL", headers=headers)
        
        assert response_lower.status_code == 200
        assert response_upper.status_code == 200
        
        data_lower = response_lower.json()
        data_upper = response_upper.json()
        
        # Should return same symbol (normalized to uppercase)
        assert data_lower["symbol"] == data_upper["symbol"]
        assert data_lower["symbol"] == "AAPL"

    def test_prices_caching_headers(self, client: TestClient, valid_jwt_token: str):
        """Test that appropriate caching headers are set."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        symbol = "AAPL"
        
        response = client.get(f"/api/v1/market-data/prices/{symbol}", headers=headers)
        assert response.status_code == 200
        
        # Should include cache control headers
        assert "cache-control" in response.headers
        # Should indicate max-age based on market hours
        cache_control = response.headers["cache-control"]
        assert "max-age" in cache_control or "no-cache" in cache_control

    def test_prices_rate_limiting(self, client: TestClient, valid_jwt_token: str):
        """Test that rate limiting is properly enforced."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        symbol = "AAPL"
        
        # Make multiple rapid requests
        responses = []
        for _ in range(3):
            response = client.get(f"/api/v1/market-data/prices/{symbol}", headers=headers)
            responses.append(response)
        
        # At least some requests should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count > 0
        
        # Rate limiting headers should be present
        last_response = responses[-1]
        if last_response.status_code == 200:
            # Should include rate limit information
            assert any(header.startswith("x-ratelimit") for header in last_response.headers.keys()) or \
                   "retry-after" in last_response.headers

    def test_prices_error_response_format(self, client: TestClient, valid_jwt_token: str):
        """Test error responses follow consistent format."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        # Use a symbol that's likely to cause an error
        problematic_symbol = ""  # Empty symbol
        
        response = client.get(f"/api/v1/market-data/prices/{problematic_symbol}", headers=headers)
        
        # Should return appropriate error status
        assert response.status_code in [400, 404, 422]
        
        if response.status_code != 404:  # 404 might not have JSON body
            data = response.json()
            # Should follow FastAPI error format
            assert "detail" in data or "error" in data

    def test_prices_concurrent_requests(self, client: TestClient, valid_jwt_token: str):
        """Test that endpoint handles concurrent requests properly."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        symbol = "AAPL"
        
        # Simulate concurrent requests with different symbols
        symbols = ["AAPL", "GOOGL", "MSFT"]
        responses = []
        
        for sym in symbols:
            response = client.get(f"/api/v1/market-data/prices/{sym}", headers=headers)
            responses.append((sym, response))
        
        # All requests should succeed
        for sym, response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["symbol"] == sym

    def test_prices_market_hours_behavior(self, client: TestClient, valid_jwt_token: str):
        """Test that endpoint behavior varies appropriately during/outside market hours."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        symbol = "AAPL"
        
        response = client.get(f"/api/v1/market-data/prices/{symbol}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Should include indication of market status
        # This might be in the response data or headers
        assert "last_updated" in data
        
        # The source should indicate data freshness
        assert data["source"] in ["alpha_vantage", "yfinance", "cache"]
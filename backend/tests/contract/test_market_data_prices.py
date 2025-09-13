"""
Contract tests for market data price endpoints.

These tests verify the API contract for fetching stock prices.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


class TestMarketDataPricesContract:
    """Contract tests for market data price endpoints."""

    def test_get_single_price_endpoint_exists(self, client: TestClient, valid_jwt_token: str):
        """Test that the single price endpoint exists and accepts requests."""

        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = client.get("/api/v1/market-data/prices/AAPL", headers=headers)

        # Should return 200 for successful retrieval or 404 if not available
        assert response.status_code in [200, 404]

        # Should return JSON content
        assert response.headers["content-type"] == "application/json"

    def test_get_single_price_requires_authentication(self, client: TestClient):
        """Test that single price endpoint requires valid authentication."""

        response = client.get("/api/v1/market-data/prices/AAPL")

        assert response.status_code == 401

    def test_get_single_price_response_structure(self, client: TestClient, valid_jwt_token: str):
        """Test that single price endpoint returns correct response structure when successful."""

        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = client.get("/api/v1/market-data/prices/AAPL", headers=headers)

        if response.status_code == 200:
            data = response.json()

            # Verify required fields
            assert "symbol" in data
            assert "price" in data
            assert "fetched_at" in data
            assert "cached" in data

            # Verify data types
            assert isinstance(data["symbol"], str)
            assert isinstance(data["price"], (int, float))
            assert isinstance(data["fetched_at"], str)
            assert isinstance(data["cached"], bool)

            # Verify symbol matches request
            assert data["symbol"] == "AAPL"

    def test_get_bulk_prices_endpoint_exists(self, client: TestClient, valid_jwt_token: str):
        """Test that the bulk prices endpoint exists and accepts requests."""

        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = client.get("/api/v1/market-data/prices?symbols=AAPL&symbols=GOOGL", headers=headers)

        # Should return 200 for successful retrieval
        assert response.status_code == 200

        # Should return JSON content
        assert response.headers["content-type"] == "application/json"

    def test_get_bulk_prices_requires_authentication(self, client: TestClient):
        """Test that bulk prices endpoint requires valid authentication."""

        response = client.get("/api/v1/market-data/prices?symbols=AAPL&symbols=GOOGL")

        assert response.status_code == 401

    def test_get_bulk_prices_response_structure(self, client: TestClient, valid_jwt_token: str):
        """Test that bulk prices endpoint returns correct response structure."""

        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = client.get("/api/v1/market-data/prices?symbols=AAPL&symbols=GOOGL", headers=headers)
        assert response.status_code == 200

        data = response.json()

        # Verify required top-level fields
        assert "prices" in data
        assert "fetched_at" in data
        assert "cached_count" in data
        assert "fresh_count" in data

        # Verify data types
        assert isinstance(data["prices"], dict)
        assert isinstance(data["fetched_at"], str)
        assert isinstance(data["cached_count"], int)
        assert isinstance(data["fresh_count"], int)

        # Verify price entries have correct structure
        for symbol, price_data in data["prices"].items():
            assert "symbol" in price_data
            assert "price" in price_data
            assert "fetched_at" in price_data
            assert "cached" in price_data

    def test_get_service_status_endpoint_exists(self, client: TestClient, valid_jwt_token: str):
        """Test that the service status endpoint exists and accepts requests."""

        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = client.get("/api/v1/market-data/status", headers=headers)

        # Should return 200 for successful retrieval
        assert response.status_code == 200

        # Should return JSON content
        assert response.headers["content-type"] == "application/json"

    def test_get_service_status_requires_authentication(self, client: TestClient):
        """Test that service status endpoint requires valid authentication."""

        response = client.get("/api/v1/market-data/status")

        assert response.status_code == 401

    def test_refresh_prices_endpoint_exists(self, client: TestClient, valid_jwt_token: str):
        """Test that the refresh prices endpoint exists and accepts requests."""

        headers = {
            "Authorization": f"Bearer {valid_jwt_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "symbols": ["AAPL", "GOOGL"],
            "force": False
        }

        response = client.post("/api/v1/market-data/refresh", headers=headers, json=payload)

        # Should return 200 for successful refresh
        assert response.status_code == 200

        # Should return JSON content
        assert response.headers["content-type"] == "application/json"

    def test_refresh_prices_requires_authentication(self, client: TestClient):
        """Test that refresh prices endpoint requires valid authentication."""

        payload = {
            "symbols": ["AAPL", "GOOGL"],
            "force": False
        }

        response = client.post("/api/v1/market-data/refresh", json=payload)

        assert response.status_code == 401

    def test_stream_endpoint_exists(self, client: TestClient, valid_jwt_token: str):
        """Test that the SSE stream endpoint exists and accepts requests."""

        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = client.get("/api/v1/market-data/stream?symbols=AAPL", headers=headers)

        # Should return 200 for successful stream connection
        assert response.status_code == 200

        # Should return event-stream content type
        assert "text/event-stream" in response.headers["content-type"]

    def test_stream_requires_authentication(self, client: TestClient):
        """Test that SSE stream endpoint requires valid authentication."""

        response = client.get("/api/v1/market-data/stream?symbols=AAPL")

        assert response.status_code == 401
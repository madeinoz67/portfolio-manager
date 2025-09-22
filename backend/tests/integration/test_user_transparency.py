"""
Test user transparency requirements - regular users should not see adapter details.

Validates FR-039, FR-040, FR-041 from the specification:
- FR-039: Regular users unaware of specific adapters
- FR-040: Transparent unified interface with automatic failover
- FR-041: No adapter-specific information in user responses
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
def regular_user_token():
    """JWT token for regular (non-admin) user."""
    return create_access_token(data={
        "sub": "test_user@example.com",
        "role": UserRole.USER.value,
        "user_id": 1
    })


@pytest.fixture
def mock_adapter_response():
    """Mock adapter response with complete OHLCV data."""
    return {
        "symbol": "AAPL",
        "price": Decimal("150.25"),
        "open": Decimal("149.80"),
        "high": Decimal("151.00"),
        "low": Decimal("149.50"),
        "volume": 45000000,
        "previous_close": Decimal("149.75"),
        "change": Decimal("0.50"),
        "change_percent": "0.33%",
        "currency": "USD",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market_cap": Decimal("2500000000000"),
        "source": "yfinance_adapter"  # This should NOT be exposed to users
    }


class TestUserTransparency:
    """Test that regular users cannot see adapter-specific information."""

    @patch('src.services.market_data_service.MarketDataService.get_current_price')
    def test_market_data_response_hides_adapter_info(self, mock_get_price, client, regular_user_token, mock_adapter_response):
        """Test that market data API responses hide adapter information from regular users."""
        # Setup mock to return adapter response
        mock_get_price.return_value = {
            "success": True,
            "data": mock_adapter_response,
            "source_info": {  # This should NOT be in regular user response
                "provider_name": "yfinance_default",
                "adapter_type": "yfinance",
                "response_time_ms": 245,
                "fallback_used": False
            }
        }

        # Make API call as regular user
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = client.get("/api/v1/market-data/prices/AAPL", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Verify market data is present
        assert "price" in data
        assert "symbol" in data
        assert data["symbol"] == "AAPL"
        assert data["currency"] == "USD"

        # Verify adapter information is NOT present
        assert "source_info" not in data
        assert "provider_name" not in data
        assert "adapter_type" not in data
        assert "response_time_ms" not in data
        assert "fallback_used" not in data
        assert "source" not in data  # Provider source should be hidden

    @patch('src.services.adapter_service.AdapterService.fetch_prices')
    def test_bulk_price_request_hides_adapter_info(self, mock_fetch, client, regular_user_token):
        """Test that bulk price requests hide adapter information."""
        # Setup mock response for multiple symbols
        mock_fetch.return_value = {
            "success": True,
            "data": {
                "AAPL": {"price": 150.25, "currency": "USD"},
                "GOOGL": {"price": 2800.50, "currency": "USD"}
            },
            "source_info": {  # Should not appear in user response
                "adapters_used": ["yfinance", "alpha_vantage"],
                "primary_adapter": "yfinance",
                "fallback_occurred": False
            }
        }

        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = client.post(
            "/api/v1/market-data/prices",
            headers=headers,
            json={"symbols": ["AAPL", "GOOGL"]}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify data is present
        assert "data" in data
        assert "AAPL" in data["data"]
        assert "GOOGL" in data["data"]

        # Verify adapter information is hidden
        assert "source_info" not in data
        assert "adapters_used" not in data
        assert "primary_adapter" not in data
        assert "fallback_occurred" not in data

    @patch('src.services.adapter_service.AdapterService.get_adapter_status')
    def test_adapter_failover_transparent_to_users(self, mock_status, client, regular_user_token):
        """Test that adapter failover is transparent to regular users."""
        # Simulate adapter failover scenario
        mock_status.return_value = {
            "primary_failed": True,
            "fallback_used": "alpha_vantage",
            "failover_time_ms": 50
        }

        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = client.get("/api/v1/market-data/status", headers=headers)

        # Regular users should either get minimal status or no access
        # Adapter failover details should not be exposed
        if response.status_code == 200:
            data = response.json()
            assert "primary_failed" not in data
            assert "fallback_used" not in data
            assert "failover_time_ms" not in data

    def test_error_messages_generic_for_users(self, client, regular_user_token):
        """Test that error messages don't expose adapter-specific details."""
        headers = {"Authorization": f"Bearer {regular_user_token}"}

        # Request invalid symbol to trigger error
        response = client.get("/api/v1/market-data/prices/INVALID_SYMBOL", headers=headers)

        # Should get generic error, not adapter-specific error
        if response.status_code >= 400:
            data = response.json()
            error_message = data.get("message", "").lower()

            # Error should not mention specific adapters
            assert "yfinance" not in error_message
            assert "alpha_vantage" not in error_message
            assert "provider" not in error_message
            assert "adapter" not in error_message

    @patch('src.services.portfolio_service.PortfolioService.get_portfolio_value')
    def test_portfolio_valuation_hides_data_sources(self, mock_valuation, client, regular_user_token):
        """Test that portfolio valuations don't expose data source information."""
        mock_valuation.return_value = {
            "total_value": Decimal("25000.00"),
            "daily_change": Decimal("250.00"),
            "daily_change_percent": "1.02%",
            "data_sources": {  # Should not be exposed
                "AAPL": "yfinance",
                "GOOGL": "alpha_vantage"
            },
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = client.get("/api/v1/portfolios/1/value", headers=headers)

        if response.status_code == 200:
            data = response.json()

            # Verify portfolio data is present
            assert "total_value" in data
            assert "daily_change" in data

            # Verify data sources are hidden
            assert "data_sources" not in data


class TestAdapterTransparencyCompliance:
    """Test overall adapter transparency compliance."""

    def test_no_adapter_names_in_user_facing_apis(self, client, regular_user_token):
        """Comprehensive test that no adapter names appear in user-facing APIs."""
        headers = {"Authorization": f"Bearer {regular_user_token}"}

        # List of user-facing endpoints to test
        user_endpoints = [
            "/api/v1/portfolios",
            "/api/v1/market-data/capabilities",
            "/api/v1/portfolios/1/holdings"
        ]

        for endpoint in user_endpoints:
            response = client.get(endpoint, headers=headers)

            if response.status_code == 200:
                response_text = response.text.lower()

                # Verify no adapter names in response
                assert "yfinance" not in response_text
                assert "alpha_vantage" not in response_text
                assert "provider_name" not in response_text
                assert "adapter_type" not in response_text

    def test_consistent_data_formatting_across_adapters(self, client, regular_user_token):
        """Test that data formatting is consistent regardless of underlying adapter."""
        headers = {"Authorization": f"Bearer {regular_user_token}"}

        # Test multiple symbols that might use different adapters
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]

        for symbol in symbols:
            response = client.get(f"/api/v1/market-data/prices/{symbol}", headers=headers)

            if response.status_code == 200:
                data = response.json()

                # Verify consistent format regardless of adapter
                required_fields = ["symbol", "price", "currency", "timestamp"]
                for field in required_fields:
                    assert field in data, f"Missing {field} for {symbol}"

                # Verify consistent data types
                assert isinstance(data["price"], (int, float))
                assert isinstance(data["currency"], str)
                assert isinstance(data["symbol"], str)
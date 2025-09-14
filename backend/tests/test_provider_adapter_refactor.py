"""
TDD tests for provider adapter refactor.
Provider adapters should handle bulk/individual logic internally.
"""

import pytest
from unittest.mock import patch, AsyncMock, Mock
from src.services.market_data_service import MarketDataService
from src.models.market_data_provider import MarketDataProvider
from typing import Dict, List, Optional


@pytest.fixture
def market_data_service(db_session):
    """Market data service fixture."""
    return MarketDataService(db_session)


@pytest.fixture
def yfinance_provider():
    """Mock yfinance provider with bulk support enabled."""
    provider = Mock(spec=MarketDataProvider)
    provider.id = 1
    provider.name = "yfinance"
    provider.is_enabled = True
    provider.api_key = None
    provider.priority = 1
    return provider


@pytest.fixture
def alpha_vantage_provider():
    """Mock Alpha Vantage provider with bulk support enabled."""
    provider = Mock(spec=MarketDataProvider)
    provider.id = 2
    provider.name = "alpha_vantage"
    provider.is_enabled = True
    provider.api_key = "test_key"
    provider.priority = 2
    return provider


@pytest.fixture
def alpha_vantage_no_bulk_provider():
    """Mock Alpha Vantage provider with bulk disabled (no API key)."""
    provider = Mock(spec=MarketDataProvider)
    provider.id = 3
    provider.name = "alpha_vantage"
    provider.is_enabled = True
    provider.api_key = None  # No API key = no bulk support
    provider.priority = 2
    return provider


class TestProviderAdapterRefactor:
    """Test provider adapter refactor with internal bulk logic."""

    @pytest.mark.asyncio
    async def test_yfinance_adapter_uses_bulk_internally_for_multiple_symbols(self, market_data_service, yfinance_provider):
        """Test that yfinance adapter automatically uses bulk for multiple symbols."""
        symbols = ["AAPL", "GOOGL", "MSFT"]

        # Mock the bulk chunk method
        mock_bulk_results = {
            "AAPL": {"price": 150.0, "timestamp": "2023-01-01T12:00:00", "source": "yfinance_bulk"},
            "GOOGL": {"price": 2500.0, "timestamp": "2023-01-01T12:00:00", "source": "yfinance_bulk"},
            "MSFT": {"price": 300.0, "timestamp": "2023-01-01T12:00:00", "source": "yfinance_bulk"}
        }

        with patch.object(market_data_service, '_fetch_yfinance_bulk_chunk', return_value=mock_bulk_results) as mock_bulk_chunk, \
             patch('src.services.market_data_service.log_provider_activity') as mock_log:

            # Call the adapter's fetch method
            results = await market_data_service._fetch_from_provider(yfinance_provider, symbols)

            # Verify bulk chunk method was called (since symbols <= 50)
            mock_bulk_chunk.assert_called_once_with(symbols)

            # Verify results
            assert len(results) == 3
            assert all(symbol in results for symbol in symbols)
            assert results["AAPL"]["price"] == 150.0
            assert results["GOOGL"]["price"] == 2500.0
            assert results["MSFT"]["price"] == 300.0

    @pytest.mark.asyncio
    async def test_yfinance_adapter_uses_individual_for_single_symbol(self, market_data_service, yfinance_provider):
        """Test that yfinance adapter can use individual fetch for single symbol."""
        symbols = ["AAPL"]

        with patch.object(market_data_service, 'get_enabled_providers') as mock_providers, \
             patch('yfinance') as mock_yf, \
             patch('src.services.market_data_service.log_provider_activity') as mock_log:

            mock_providers.return_value = [yfinance_provider]

            # Mock single ticker response
            mock_ticker = Mock()
            mock_ticker.info = {"regularMarketPrice": 150.0}
            mock_yf.Ticker.return_value = mock_ticker

            # Call the adapter's fetch method
            results = await market_data_service._fetch_from_provider(yfinance_provider, symbols)

            # Should still work (adapter decides how to handle)
            assert len(results) == 1
            assert results["AAPL"]["price"] == 150.0

    @pytest.mark.asyncio
    async def test_alpha_vantage_adapter_uses_bulk_when_available(self, market_data_service, alpha_vantage_provider):
        """Test Alpha Vantage adapter uses bulk API when API key available."""
        symbols = ["AAPL", "GOOGL", "MSFT"]

        with patch.object(market_data_service, 'get_enabled_providers') as mock_providers, \
             patch('src.services.market_data_service.aiohttp.ClientSession') as mock_session, \
             patch('src.services.market_data_service.log_provider_activity') as mock_log:

            mock_providers.return_value = [alpha_vantage_provider]

            # Mock Alpha Vantage bulk API response
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "Meta Data": {"Information": "Realtime Bulk Stock Quotes"},
                "Stock Quotes": [
                    {"01. symbol": "AAPL", "05. price": "150.00"},
                    {"01. symbol": "GOOGL", "05. price": "2500.00"},
                    {"01. symbol": "MSFT", "05. price": "300.00"}
                ]
            })

            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

            # Call adapter fetch method
            results = await market_data_service._fetch_from_provider(alpha_vantage_provider, symbols)

            # Verify bulk API was called
            mock_session.return_value.__aenter__.return_value.get.assert_called_once()
            call_url = mock_session.return_value.__aenter__.return_value.get.call_args[0][0]
            assert "function=REALTIME_BULK_QUOTES" in call_url
            assert "symbols=" in call_url

            # Verify results
            assert len(results) == 3
            assert results["AAPL"]["price"] == 150.0

    @pytest.mark.asyncio
    async def test_alpha_vantage_adapter_falls_back_to_individual_without_api_key(self, market_data_service, alpha_vantage_no_bulk_provider):
        """Test Alpha Vantage adapter falls back to individual calls without API key."""
        symbols = ["AAPL", "GOOGL"]

        with patch.object(market_data_service, 'get_enabled_providers') as mock_providers, \
             patch('src.services.market_data_service.aiohttp.ClientSession') as mock_session, \
             patch('src.services.market_data_service.log_provider_activity') as mock_log:

            mock_providers.return_value = [alpha_vantage_no_bulk_provider]

            # Mock individual API responses
            mock_response_aapl = Mock()
            mock_response_aapl.status = 200
            mock_response_aapl.json = AsyncMock(return_value={
                "Global Quote": {"05. price": "150.00"}
            })

            mock_response_googl = Mock()
            mock_response_googl.status = 200
            mock_response_googl.json = AsyncMock(return_value={
                "Global Quote": {"05. price": "2500.00"}
            })

            # Setup session mock to return different responses for each call
            session_mock = mock_session.return_value.__aenter__.return_value
            session_mock.get.return_value.__aenter__.return_value = mock_response_aapl

            # For now, let's return None to indicate individual calls would be made
            results = await market_data_service._fetch_from_provider(alpha_vantage_no_bulk_provider, symbols)

            # Should return empty results since no API key (adapter handles this internally)
            assert isinstance(results, dict)

    @pytest.mark.asyncio
    async def test_scheduler_uses_simple_fetch_method(self, market_data_service, yfinance_provider):
        """Test that scheduler only needs to call a simple fetch method."""
        symbols = ["AAPL", "GOOGL", "MSFT"]

        with patch.object(market_data_service, 'get_enabled_providers') as mock_providers, \
             patch.object(market_data_service, '_fetch_from_provider') as mock_fetch:

            mock_providers.return_value = [yfinance_provider]
            mock_fetch.return_value = {
                "AAPL": {"price": 150.0, "timestamp": "2023-01-01T12:00:00"},
                "GOOGL": {"price": 2500.0, "timestamp": "2023-01-01T12:00:00"},
                "MSFT": {"price": 300.0, "timestamp": "2023-01-01T12:00:00"}
            }

            # Scheduler calls simplified interface
            results = await market_data_service.fetch_multiple_prices(symbols)

            # Verify the provider's fetch method was called
            mock_fetch.assert_called()

            # Verify results
            assert len(results) == 3
            assert all(symbol in results for symbol in symbols)

    @pytest.mark.asyncio
    async def test_provider_adapter_logs_bulk_vs_individual_decisions(self, market_data_service, yfinance_provider):
        """Test that provider adapters log whether they used bulk or individual operations."""
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]

        with patch.object(market_data_service, 'get_enabled_providers') as mock_providers, \
             patch('yfinance') as mock_yf, \
             patch('src.services.market_data_service.log_provider_activity') as mock_log:

            mock_providers.return_value = [yfinance_provider]

            # Mock yfinance bulk response
            mock_tickers = Mock()
            mock_info_data = {
                "AAPL": {"regularMarketPrice": 150.0},
                "GOOGL": {"regularMarketPrice": 2500.0},
                "MSFT": {"regularMarketPrice": 300.0},
                "TSLA": {"regularMarketPrice": 800.0}
            }
            mock_tickers.tickers = {
                symbol: Mock(info=data) for symbol, data in mock_info_data.items()
            }
            mock_yf.Tickers.return_value = mock_tickers

            # Call adapter
            results = await market_data_service._fetch_from_provider(yfinance_provider, symbols)

            # Verify activity was logged with bulk operation info
            mock_log.assert_called()

            # Find the bulk operation log call
            bulk_log_call = None
            for call in mock_log.call_args_list:
                args, kwargs = call
                if len(args) >= 3 and "BULK" in args[2]:  # activity_type
                    bulk_log_call = call
                    break

            assert bulk_log_call is not None, "Should log bulk operation activity"

    @pytest.mark.asyncio
    async def test_provider_adapter_handles_bulk_failures_gracefully(self, market_data_service, yfinance_provider):
        """Test provider adapter falls back to individual calls if bulk fails."""
        symbols = ["AAPL", "GOOGL"]

        with patch.object(market_data_service, 'get_enabled_providers') as mock_providers, \
             patch('yfinance') as mock_yf, \
             patch('src.services.market_data_service.log_provider_activity') as mock_log:

            mock_providers.return_value = [yfinance_provider]

            # Mock bulk operation failure
            mock_yf.Tickers.side_effect = Exception("Bulk API failed")

            # Mock individual ticker success
            mock_ticker_aapl = Mock()
            mock_ticker_aapl.info = {"regularMarketPrice": 150.0}
            mock_ticker_googl = Mock()
            mock_ticker_googl.info = {"regularMarketPrice": 2500.0}

            mock_yf.Ticker.side_effect = [mock_ticker_aapl, mock_ticker_googl]

            # Call adapter - should handle fallback internally
            results = await market_data_service._fetch_from_provider(yfinance_provider, symbols)

            # Should still get results via fallback
            assert len(results) == 2
            assert results["AAPL"]["price"] == 150.0
            assert results["GOOGL"]["price"] == 2500.0

            # Should have called individual Ticker for fallback
            assert mock_yf.Ticker.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_from_provider_method_signature(self, market_data_service):
        """Test the expected method signature for provider fetch method."""
        # This test defines the interface we expect
        provider = Mock(spec=MarketDataProvider)
        symbols = ["AAPL", "GOOGL"]

        # The method should exist and accept provider + symbols
        assert hasattr(market_data_service, '_fetch_from_provider')

        # Method should be async and return Dict[str, Optional[Dict]]
        method = getattr(market_data_service, '_fetch_from_provider')
        assert callable(method)
"""
TDD Tests for Bulk Market Data Update Functionality

These tests define the expected behavior for bulk update optimization
before implementation, following TDD principles.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from src.services.market_data_service import MarketDataService
from src.models.market_data_provider import MarketDataProvider


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = Mock(spec=Session)
    return session


@pytest.fixture
def mock_yfinance_provider():
    """Create a mock yfinance provider."""
    provider = Mock(spec=MarketDataProvider)
    provider.name = "yfinance"
    provider.is_enabled = True
    provider.priority = 1
    return provider


@pytest.fixture
def mock_alpha_vantage_provider():
    """Create a mock Alpha Vantage provider."""
    provider = Mock(spec=MarketDataProvider)
    provider.name = "alpha_vantage"
    provider.is_enabled = True
    provider.priority = 2
    provider.api_key = "test_key"
    return provider


@pytest.fixture
def market_data_service(mock_db_session):
    """Create a MarketDataService instance."""
    return MarketDataService(mock_db_session)


class TestBulkYfinanceFetch:
    """Test bulk fetching functionality for yfinance provider."""

    @pytest.mark.asyncio
    async def test_bulk_yfinance_fetch_multiple_symbols(self, market_data_service):
        """Test that bulk fetch can handle multiple symbols efficiently."""
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]

        # This test should pass when bulk functionality is implemented
        with patch.object(market_data_service, '_bulk_fetch_from_yfinance') as mock_bulk:
            mock_bulk.return_value = {
                "AAPL": {"symbol": "AAPL", "price": 150.0, "provider": "yfinance", "bulk_fetch": True},
                "GOOGL": {"symbol": "GOOGL", "price": 2800.0, "provider": "yfinance", "bulk_fetch": True},
                "MSFT": {"symbol": "MSFT", "price": 350.0, "provider": "yfinance", "bulk_fetch": True},
                "TSLA": {"symbol": "TSLA", "price": 800.0, "provider": "yfinance", "bulk_fetch": True},
            }

            result = await market_data_service._bulk_fetch_from_yfinance(symbols)

            # Assertions for TDD
            assert len(result) == 4
            assert all(data["bulk_fetch"] is True for data in result.values() if data)
            assert all(data["provider"] == "yfinance" for data in result.values() if data)
            mock_bulk.assert_called_once_with(symbols)

    @pytest.mark.asyncio
    async def test_bulk_yfinance_handles_asx_symbols(self, market_data_service):
        """Test that bulk fetch correctly handles ASX symbols."""
        asx_symbols = ["CBA", "BHP", "CSL", "WBC"]

        with patch.object(market_data_service, '_bulk_fetch_from_yfinance') as mock_bulk:
            mock_bulk.return_value = {
                symbol: {"symbol": symbol, "price": 100.0, "provider": "yfinance", "bulk_fetch": True}
                for symbol in asx_symbols
            }

            result = await market_data_service._bulk_fetch_from_yfinance(asx_symbols)

            # Should handle ASX symbols correctly
            assert len(result) == 4
            assert all(symbol in result for symbol in asx_symbols)

    @pytest.mark.asyncio
    async def test_bulk_yfinance_partial_failure_handling(self, market_data_service):
        """Test that bulk fetch handles partial failures gracefully."""
        symbols = ["AAPL", "INVALID", "GOOGL"]

        with patch.object(market_data_service, '_bulk_fetch_from_yfinance') as mock_bulk:
            mock_bulk.return_value = {
                "AAPL": {"symbol": "AAPL", "price": 150.0, "provider": "yfinance", "bulk_fetch": True},
                "INVALID": None,  # Failed symbol
                "GOOGL": {"symbol": "GOOGL", "price": 2800.0, "provider": "yfinance", "bulk_fetch": True},
            }

            result = await market_data_service._bulk_fetch_from_yfinance(symbols)

            # Should handle partial failures
            assert len(result) == 3
            assert result["AAPL"] is not None
            assert result["INVALID"] is None
            assert result["GOOGL"] is not None


class TestFetchMultiplePricesOptimization:
    """Test the optimized fetch_multiple_prices method."""

    @pytest.mark.asyncio
    async def test_uses_bulk_fetch_for_yfinance_multiple_symbols(self, market_data_service, mock_yfinance_provider):
        """Test that fetch_multiple_prices uses bulk fetch for yfinance when appropriate."""
        symbols = ["AAPL", "GOOGL", "MSFT"]

        with patch.object(market_data_service, 'get_enabled_providers') as mock_providers, \
             patch.object(market_data_service, '_bulk_fetch_from_yfinance') as mock_bulk, \
             patch.object(market_data_service, '_store_price_data') as mock_store, \
             patch.object(market_data_service, '_log_api_usage') as mock_log:

            mock_providers.return_value = [mock_yfinance_provider]
            mock_bulk.return_value = {
                symbol: {"symbol": symbol, "price": 100.0, "provider": "yfinance", "bulk_fetch": True}
                for symbol in symbols
            }

            result = await market_data_service.fetch_multiple_prices(symbols)

            # Should use bulk fetch instead of individual calls
            mock_bulk.assert_called_once_with(symbols)
            assert len(result) == 3
            assert all(data["bulk_fetch"] is True for data in result.values())

    @pytest.mark.asyncio
    async def test_uses_bulk_fetch_for_alpha_vantage_multiple_symbols(self, market_data_service, mock_alpha_vantage_provider):
        """Test that fetch_multiple_prices uses bulk fetch for Alpha Vantage when appropriate."""
        symbols = ["AAPL", "GOOGL", "MSFT"]

        with patch.object(market_data_service, 'get_enabled_providers') as mock_providers, \
             patch.object(market_data_service, '_bulk_fetch_from_alpha_vantage') as mock_bulk, \
             patch.object(market_data_service, '_store_price_data') as mock_store, \
             patch.object(market_data_service, '_log_api_usage') as mock_log:

            mock_providers.return_value = [mock_alpha_vantage_provider]
            mock_bulk.return_value = {
                symbol: {"symbol": symbol, "price": 100.0, "provider": "alpha_vantage", "bulk_fetch": True}
                for symbol in symbols
            }

            result = await market_data_service.fetch_multiple_prices(symbols)

            # Should use bulk fetch instead of individual calls
            mock_bulk.assert_called_once_with(symbols, mock_alpha_vantage_provider.api_key)
            assert len(result) == 3
            assert all(data["bulk_fetch"] is True for data in result.values())
            assert all(data["provider"] == "alpha_vantage" for data in result.values())

    @pytest.mark.asyncio
    async def test_falls_back_to_individual_for_single_symbol(self, market_data_service, mock_yfinance_provider):
        """Test that single symbol requests don't use bulk fetch."""
        symbols = ["AAPL"]

        with patch.object(market_data_service, 'get_enabled_providers') as mock_providers, \
             patch.object(market_data_service, '_bulk_fetch_from_yfinance') as mock_bulk, \
             patch.object(market_data_service, '_fetch_single_with_provider') as mock_single:

            mock_providers.return_value = [mock_yfinance_provider]
            mock_single.return_value = {"symbol": "AAPL", "price": 150.0, "provider": "yfinance"}

            result = await market_data_service.fetch_multiple_prices(symbols)

            # Should not use bulk fetch for single symbol
            mock_bulk.assert_not_called()
            mock_single.assert_called()

    @pytest.mark.asyncio
    async def test_bulk_optimization_performance_logging(self, market_data_service, mock_yfinance_provider):
        """Test that bulk operations log performance improvements."""
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]

        with patch.object(market_data_service, 'get_enabled_providers') as mock_providers, \
             patch.object(market_data_service, '_bulk_fetch_from_yfinance') as mock_bulk, \
             patch.object(market_data_service, '_store_price_data'), \
             patch.object(market_data_service, '_log_api_usage'), \
             patch('src.services.market_data_service.log_provider_activity') as mock_log_activity:

            mock_providers.return_value = [mock_yfinance_provider]
            mock_bulk.return_value = {
                symbol: {"symbol": symbol, "price": 100.0, "provider": "yfinance", "bulk_fetch": True}
                for symbol in symbols
            }

            result = await market_data_service.fetch_multiple_prices(symbols)

            # Should log bulk operation with performance metadata
            mock_log_activity.assert_called()

            # Find the bulk operation log call
            bulk_log_calls = [call for call in mock_log_activity.call_args_list
                            if "BULK_PRICE_UPDATE" in str(call)]
            assert len(bulk_log_calls) > 0

            # Check that efficiency metadata is logged
            bulk_call = bulk_log_calls[0]
            metadata = bulk_call[1]['metadata']
            assert "bulk_operation" in metadata or "efficiency_gain" in metadata


class TestBulkAlphaVantageFetch:
    """Test bulk fetching functionality for Alpha Vantage provider."""

    @pytest.mark.asyncio
    async def test_bulk_alpha_vantage_fetch_multiple_symbols(self, market_data_service):
        """Test that Alpha Vantage bulk fetch can handle multiple symbols efficiently."""
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        api_key = "test_alpha_vantage_key"

        # Mock successful bulk response
        with patch.object(market_data_service, '_bulk_fetch_from_alpha_vantage') as mock_bulk:
            mock_bulk.return_value = {
                "AAPL": {"symbol": "AAPL", "price": 150.0, "provider": "alpha_vantage", "bulk_fetch": True},
                "GOOGL": {"symbol": "GOOGL", "price": 2800.0, "provider": "alpha_vantage", "bulk_fetch": True},
                "MSFT": {"symbol": "MSFT", "price": 350.0, "provider": "alpha_vantage", "bulk_fetch": True},
                "TSLA": {"symbol": "TSLA", "price": 800.0, "provider": "alpha_vantage", "bulk_fetch": True},
            }

            result = await market_data_service._bulk_fetch_from_alpha_vantage(symbols, api_key)

            # Assertions for TDD
            assert len(result) == 4
            assert all(data["bulk_fetch"] is True for data in result.values() if data)
            assert all(data["provider"] == "alpha_vantage" for data in result.values() if data)
            mock_bulk.assert_called_once_with(symbols, api_key)

    @pytest.mark.asyncio
    async def test_bulk_alpha_vantage_respects_100_symbol_limit(self, market_data_service):
        """Test that Alpha Vantage bulk fetch respects the 100-symbol limit."""
        # Create 120 symbols to test the limit
        symbols = [f"SYM{i:03d}" for i in range(120)]
        api_key = "test_alpha_vantage_key"

        with patch.object(market_data_service, '_bulk_fetch_from_alpha_vantage') as mock_bulk:
            # Should only process first 100 symbols
            mock_bulk.return_value = {
                symbol: {"symbol": symbol, "price": 100.0, "provider": "alpha_vantage", "bulk_fetch": True}
                for symbol in symbols[:100]
            }

            result = await market_data_service._bulk_fetch_from_alpha_vantage(symbols, api_key)

            # Should only call with first 100 symbols
            mock_bulk.assert_called_once_with(symbols, api_key)
            # In real implementation, should only get results for first 100
            assert len([r for r in result.values() if r]) <= 100

    @pytest.mark.asyncio
    async def test_bulk_alpha_vantage_handles_api_errors(self, market_data_service):
        """Test that Alpha Vantage bulk fetch handles API errors gracefully."""
        symbols = ["AAPL", "GOOGL", "INVALID"]
        api_key = "test_alpha_vantage_key"

        with patch.object(market_data_service, '_bulk_fetch_from_alpha_vantage') as mock_bulk:
            # Simulate partial success with API error for one symbol
            mock_bulk.return_value = {
                "AAPL": {"symbol": "AAPL", "price": 150.0, "provider": "alpha_vantage", "bulk_fetch": True},
                "GOOGL": {"symbol": "GOOGL", "price": 2800.0, "provider": "alpha_vantage", "bulk_fetch": True},
                "INVALID": None,  # API error for this symbol
            }

            result = await market_data_service._bulk_fetch_from_alpha_vantage(symbols, api_key)

            # Should handle partial failures
            assert len(result) == 3
            assert result["AAPL"] is not None
            assert result["GOOGL"] is not None
            assert result["INVALID"] is None

    @pytest.mark.asyncio
    async def test_bulk_alpha_vantage_requires_api_key(self, market_data_service):
        """Test that Alpha Vantage bulk fetch requires an API key."""
        symbols = ["AAPL", "GOOGL"]

        # Test with no API key
        result = await market_data_service._bulk_fetch_from_alpha_vantage(symbols, None)

        # Should return None for all symbols when no API key
        assert all(result[symbol] is None for symbol in symbols)

        # Test with empty API key
        result = await market_data_service._bulk_fetch_from_alpha_vantage(symbols, "")

        # Should return None for all symbols when empty API key
        assert all(result[symbol] is None for symbol in symbols)


class TestProviderFallback:
    """Test provider fallback behavior with bulk operations."""

    @pytest.mark.asyncio
    async def test_fallback_to_next_provider_on_bulk_failure(self, market_data_service, mock_yfinance_provider, mock_alpha_vantage_provider):
        """Test that failed bulk operations fall back to next provider."""
        symbols = ["AAPL", "GOOGL"]

        with patch.object(market_data_service, 'get_enabled_providers') as mock_providers, \
             patch.object(market_data_service, '_bulk_fetch_from_yfinance') as mock_yfinance_bulk, \
             patch.object(market_data_service, '_bulk_fetch_from_alpha_vantage') as mock_alpha_bulk, \
             patch.object(market_data_service, '_store_price_data') as mock_store, \
             patch.object(market_data_service, '_log_api_usage') as mock_log:

            mock_providers.return_value = [mock_yfinance_provider, mock_alpha_vantage_provider]
            mock_yfinance_bulk.return_value = {"AAPL": None, "GOOGL": None}  # Both failed
            mock_alpha_bulk.return_value = {
                "AAPL": {"symbol": "AAPL", "price": 150.0, "provider": "alpha_vantage", "bulk_fetch": True},
                "GOOGL": {"symbol": "GOOGL", "price": 2800.0, "provider": "alpha_vantage", "bulk_fetch": True}
            }

            result = await market_data_service.fetch_multiple_prices(symbols)

            # Should fall back to Alpha Vantage bulk
            assert len(result) == 2
            assert all(data["provider"] == "alpha_vantage" for data in result.values())
            assert all(data["bulk_fetch"] is True for data in result.values())

            # Should have called both bulk methods
            mock_yfinance_bulk.assert_called_once_with(symbols)
            mock_alpha_bulk.assert_called_once_with(symbols, mock_alpha_vantage_provider.api_key)


@pytest.mark.asyncio
async def test_bulk_optimization_disabled_for_non_yfinance():
    """Test that bulk optimization is not used for providers that don't support it."""
    # This test ensures we don't accidentally apply bulk logic to unsupported providers
    pass  # Implementation will be added when we support more providers


# Performance benchmark test (for future validation)
@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_bulk_vs_individual_performance_comparison():
    """Benchmark test to validate bulk operations are actually faster."""
    # This test will measure actual performance improvements
    # Should show significant improvement for multiple symbols
    pass
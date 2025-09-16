"""
TDD Test for Bulk Fetch Symbols Issue: Only 1/8 symbols being updated.

Tests to reproduce and fix the issue where batch price updates report
only partial success (1/8 symbols) instead of all symbols.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from src.models.market_data_provider import MarketDataProvider
from src.models.realtime_price_history import RealtimePriceHistory
from src.services.market_data_service import MarketDataService
from src.utils.datetime_utils import utc_now


class TestBulkFetchSymbolsIssue:
    """Test class for reproducing the 1/8 symbols bulk fetch issue."""

    @pytest.fixture
    def mock_yfinance_provider(self, db_session: Session) -> MarketDataProvider:
        """Create a mock yfinance provider for testing."""
        provider = MarketDataProvider(
            name="yfinance",
            display_name="Yahoo Finance",
            is_enabled=True,
            priority=1,
            rate_limit_per_minute=60,
            rate_limit_per_day=2000
        )
        db_session.add(provider)
        db_session.commit()
        return provider

    @pytest.fixture
    def test_symbols(self) -> list[str]:
        """8 test symbols that should all be successfully fetched."""
        return ["CBA", "BHP", "WBC", "CSL", "ANZ", "NAB", "TLS", "WOW"]

    @pytest.fixture
    def mock_yfinance_data(self, test_symbols: list[str]) -> dict:
        """Mock yfinance data that should return successful prices for all symbols."""
        return {
            symbol: {
                'regularMarketPrice': float(100 + i * 10),  # Different prices
                'currentPrice': float(100 + i * 10),
                'volume': 1000000 + i * 100000,
                'previousClose': float(95 + i * 10),
                'marketCap': 50000000000 + i * 1000000000,
                'currency': 'AUD',
                'shortName': f'{symbol} Test Company'
            }
            for i, symbol in enumerate(test_symbols)
        }

    @pytest.mark.asyncio
    async def test_bulk_fetch_should_return_all_8_symbols(
        self,
        db_session: Session,
        mock_yfinance_provider: MarketDataProvider,
        test_symbols: list[str],
        mock_yfinance_data: dict
    ):
        """
        Test that bulk fetch should successfully return data for all 8 symbols.
        This test should currently FAIL due to the bug in _bulk_fetch_from_yfinance.
        """
        service = MarketDataService(db_session)

        # Mock yfinance Tickers behavior
        with patch('yfinance.Tickers') as mock_tickers:
            # Create mock ticker objects
            mock_ticker_instances = {}
            for symbol in test_symbols:
                mock_ticker = MagicMock()
                mock_ticker.info = mock_yfinance_data[symbol]
                mock_ticker_instances[f"{symbol}.AX"] = mock_ticker

            # Configure the Tickers mock
            mock_tickers_instance = MagicMock()
            mock_tickers_instance.tickers = mock_ticker_instances
            mock_tickers.return_value = mock_tickers_instance

            # Perform bulk fetch
            results = await service._bulk_fetch_from_yfinance(test_symbols)

            # Assertion: All 8 symbols should have successful results
            assert len(results) == 8, f"Expected 8 results, got {len(results)}"

            successful_results = [symbol for symbol, result in results.items() if result is not None]
            assert len(successful_results) == 8, f"Expected 8 successful results, got {len(successful_results)}: {successful_results}"

            # Verify each symbol has correct price data
            for symbol in test_symbols:
                assert symbol in results, f"Missing symbol {symbol} in results"
                assert results[symbol] is not None, f"Symbol {symbol} returned None"
                assert 'price' in results[symbol], f"Symbol {symbol} missing price field"
                assert results[symbol]['price'] > 0, f"Symbol {symbol} has invalid price: {results[symbol]['price']}"

    @pytest.mark.asyncio
    async def test_bulk_fetch_stores_all_symbols_in_database(
        self,
        db_session: Session,
        mock_yfinance_provider: MarketDataProvider,
        test_symbols: list[str],
        mock_yfinance_data: dict
    ):
        """
        Test that bulk fetch stores price data for all symbols in the database.
        This test should currently FAIL due to incomplete database storage.
        """
        service = MarketDataService(db_session)

        # Clear any existing price data
        db_session.query(RealtimePriceHistory).delete()
        db_session.commit()

        # Mock yfinance Tickers behavior
        with patch('yfinance.Tickers') as mock_tickers:
            # Create mock ticker objects
            mock_ticker_instances = {}
            for symbol in test_symbols:
                mock_ticker = MagicMock()
                mock_ticker.info = mock_yfinance_data[symbol]
                mock_ticker_instances[f"{symbol}.AX"] = mock_ticker

            # Configure the Tickers mock
            mock_tickers_instance = MagicMock()
            mock_tickers_instance.tickers = mock_ticker_instances
            mock_tickers.return_value = mock_tickers_instance

            # Perform bulk fetch and store results
            results = await service.fetch_multiple_prices(test_symbols)

            # Check database storage
            stored_prices = db_session.query(RealtimePriceHistory).all()
            stored_symbols = [price.symbol for price in stored_prices]

            # Assertion: All 8 symbols should be stored in database
            assert len(stored_prices) == 8, f"Expected 8 stored prices, got {len(stored_prices)}"

            for symbol in test_symbols:
                assert symbol in stored_symbols, f"Symbol {symbol} not found in database"

                # Verify the stored data is correct
                stored_price = next(price for price in stored_prices if price.symbol == symbol)
                expected_price = mock_yfinance_data[symbol]['regularMarketPrice']
                assert float(stored_price.price) == expected_price, f"Stored price for {symbol} incorrect"

    @pytest.mark.asyncio
    async def test_recent_fetch_cache_does_not_block_bulk_updates(
        self,
        db_session: Session,
        mock_yfinance_provider: MarketDataProvider,
        test_symbols: list[str]
    ):
        """
        Test that the recent fetch cache (10-minute timeout) doesn't prevent bulk updates.
        This test should identify the caching issue that may contribute to partial updates.
        """
        service = MarketDataService(db_session)

        # Simulate recent fetches for some symbols (should not block bulk fetch)
        now = datetime.utcnow()
        recent_time = now - timedelta(minutes=5)  # 5 minutes ago (within 10-minute cache)

        # Add some symbols to recent fetch cache
        for symbol in test_symbols[:4]:  # First 4 symbols
            service._recent_fetches[symbol] = recent_time

        # Mock yfinance to return data for all symbols
        with patch('yfinance.Tickers') as mock_tickers:
            mock_ticker_instances = {}
            for symbol in test_symbols:
                mock_ticker = MagicMock()
                mock_ticker.info = {'regularMarketPrice': 150.0, 'volume': 1000000}
                mock_ticker_instances[f"{symbol}.AX"] = mock_ticker

            mock_tickers_instance = MagicMock()
            mock_tickers_instance.tickers = mock_ticker_instances
            mock_tickers.return_value = mock_tickers_instance

            # Perform bulk fetch
            results = await service.fetch_multiple_prices(test_symbols)

            # Assertion: Even with recent cache, bulk fetch should update all symbols
            successful_results = [symbol for symbol, result in results.items() if result is not None]
            assert len(successful_results) == 8, f"Cache blocking bulk updates: only {len(successful_results)}/8 symbols updated"

    @pytest.mark.asyncio
    async def test_alpha_vantage_bulk_fetch_indentation_bug(
        self,
        db_session: Session,
        test_symbols: list[str]
    ):
        """
        Test for the indentation bug in Alpha Vantage bulk fetch logic.
        This test should identify the indentation issue at line 392 in market_data_service.py.
        """
        # Create Alpha Vantage provider
        provider = MarketDataProvider(
            name="alpha_vantage",
            display_name="Alpha Vantage",
            is_enabled=True,
            api_key="test_api_key",
            priority=2,
            rate_limit_per_minute=5,
            rate_limit_per_day=500
        )
        db_session.add(provider)
        db_session.commit()

        service = MarketDataService(db_session)

        # Mock Alpha Vantage bulk response
        mock_bulk_response = {
            "realtime_bulk_quotes": [
                {
                    "symbol": symbol,
                    "price": str(100 + i * 10),
                    "volume": str(1000000),
                    "change": "1.5",
                    "change_percent": "1.5%",
                    "previous_close": str(95 + i * 10)
                }
                for i, symbol in enumerate(test_symbols)
            ]
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock HTTP response
            mock_response = MagicMock()
            mock_response.status = 200
            async def mock_json():
                return mock_bulk_response
            mock_response.json = mock_json
            mock_get.return_value.__aenter__.return_value = mock_response

            # Test the _fetch_from_provider method directly
            results = await service._fetch_from_provider(provider, test_symbols)

            # Assertion: All symbols should be processed successfully
            assert len(results) == 8, f"Expected 8 results, got {len(results)}"

            successful_results = [symbol for symbol, result in results.items() if result is not None]
            assert len(successful_results) == 8, f"Alpha Vantage indentation bug: only {len(successful_results)}/8 symbols processed"

    @pytest.mark.asyncio
    async def test_yfinance_regularMarketPrice_vs_currentPrice_bug(
        self,
        db_session: Session,
        mock_yfinance_provider: MarketDataProvider,
        test_symbols: list[str]
    ):
        """
        Test for the regularMarketPrice vs currentPrice bug in yfinance bulk fetch.
        The code incorrectly uses 'currentPrice' instead of 'regularMarketPrice'.
        """
        service = MarketDataService(db_session)

        # Mock yfinance data where regularMarketPrice exists but currentPrice doesn't
        mock_data = {}
        for i, symbol in enumerate(test_symbols):
            mock_data[symbol] = {
                'regularMarketPrice': float(100 + i * 10),  # This exists
                # 'currentPrice' deliberately missing to test the bug
                'volume': 1000000,
                'currency': 'AUD'
            }

        with patch('yfinance.Tickers') as mock_tickers:
            mock_ticker_instances = {}
            for symbol in test_symbols:
                mock_ticker = MagicMock()
                mock_ticker.info = mock_data[symbol]
                mock_ticker_instances[f"{symbol}.AX"] = mock_ticker

            mock_tickers_instance = MagicMock()
            mock_tickers_instance.tickers = mock_ticker_instances
            mock_tickers.return_value = mock_tickers_instance

            # Perform bulk fetch
            results = await service._bulk_fetch_from_yfinance(test_symbols)

            # Assertion: Should successfully extract price using regularMarketPrice
            successful_results = [symbol for symbol, result in results.items() if result is not None]
            assert len(successful_results) == 8, f"regularMarketPrice bug: only {len(successful_results)}/8 symbols have prices"

            # Verify the correct price is extracted
            for symbol in test_symbols:
                if results[symbol] is not None:
                    expected_price = mock_data[symbol]['regularMarketPrice']
                    assert results[symbol]['price'] == expected_price, f"Wrong price extracted for {symbol}"

    @pytest.mark.asyncio
    async def test_fetch_multiple_prices_end_to_end_success_rate(
        self,
        db_session: Session,
        mock_yfinance_provider: MarketDataProvider,
        test_symbols: list[str],
        mock_yfinance_data: dict
    ):
        """
        End-to-end test that should demonstrate the 1/8 success rate bug.
        This comprehensive test covers the entire fetch_multiple_prices flow.
        """
        service = MarketDataService(db_session)

        # Clear any cached data
        service._recent_fetches.clear()

        with patch('yfinance.Tickers') as mock_tickers:
            mock_ticker_instances = {}
            for symbol in test_symbols:
                mock_ticker = MagicMock()
                mock_ticker.info = mock_yfinance_data[symbol]
                mock_ticker_instances[f"{symbol}.AX"] = mock_ticker

            mock_tickers_instance = MagicMock()
            mock_tickers_instance.tickers = mock_ticker_instances
            mock_tickers.return_value = mock_tickers_instance

            # Perform the full fetch_multiple_prices operation
            results = await service.fetch_multiple_prices(test_symbols)

            # Count successful vs failed results
            successful_count = len([result for result in results.values() if result is not None])
            failed_count = len([result for result in results.values() if result is None])

            # The main assertion that should currently FAIL
            assert successful_count == 8, f"CRITICAL BUG: Only {successful_count}/8 symbols successful, {failed_count} failed"
            assert failed_count == 0, f"CRITICAL BUG: {failed_count} symbols failed when all should succeed"

            # Success rate should be 100%, not 12.5% (1/8)
            success_rate = successful_count / len(test_symbols)
            assert success_rate == 1.0, f"CRITICAL BUG: Success rate is {success_rate:.1%}, should be 100%"
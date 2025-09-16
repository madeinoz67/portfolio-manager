"""
TDD test to investigate market data freshness issues.

Based on user screenshot showing:
- Most stocks: "4 minutes ago" (fresh)
- WBC: "15 minutes ago" (stale)

This suggests inconsistent data fetching or caching behavior.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.models.realtime_price_history import RealtimePriceHistory
from src.services.market_data_service import MarketDataService
# Remove import since we use the fixture directly


class TestMarketDataFreshness:
    """Test suite to investigate data freshness inconsistencies."""

    def test_should_have_recent_price_data_for_all_symbols(self, db: Session):
        """
        Test: All symbols should have recent price data (within 15 minutes).

        This test validates that the background scheduler is updating
        all symbols consistently.
        """
        # Arrange: Get symbols from the screenshot
        expected_symbols = ["CBA", "BHP", "WBC", "CSL", "NAB", "TLS", "NEM"]
        cutoff_time = datetime.utcnow() - timedelta(minutes=15)

        # Act: Query recent price data for each symbol
        recent_prices = {}
        stale_symbols = []

        for symbol in expected_symbols:
            latest_price = db.query(RealtimePriceHistory).filter(
                RealtimePriceHistory.symbol == symbol
            ).order_by(RealtimePriceHistory.fetched_at.desc()).first()

            if latest_price:
                recent_prices[symbol] = latest_price.fetched_at
                if latest_price.fetched_at < cutoff_time:
                    stale_symbols.append(symbol)
            else:
                stale_symbols.append(symbol)

        # Assert: All symbols should have recent data
        assert len(stale_symbols) == 0, f"Stale symbols found: {stale_symbols}. Recent prices: {recent_prices}"

    def test_should_identify_why_wbc_is_stale(self, db: Session):
        """
        Test: Investigate why WBC specifically shows stale data.

        This test examines the fetching pattern for WBC vs other symbols.
        """
        # Arrange: Focus on WBC vs a fresh symbol like CBA
        symbols_to_check = ["WBC", "CBA"]

        # Act: Get last 5 price updates for each symbol
        price_history = {}
        for symbol in symbols_to_check:
            history = db.query(RealtimePriceHistory).filter(
                RealtimePriceHistory.symbol == symbol
            ).order_by(RealtimePriceHistory.fetched_at.desc()).limit(5).all()

            price_history[symbol] = [
                {
                    "fetched_at": price.fetched_at,
                    "price": float(price.price) if price.price else None,
                    "provider": price.provider_name
                }
                for price in history
            ]

        # Assert: Both symbols should have similar update patterns
        wbc_updates = len(price_history.get("WBC", []))
        cba_updates = len(price_history.get("CBA", []))

        # Debug information
        print(f"\nWBC price history: {price_history.get('WBC', [])}")
        print(f"CBA price history: {price_history.get('CBA', [])}")

        # WBC should have at least some recent updates
        assert wbc_updates > 0, f"WBC has no price history. Full history: {price_history}"

    def test_should_verify_background_scheduler_is_running(self, db: Session):
        """
        Test: Verify the background scheduler is actively updating prices.

        This test checks for evidence that the 15-minute scheduler is working.
        """
        # Arrange: Look for price updates in the last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        # Act: Count total price updates in the last hour
        recent_updates = db.query(RealtimePriceHistory).filter(
            RealtimePriceHistory.fetched_at >= one_hour_ago
        ).count()

        # Get unique symbols updated in the last hour
        updated_symbols = db.query(RealtimePriceHistory.symbol).filter(
            RealtimePriceHistory.fetched_at >= one_hour_ago
        ).distinct().all()

        updated_symbol_list = [row[0] for row in updated_symbols]

        # Assert: Should have some recent activity
        assert recent_updates > 0, f"No price updates in the last hour. Updated symbols: {updated_symbol_list}"

        # Should have multiple symbols being updated
        assert len(updated_symbol_list) > 1, f"Only {len(updated_symbol_list)} symbols updated: {updated_symbol_list}"

    def test_should_check_provider_performance(self, db: Session):
        """
        Test: Check if specific providers are failing for certain symbols.

        This investigates if provider-specific issues cause stale data.
        """
        # Arrange: Check the last 10 price fetches per symbol
        symbols = ["CBA", "BHP", "WBC", "CSL", "NAB", "TLS", "NEM"]
        provider_performance = {}

        # Act: Analyze provider success rates per symbol
        for symbol in symbols:
            recent_fetches = db.query(RealtimePriceHistory).filter(
                RealtimePriceHistory.symbol == symbol
            ).order_by(RealtimePriceHistory.fetched_at.desc()).limit(10).all()

            if recent_fetches:
                providers_used = [fetch.provider_name for fetch in recent_fetches if fetch.provider_name]
                successful_fetches = [fetch for fetch in recent_fetches if fetch.price is not None]

                provider_performance[symbol] = {
                    "total_fetches": len(recent_fetches),
                    "successful_fetches": len(successful_fetches),
                    "providers_used": list(set(providers_used)),
                    "latest_fetch": recent_fetches[0].fetched_at if recent_fetches else None,
                    "success_rate": len(successful_fetches) / len(recent_fetches) if recent_fetches else 0
                }

        # Debug output
        print(f"\nProvider performance analysis: {provider_performance}")

        # Assert: All symbols should have reasonable success rates
        for symbol, perf in provider_performance.items():
            assert perf["success_rate"] >= 0.5, f"{symbol} has low success rate: {perf['success_rate']}"

    @pytest.mark.integration
    async def test_should_fetch_fresh_prices_on_demand(self, db: Session):
        """
        Test: Verify that manual price fetching works for all symbols.

        This tests the market data service directly.
        """
        # Arrange: Initialize market data service
        service = MarketDataService(db)
        test_symbols = ["CBA", "WBC"]  # Focus on fresh vs stale

        # Act: Fetch prices for test symbols
        results = {}
        for symbol in test_symbols:
            try:
                price_data = await service.fetch_stock_price(symbol)
                results[symbol] = {
                    "success": price_data is not None,
                    "price": float(price_data) if price_data else None
                }
            except Exception as e:
                results[symbol] = {
                    "success": False,
                    "error": str(e)
                }

        # Assert: All symbols should fetch successfully
        for symbol, result in results.items():
            assert result["success"], f"Failed to fetch {symbol}: {result.get('error', 'Unknown error')}"
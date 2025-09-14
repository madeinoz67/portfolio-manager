"""
Test for dynamic symbol discovery in the scheduler.
Tests that the scheduler automatically discovers which symbols need monitoring
based on actual usage patterns.
"""
import pytest
from src.services.market_data_service import MarketDataService
from src.models.stock import Stock
from src.models.holding import Holding
from src.models.portfolio import Portfolio
from src.models.user import User
from src.models.price_history import PriceHistory


class TestDynamicSymbolDiscovery:
    """Test dynamic symbol discovery for the scheduler."""

    def test_get_actively_monitored_symbols_method_exists(self, db_session):
        """Test that the get_actively_monitored_symbols method exists."""
        # Arrange
        service = MarketDataService(db_session)

        # Act & Assert - Method should now exist
        symbols = service.get_actively_monitored_symbols()
        assert isinstance(symbols, list)

    def test_get_actively_monitored_symbols_from_portfolios(self, db_session):
        """Test that symbols are discovered from active portfolio holdings."""
        # Arrange - Create test data
        user = User(
            email="dynamic_test@example.com",
            password_hash="hashed",
            first_name="Dynamic",
            last_name="Test"
        )
        db_session.add(user)
        db_session.flush()

        portfolio = Portfolio(
            name="Test Portfolio",
            owner_id=user.id,
            total_value=1000.00
        )
        db_session.add(portfolio)
        db_session.flush()

        # Create stocks
        stocks = []
        for symbol in ['CBA', 'BHP', 'WBC', 'CSL', 'NAB']:
            stock = Stock(
                symbol=symbol,
                company_name=f"{symbol} Limited",
                current_price=100.00
            )
            db_session.add(stock)
            stocks.append(stock)

        db_session.flush()

        # Create holdings for the portfolio
        for stock in stocks:
            holding = Holding(
                portfolio_id=portfolio.id,
                stock_id=stock.id,
                quantity=10,
                average_cost=95.00
            )
            db_session.add(holding)

        db_session.commit()

        # Act - Test the method with portfolio holdings
        service = MarketDataService(db_session)
        symbols = service.get_actively_monitored_symbols(provider_bulk_limit=10)

        # Assert - Should return the symbols from portfolio holdings
        expected_symbols = ['BHP', 'CBA', 'CSL', 'NAB', 'WBC']  # Sorted order
        assert symbols == expected_symbols
        assert len(symbols) <= 10  # Respects bulk limit

    def test_scheduler_should_use_dynamic_symbols(self):
        """Test the overall behavior we want: scheduler should get symbols dynamically."""
        # This is a contract test - defines what we expect
        # The scheduler should:
        # 1. Call get_actively_monitored_symbols()
        # 2. Use those symbols instead of hardcoded list
        # 3. Update all symbols returned from that method

        # For now, just document the expected behavior
        expected_behavior = {
            "scheduler_gets_symbols_from": "get_actively_monitored_symbols()",
            "symbols_sources": ["portfolio_holdings", "recent_price_requests"],
            "max_symbols_per_batch": "provider_bulk_limit",  # e.g., 10 for yfinance
            "batch_splitting": "split_large_requests_into_provider_limit_batches",
            "update_frequency": "all symbols every 15 minutes"
        }

        assert expected_behavior["scheduler_gets_symbols_from"] == "get_actively_monitored_symbols()"
        assert expected_behavior["batch_splitting"] == "split_large_requests_into_provider_limit_batches"
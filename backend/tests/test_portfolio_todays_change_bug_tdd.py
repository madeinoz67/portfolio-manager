"""
TDD test suite for portfolio today's change calculation bug.

This test defines the expected behavior for today's change calculations:
- Today's change should be based on current price vs previous close price
- Should handle missing previous close data gracefully
- Should aggregate correctly across multiple holdings
- Must use single master symbol table for consistent pricing
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from src.models.portfolio import Portfolio
from src.models.holding import Holding
from src.models.user import User
from src.models.stock import Stock
from src.models.realtime_symbol import RealtimeSymbol
from src.models.realtime_price_history import RealtimePriceHistory
from src.models.market_data_provider import MarketDataProvider
from src.services.dynamic_portfolio_service import DynamicPortfolioService
from src.utils.datetime_utils import utc_now


class TestPortfolioTodaysChangeBug:
    """Test suite for portfolio today's change calculation accuracy."""

    @pytest.fixture
    def test_user(self, db_session: Session):
        """Create test user."""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def test_provider(self, db_session: Session):
        """Create test market data provider."""
        provider = MarketDataProvider(
            name="test_provider",
            display_name="Test Provider",
            api_key="",
            is_enabled=True
        )
        db_session.add(provider)
        db_session.commit()
        return provider

    @pytest.fixture
    def test_portfolio(self, db_session: Session, test_user):
        """Create test portfolio."""
        portfolio = Portfolio(
            name="Test Portfolio",
            owner_id=test_user.id
        )
        db_session.add(portfolio)
        db_session.commit()
        return portfolio

    def test_todays_change_calculation_single_holding(
        self, db_session: Session, test_portfolio, test_provider
    ):
        """
        Test today's change calculation for single holding.

        Today's change = (current_price - previous_close) * quantity
        """
        # Arrange: Create stock with current and previous prices
        stock = Stock(
            symbol="AAPL",
            company_name="Apple Inc",
            current_price=Decimal("150.00")
        )
        db_session.add(stock)

        # Create master symbol record with current price
        master_symbol = RealtimeSymbol(
            symbol="AAPL",
            current_price=Decimal("150.00"),
            company_name="Apple Inc",
            last_updated=utc_now(),
            provider_id=test_provider.id
        )
        db_session.add(master_symbol)

        # Create price history with previous close
        price_history = RealtimePriceHistory(
            symbol="AAPL",
            price=Decimal("150.00"),
            previous_close=Decimal("145.00"),  # Previous close for today's change calculation
            source_timestamp=utc_now(),
            fetched_at=utc_now(),
            provider_id=test_provider.id
        )
        db_session.add(price_history)
        db_session.commit()

        # Link master symbol to latest history
        master_symbol.latest_history_id = price_history.id
        db_session.commit()

        # Create holding: 10 shares at $140 average cost
        holding = Holding(
            portfolio_id=test_portfolio.id,
            stock_id=stock.id,
            quantity=10,
            average_cost=Decimal("140.00")
        )
        db_session.add(holding)
        db_session.commit()

        # Act: Calculate today's change via portfolio service
        portfolio_service = DynamicPortfolioService(db_session)
        dynamic_portfolio = portfolio_service.get_dynamic_portfolio(test_portfolio.id)

        # Assert: Today's change should be (150 - 145) * 10 = $50.00
        expected_todays_change = Decimal("50.00")
        assert dynamic_portfolio.daily_change == expected_todays_change
        assert dynamic_portfolio.daily_change_percent is not None

    def test_todays_change_multiple_holdings(
        self, db_session: Session, test_portfolio, test_provider
    ):
        """
        Test today's change calculation aggregation across multiple holdings.
        """
        # Arrange: Create multiple stocks with different price changes
        stocks_data = [
            ("AAPL", Decimal("150.00"), Decimal("145.00"), 10),  # +$5 per share, 10 shares = +$50
            ("GOOGL", Decimal("2500.00"), Decimal("2520.00"), 5),  # -$20 per share, 5 shares = -$100
            ("MSFT", Decimal("300.00"), Decimal("295.00"), 20)   # +$5 per share, 20 shares = +$100
        ]

        total_expected_change = Decimal("50.00")  # +50 - 100 + 100 = +50

        for symbol, current_price, previous_close, quantity in stocks_data:
            # Create stock
            stock = Stock(
                symbol=symbol,
                company_name=f"{symbol} Corp",
                current_price=current_price
            )
            db_session.add(stock)

            # Create master symbol
            master_symbol = RealtimeSymbol(
                symbol=symbol,
                current_price=current_price,
                company_name=f"{symbol} Corp",
                last_updated=utc_now(),
                provider_id=test_provider.id
            )
            db_session.add(master_symbol)

            # Create price history with previous close
            price_history = RealtimePriceHistory(
                symbol=symbol,
                price=current_price,
                previous_close=previous_close,
                source_timestamp=utc_now(),
                fetched_at=utc_now(),
                provider_id=test_provider.id
            )
            db_session.add(price_history)
            db_session.commit()

            # Link master to history
            master_symbol.latest_history_id = price_history.id

            # Create holding
            holding = Holding(
                portfolio_id=test_portfolio.id,
                stock_id=stock.id,
                quantity=quantity,
                average_cost=current_price - Decimal("10.00")  # Some arbitrary cost basis
            )
            db_session.add(holding)

        db_session.commit()

        # Act: Calculate aggregated today's change
        portfolio_service = DynamicPortfolioService(db_session)
        dynamic_portfolio = portfolio_service.get_dynamic_portfolio(test_portfolio.id)

        # Assert: Today's change should aggregate correctly
        assert dynamic_portfolio.daily_change == total_expected_change

    def test_todays_change_missing_previous_close(
        self, db_session: Session, test_portfolio, test_provider
    ):
        """
        Test today's change when previous close data is missing.

        Should gracefully handle missing previous close by showing 0 or null.
        """
        # Arrange: Create stock with no previous close data
        stock = Stock(
            symbol="NEWCO",
            company_name="New Company",
            current_price=Decimal("25.00")
        )
        db_session.add(stock)

        # Create master symbol
        master_symbol = RealtimeSymbol(
            symbol="NEWCO",
            current_price=Decimal("25.00"),
            company_name="New Company",
            last_updated=utc_now(),
            provider_id=test_provider.id
        )
        db_session.add(master_symbol)

        # Create price history WITHOUT previous close
        price_history = RealtimePriceHistory(
            symbol="NEWCO",
            price=Decimal("25.00"),
            previous_close=None,  # Missing previous close
            source_timestamp=utc_now(),
            fetched_at=utc_now(),
            provider_id=test_provider.id
        )
        db_session.add(price_history)
        db_session.commit()

        master_symbol.latest_history_id = price_history.id

        # Create holding
        holding = Holding(
            portfolio_id=test_portfolio.id,
            stock_id=stock.id,
            quantity=100,
            average_cost=Decimal("20.00")
        )
        db_session.add(holding)
        db_session.commit()

        # Act: Calculate today's change with missing data
        portfolio_service = DynamicPortfolioService(db_session)
        dynamic_portfolio = portfolio_service.get_dynamic_portfolio(test_portfolio.id)

        # Assert: Should handle gracefully (return 0 or None, not crash)
        assert dynamic_portfolio.daily_change is not None
        # When previous close is missing, today's change should be 0
        assert dynamic_portfolio.daily_change == Decimal("0.00")

    def test_todays_change_uses_master_table_prices(
        self, db_session: Session, test_portfolio, test_provider
    ):
        """
        Test that today's change calculation uses master table for current prices.

        Critical: Must use single source of truth from realtime_symbols table.
        """
        # Arrange: Create stock with different price in stocks table vs master table
        stock = Stock(
            symbol="TSLA",
            company_name="Tesla Inc",
            current_price=Decimal("800.00")  # Old price in stocks table
        )
        db_session.add(stock)

        # Master table has updated price (single source of truth)
        master_symbol = RealtimeSymbol(
            symbol="TSLA",
            current_price=Decimal("850.00"),  # Updated price in master table
            company_name="Tesla Inc",
            last_updated=utc_now(),
            provider_id=test_provider.id
        )
        db_session.add(master_symbol)

        # Price history with previous close
        price_history = RealtimePriceHistory(
            symbol="TSLA",
            price=Decimal("850.00"),
            previous_close=Decimal("820.00"),
            source_timestamp=utc_now(),
            fetched_at=utc_now(),
            provider_id=test_provider.id
        )
        db_session.add(price_history)
        db_session.commit()

        master_symbol.latest_history_id = price_history.id

        # Create holding
        holding = Holding(
            portfolio_id=test_portfolio.id,
            stock_id=stock.id,
            quantity=5,
            average_cost=Decimal("750.00")
        )
        db_session.add(holding)
        db_session.commit()

        # Act: Calculate today's change
        portfolio_service = DynamicPortfolioService(db_session)
        dynamic_portfolio = portfolio_service.get_dynamic_portfolio(test_portfolio.id)

        # Assert: Should use master table price (850) not stocks table price (800)
        # Today's change = (850 - 820) * 5 = $150.00
        expected_change = Decimal("150.00")
        assert dynamic_portfolio.daily_change == expected_change

    def test_todays_change_percent_calculation(
        self, db_session: Session, test_portfolio, test_provider
    ):
        """
        Test today's change percentage calculation.

        Percentage = (today's change / yesterday's portfolio value) * 100
        """
        # Arrange: Create holding with known values
        stock = Stock(
            symbol="NVDA",
            company_name="NVIDIA Corp",
            current_price=Decimal("400.00")
        )
        db_session.add(stock)

        master_symbol = RealtimeSymbol(
            symbol="NVDA",
            current_price=Decimal("400.00"),
            company_name="NVIDIA Corp",
            last_updated=utc_now(),
            provider_id=test_provider.id
        )
        db_session.add(master_symbol)

        price_history = RealtimePriceHistory(
            symbol="NVDA",
            price=Decimal("400.00"),
            previous_close=Decimal("380.00"),  # $20 increase
            source_timestamp=utc_now(),
            fetched_at=utc_now(),
            provider_id=test_provider.id
        )
        db_session.add(price_history)
        db_session.commit()

        master_symbol.latest_history_id = price_history.id

        # 10 shares: yesterday value = 380 * 10 = $3800, today change = $20 * 10 = $200
        holding = Holding(
            portfolio_id=test_portfolio.id,
            stock_id=stock.id,
            quantity=10,
            average_cost=Decimal("350.00")
        )
        db_session.add(holding)
        db_session.commit()

        # Act: Calculate percentage
        portfolio_service = DynamicPortfolioService(db_session)
        dynamic_portfolio = portfolio_service.get_dynamic_portfolio(test_portfolio.id)

        # Assert: Change percentage = (200 / 3800) * 100 = 5.26%
        expected_change = Decimal("200.00")
        expected_percentage = Decimal("5.26")  # 200/3800 * 100

        assert dynamic_portfolio.daily_change == expected_change
        assert abs(dynamic_portfolio.daily_change_percent - expected_percentage) < Decimal("0.01")

    def test_portfolio_overview_api_returns_correct_todays_change(
        self, db_session: Session, test_portfolio, test_provider
    ):
        """
        Test that portfolio overview API returns correct today's change values.

        This tests the complete flow from API to frontend display.
        """
        # Arrange: Simple holding with clear expected values
        stock = Stock(
            symbol="AMD",
            company_name="AMD Inc",
            current_price=Decimal("100.00")
        )
        db_session.add(stock)

        master_symbol = RealtimeSymbol(
            symbol="AMD",
            current_price=Decimal("100.00"),
            company_name="AMD Inc",
            last_updated=utc_now(),
            provider_id=test_provider.id
        )
        db_session.add(master_symbol)

        price_history = RealtimePriceHistory(
            symbol="AMD",
            price=Decimal("100.00"),
            previous_close=Decimal("95.00"),  # $5 increase
            source_timestamp=utc_now(),
            fetched_at=utc_now(),
            provider_id=test_provider.id
        )
        db_session.add(price_history)
        db_session.commit()

        master_symbol.latest_history_id = price_history.id

        # 50 shares: today's change = $5 * 50 = $250
        holding = Holding(
            portfolio_id=test_portfolio.id,
            stock_id=stock.id,
            quantity=50,
            average_cost=Decimal("90.00")
        )
        db_session.add(holding)
        db_session.commit()

        # Act: Get portfolio via service (same as API)
        portfolio_service = DynamicPortfolioService(db_session)
        portfolio_response = portfolio_service.get_dynamic_portfolio(test_portfolio.id)

        # Assert: API response has correct today's change
        assert portfolio_response.daily_change == Decimal("250.00")
        assert portfolio_response.daily_change_percent is not None
        assert portfolio_response.daily_change_percent > 0  # Positive change

    def test_empty_portfolio_todays_change(
        self, db_session: Session, test_portfolio
    ):
        """
        Test today's change calculation for empty portfolio.

        Should return 0 for portfolios with no holdings.
        """
        # Act: Calculate today's change for empty portfolio
        portfolio_service = DynamicPortfolioService(db_session)
        dynamic_portfolio = portfolio_service.get_dynamic_portfolio(test_portfolio.id)

        # Assert: Empty portfolio should have 0 today's change
        assert dynamic_portfolio.daily_change == Decimal("0.00")
        assert dynamic_portfolio.daily_change_percent == Decimal("0.00")
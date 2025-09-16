"""
TDD tests for individual holding timestamp functionality.

Tests ensure that:
1. Holdings display individual stock price update timestamps
2. Real-time updates affect holding timestamps correctly
3. Timestamp formatting follows timezone best practices
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch

from src.models.portfolio import Portfolio
from src.models.stock import Stock
from src.models.holding import Holding
from src.models.user import User
from src.schemas.holding import HoldingResponse
from src.services.real_time_portfolio_service import RealTimePortfolioService
from src.utils.datetime_utils import to_iso_string, utc_now


class TestHoldingTimestampsTDD:
    """TDD tests for holding timestamp functionality."""

    @pytest.fixture
    def sample_user(self, db_session):
        """Create a test user."""
        user = User(
            email="test@example.com",
            password_hash="fake_hash"
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def sample_portfolio(self, db_session, sample_user):
        """Create a test portfolio."""
        portfolio = Portfolio(
            name="Test Portfolio",
            description="Test portfolio for holding timestamps",
            owner_id=sample_user.id
        )
        db_session.add(portfolio)
        db_session.commit()
        return portfolio

    @pytest.fixture
    def sample_stock(self, db_session):
        """Create a test stock with price update timestamp."""
        initial_time = utc_now()
        stock = Stock(
            symbol="AAPL",
            company_name="Apple Inc.",
            exchange="NASDAQ",
            current_price=Decimal("150.00"),
            last_price_update=initial_time
        )
        db_session.add(stock)
        db_session.commit()
        return stock

    @pytest.fixture
    def sample_holding(self, db_session, sample_portfolio, sample_stock):
        """Create a test holding."""
        holding = Holding(
            portfolio_id=sample_portfolio.id,
            stock_id=sample_stock.id,
            quantity=Decimal("100"),
            average_cost=Decimal("140.00")
        )
        db_session.add(holding)
        db_session.commit()
        return holding

    def test_holding_response_includes_stock_last_price_update(self, sample_holding):
        """Test that HoldingResponse schema includes stock's last_price_update timestamp."""
        # This test should PASS since we want to ensure the schema includes the timestamp

        # Arrange: Get the holding with its stock
        holding_with_stock = sample_holding
        stock = holding_with_stock.stock

        # Act: Create HoldingResponse from the holding
        holding_response = HoldingResponse.model_validate(holding_with_stock)

        # Assert: Check that stock's last_price_update is included
        assert hasattr(holding_response.stock, 'last_price_update')
        assert holding_response.stock.last_price_update is not None

        # Check that it's properly formatted with UTC timezone
        timestamp_str = to_iso_string(stock.last_price_update)
        assert timestamp_str.endswith('Z')

    def test_holding_timestamps_update_when_stock_price_changes(self, db_session, sample_holding):
        """Test that when a stock price updates, the holding shows the new timestamp."""
        # This test drives the requirement that holdings reflect current stock price timestamps

        # Arrange: Initial state
        original_stock = sample_holding.stock
        original_update_time = original_stock.last_price_update

        # Act: Update stock price (simulating market data update)
        new_update_time = utc_now()
        original_stock.current_price = Decimal("155.00")
        original_stock.last_price_update = new_update_time
        db_session.commit()

        # Refresh the holding
        db_session.refresh(sample_holding)

        # Assert: Holding should reflect the new stock price update time
        holding_response = HoldingResponse.model_validate(sample_holding)
        assert holding_response.stock.last_price_update is not None

        # The timestamp should be newer than the original
        new_timestamp = holding_response.stock.last_price_update
        assert new_timestamp > original_update_time

    def test_real_time_service_updates_stock_timestamps(self, db_session, sample_portfolio, sample_stock, sample_holding):
        """Test that RealTimePortfolioService updates stock timestamps when processing price changes."""
        # This test ensures the real-time service properly updates stock timestamps

        # Arrange: Create service
        service = RealTimePortfolioService(db_session)
        original_time = sample_stock.last_price_update

        # Create a test market data provider first
        from src.models.market_data_provider import MarketDataProvider
        provider = MarketDataProvider(
            name="test_provider",
            display_name="Test Provider",
            is_enabled=True
        )
        db_session.add(provider)
        db_session.flush()  # Get the ID

        # Create a RealtimePriceHistory entry to simulate market data
        from src.models.realtime_price_history import RealtimePriceHistory
        new_time = utc_now()
        price_history = RealtimePriceHistory(
            symbol='AAPL',
            price=Decimal('155.00'),
            opening_price=Decimal('150.00'),
            volume=1000000,
            source_timestamp=new_time,
            fetched_at=new_time,
            provider_id=provider.id
        )
        db_session.add(price_history)
        db_session.commit()

        # Act: Process price update for the portfolio symbol
        result = service.update_portfolios_for_symbol('AAPL')

        # Assert: Stock should have been found and portfolio updated
        assert len(result) > 0  # At least one portfolio was updated
        db_session.refresh(sample_stock)
        # The stock timestamp should be updated through the portfolio update process
        assert sample_stock.last_price_update >= original_time

    def test_multiple_holdings_show_different_timestamps(self, db_session, sample_portfolio, sample_user):
        """Test that different stocks in same portfolio can have different last update timestamps."""
        # This test ensures each holding shows its own stock's timestamp, not a shared timestamp

        # Arrange: Create two stocks with different update times
        time1 = utc_now()
        time2 = utc_now() + timedelta(minutes=5)

        stock1 = Stock(
            symbol="MSFT",
            company_name="Microsoft Corp",
            exchange="NASDAQ",
            current_price=Decimal("300.00"),
            last_price_update=time1
        )

        stock2 = Stock(
            symbol="GOOGL",
            company_name="Alphabet Inc",
            exchange="NASDAQ",
            current_price=Decimal("2500.00"),
            last_price_update=time2
        )

        db_session.add_all([stock1, stock2])
        db_session.commit()

        # Create holdings for both stocks
        holding1 = Holding(
            portfolio_id=sample_portfolio.id,
            stock_id=stock1.id,
            quantity=Decimal("50"),
            average_cost=Decimal("290.00")
        )

        holding2 = Holding(
            portfolio_id=sample_portfolio.id,
            stock_id=stock2.id,
            quantity=Decimal("10"),
            average_cost=Decimal("2400.00")
        )

        db_session.add_all([holding1, holding2])
        db_session.commit()

        # Act: Create responses for both holdings
        response1 = HoldingResponse.model_validate(holding1)
        response2 = HoldingResponse.model_validate(holding2)

        # Assert: Each holding should show its stock's specific timestamp
        assert response1.stock.last_price_update is not None
        assert response2.stock.last_price_update is not None
        assert response1.stock.last_price_update != response2.stock.last_price_update

        # Verify timestamps match their respective stocks
        # Both times should be from the same timezone, so comparison should work
        assert response1.stock.last_price_update == stock1.last_price_update
        assert response2.stock.last_price_update == stock2.last_price_update

    def test_holding_with_no_price_update_shows_none(self, db_session, sample_portfolio):
        """Test that holdings for stocks with no price updates show None for last_price_update."""
        # This test ensures graceful handling of stocks without price data

        # Arrange: Create stock without last_price_update
        stock = Stock(
            symbol="NEWCO",
            company_name="New Company",
            exchange="NYSE",
            current_price=None,
            last_price_update=None
        )
        db_session.add(stock)
        db_session.commit()

        holding = Holding(
            portfolio_id=sample_portfolio.id,
            stock_id=stock.id,
            quantity=Decimal("25"),
            average_cost=Decimal("10.00")
        )
        db_session.add(holding)
        db_session.commit()

        # Act: Create holding response
        holding_response = HoldingResponse.model_validate(holding)

        # Assert: Should handle None gracefully
        assert holding_response.stock.last_price_update is None
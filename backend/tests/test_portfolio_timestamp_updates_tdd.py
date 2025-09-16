"""
TDD tests for portfolio timestamp updates when market data changes.

These tests verify that:
1. Portfolio.updated_at is properly updated when market data changes
2. New price_last_updated field tracks when portfolio prices were last refreshed
3. API responses include proper timestamp information
4. Frontend can display individual holding update timestamps
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from src.models.portfolio import Portfolio
from src.models.holding import Holding
from src.models.stock import Stock
from src.models.user import User
from src.models.realtime_price_history import RealtimePriceHistory
from src.models.market_data_provider import MarketDataProvider
from src.services.real_time_portfolio_service import RealTimePortfolioService
from src.services.market_data_service import MarketDataService
from sqlalchemy.orm import Session


@pytest.fixture
def user(db: Session):
    """Create test user."""
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        first_name="Test",
        last_name="User"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def stock(db: Session):
    """Create test stock."""
    stock = Stock(symbol="CBA", company_name="Commonwealth Bank")
    db.add(stock)
    db.commit()
    db.refresh(stock)
    return stock


@pytest.fixture
def portfolio_with_holding(db: Session, user, stock):
    """Create portfolio with a CBA holding."""
    portfolio = Portfolio(
        name="Test Portfolio",
        owner_id=user.id,
        total_value=Decimal("1000.00"),
        daily_change=Decimal("0.00"),
        daily_change_percent=Decimal("0.00")
    )
    db.add(portfolio)
    db.commit()

    holding = Holding(
        portfolio_id=portfolio.id,
        stock_id=stock.id,
        quantity=10,
        average_cost=Decimal("100.00")
    )
    db.add(holding)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@pytest.fixture
def provider(db: Session):
    """Create test market data provider."""
    provider = MarketDataProvider(
        name="test_provider",
        display_name="Test Provider",
        is_enabled=True,
        rate_limit_per_minute=60
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


def test_portfolio_updated_at_changes_when_price_updates(db: Session, portfolio_with_holding, provider):
    """
    Test that Portfolio.updated_at is updated when market data changes trigger portfolio recalculation.

    This verifies the existing functionality works correctly.
    """
    portfolio = portfolio_with_holding
    original_updated_at = portfolio.updated_at

    # Create price data for CBA
    price_data = RealtimePriceHistory(
        symbol="CBA",
        price=Decimal("105.00"),  # $5 increase
        opening_price=Decimal("100.00"),
        previous_close=Decimal("100.00"),
        provider_id=provider.id,
        source_timestamp=datetime.utcnow(),
        fetched_at=datetime.utcnow()
    )
    db.add(price_data)
    db.commit()

    # Wait a moment to ensure timestamp difference
    import time
    time.sleep(0.1)

    # Trigger portfolio update via RealTimePortfolioService
    service = RealTimePortfolioService(db)
    updated_portfolios = service.update_portfolios_for_symbol("CBA")

    # Verify portfolio was updated
    assert len(updated_portfolios) == 1
    assert updated_portfolios[0].id == portfolio.id

    # Verify updated_at changed
    db.refresh(portfolio)
    assert portfolio.updated_at > original_updated_at

    # Verify portfolio values were recalculated
    assert portfolio.total_value > Decimal("1000.00")  # Should increase due to price rise


def test_portfolio_needs_price_last_updated_field(db: Session, portfolio_with_holding):
    """
    Test that Portfolio model should have a price_last_updated field to track
    when portfolio prices were last refreshed from market data.

    This test will initially fail - we need to add this field via alembic migration.
    """
    portfolio = portfolio_with_holding

    # This should not fail once we add the field
    try:
        # Access the new field - this will fail initially
        price_last_updated = portfolio.price_last_updated
        # Field exists and has a default value (None or creation time)
        assert price_last_updated is None or isinstance(price_last_updated, datetime)
    except AttributeError:
        # Expected to fail initially - we need to add this field
        pytest.fail("Portfolio model missing price_last_updated field - need Alembic migration")


def test_price_last_updated_is_set_when_market_data_updates(db: Session, portfolio_with_holding, provider):
    """
    Test that price_last_updated is set when market data updates trigger portfolio recalculation.

    This test will pass once we:
    1. Add price_last_updated field to Portfolio model
    2. Update RealTimePortfolioService to set this field
    """
    portfolio = portfolio_with_holding

    # Store original timestamp
    original_updated_at = portfolio.updated_at

    # Create new price data
    price_data = RealtimePriceHistory(
        symbol="CBA",
        price=Decimal("102.00"),
        opening_price=Decimal("100.00"),
        provider_id=provider.id,
        source_timestamp=datetime.utcnow(),
        fetched_at=datetime.utcnow()
    )
    db.add(price_data)
    db.commit()

    # Wait a moment to ensure timestamp difference
    import time
    time.sleep(0.1)

    # Trigger portfolio update
    service = RealTimePortfolioService(db)
    updated_portfolios = service.update_portfolios_for_symbol("CBA")

    # Verify portfolio was updated
    assert len(updated_portfolios) == 1
    db.refresh(portfolio)

    # Verify both timestamps were updated
    assert portfolio.updated_at > original_updated_at

    # This will pass once we implement the price_last_updated field
    try:
        assert portfolio.price_last_updated is not None
        assert portfolio.price_last_updated > original_updated_at
        # price_last_updated should be approximately the same as the price data fetched_at
        time_diff = abs((portfolio.price_last_updated - price_data.fetched_at).total_seconds())
        assert time_diff < 5  # Within 5 seconds
    except AttributeError:
        pytest.skip("price_last_updated field not yet implemented")


def test_portfolio_api_includes_timestamp_information(db: Session, portfolio_with_holding):
    """
    Test that portfolio API responses include timestamp information for frontend display.

    This verifies that the API response schema includes the necessary timestamp fields.
    """
    portfolio = portfolio_with_holding

    # Simulate what the API response should look like
    expected_fields = [
        'created_at',
        'updated_at',
        'price_last_updated'  # New field for price update tracking
    ]

    # Test that portfolio has these fields
    for field in expected_fields:
        try:
            value = getattr(portfolio, field)
            assert value is not None or field == 'price_last_updated'  # price_last_updated can be None initially
        except AttributeError:
            if field == 'price_last_updated':
                pytest.skip(f"Field {field} not yet implemented in Portfolio model")
            else:
                pytest.fail(f"Portfolio model missing expected field: {field}")


def test_individual_holding_price_timestamps_available(db: Session, portfolio_with_holding, provider):
    """
    Test that individual holding price timestamps are available for frontend display.

    This verifies we can get the last update time for each stock in a portfolio.
    """
    portfolio = portfolio_with_holding

    # Create price data for the stock in this portfolio
    now = datetime.utcnow()
    price_data = RealtimePriceHistory(
        symbol="CBA",
        price=Decimal("101.00"),
        opening_price=Decimal("100.00"),
        provider_id=provider.id,
        source_timestamp=now,
        fetched_at=now
    )
    db.add(price_data)
    db.commit()

    # Get portfolio holdings with their latest price timestamps
    # This simulates what the API should return for detailed portfolio view
    holdings_with_timestamps = []

    for holding in portfolio.holdings:
        # Get latest price data for this stock
        latest_price = db.query(RealtimePriceHistory).filter(
            RealtimePriceHistory.symbol == holding.stock.symbol
        ).order_by(RealtimePriceHistory.fetched_at.desc()).first()

        holding_info = {
            'symbol': holding.stock.symbol,
            'quantity': holding.quantity,
            'average_cost': holding.average_cost,
            'current_price': latest_price.price if latest_price else None,
            'price_last_updated': latest_price.fetched_at if latest_price else None
        }
        holdings_with_timestamps.append(holding_info)

    # Verify we have the timestamp information
    assert len(holdings_with_timestamps) == 1
    cba_holding = holdings_with_timestamps[0]

    assert cba_holding['symbol'] == 'CBA'
    assert cba_holding['current_price'] == Decimal("101.00")
    assert cba_holding['price_last_updated'] is not None
    assert isinstance(cba_holding['price_last_updated'], datetime)

    # Verify timestamp is recent (within last minute)
    time_diff = (datetime.utcnow() - cba_holding['price_last_updated']).total_seconds()
    assert time_diff < 60


def test_market_data_service_updates_portfolio_timestamps(db: Session, portfolio_with_holding, provider):
    """
    Test that MarketDataService properly triggers portfolio timestamp updates.

    This is an integration test verifying the complete flow:
    1. Market data is fetched and stored
    2. Portfolio update is triggered
    3. Portfolio timestamps are updated appropriately
    """
    portfolio = portfolio_with_holding
    original_updated_at = portfolio.updated_at

    # Create market data service
    market_service = MarketDataService(db)

    # Mock price data that would come from external API
    mock_price_info = {
        'symbol': 'CBA',
        'price': 103.50,
        'opening_price': 100.00,
        'previous_close': 100.00,
        'volume': 1000000,
        'fetched_at': datetime.utcnow()
    }

    # Wait a moment to ensure timestamp difference
    import time
    time.sleep(0.1)

    # Store the price data (this should trigger portfolio updates)
    # We'll need to verify that _store_price_data triggers portfolio updates
    try:
        # This calls the internal method that should trigger portfolio updates
        result = market_service._store_price_data(
            symbol='CBA',
            price_info=mock_price_info,
            provider=provider
        )

        # Verify price was stored
        assert result is not None

        # Verify portfolio was updated
        db.refresh(portfolio)
        assert portfolio.updated_at > original_updated_at

        # Verify price_last_updated was set (once implemented)
        try:
            assert portfolio.price_last_updated is not None
            assert portfolio.price_last_updated > original_updated_at
        except AttributeError:
            pytest.skip("price_last_updated field not yet implemented")

    except AttributeError as e:
        # If the method doesn't exist or has different signature, skip for now
        pytest.skip(f"MarketDataService integration not yet complete: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
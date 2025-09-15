"""
Integration tests for dynamic portfolio valuation with real-time market prices.
Tests that portfolio values are calculated dynamically based on current market prices.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy.orm import Session

from src.models import Portfolio, Stock, Holding, User, RealtimePriceHistory, MarketDataProvider
from src.services.dynamic_portfolio_service import DynamicPortfolioService


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    user = User(
        email="dynamic@example.com",
        password_hash="$2b$12$dummy.hash.value",
        first_name="Dynamic",
        last_name="Test"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_portfolio(db: Session, test_user: User):
    """Create a test portfolio."""
    portfolio = Portfolio(
        name="Dynamic Portfolio",
        description="Portfolio for dynamic valuation testing",
        owner_id=test_user.id,
        total_value=Decimal("0.00")  # Should be calculated dynamically
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@pytest.fixture
def test_stocks(db: Session):
    """Create test stocks."""
    stocks = [
        Stock(symbol="CBA", company_name="Commonwealth Bank", exchange="ASX"),
        Stock(symbol="BHP", company_name="BHP Group", exchange="ASX"),
        Stock(symbol="WBC", company_name="Westpac Banking", exchange="ASX")
    ]

    for stock in stocks:
        db.add(stock)

    db.commit()

    for stock in stocks:
        db.refresh(stock)

    return stocks


@pytest.fixture
def test_holdings(db: Session, test_portfolio: Portfolio, test_stocks: list):
    """Create test holdings."""
    holdings = [
        Holding(
            portfolio_id=test_portfolio.id,
            stock_id=test_stocks[0].id,  # CBA
            quantity=Decimal("100"),
            average_cost=Decimal("50.00")
            # current_value is calculated dynamically via hybrid_property
        ),
        Holding(
            portfolio_id=test_portfolio.id,
            stock_id=test_stocks[1].id,  # BHP
            quantity=Decimal("200"),
            average_cost=Decimal("30.00")
            # current_value is calculated dynamically via hybrid_property
        ),
        Holding(
            portfolio_id=test_portfolio.id,
            stock_id=test_stocks[2].id,  # WBC
            quantity=Decimal("150"),
            average_cost=Decimal("20.00")
            # current_value is calculated dynamically via hybrid_property
        )
    ]

    for holding in holdings:
        db.add(holding)

    db.commit()

    for holding in holdings:
        db.refresh(holding)

    return holdings


@pytest.fixture
def test_market_data_provider(db: Session):
    """Create a test market data provider."""
    provider = MarketDataProvider(
        name="yfinance",
        display_name="Yahoo Finance",
        is_enabled=True,
        priority=1
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


@pytest.fixture
def test_cached_prices(db: Session, test_market_data_provider: MarketDataProvider):
    """Create cached price data for test stocks."""
    now = datetime.utcnow()

    prices = [
        RealtimePriceHistory(
            symbol="CBA",
            price=Decimal("55.00"),  # Up from $50 average cost
            provider_id=test_market_data_provider.id,
            source_timestamp=now,
            fetched_at=now
        ),
        RealtimePriceHistory(
            symbol="BHP",
            price=Decimal("35.00"),  # Up from $30 average cost
            provider_id=test_market_data_provider.id,
            source_timestamp=now,
            fetched_at=now
        ),
        RealtimePriceHistory(
            symbol="WBC",
            price=Decimal("18.00"),  # Down from $20 average cost
            provider_id=test_market_data_provider.id,
            source_timestamp=now,
            fetched_at=now
        )
    ]

    for price in prices:
        db.add(price)

    db.commit()

    for price in prices:
        db.refresh(price)

    return prices


class TestDynamicPortfolioValuation:
    """Test dynamic portfolio valuation with real-time market prices."""

    def test_calculate_dynamic_portfolio_value(self, db: Session, test_portfolio: Portfolio, test_holdings: list, test_cached_prices: list):
        """Test dynamic calculation of portfolio total value based on cached market prices."""
        service = DynamicPortfolioService(db)

        # Calculate dynamic portfolio value using cached prices
        portfolio_value = service.calculate_portfolio_value(test_portfolio.id, use_cache=False)

        # Expected calculations based on cached prices:
        # CBA: 100 shares * $55.00 = $5,500.00
        # BHP: 200 shares * $35.00 = $7,000.00
        # WBC: 150 shares * $18.00 = $2,700.00
        # Total: $15,200.00
        expected_total = Decimal("15200.00")

        assert portfolio_value.total_value == expected_total
        assert portfolio_value.total_cost_basis == Decimal("14000.00")  # (100*50) + (200*30) + (150*20)
        assert portfolio_value.total_unrealized_gain == Decimal("1200.00")  # 15200 - 14000
        assert abs(portfolio_value.total_gain_percent - Decimal("8.57")) < Decimal("0.01")  # (1200/14000) * 100, allow rounding

    def test_get_dynamic_portfolio_response(self, db: Session, test_portfolio: Portfolio, test_holdings: list, test_cached_prices: list):
        """Test getting complete portfolio response with dynamic values."""
        service = DynamicPortfolioService(db)

        # Get dynamic portfolio response
        portfolio_response = service.get_dynamic_portfolio(test_portfolio.id)

        # Verify portfolio values are calculated dynamically
        assert portfolio_response.total_value == Decimal("15200.00")
        assert portfolio_response.daily_change == Decimal("1200.00")
        assert abs(portfolio_response.daily_change_percent - Decimal("8.57")) < Decimal("0.01")

        # TODO: Holdings test to be implemented when Pydantic validation issues resolved

    def test_handle_missing_price_data(self, db: Session, test_portfolio: Portfolio, test_holdings: list, test_market_data_provider: MarketDataProvider):
        """Test handling when price data is not available for some stocks."""
        # Create partial cached price data (missing WBC)
        now = datetime.utcnow()

        prices = [
            RealtimePriceHistory(
                symbol="CBA",
                price=Decimal("55.00"),
                provider_id=test_market_data_provider.id,
                source_timestamp=now,
                fetched_at=now
            ),
            RealtimePriceHistory(
                symbol="BHP",
                price=Decimal("35.00"),
                provider_id=test_market_data_provider.id,
                source_timestamp=now,
                fetched_at=now
            )
            # WBC price missing
        ]

        for price in prices:
            db.add(price)
        db.commit()

        service = DynamicPortfolioService(db)
        portfolio_value = service.calculate_portfolio_value(test_portfolio.id, use_cache=False)

        # Should use fallback to average_cost for WBC
        expected_cba_value = Decimal("5500.00")  # 100 * 55.00
        expected_bhp_value = Decimal("7000.00")  # 200 * 35.00
        expected_wbc_value = Decimal("3000.00")  # 150 * 20.00 (fallback to average_cost)

        expected_total = expected_cba_value + expected_bhp_value + expected_wbc_value
        assert portfolio_value.total_value == expected_total

    def test_empty_portfolio_returns_zero_value(self, db: Session, test_portfolio: Portfolio):
        """Test that empty portfolio returns zero values."""
        service = DynamicPortfolioService(db)
        portfolio_value = service.calculate_portfolio_value(test_portfolio.id)

        assert portfolio_value.total_value == Decimal("0.00")
        assert portfolio_value.total_cost_basis == Decimal("0.00")
        assert portfolio_value.total_unrealized_gain == Decimal("0.00")
        assert portfolio_value.total_gain_percent == Decimal("0.00")

    def test_portfolio_api_returns_dynamic_values(self, db: Session, test_portfolio: Portfolio, test_holdings: list, test_cached_prices: list):
        """Test that portfolio API endpoints return dynamically calculated values."""
        # This test will be implemented after we update the API endpoints
        # to use dynamic portfolio service
        pass
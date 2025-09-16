"""
Integration tests for market data service triggering portfolio updates.
Tests the complete flow from price data arrival to portfolio value updates.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from src.models import Portfolio, User, Stock, Holding, RealtimePriceHistory, MarketDataProvider
from src.services.market_data_service import MarketDataService
from src.services.real_time_portfolio_service import RealTimePortfolioService


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    user = User(
        email="integration@example.com",
        password_hash="$2b$12$dummy.hash.value",
        first_name="Integration",
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
        name="Integration Portfolio",
        description="Portfolio for market data integration testing",
        owner_id=test_user.id,
        total_value=Decimal("0.00"),  # Will be calculated
        daily_change=Decimal("0.00"),  # Will be calculated
        daily_change_percent=Decimal("0.00")  # Will be calculated
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@pytest.fixture
def test_stock(db: Session):
    """Create a test stock."""
    stock = Stock(
        symbol="TSLA",
        company_name="Tesla Inc.",
        exchange="NASDAQ"
    )
    db.add(stock)
    db.commit()
    db.refresh(stock)
    return stock


@pytest.fixture
def test_holding(db: Session, test_portfolio: Portfolio, test_stock: Stock):
    """Create a test holding."""
    holding = Holding(
        portfolio_id=test_portfolio.id,
        stock_id=test_stock.id,
        quantity=Decimal("50"),
        average_cost=Decimal("200.00")  # Cost basis $200
    )
    db.add(holding)
    db.commit()
    db.refresh(holding)
    return holding


@pytest.fixture
def test_provider(db: Session):
    """Create a test market data provider."""
    provider = MarketDataProvider(
        name="test_integration_provider",
        display_name="Test Integration Provider",
        is_enabled=True,
        priority=1
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


class TestMarketDataPortfolioIntegration:
    """Test integration between market data service and portfolio updates."""

    @pytest.mark.asyncio
    async def test_market_data_storage_triggers_portfolio_update(self, db: Session, test_portfolio: Portfolio, test_holding: Holding, test_stock: Stock, test_provider: MarketDataProvider):
        """Test that storing price data automatically triggers portfolio updates."""
        market_service = MarketDataService(db)

        # Initially portfolio should have 0 values since no price data exists
        assert test_portfolio.total_value == Decimal("0.00")
        assert test_portfolio.daily_change == Decimal("0.00")
        assert test_portfolio.daily_change_percent == Decimal("0.00")

        # Simulate price data being stored through market data service
        price_data = {
            "price": Decimal("220.00"),  # Current price $220 (up from opening)
            "open_price": Decimal("210.00"),  # Opened at $210
            "volume": 1000000,
            "source_timestamp": datetime.utcnow(),
            "provider": "test"
        }

        # Store price data - this should automatically trigger portfolio update
        await market_service._store_price_data("TSLA", price_data, test_provider)

        # Refresh portfolio to see updates
        db.refresh(test_portfolio)

        # Portfolio should now be updated automatically
        # Portfolio value: 50 shares * $220 = $11,000
        assert test_portfolio.total_value == Decimal("11000.00")

        # Daily change: (220-210) * 50 shares = $500
        assert test_portfolio.daily_change == Decimal("500.00")

        # Daily change percentage: $500 / (210 * 50) = 4.76%
        expected_percent = round((Decimal("500.00") / Decimal("10500.00")) * 100, 2)
        assert test_portfolio.daily_change_percent == expected_percent

    @pytest.mark.asyncio
    async def test_bulk_price_updates_trigger_efficient_portfolio_updates(self, db: Session, test_user: User, test_provider: MarketDataProvider):
        """Test that bulk price updates trigger efficient bulk portfolio updates."""
        market_service = MarketDataService(db)

        # Create portfolio with multiple stocks
        portfolio = Portfolio(
            name="Bulk Update Portfolio",
            description="Portfolio for bulk update testing",
            owner_id=test_user.id
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)

        # Add multiple stocks and holdings
        symbols = ["AAPL", "GOOGL", "MSFT"]
        stocks = []
        for symbol in symbols:
            stock = Stock(symbol=symbol, company_name=f"{symbol} Inc.", exchange="NASDAQ")
            db.add(stock)
            db.commit()
            db.refresh(stock)
            stocks.append(stock)

            holding = Holding(
                portfolio_id=portfolio.id,
                stock_id=stock.id,
                quantity=Decimal("100"),
                average_cost=Decimal("150.00")
            )
            db.add(holding)

        db.commit()

        # Create mock bulk price data
        bulk_price_data = {}
        for symbol in symbols:
            bulk_price_data[symbol] = {
                "price": Decimal("160.00"),  # All up $10 from opening
                "open_price": Decimal("150.00"),
                "volume": 1000000,
                "source_timestamp": datetime.utcnow(),
                "provider": "test"
            }

        # Store all price data - this should trigger individual portfolio updates
        # but our bulk trigger should optimize this
        for symbol, price_data in bulk_price_data.items():
            await market_service._store_price_data(symbol, price_data, test_provider)

        # Now simulate a bulk operation completing and triggering bulk updates
        market_service._trigger_bulk_portfolio_updates(symbols)

        # Refresh portfolio
        db.refresh(portfolio)

        # Portfolio should be updated correctly
        # Portfolio value: 3 stocks * 100 shares * $160 = $48,000
        assert portfolio.total_value == Decimal("48000.00")

        # Daily change: 3 stocks * 100 shares * $10 = $3,000
        assert portfolio.daily_change == Decimal("3000.00")

    @pytest.mark.asyncio
    async def test_price_storage_failure_does_not_break_portfolio_updates(self, db: Session, test_portfolio: Portfolio, test_holding: Holding, test_stock: Stock, test_provider: MarketDataProvider):
        """Test that portfolio update errors don't break price storage."""
        market_service = MarketDataService(db)

        # Create price data
        price_data = {
            "price": Decimal("250.00"),
            "open_price": Decimal("240.00"),
            "volume": 500000,
            "source_timestamp": datetime.utcnow(),
            "provider": "test"
        }

        # Even if portfolio update fails, price storage should succeed
        # Store price data
        price_record = await market_service._store_price_data("TSLA", price_data, test_provider)

        # Price should be stored successfully
        assert price_record is not None
        assert price_record.symbol == "TSLA"
        assert price_record.price == Decimal("250.00")

        # Check that price record exists in database
        stored_price = db.query(RealtimePriceHistory).filter(
            RealtimePriceHistory.symbol == "TSLA"
        ).first()

        assert stored_price is not None
        assert stored_price.price == Decimal("250.00")

    @pytest.mark.asyncio
    async def test_portfolio_updates_only_for_relevant_symbols(self, db: Session, test_portfolio: Portfolio, test_holding: Holding, test_stock: Stock, test_provider: MarketDataProvider):
        """Test that portfolio updates only happen for symbols in portfolios."""
        market_service = MarketDataService(db)

        # Store price for a symbol NOT in any portfolio
        irrelevant_price_data = {
            "price": Decimal("100.00"),
            "open_price": Decimal("95.00"),
            "volume": 100000,
            "source_timestamp": datetime.utcnow(),
            "provider": "test"
        }

        # Store price for symbol not in portfolio
        await market_service._store_price_data("NVDA", irrelevant_price_data, test_provider)

        # Portfolio should remain unchanged
        db.refresh(test_portfolio)
        assert test_portfolio.total_value == Decimal("0.00")
        assert test_portfolio.daily_change == Decimal("0.00")

        # Now store price for symbol IN the portfolio
        relevant_price_data = {
            "price": Decimal("230.00"),
            "open_price": Decimal("220.00"),
            "volume": 200000,
            "source_timestamp": datetime.utcnow(),
            "provider": "test"
        }

        await market_service._store_price_data("TSLA", relevant_price_data, test_provider)

        # Portfolio should now be updated
        db.refresh(test_portfolio)
        assert test_portfolio.total_value > Decimal("0.00")
        assert test_portfolio.daily_change > Decimal("0.00")
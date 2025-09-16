"""
Integration tests for real-time portfolio updates triggered by market data changes.
Tests that portfolio values and daily changes update automatically when market prices change.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from src.models import Portfolio, User, Stock, Holding, RealtimePriceHistory, MarketDataProvider
from src.services.real_time_portfolio_service import RealTimePortfolioService
from src.services.market_data_service import MarketDataService


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    user = User(
        email="realtime@example.com",
        password_hash="$2b$12$dummy.hash.value",
        first_name="RealTime",
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
        name="RealTime Portfolio",
        description="Portfolio for real-time update testing",
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
        symbol="AAPL",
        company_name="Apple Inc.",
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
        quantity=Decimal("100"),
        average_cost=Decimal("150.00")  # Cost basis $150
    )
    db.add(holding)
    db.commit()
    db.refresh(holding)
    return holding


@pytest.fixture
def test_provider(db: Session):
    """Create a test market data provider."""
    provider = MarketDataProvider(
        name="test_provider",
        display_name="Test Provider",
        is_enabled=True,
        priority=1
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


class TestRealTimePortfolioUpdates:
    """Test real-time portfolio updates triggered by market data changes."""

    def test_portfolio_updates_when_price_changes_first_time(self, db: Session, test_portfolio: Portfolio, test_holding: Holding, test_stock: Stock, test_provider: MarketDataProvider):
        """Test that portfolio updates when stock price changes for the first time (no previous close)."""
        service = RealTimePortfolioService(db)

        # Initially portfolio should have 0 values since no price data exists
        assert test_portfolio.total_value == Decimal("0.00")
        assert test_portfolio.daily_change == Decimal("0.00")
        assert test_portfolio.daily_change_percent == Decimal("0.00")

        # Simulate price data arrival (first price of the day)
        price_data = RealtimePriceHistory(
            symbol="AAPL",
            price=Decimal("160.00"),  # Current price $160
            opening_price=Decimal("155.00"),  # Opened at $155
            provider_id=test_provider.id,
            source_timestamp=datetime.utcnow(),
            fetched_at=datetime.utcnow()
        )
        db.add(price_data)
        db.commit()

        # Trigger portfolio update for affected portfolios
        affected_portfolios = service.update_portfolios_for_symbol("AAPL")

        # Verify portfolio was updated
        assert len(affected_portfolios) == 1
        db.refresh(test_portfolio)

        # Portfolio value: 100 shares * $160 = $16,000
        assert test_portfolio.total_value == Decimal("16000.00")

        # Daily change: Current ($160) vs Opening ($155) = $5 per share * 100 shares = $500
        assert test_portfolio.daily_change == Decimal("500.00")

        # Daily change percentage: $500 / ($155 * 100 shares) = 3.23%
        expected_percent = round((Decimal("500.00") / Decimal("15500.00")) * 100, 2)
        assert test_portfolio.daily_change_percent == expected_percent

    def test_portfolio_updates_when_price_drops(self, db: Session, test_portfolio: Portfolio, test_holding: Holding, test_stock: Stock, test_provider: MarketDataProvider):
        """Test that portfolio correctly calculates negative daily changes when price drops."""
        service = RealTimePortfolioService(db)

        # Simulate price drop
        price_data = RealtimePriceHistory(
            symbol="AAPL",
            price=Decimal("145.00"),  # Current price $145 (down from opening)
            opening_price=Decimal("150.00"),  # Opened at $150
            provider_id=test_provider.id,
            source_timestamp=datetime.utcnow(),
            fetched_at=datetime.utcnow()
        )
        db.add(price_data)
        db.commit()

        # Trigger portfolio update
        service.update_portfolios_for_symbol("AAPL")
        db.refresh(test_portfolio)

        # Portfolio value: 100 shares * $145 = $14,500
        assert test_portfolio.total_value == Decimal("14500.00")

        # Daily change: Current ($145) vs Opening ($150) = -$5 per share * 100 shares = -$500
        assert test_portfolio.daily_change == Decimal("-500.00")

        # Daily change percentage: -$500 / ($150 * 100 shares) = -3.33%
        expected_percent = round((Decimal("-500.00") / Decimal("15000.00")) * 100, 2)
        assert test_portfolio.daily_change_percent == expected_percent

    def test_portfolio_updates_when_multiple_stocks_change(self, db: Session, test_portfolio: Portfolio, test_stock: Stock, test_holding: Holding, test_provider: MarketDataProvider):
        """Test portfolio updates correctly when multiple stocks in portfolio change."""
        service = RealTimePortfolioService(db)

        # Add another stock to the portfolio
        stock2 = Stock(symbol="GOOGL", company_name="Alphabet Inc.", exchange="NASDAQ")
        db.add(stock2)
        db.commit()
        db.refresh(stock2)

        holding2 = Holding(
            portfolio_id=test_portfolio.id,
            stock_id=stock2.id,
            quantity=Decimal("50"),
            average_cost=Decimal("2000.00")  # Cost basis $2000
        )
        db.add(holding2)
        db.commit()

        # Add price data for both stocks
        price1 = RealtimePriceHistory(
            symbol="AAPL",
            price=Decimal("155.00"),  # Current $155
            opening_price=Decimal("150.00"),  # Opened at $150, up $5
            provider_id=test_provider.id,
            source_timestamp=datetime.utcnow(),
            fetched_at=datetime.utcnow()
        )

        price2 = RealtimePriceHistory(
            symbol="GOOGL",
            price=Decimal("1950.00"),  # Current $1950
            opening_price=Decimal("2000.00"),  # Opened at $2000, down $50
            provider_id=test_provider.id,
            source_timestamp=datetime.utcnow(),
            fetched_at=datetime.utcnow()
        )

        db.add(price1)
        db.add(price2)
        db.commit()

        # Update portfolio for both stocks
        service.update_portfolios_for_symbol("AAPL")
        service.update_portfolios_for_symbol("GOOGL")
        db.refresh(test_portfolio)

        # Portfolio value: (100 * $155) + (50 * $1950) = $15,500 + $97,500 = $113,000
        assert test_portfolio.total_value == Decimal("113000.00")

        # Daily change:
        # AAPL: (155-150) * 100 = +$500
        # GOOGL: (1950-2000) * 50 = -$2,500
        # Total: +$500 - $2,500 = -$2,000
        assert test_portfolio.daily_change == Decimal("-2000.00")

        # Daily change percentage: -$2000 / opening value
        # Opening value: (150 * 100) + (2000 * 50) = $15,000 + $100,000 = $115,000
        expected_percent = round((Decimal("-2000.00") / Decimal("115000.00")) * 100, 2)
        assert test_portfolio.daily_change_percent == expected_percent

    def test_portfolio_ignores_old_price_data(self, db: Session, test_portfolio: Portfolio, test_holding: Holding, test_stock: Stock, test_provider: MarketDataProvider):
        """Test that portfolio updates use only the most recent price data."""
        service = RealTimePortfolioService(db)

        # Add old price data (should be ignored)
        old_time = datetime.utcnow() - timedelta(hours=2)
        old_price = RealtimePriceHistory(
            symbol="AAPL",
            price=Decimal("100.00"),  # Old price
            opening_price=Decimal("95.00"),
            provider_id=test_provider.id,
            source_timestamp=old_time,
            fetched_at=old_time
        )
        db.add(old_price)
        db.commit()

        # Add recent price data (should be used)
        recent_time = datetime.utcnow()
        recent_price = RealtimePriceHistory(
            symbol="AAPL",
            price=Decimal("160.00"),  # Recent price
            opening_price=Decimal("155.00"),
            provider_id=test_provider.id,
            source_timestamp=recent_time,
            fetched_at=recent_time
        )
        db.add(recent_price)
        db.commit()

        # Update portfolio
        service.update_portfolios_for_symbol("AAPL")
        db.refresh(test_portfolio)

        # Should use recent price, not old price
        # Portfolio value: 100 shares * $160 = $16,000 (not 100 * $100 = $10,000)
        assert test_portfolio.total_value == Decimal("16000.00")

        # Daily change based on recent data: (160-155) * 100 = $500
        assert test_portfolio.daily_change == Decimal("500.00")

    def test_service_finds_affected_portfolios_efficiently(self, db: Session, test_user: User, test_stock: Stock, test_provider: MarketDataProvider):
        """Test that the service efficiently finds all portfolios affected by a stock price change."""
        service = RealTimePortfolioService(db)

        # Create multiple portfolios with the same stock
        portfolios = []
        for i in range(3):
            portfolio = Portfolio(
                name=f"Portfolio {i}",
                description=f"Test portfolio {i}",
                owner_id=test_user.id
            )
            db.add(portfolio)
            db.commit()
            db.refresh(portfolio)

            holding = Holding(
                portfolio_id=portfolio.id,
                stock_id=test_stock.id,
                quantity=Decimal(str(100 * (i + 1))),  # 100, 200, 300 shares
                average_cost=Decimal("150.00")
            )
            db.add(holding)
            portfolios.append(portfolio)

        db.commit()

        # Add price data
        price_data = RealtimePriceHistory(
            symbol="AAPL",
            price=Decimal("160.00"),
            opening_price=Decimal("155.00"),
            provider_id=test_provider.id,
            source_timestamp=datetime.utcnow(),
            fetched_at=datetime.utcnow()
        )
        db.add(price_data)
        db.commit()

        # Update portfolios for the stock
        affected_portfolios = service.update_portfolios_for_symbol("AAPL")

        # Should find all 3 portfolios
        assert len(affected_portfolios) == 3

        # Verify all portfolios were updated with correct values
        for i, portfolio in enumerate(portfolios):
            db.refresh(portfolio)
            expected_value = Decimal(str(160.00 * 100 * (i + 1)))  # 16000, 32000, 48000
            expected_change = Decimal(str(5.00 * 100 * (i + 1)))    # 500, 1000, 1500

            assert portfolio.total_value == expected_value
            assert portfolio.daily_change == expected_change

    def test_service_handles_missing_opening_price_gracefully(self, db: Session, test_portfolio: Portfolio, test_holding: Holding, test_stock: Stock, test_provider: MarketDataProvider):
        """Test that service handles missing opening price data gracefully."""
        service = RealTimePortfolioService(db)

        # Add price data without opening price (some providers might not provide this)
        price_data = RealtimePriceHistory(
            symbol="AAPL",
            price=Decimal("160.00"),  # Current price only
            opening_price=None,  # Missing opening price
            provider_id=test_provider.id,
            source_timestamp=datetime.utcnow(),
            fetched_at=datetime.utcnow()
        )
        db.add(price_data)
        db.commit()

        # Update portfolio
        service.update_portfolios_for_symbol("AAPL")
        db.refresh(test_portfolio)

        # Should still update portfolio value
        assert test_portfolio.total_value == Decimal("16000.00")

        # Daily change should be 0 when opening price is missing
        assert test_portfolio.daily_change == Decimal("0.00")
        assert test_portfolio.daily_change_percent == Decimal("0.00")

    def test_bulk_portfolio_updates_are_efficient(self, db: Session, test_user: User, test_provider: MarketDataProvider):
        """Test that bulk portfolio updates for multiple symbols are efficient."""
        service = RealTimePortfolioService(db)

        # Create multiple stocks and portfolios
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        stocks = []
        portfolio = Portfolio(
            name="Diversified Portfolio",
            description="Portfolio with multiple stocks",
            owner_id=test_user.id
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)

        # Add stocks and holdings
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

        # Add price data for all symbols
        for symbol in symbols:
            price_data = RealtimePriceHistory(
                symbol=symbol,
                price=Decimal("160.00"),
                opening_price=Decimal("155.00"),
                provider_id=test_provider.id,
                source_timestamp=datetime.utcnow(),
                fetched_at=datetime.utcnow()
            )
            db.add(price_data)

        db.commit()

        # Bulk update portfolios for all symbols
        all_affected = service.bulk_update_portfolios_for_symbols(symbols)

        # Should find the portfolio once (not 4 times)
        assert len(all_affected) == 1
        assert all_affected[0].id == portfolio.id

        db.refresh(portfolio)

        # Portfolio value: 4 stocks * 100 shares * $160 = $64,000
        assert portfolio.total_value == Decimal("64000.00")

        # Daily change: 4 stocks * 100 shares * $5 = $2,000
        assert portfolio.daily_change == Decimal("2000.00")
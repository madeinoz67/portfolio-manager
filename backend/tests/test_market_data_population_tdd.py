"""
TDD test suite for market data population to enable frontend daily change display.

This test defines the expected behavior for populating market data tables
so that portfolio daily change calculations work correctly in production.

The issue: Frontend shows $0.00 daily change because:
- realtime_symbols table is empty (no master records)
- stocks table has no previous_close data
- Daily change calculation needs both for (current_price - previous_close) * quantity
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.models.portfolio import Portfolio
from src.models.holding import Holding
from src.models.user import User
from src.models.stock import Stock
from src.models.realtime_symbol import RealtimeSymbol
from src.models.realtime_price_history import RealtimePriceHistory
from src.models.market_data_provider import MarketDataProvider
from src.services.dynamic_portfolio_service import DynamicPortfolioService
from src.utils.datetime_utils import utc_now


class TestMarketDataPopulationForDailyChange:
    """Test suite for market data population to enable daily change calculations."""

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
            name="yfinance",
            display_name="Yahoo Finance",
            api_key="",
            is_enabled=True
        )
        db_session.add(provider)
        db_session.commit()
        return provider

    @pytest.fixture
    def test_portfolio_with_holdings(self, db_session: Session, test_user, test_provider):
        """Create test portfolio with holdings that match production data."""
        # Create portfolio
        portfolio = Portfolio(
            name="Test Portfolio",
            owner_id=test_user.id
        )
        db_session.add(portfolio)

        # Create stocks that match production (FE and CSL)
        stocks_data = [
            {"symbol": "FE", "company_name": "FirstEnergy Corp", "current_price": Decimal("43.59")},
            {"symbol": "CSL", "company_name": "Carlisle Companies Inc", "current_price": Decimal("201.53")}
        ]

        stocks = []
        for stock_data in stocks_data:
            stock = Stock(
                symbol=stock_data["symbol"],
                company_name=stock_data["company_name"],
                current_price=stock_data["current_price"]
            )
            db_session.add(stock)
            stocks.append(stock)

        db_session.commit()

        # Create holdings that match production
        holdings_data = [
            {"stock": stocks[0], "quantity": 100, "average_cost": Decimal("44.14")},  # FE
            {"stock": stocks[1], "quantity": 50, "average_cost": Decimal("203.70")}   # CSL
        ]

        for holding_data in holdings_data:
            holding = Holding(
                portfolio_id=portfolio.id,
                stock_id=holding_data["stock"].id,
                quantity=holding_data["quantity"],
                average_cost=holding_data["average_cost"]
            )
            db_session.add(holding)

        db_session.commit()
        return portfolio, stocks

    def test_empty_market_data_results_in_zero_daily_change(
        self, db_session: Session, test_portfolio_with_holdings
    ):
        """
        Test that empty market data tables result in zero daily change.

        This reproduces the current production issue where the frontend
        shows $0.00 daily change because market data is not populated.
        """
        portfolio, stocks = test_portfolio_with_holdings

        # Verify market data tables are empty (like production)
        realtime_symbols_count = db_session.query(RealtimeSymbol).count()
        assert realtime_symbols_count == 0, "Realtime symbols table should be empty initially"

        # Verify stocks have no previous_close data (like production)
        for stock in stocks:
            db_session.refresh(stock)
            assert stock.previous_close is None, f"Stock {stock.symbol} should have no previous_close initially"

        # Calculate daily change - should be $0.00 due to missing data
        portfolio_service = DynamicPortfolioService(db_session)
        dynamic_portfolio = portfolio_service.get_dynamic_portfolio(portfolio.id)

        # Assert: Daily change is $0.00 due to missing market data
        assert dynamic_portfolio.daily_change == Decimal("0.00")
        assert dynamic_portfolio.daily_change_percent == Decimal("0.00")

    def test_populated_market_data_enables_daily_change_calculation(
        self, db_session: Session, test_portfolio_with_holdings, test_provider
    ):
        """
        Test that properly populated market data enables daily change calculation.

        This test defines the expected behavior after market data population.
        """
        portfolio, stocks = test_portfolio_with_holdings

        # Arrange: Populate market data like a market data service would
        market_data = [
            {
                "symbol": "FE",
                "current_price": Decimal("43.59"),
                "previous_close": Decimal("42.50")  # $1.09 increase
            },
            {
                "symbol": "CSL",
                "current_price": Decimal("201.53"),
                "previous_close": Decimal("200.00")  # $1.53 increase
            }
        ]

        for data in market_data:
            # Update stock with previous_close
            stock = db_session.query(Stock).filter(Stock.symbol == data["symbol"]).first()
            stock.previous_close = data["previous_close"]

            # Create price history record
            price_history = RealtimePriceHistory(
                symbol=data["symbol"],
                price=data["current_price"],
                previous_close=data["previous_close"],
                source_timestamp=utc_now(),
                fetched_at=utc_now(),
                provider_id=test_provider.id
            )
            db_session.add(price_history)
            db_session.commit()

            # Create master symbol record (single source of truth)
            master_symbol = RealtimeSymbol(
                symbol=data["symbol"],
                current_price=data["current_price"],
                company_name=stock.company_name,
                last_updated=utc_now(),
                provider_id=test_provider.id,
                latest_history_id=price_history.id
            )
            db_session.add(master_symbol)

        db_session.commit()

        # Act: Calculate daily change with populated data
        portfolio_service = DynamicPortfolioService(db_session)
        dynamic_portfolio = portfolio_service.get_dynamic_portfolio(portfolio.id)

        # Assert: Daily change should be calculated correctly
        # FE: (43.59 - 42.50) * 100 = $109.00
        # CSL: (201.53 - 200.00) * 50 = $76.50
        # Total: $109.00 + $76.50 = $185.50
        expected_daily_change = Decimal("185.50")

        assert dynamic_portfolio.daily_change == expected_daily_change
        assert dynamic_portfolio.daily_change_percent > Decimal("0.00")

    def test_market_data_service_populates_existing_portfolio_symbols(
        self, db_session: Session, test_portfolio_with_holdings, test_provider
    ):
        """
        Test that a market data service can populate data for existing portfolio symbols.

        This test defines how a market data population service should work.
        """
        portfolio, stocks = test_portfolio_with_holdings

        # Get symbols from existing portfolios with holdings
        portfolio_symbols = db_session.execute(text("""
            SELECT DISTINCT s.symbol, s.current_price, s.company_name
            FROM stocks s
            JOIN holdings h ON s.id = h.stock_id
            JOIN portfolios p ON h.portfolio_id = p.id
            WHERE p.is_active = true AND h.quantity > 0
        """)).fetchall()

        assert len(portfolio_symbols) == 2  # FE and CSL
        symbols_list = [row.symbol for row in portfolio_symbols]
        assert "FE" in symbols_list
        assert "CSL" in symbols_list

        # Simulate market data service populating these symbols
        for row in portfolio_symbols:
            # Mock previous close as 98% of current price
            mock_previous_close = Decimal(str(row.current_price)) * Decimal("0.98")

            # Update stock record
            stock = db_session.query(Stock).filter(Stock.symbol == row.symbol).first()
            stock.previous_close = mock_previous_close

            # Create history record
            price_history = RealtimePriceHistory(
                symbol=row.symbol,
                price=row.current_price,
                previous_close=mock_previous_close,
                source_timestamp=utc_now(),
                fetched_at=utc_now(),
                provider_id=test_provider.id
            )
            db_session.add(price_history)
            db_session.commit()

            # Create master symbol record
            master_symbol = RealtimeSymbol(
                symbol=row.symbol,
                current_price=row.current_price,
                company_name=row.company_name,
                last_updated=utc_now(),
                provider_id=test_provider.id,
                latest_history_id=price_history.id
            )
            db_session.add(master_symbol)

        db_session.commit()

        # Verify market data is now populated
        realtime_symbols_count = db_session.query(RealtimeSymbol).count()
        assert realtime_symbols_count == 2, "Should have created master records for both symbols"

        # Verify daily change calculation now works
        portfolio_service = DynamicPortfolioService(db_session)
        dynamic_portfolio = portfolio_service.get_dynamic_portfolio(portfolio.id)

        # Should have non-zero daily change due to 2% price increases
        assert dynamic_portfolio.daily_change > Decimal("0.00")
        assert dynamic_portfolio.daily_change_percent > Decimal("0.00")

    def test_market_data_population_service_integration(
        self, db_session: Session, test_portfolio_with_holdings, test_provider
    ):
        """
        Test integration with a market data population service.

        This test defines the expected interface and behavior for a service
        that populates market data for existing portfolio holdings.
        """
        portfolio, stocks = test_portfolio_with_holdings

        # This will be implemented: MarketDataPopulationService
        # For now, we simulate what it should do

        # Step 1: Identify symbols that need market data
        symbols_needing_data = db_session.execute(text("""
            SELECT DISTINCT s.symbol
            FROM stocks s
            JOIN holdings h ON s.id = h.stock_id
            WHERE s.symbol NOT IN (SELECT symbol FROM realtime_symbols)
        """)).fetchall()

        assert len(symbols_needing_data) == 2  # FE and CSL initially missing

        # Step 2: Simulate populating market data (what the service should do)
        for row in symbols_needing_data:
            symbol = row.symbol
            stock = db_session.query(Stock).filter(Stock.symbol == symbol).first()

            # Mock market data fetch
            current_price = stock.current_price
            previous_close = current_price * Decimal("0.97")  # 3% increase

            # Update stock
            stock.previous_close = previous_close

            # Create history
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

            # Create master symbol
            master_symbol = RealtimeSymbol(
                symbol=symbol,
                current_price=current_price,
                company_name=stock.company_name,
                last_updated=utc_now(),
                provider_id=test_provider.id,
                latest_history_id=price_history.id
            )
            db_session.add(master_symbol)

        db_session.commit()

        # Step 3: Verify no more symbols need data
        remaining_symbols = db_session.execute(text("""
            SELECT COUNT(*) as count
            FROM stocks s
            JOIN holdings h ON s.id = h.stock_id
            WHERE s.symbol NOT IN (SELECT symbol FROM realtime_symbols)
        """)).fetchone()

        assert remaining_symbols.count == 0, "All portfolio symbols should now have market data"

        # Step 4: Verify daily change calculation works
        portfolio_service = DynamicPortfolioService(db_session)
        dynamic_portfolio = portfolio_service.get_dynamic_portfolio(portfolio.id)

        # Should have positive daily change due to 3% increases
        assert dynamic_portfolio.daily_change > Decimal("0.00")

        # Verify calculation correctness
        # FE: (43.59 - 42.28) * 100 = 131.00 (approx)
        # CSL: (201.53 - 195.48) * 50 = 302.50 (approx)
        assert dynamic_portfolio.daily_change > Decimal("400.00")  # Should be around $433.50
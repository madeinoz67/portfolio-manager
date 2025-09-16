"""
TDD test suite to understand holdings table display requirements.

This test defines the expected behavior for displaying daily change vs gain/loss
in the holdings table and portfolio summary.

The issue: Holdings table shows "GAIN/LOSS" column with negative values
based on (current_price - average_cost), but user may expect to see
daily change (current_price - previous_close) in addition to or instead of
the total gain/loss against cost basis.

Two different metrics:
1. Daily Change: (current_price - previous_close) * quantity
2. Total Gain/Loss: (current_price - average_cost) * quantity
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


class TestHoldingsDailyChangeDisplay:
    """Test suite to understand and define holdings table display requirements."""

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
    def test_portfolio_with_market_data(self, db_session: Session, test_user, test_provider):
        """Create test portfolio with holdings and complete market data."""
        # Create portfolio
        portfolio = Portfolio(
            name="Test Portfolio",
            owner_id=test_user.id
        )
        db_session.add(portfolio)

        # Create stocks with realistic pricing scenario:
        # - Purchased at higher price (showing loss vs cost)
        # - But gained today (showing daily gain)
        stock_csl = Stock(
            symbol="CSL",
            company_name="CSL FPO [CSL]",
            current_price=Decimal("201.91"),  # Current price
            previous_close=Decimal("195.85")  # Previous close (daily gain)
        )
        stock_fe = Stock(
            symbol="FE",
            company_name="FirstEnergy Corp",
            current_price=Decimal("43.59"),   # Current price
            previous_close=Decimal("42.28")   # Previous close (daily gain)
        )
        db_session.add(stock_csl)
        db_session.add(stock_fe)
        db_session.commit()

        # Create holdings with higher average cost (showing loss vs purchase)
        holding_csl = Holding(
            portfolio_id=portfolio.id,
            stock_id=stock_csl.id,
            quantity=50,
            average_cost=Decimal("203.70")  # Paid more than current price
        )
        holding_fe = Holding(
            portfolio_id=portfolio.id,
            stock_id=stock_fe.id,
            quantity=100,
            average_cost=Decimal("44.14")   # Paid more than current price
        )
        db_session.add(holding_csl)
        db_session.add(holding_fe)

        # Create complete market data (master table + history)
        for stock in [stock_csl, stock_fe]:
            # Create price history
            price_history = RealtimePriceHistory(
                symbol=stock.symbol,
                price=stock.current_price,
                previous_close=stock.previous_close,
                source_timestamp=utc_now(),
                fetched_at=utc_now(),
                provider_id=test_provider.id
            )
            db_session.add(price_history)
            db_session.commit()

            # Create master symbol record
            master_symbol = RealtimeSymbol(
                symbol=stock.symbol,
                current_price=stock.current_price,
                company_name=stock.company_name,
                last_updated=utc_now(),
                provider_id=test_provider.id,
                latest_history_id=price_history.id
            )
            db_session.add(master_symbol)

        db_session.commit()
        return portfolio, [stock_csl, stock_fe], [holding_csl, holding_fe]

    def test_daily_change_vs_total_gain_loss_calculations(
        self, db_session: Session, test_portfolio_with_market_data
    ):
        """
        Test that distinguishes between daily change and total gain/loss.

        This test defines the expected behavior for two different metrics:
        1. Daily Change: Change from previous close to current price
        2. Total Gain/Loss: Change from purchase cost to current price
        """
        portfolio, stocks, holdings = test_portfolio_with_market_data

        # Expected calculations
        expected_calculations = [
            {
                "symbol": "CSL",
                "quantity": 50,
                "current_price": Decimal("201.91"),
                "previous_close": Decimal("195.85"),
                "average_cost": Decimal("203.70"),
                "daily_change_per_share": Decimal("6.06"),     # 201.91 - 195.85
                "total_daily_change": Decimal("303.00"),       # 6.06 * 50
                "gain_loss_per_share": Decimal("-1.79"),       # 201.91 - 203.70
                "total_gain_loss": Decimal("-89.50")           # -1.79 * 50
            },
            {
                "symbol": "FE",
                "quantity": 100,
                "current_price": Decimal("43.59"),
                "previous_close": Decimal("42.28"),
                "average_cost": Decimal("44.14"),
                "daily_change_per_share": Decimal("1.31"),     # 43.59 - 42.28
                "total_daily_change": Decimal("131.00"),       # 1.31 * 100
                "gain_loss_per_share": Decimal("-0.55"),       # 43.59 - 44.14
                "total_gain_loss": Decimal("-55.00")           # -0.55 * 100
            }
        ]

        # Verify calculations match expectations
        for expected in expected_calculations:
            stock = next(s for s in stocks if s.symbol == expected["symbol"])
            holding = next(h for h in holdings if h.stock.symbol == expected["symbol"])

            # Daily change calculations
            daily_change_per_share = stock.current_price - stock.previous_close
            total_daily_change = daily_change_per_share * holding.quantity

            # Total gain/loss calculations
            gain_loss_per_share = stock.current_price - holding.average_cost
            total_gain_loss = gain_loss_per_share * holding.quantity

            # Assert calculations are correct
            assert abs(daily_change_per_share - expected["daily_change_per_share"]) < Decimal("0.01")
            assert abs(total_daily_change - expected["total_daily_change"]) < Decimal("0.01")
            assert abs(gain_loss_per_share - expected["gain_loss_per_share"]) < Decimal("0.01")
            assert abs(total_gain_loss - expected["total_gain_loss"]) < Decimal("0.01")

    def test_portfolio_daily_change_calculation_with_mixed_scenarios(
        self, db_session: Session, test_portfolio_with_market_data
    ):
        """
        Test portfolio-level daily change calculation.

        This validates that the portfolio daily change correctly sums
        individual holding daily changes, not total gains/losses.
        """
        portfolio, stocks, holdings = test_portfolio_with_market_data

        # Calculate portfolio daily change
        portfolio_service = DynamicPortfolioService(db_session)
        dynamic_portfolio = portfolio_service.get_dynamic_portfolio(portfolio.id)

        # Expected portfolio daily change:
        # CSL: (201.91 - 195.85) * 50 = 303.00
        # FE:  (43.59 - 42.28) * 100 = 131.00
        # Total: 303.00 + 131.00 = 434.00
        expected_portfolio_daily_change = Decimal("434.00")

        # Portfolio daily change should be positive (gains today)
        assert dynamic_portfolio.daily_change > Decimal("430.00")
        assert dynamic_portfolio.daily_change < Decimal("440.00")

        # Portfolio total gain/loss should be negative (losses vs cost)
        # CSL: (201.91 - 203.70) * 50 = -89.50
        # FE:  (43.59 - 44.14) * 100 = -55.00
        # Total unrealized loss: -89.50 + -55.00 = -144.50
        assert dynamic_portfolio.unrealized_gain_loss < Decimal("0.00")
        assert abs(dynamic_portfolio.unrealized_gain_loss - Decimal("-144.50")) < Decimal("1.00")

    def test_frontend_holdings_table_data_requirements(
        self, db_session: Session, test_portfolio_with_market_data
    ):
        """
        Test defining what data the frontend holdings table should display.

        Current frontend shows:
        - GAIN/LOSS column: Total gain/loss vs purchase cost
        - TREND column: Direction arrow based on daily change

        This test defines if we need additional data for daily change display.
        """
        portfolio, stocks, holdings = test_portfolio_with_market_data

        # Get current portfolio data
        portfolio_service = DynamicPortfolioService(db_session)
        dynamic_portfolio = portfolio_service.get_dynamic_portfolio(portfolio.id)

        # Frontend should be able to calculate:
        for holding in holdings:
            stock = holding.stock

            # 1. Current gain/loss vs cost (what's currently shown)
            current_gain_loss = (stock.current_price - holding.average_cost) * holding.quantity

            # 2. Daily change (what might be needed for additional display)
            if stock.previous_close:
                daily_change = (stock.current_price - stock.previous_close) * holding.quantity
                daily_change_percent = ((stock.current_price - stock.previous_close) / stock.previous_close) * 100
            else:
                daily_change = Decimal("0.00")
                daily_change_percent = Decimal("0.00")

            # Verify we have all data needed for both calculations
            assert stock.current_price is not None
            assert holding.average_cost is not None
            assert stock.previous_close is not None  # This is now populated

            # Both calculations should be possible
            assert current_gain_loss is not None
            assert daily_change is not None

            print(f"{stock.symbol}:")
            print(f"  Current Gain/Loss: ${current_gain_loss:.2f} (vs avg cost ${holding.average_cost})")
            print(f"  Daily Change: ${daily_change:.2f} ({daily_change_percent:.2f}%)")

    def test_holdings_api_response_includes_daily_change_data(
        self, db_session: Session, test_portfolio_with_market_data
    ):
        """
        Test that the holdings API can provide both gain/loss and daily change data.

        This test defines what the API should return for the frontend to display
        both total gain/loss and daily change information.
        """
        portfolio, stocks, holdings = test_portfolio_with_market_data

        # Simulate API response format
        portfolio_service = DynamicPortfolioService(db_session)
        dynamic_portfolio = portfolio_service.get_dynamic_portfolio(portfolio.id)

        # API should be able to provide holding-level data with both metrics
        expected_holding_data = []
        for holding in holdings:
            stock = holding.stock

            holding_data = {
                "symbol": stock.symbol,
                "company_name": stock.company_name,
                "quantity": float(holding.quantity),
                "average_cost": float(holding.average_cost),
                "current_price": float(stock.current_price),
                "market_value": float(stock.current_price * holding.quantity),

                # Total gain/loss vs purchase cost (current frontend display)
                "total_gain_loss": float((stock.current_price - holding.average_cost) * holding.quantity),
                "total_gain_loss_percent": float(((stock.current_price - holding.average_cost) / holding.average_cost) * 100),

                # Daily change data (potential additional display)
                "daily_change": float((stock.current_price - stock.previous_close) * holding.quantity) if stock.previous_close else 0.0,
                "daily_change_percent": float(((stock.current_price - stock.previous_close) / stock.previous_close) * 100) if stock.previous_close else 0.0,
                "daily_change_per_share": float(stock.current_price - stock.previous_close) if stock.previous_close else 0.0,
            }
            expected_holding_data.append(holding_data)

        # Verify we can calculate both metrics
        for data in expected_holding_data:
            assert "total_gain_loss" in data      # Current frontend display
            assert "daily_change" in data         # Potential additional display
            assert data["total_gain_loss"] != data["daily_change"]  # They should be different

        # The portfolio summary shows the correct daily change
        assert dynamic_portfolio.daily_change > Decimal("0.00")  # Positive daily change
        total_daily_change = sum(data["daily_change"] for data in expected_holding_data)
        assert abs(float(dynamic_portfolio.daily_change) - total_daily_change) < 1.0
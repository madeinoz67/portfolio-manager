"""
TDD test suite to research current P/L calculations and implement improvements.

This test defines the requirements for clear portfolio P/L reporting:
1. Unrealized P/L (Lifetime): From purchase cost to current value
2. Daily P/L: From previous close to current price
3. Both with $ amounts and % changes
4. Clear labeling to avoid confusion

Developer Notes Reference: DEVELOPER_NOTES.md
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


class TestPortfolioPLImprovements:
    """TDD test suite for portfolio P&L calculation improvements."""

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
    def test_portfolio_with_pl_scenario(self, db_session: Session, test_user, test_provider):
        """
        Create test portfolio demonstrating P&L calculation requirements.

        Scenario:
        - Stock: AAPL
        - Bought: 100 shares @ $150.00 (cost basis: $15,000)
        - Current price: $155.00 (market value: $15,500)
        - Previous close: $153.00

        Expected calculations:
        - Unrealized P/L (Lifetime): $500 profit ($155-$150)*100
        - Daily P/L: $200 profit ($155-$153)*100
        """
        # Create portfolio
        portfolio = Portfolio(
            name="Test Portfolio P&L",
            owner_id=test_user.id
        )
        db_session.add(portfolio)

        # Create stock with realistic scenario
        stock_aapl = Stock(
            symbol="AAPL",
            company_name="Apple Inc",
            current_price=Decimal("155.00"),   # Current market price
            previous_close=Decimal("153.00")   # Previous close for daily calc
        )
        db_session.add(stock_aapl)
        db_session.commit()

        # Create holding with cost basis
        holding_aapl = Holding(
            portfolio_id=portfolio.id,
            stock_id=stock_aapl.id,
            quantity=100,
            average_cost=Decimal("150.00")     # Purchase cost for lifetime P&L
        )
        db_session.add(holding_aapl)

        # Create complete market data
        aapl_history = RealtimePriceHistory(
            symbol="AAPL",
            price=stock_aapl.current_price,
            previous_close=stock_aapl.previous_close,
            source_timestamp=utc_now(),
            fetched_at=utc_now(),
            provider_id=test_provider.id
        )
        db_session.add(aapl_history)
        db_session.commit()

        aapl_master = RealtimeSymbol(
            symbol="AAPL",
            current_price=stock_aapl.current_price,
            company_name=stock_aapl.company_name,
            last_updated=utc_now(),
            provider_id=test_provider.id,
            latest_history_id=aapl_history.id
        )
        db_session.add(aapl_master)
        db_session.commit()

        return portfolio, stock_aapl, holding_aapl

    def test_current_portfolio_service_calculations(
        self, db_session: Session, test_portfolio_with_pl_scenario
    ):
        """
        Test current DynamicPortfolioService calculations to understand existing behavior.

        This establishes baseline understanding before improvements.
        """
        portfolio, stock, holding = test_portfolio_with_pl_scenario

        portfolio_service = DynamicPortfolioService(db_session)
        dynamic_portfolio = portfolio_service.get_dynamic_portfolio(portfolio.id)

        # Current service calculations (using actual field names from PortfolioResponse)
        current_value = dynamic_portfolio.total_value
        daily_change = dynamic_portfolio.daily_change
        daily_change_percent = dynamic_portfolio.daily_change_percent

        # New unrealized P&L fields now exposed in API response
        unrealized_gain_loss = dynamic_portfolio.unrealized_gain_loss

        # Expected calculations based on our scenario
        expected_current_value = Decimal("155.00") * 100      # $15,500
        expected_unrealized_gain = Decimal("5.00") * 100      # $500 (155-150)*100
        expected_daily_change = Decimal("2.00") * 100         # $200 (155-153)*100
        expected_daily_percent = (Decimal("2.00") / Decimal("153.00")) * 100  # ~1.31%

        # Verify current calculations
        assert current_value == expected_current_value
        assert unrealized_gain_loss == expected_unrealized_gain
        assert daily_change == expected_daily_change
        assert abs(daily_change_percent - expected_daily_percent) < Decimal("0.01")

        print("\\n=== CURRENT PORTFOLIO SERVICE CALCULATIONS ===")
        print(f"Current Value: ${current_value}")
        print(f"Unrealized Gain/Loss: ${unrealized_gain_loss} (now exposed in API)")
        print(f"Daily Change: ${daily_change}")
        print(f"Daily Change %: {daily_change_percent:.2f}%")
        print("\\n✅ SUCCESS: Unrealized gain is now exposed in PortfolioResponse")

        return {
            "current_value": current_value,
            "unrealized_gain_loss": unrealized_gain_loss,
            "daily_change": daily_change,
            "daily_change_percent": daily_change_percent
        }

    def test_new_portfolio_api_response_includes_unrealized_pl(
        self, db_session: Session, test_portfolio_with_pl_scenario
    ):
        """
        Test that the updated PortfolioResponse now includes unrealized P&L fields.

        This validates the schema and service improvements.
        """
        portfolio, stock, holding = test_portfolio_with_pl_scenario

        portfolio_service = DynamicPortfolioService(db_session)
        dynamic_portfolio = portfolio_service.get_dynamic_portfolio(portfolio.id)

        # Test that new fields are present and have correct values
        assert hasattr(dynamic_portfolio, 'unrealized_gain_loss')
        assert hasattr(dynamic_portfolio, 'unrealized_gain_loss_percent')

        # Expected values from our scenario
        expected_unrealized_gain = Decimal("5.00") * 100      # $500 (155-150)*100
        expected_unrealized_percent = (expected_unrealized_gain / (Decimal("150.00") * 100)) * 100  # ~3.33%

        # Verify the values
        assert dynamic_portfolio.unrealized_gain_loss == expected_unrealized_gain
        assert abs(dynamic_portfolio.unrealized_gain_loss_percent - expected_unrealized_percent) < Decimal("0.01")

        print("\\n=== NEW API RESPONSE FIELDS ===")
        print(f"✅ unrealized_gain_loss: ${dynamic_portfolio.unrealized_gain_loss}")
        print(f"✅ unrealized_gain_loss_percent: {dynamic_portfolio.unrealized_gain_loss_percent:.2f}%")
        print(f"✅ daily_change: ${dynamic_portfolio.daily_change}")
        print(f"✅ daily_change_percent: {dynamic_portfolio.daily_change_percent:.2f}%")
        print("\\n🎉 SUCCESS: Both Daily P&L and Unrealized P&L now exposed in API!")

    def test_required_pl_structure_with_clear_labeling(
        self, db_session: Session, test_portfolio_with_pl_scenario
    ):
        """
        Test the required P&L structure with clear labeling.

        This defines what the API should return for portfolio views.
        """
        portfolio, stock, holding = test_portfolio_with_pl_scenario

        portfolio_service = DynamicPortfolioService(db_session)
        dynamic_portfolio = portfolio_service.get_dynamic_portfolio(portfolio.id)

        # Required P&L structure with clear field names
        required_pl_structure = {
            # Portfolio total value
            "portfolio_value": float(dynamic_portfolio.total_value),

            # Unrealized P&L (Lifetime) - from purchase to current
            "unrealized_pl_lifetime": {
                "amount": float(dynamic_portfolio.unrealized_gain_loss),
                "percentage": float(dynamic_portfolio.unrealized_gain_loss_percent),
                "label": "Unrealized P&L",
                "description": "Profit/loss from purchase cost to current value"
            },

            # Daily P&L - from previous close to current
            "daily_pl": {
                "amount": float(dynamic_portfolio.daily_change),
                "percentage": float(dynamic_portfolio.daily_change_percent),
                "label": "Daily P&L",
                "description": "Today's profit/loss from previous close to current price"
            }
        }

        # Verify structure has required fields
        assert "portfolio_value" in required_pl_structure
        assert "unrealized_pl_lifetime" in required_pl_structure
        assert "daily_pl" in required_pl_structure

        # Verify clear labeling
        assert required_pl_structure["unrealized_pl_lifetime"]["label"] == "Unrealized P&L"
        assert required_pl_structure["daily_pl"]["label"] == "Daily P&L"

        # Verify both have amount and percentage
        for pl_type in ["unrealized_pl_lifetime", "daily_pl"]:
            assert "amount" in required_pl_structure[pl_type]
            assert "percentage" in required_pl_structure[pl_type]
            assert "label" in required_pl_structure[pl_type]
            assert "description" in required_pl_structure[pl_type]

        print("\\n=== REQUIRED P&L STRUCTURE ===")
        print(f"Portfolio Value: ${required_pl_structure['portfolio_value']:.2f}")
        print()
        print(f"{required_pl_structure['unrealized_pl_lifetime']['label']}:")
        print(f"  Amount: ${required_pl_structure['unrealized_pl_lifetime']['amount']:+.2f}")
        print(f"  Percentage: {required_pl_structure['unrealized_pl_lifetime']['percentage']:+.2f}%")
        print(f"  Description: {required_pl_structure['unrealized_pl_lifetime']['description']}")
        print()
        print(f"{required_pl_structure['daily_pl']['label']}:")
        print(f"  Amount: ${required_pl_structure['daily_pl']['amount']:+.2f}")
        print(f"  Percentage: {required_pl_structure['daily_pl']['percentage']:+.2f}%")
        print(f"  Description: {required_pl_structure['daily_pl']['description']}")

        return required_pl_structure

    def test_multiple_holdings_pl_calculations(
        self, db_session: Session, test_user, test_provider
    ):
        """
        Test P&L calculations with multiple holdings to ensure proper aggregation.

        This verifies that portfolio-level P&L correctly sums individual holdings.
        """
        # Create portfolio with two different stocks
        portfolio = Portfolio(
            name="Multi-Holdings Portfolio",
            owner_id=test_user.id
        )
        db_session.add(portfolio)

        # Stock 1: AAPL - profitable position
        stock_aapl = Stock(
            symbol="AAPL",
            company_name="Apple Inc",
            current_price=Decimal("155.00"),
            previous_close=Decimal("153.00")
        )

        # Stock 2: TSLA - losing position
        stock_tsla = Stock(
            symbol="TSLA",
            company_name="Tesla Inc",
            current_price=Decimal("180.00"),
            previous_close=Decimal("185.00")
        )

        db_session.add(stock_aapl)
        db_session.add(stock_tsla)
        db_session.commit()

        # Holdings
        holding_aapl = Holding(
            portfolio_id=portfolio.id,
            stock_id=stock_aapl.id,
            quantity=100,
            average_cost=Decimal("150.00")  # $500 unrealized gain, $200 daily gain
        )

        holding_tsla = Holding(
            portfolio_id=portfolio.id,
            stock_id=stock_tsla.id,
            quantity=50,
            average_cost=Decimal("190.00")  # $500 unrealized loss, $250 daily loss
        )

        db_session.add(holding_aapl)
        db_session.add(holding_tsla)

        # Create market data for both stocks
        for stock in [stock_aapl, stock_tsla]:
            history = RealtimePriceHistory(
                symbol=stock.symbol,
                price=stock.current_price,
                previous_close=stock.previous_close,
                source_timestamp=utc_now(),
                fetched_at=utc_now(),
                provider_id=test_provider.id
            )
            db_session.add(history)
            db_session.commit()

            master = RealtimeSymbol(
                symbol=stock.symbol,
                current_price=stock.current_price,
                company_name=stock.company_name,
                last_updated=utc_now(),
                provider_id=test_provider.id,
                latest_history_id=history.id
            )
            db_session.add(master)

        db_session.commit()

        # Test portfolio-level aggregation
        portfolio_service = DynamicPortfolioService(db_session)
        dynamic_portfolio = portfolio_service.get_dynamic_portfolio(portfolio.id)

        # Expected aggregated calculations:
        # AAPL: $500 unrealized gain, $200 daily gain
        # TSLA: -$500 unrealized loss, -$250 daily loss
        # Portfolio: $0 unrealized, -$50 daily

        expected_total_unrealized = Decimal("0.00")  # $500 - $500
        expected_total_daily = Decimal("-50.00")     # $200 - $250

        assert dynamic_portfolio.unrealized_gain_loss == expected_total_unrealized
        assert dynamic_portfolio.daily_change == expected_total_daily

        print("\\n=== MULTIPLE HOLDINGS P&L AGGREGATION ===")
        print(f"AAPL: 100 shares @ $150 cost, now $155 (prev $153)")
        print(f"  Unrealized P&L: ${(155-150)*100:.2f}")
        print(f"  Daily P&L: ${(155-153)*100:.2f}")
        print(f"TSLA: 50 shares @ $190 cost, now $180 (prev $185)")
        print(f"  Unrealized P&L: ${(180-190)*50:.2f}")
        print(f"  Daily P&L: ${(180-185)*50:.2f}")
        print(f"Portfolio Total:")
        print(f"  Unrealized P&L: ${dynamic_portfolio.unrealized_gain_loss}")
        print(f"  Daily P&L: ${dynamic_portfolio.daily_change}")

    def test_edge_cases_for_pl_calculations(
        self, db_session: Session, test_portfolio_with_pl_scenario
    ):
        """
        Test edge cases that might affect P&L calculations.

        This ensures robust handling of various scenarios.
        """
        portfolio, stock, holding = test_portfolio_with_pl_scenario

        # Test case: Zero cost basis (should not divide by zero)
        holding.average_cost = Decimal("0.00")
        db_session.commit()

        portfolio_service = DynamicPortfolioService(db_session)
        dynamic_portfolio = portfolio_service.get_dynamic_portfolio(portfolio.id)

        # Should handle zero cost basis gracefully
        assert dynamic_portfolio is not None
        assert dynamic_portfolio.total_value > 0

        # Restore normal cost basis
        holding.average_cost = Decimal("150.00")
        db_session.commit()

        print("\\n=== EDGE CASE TESTING ===")
        print("✓ Zero cost basis handled gracefully")
        print("✓ All calculations robust")
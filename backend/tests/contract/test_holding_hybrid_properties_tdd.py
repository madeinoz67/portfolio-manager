"""
TDD Tests for Holding Model Hybrid Properties
Tests the new architecture where calculated values are hybrid properties.
"""

import pytest
from decimal import Decimal
from src.models.holding import Holding
from src.models.stock import Stock, StockStatus
from src.models.portfolio import Portfolio
from src.models.user import User, UserRole


class TestHoldingHybridProperties:
    """Test holding calculations using hybrid properties."""

    def test_current_value_with_stock_current_price(self):
        """Test current_value calculation when stock has current_price."""
        # Arrange
        stock = Stock(
            symbol="BHP",
            company_name="BHP Corporation",
            exchange="ASX",
            current_price=Decimal("42.50"),  # Current market price
            status=StockStatus.ACTIVE
        )

        holding = Holding(
            quantity=Decimal("100"),
            average_cost=Decimal("40.00"),  # Purchased at $40
            stock=stock
        )

        # Act & Assert
        assert holding.current_value == Decimal("4250.00")  # 100 × $42.50

    def test_current_value_fallback_to_cost_basis(self):
        """Test current_value falls back to cost basis when no current_price."""
        # Arrange
        stock = Stock(
            symbol="BHP",
            company_name="BHP Corporation",
            exchange="ASX",
            current_price=None,  # No current price available
            status=StockStatus.ACTIVE
        )

        holding = Holding(
            quantity=Decimal("100"),
            average_cost=Decimal("40.00"),
            stock=stock
        )

        # Act & Assert
        assert holding.current_value == Decimal("4000.00")  # 100 × $40.00 (cost basis)

    def test_cost_basis_calculation(self):
        """Test cost_basis hybrid property."""
        # Arrange
        holding = Holding(
            quantity=Decimal("150"),
            average_cost=Decimal("33.75")
        )

        # Act & Assert
        assert holding.cost_basis == Decimal("5062.50")  # 150 × $33.75

    def test_unrealized_gain_loss_profit(self):
        """Test unrealized gain calculation when stock price increased."""
        # Arrange
        stock = Stock(
            symbol="CBA",
            company_name="Commonwealth Bank",
            exchange="ASX",
            current_price=Decimal("55.20"),  # Higher than purchase price
            status=StockStatus.ACTIVE
        )

        holding = Holding(
            quantity=Decimal("50"),
            average_cost=Decimal("52.80"),  # Including fees
            stock=stock
        )

        # Act & Assert
        cost_basis = Decimal("2640.00")  # 50 × $52.80
        current_value = Decimal("2760.00")  # 50 × $55.20
        expected_gain = Decimal("120.00")  # $2760 - $2640

        assert holding.cost_basis == cost_basis
        assert holding.current_value == current_value
        assert holding.unrealized_gain_loss == expected_gain

    def test_unrealized_gain_loss_loss(self):
        """Test unrealized loss calculation when stock price decreased."""
        # Arrange
        stock = Stock(
            symbol="WES",
            company_name="Wesfarmers",
            exchange="ASX",
            current_price=Decimal("60.00"),  # Lower than purchase price
            status=StockStatus.ACTIVE
        )

        holding = Holding(
            quantity=Decimal("75"),
            average_cost=Decimal("65.666"),  # Including fees from purchase
            stock=stock
        )

        # Act & Assert
        cost_basis = Decimal("4924.95")  # 75 × $65.666
        current_value = Decimal("4500.00")  # 75 × $60.00
        expected_loss = Decimal("-424.95")  # $4500 - $4924.95

        assert holding.cost_basis == cost_basis
        assert holding.current_value == current_value
        assert holding.unrealized_gain_loss == expected_loss

    def test_unrealized_gain_loss_percent_profit(self):
        """Test unrealized gain percentage calculation."""
        # Arrange
        stock = Stock(
            symbol="ANZ",
            company_name="ANZ Bank",
            exchange="ASX",
            current_price=Decimal("25.00"),  # 25% higher than cost
            status=StockStatus.ACTIVE
        )

        holding = Holding(
            quantity=Decimal("100"),
            average_cost=Decimal("20.00"),
            stock=stock
        )

        # Act & Assert
        # Cost basis: $2000, Current value: $2500, Gain: $500
        # Percentage: ($500 / $2000) × 100 = 25%
        assert holding.unrealized_gain_loss_percent == Decimal("25.00")

    def test_unrealized_gain_loss_percent_loss(self):
        """Test unrealized loss percentage calculation."""
        # Arrange
        stock = Stock(
            symbol="TLS",
            company_name="Telstra",
            exchange="ASX",
            current_price=Decimal("3.60"),  # 10% lower than cost
            status=StockStatus.ACTIVE
        )

        holding = Holding(
            quantity=Decimal("200"),
            average_cost=Decimal("4.00"),
            stock=stock
        )

        # Act & Assert
        # Cost basis: $800, Current value: $720, Loss: -$80
        # Percentage: (-$80 / $800) × 100 = -10%
        assert holding.unrealized_gain_loss_percent == Decimal("-10.00")

    def test_unrealized_gain_loss_percent_zero_cost_basis(self):
        """Test percentage calculation with zero cost basis (edge case)."""
        # Arrange
        holding = Holding(
            quantity=Decimal("0"),  # No shares
            average_cost=Decimal("40.00")
        )

        # Act & Assert
        assert holding.unrealized_gain_loss_percent == Decimal("0.00")

    def test_hybrid_properties_with_no_stock_relationship(self):
        """Test hybrid properties when stock relationship is not loaded."""
        # Arrange
        holding = Holding(
            quantity=Decimal("100"),
            average_cost=Decimal("40.00"),
            stock=None  # No stock relationship loaded
        )

        # Act & Assert
        # Should fall back to cost basis for current_value
        assert holding.current_value == Decimal("4000.00")  # 100 × $40.00
        assert holding.cost_basis == Decimal("4000.00")
        assert holding.unrealized_gain_loss == Decimal("0.00")
        assert holding.unrealized_gain_loss_percent == Decimal("0.00")

    def test_average_cost_includes_fees_scenario(self):
        """Test realistic scenario with fees included in average cost."""
        # Arrange: Bought 100 shares at $41.25 + $19.95 fees
        # Total cost: $4125 + $19.95 = $4144.95
        # Average cost per share: $4144.95 / 100 = $41.4495

        stock = Stock(
            symbol="BHP",
            company_name="BHP Corporation",
            exchange="ASX",
            current_price=Decimal("42.50"),  # Current market price
            status=StockStatus.ACTIVE
        )

        holding = Holding(
            quantity=Decimal("100"),
            average_cost=Decimal("41.4495"),  # Includes fees
            stock=stock
        )

        # Act & Assert
        cost_basis = Decimal("4144.95")  # 100 × $41.4495
        current_value = Decimal("4250.00")  # 100 × $42.50
        expected_gain = Decimal("105.05")  # $4250 - $4144.95
        expected_gain_percent = Decimal("2.53")  # (105.05 / 4144.95) × 100 ≈ 2.53%

        assert holding.cost_basis == cost_basis
        assert holding.current_value == current_value
        assert holding.unrealized_gain_loss == expected_gain
        # Allow small rounding difference for percentage
        assert abs(holding.unrealized_gain_loss_percent - expected_gain_percent) < Decimal("0.01")
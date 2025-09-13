"""
TDD Tests for Fee Calculations in Portfolio Management
Tests ensure that transaction fees are properly included in cost basis calculations.
"""

import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from src.database import engine
from src.models import User, Portfolio, Stock, Transaction, Holding
from src.models.transaction import TransactionType, SourceType
from src.models.stock import StockStatus
from src.schemas.transaction import TransactionCreate
from src.services.transaction_service import process_transaction
from src.core.auth import get_password_hash


class TestFeeCalculations:
    """Test fee calculations in portfolio transactions."""

    @pytest.fixture
    def db_session(self):
        """Create a database session for testing."""
        with Session(engine) as session:
            yield session

    @pytest.fixture
    def test_user(self, db_session):
        """Create a test user."""
        user = User(
            email="test@example.com",
            password_hash=get_password_hash("test123"),
            first_name="Test",
            last_name="User",
            role="USER"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    @pytest.fixture
    def test_portfolio(self, db_session, test_user):
        """Create a test portfolio."""
        portfolio = Portfolio(
            name="Test Fee Portfolio",
            description="Portfolio for testing fee calculations",
            owner_id=test_user.id
        )
        db_session.add(portfolio)
        db_session.commit()
        db_session.refresh(portfolio)
        return portfolio

    @pytest.fixture
    def test_stock(self, db_session):
        """Create a test stock."""
        stock = Stock(
            symbol="TEST",
            company_name="Test Corporation",
            exchange="ASX",
            current_price=Decimal("100.00"),
            status=StockStatus.ACTIVE
        )
        db_session.add(stock)
        db_session.commit()
        db_session.refresh(stock)
        return stock

    def test_buy_transaction_with_no_fees_creates_correct_average_cost(self, db_session, test_portfolio, test_stock):
        """Test BUY transaction with no fees creates holding with correct average cost."""
        # Arrange
        transaction_data = TransactionCreate(
            stock_symbol=test_stock.symbol,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price_per_share=Decimal("50.00"),
            fees=Decimal("0.00"),
            transaction_date=date(2024, 1, 15),
            notes="Test transaction with no fees"
        )

        # Act
        result = process_transaction(db_session, test_portfolio.id, transaction_data)

        # Assert
        assert result.total_amount == Decimal("5000.00")  # 100 * 50.00 + 0.00

        holding = db_session.query(Holding).filter(
            Holding.portfolio_id == test_portfolio.id,
            Holding.stock_id == test_stock.id
        ).first()

        assert holding is not None
        assert holding.quantity == Decimal("100.0000")
        assert holding.average_cost == Decimal("50.0000")  # No fees, so average cost = price per share
        assert holding.current_value == Decimal("10000.0000")  # 100 * 100.00 (current price)

        # Cost basis (without fees) = 100 * 50.00 = 5000
        expected_cost_basis = Decimal("5000.00")
        expected_current_value = Decimal("10000.00")  # 100 * 100.00
        expected_gain = expected_current_value - expected_cost_basis

        assert holding.unrealized_gain_loss == expected_gain

    def test_buy_transaction_with_fees_includes_fees_in_average_cost(self, db_session, test_portfolio, test_stock):
        """Test BUY transaction with fees properly includes fees in average cost calculation."""
        # Arrange
        transaction_data = TransactionCreate(
            stock_symbol=test_stock.symbol,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price_per_share=Decimal("50.00"),
            fees=Decimal("19.95"),
            transaction_date=date(2024, 1, 15),
            notes="Test transaction with fees"
        )

        # Act
        result = process_transaction(db_session, test_portfolio.id, transaction_data)

        # Assert
        assert result.fees == Decimal("19.95")
        assert result.total_amount == Decimal("5019.95")  # 100 * 50.00 + 19.95

        holding = db_session.query(Holding).filter(
            Holding.portfolio_id == test_portfolio.id,
            Holding.stock_id == test_stock.id
        ).first()

        assert holding is not None
        assert holding.quantity == Decimal("100.0000")

        # Average cost should include fees: (100 * 50.00 + 19.95) / 100 = 50.1995
        expected_average_cost = Decimal("50.1995")
        assert holding.average_cost == expected_average_cost

        # Current value based on market price: 100 * 100.00 = 10000
        assert holding.current_value == Decimal("10000.0000")

        # Cost basis with fees = 100 * 50.1995 = 5019.95
        expected_cost_basis = Decimal("5019.95")
        expected_current_value = Decimal("10000.00")
        expected_gain = expected_current_value - expected_cost_basis  # 4980.05

        assert holding.unrealized_gain_loss == expected_gain

    def test_multiple_buy_transactions_with_fees_calculates_weighted_average_cost(self, db_session, test_portfolio, test_stock):
        """Test multiple BUY transactions with fees calculate correct weighted average cost."""
        # Arrange - First transaction
        transaction_data_1 = TransactionCreate(
            stock_symbol=test_stock.symbol,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price_per_share=Decimal("50.00"),
            fees=Decimal("19.95"),
            transaction_date=date(2024, 1, 15),
            notes="First purchase with fees"
        )

        # Act - First transaction
        result_1 = process_transaction(db_session, test_portfolio.id, transaction_data_1)

        # Arrange - Second transaction
        transaction_data_2 = TransactionCreate(
            stock_symbol=test_stock.symbol,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("50"),
            price_per_share=Decimal("60.00"),
            fees=Decimal("15.00"),
            transaction_date=date(2024, 2, 15),
            notes="Second purchase with fees"
        )

        # Act - Second transaction
        result_2 = process_transaction(db_session, test_portfolio.id, transaction_data_2)

        # Assert
        holding = db_session.query(Holding).filter(
            Holding.portfolio_id == test_portfolio.id,
            Holding.stock_id == test_stock.id
        ).first()

        assert holding is not None
        assert holding.quantity == Decimal("150.0000")  # 100 + 50

        # Calculate expected weighted average cost with fees:
        # First purchase: (100 * 50.00 + 19.95) = 5019.95
        # Second purchase: (50 * 60.00 + 15.00) = 3015.00
        # Total cost: 5019.95 + 3015.00 = 8034.95
        # Total quantity: 150
        # Weighted average: 8034.95 / 150 = 53.566
        expected_average_cost = Decimal("53.566")
        assert abs(holding.average_cost - expected_average_cost) < Decimal("0.01")

        # Current value: 150 * 100.00 = 15000
        assert holding.current_value == Decimal("15000.0000")

        # Cost basis with fees: 150 * 53.566 = 8034.90 (approximately)
        expected_cost_basis = Decimal("8034.95")  # More precise calculation
        expected_current_value = Decimal("15000.00")
        expected_gain = expected_current_value - expected_cost_basis

        assert abs(holding.unrealized_gain_loss - expected_gain) < Decimal("0.10")

    def test_sell_transaction_with_fees_reduces_holding_but_preserves_average_cost(self, db_session, test_portfolio, test_stock):
        """Test SELL transaction with fees reduces holding but preserves average cost."""
        # Arrange - Buy first
        buy_transaction = TransactionCreate(
            stock_symbol=test_stock.symbol,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price_per_share=Decimal("50.00"),
            fees=Decimal("19.95"),
            transaction_date=date(2024, 1, 15),
            notes="Initial purchase with fees"
        )

        process_transaction(db_session, test_portfolio.id, buy_transaction)

        # Get initial holding state
        holding_before = db_session.query(Holding).filter(
            Holding.portfolio_id == test_portfolio.id,
            Holding.stock_id == test_stock.id
        ).first()

        initial_average_cost = holding_before.average_cost

        # Arrange - Sell transaction
        sell_transaction = TransactionCreate(
            stock_symbol=test_stock.symbol,
            transaction_type=TransactionType.SELL,
            quantity=Decimal("30"),
            price_per_share=Decimal("55.00"),
            fees=Decimal("15.00"),
            transaction_date=date(2024, 2, 15),
            notes="Partial sale with fees"
        )

        # Act - Sell transaction
        result = process_transaction(db_session, test_portfolio.id, sell_transaction)

        # Assert
        holding_after = db_session.query(Holding).filter(
            Holding.portfolio_id == test_portfolio.id,
            Holding.stock_id == test_stock.id
        ).first()

        assert holding_after is not None
        assert holding_after.quantity == Decimal("70.0000")  # 100 - 30

        # Average cost should remain the same (fees from sales don't affect average cost)
        assert holding_after.average_cost == initial_average_cost

        # Current value: 70 * 100.00 = 7000
        assert holding_after.current_value == Decimal("7000.0000")

        # Sell transaction should record fees
        assert result.fees == Decimal("15.00")
        assert result.total_amount == Decimal("1635.00")  # 30 * 55.00 - 15.00 (seller pays fees)

    def test_fee_impact_on_portfolio_returns(self, db_session, test_portfolio, test_stock):
        """Test that fees correctly impact portfolio-level return calculations."""
        # Arrange - Create transaction with significant fees
        transaction_data = TransactionCreate(
            stock_symbol=test_stock.symbol,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price_per_share=Decimal("50.00"),
            fees=Decimal("100.00"),  # Large fee to see clear impact
            transaction_date=date(2024, 1, 15),
            notes="High fee transaction"
        )

        # Act
        process_transaction(db_session, test_portfolio.id, transaction_data)

        # Assert
        holding = db_session.query(Holding).filter(
            Holding.portfolio_id == test_portfolio.id,
            Holding.stock_id == test_stock.id
        ).first()

        # Average cost with high fees: (100 * 50.00 + 100.00) / 100 = 51.00
        assert holding.average_cost == Decimal("51.0000")

        # Cost basis: 100 * 51.00 = 5100
        expected_cost_basis = Decimal("5100.00")

        # Current value: 100 * 100.00 = 10000
        expected_current_value = Decimal("10000.00")

        # Gain with fees: 10000 - 5100 = 4900
        expected_gain_with_fees = Decimal("4900.00")

        # Gain without fees would have been: 10000 - 5000 = 5000
        expected_gain_without_fees = Decimal("5000.00")

        # Fee impact: 5000 - 4900 = 100
        fee_impact = expected_gain_without_fees - expected_gain_with_fees

        assert holding.unrealized_gain_loss == expected_gain_with_fees
        assert fee_impact == Decimal("100.00")  # Fees reduced returns by exactly the fee amount

    def test_zero_quantity_after_full_sale_removes_holding(self, db_session, test_portfolio, test_stock):
        """Test that selling entire position removes the holding."""
        # Arrange - Buy first
        buy_transaction = TransactionCreate(
            stock_symbol=test_stock.symbol,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price_per_share=Decimal("50.00"),
            fees=Decimal("19.95"),
            transaction_date=date(2024, 1, 15),
            notes="Initial purchase"
        )

        process_transaction(db_session, test_portfolio.id, buy_transaction)

        # Verify holding exists
        holding_before = db_session.query(Holding).filter(
            Holding.portfolio_id == test_portfolio.id,
            Holding.stock_id == test_stock.id
        ).first()
        assert holding_before is not None

        # Arrange - Sell everything
        sell_transaction = TransactionCreate(
            stock_symbol=test_stock.symbol,
            transaction_type=TransactionType.SELL,
            quantity=Decimal("100"),
            price_per_share=Decimal("60.00"),
            fees=Decimal("20.00"),
            transaction_date=date(2024, 2, 15),
            notes="Full sale"
        )

        # Act
        process_transaction(db_session, test_portfolio.id, sell_transaction)

        # Assert - Holding should be removed
        holding_after = db_session.query(Holding).filter(
            Holding.portfolio_id == test_portfolio.id,
            Holding.stock_id == test_stock.id
        ).first()
        assert holding_after is None

    def test_transaction_total_amount_calculation_includes_fees(self, db_session, test_portfolio, test_stock):
        """Test that transaction total_amount correctly includes fees."""
        # Arrange
        transaction_data = TransactionCreate(
            stock_symbol=test_stock.symbol,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price_per_share=Decimal("50.00"),
            fees=Decimal("25.50"),
            transaction_date=date(2024, 1, 15),
            notes="Transaction with specific fees"
        )

        # Act
        result = process_transaction(db_session, test_portfolio.id, transaction_data)

        # Assert
        expected_total = (Decimal("100") * Decimal("50.00")) + Decimal("25.50")
        assert result.total_amount == expected_total  # 5025.50
        assert result.fees == Decimal("25.50")
        assert result.price_per_share == Decimal("50.00")
        assert result.quantity == Decimal("100.0000")

    def test_fee_precision_maintained_in_calculations(self, db_session, test_portfolio, test_stock):
        """Test that fee precision is maintained throughout calculations."""
        # Arrange - Use fees with multiple decimal places
        transaction_data = TransactionCreate(
            stock_symbol=test_stock.symbol,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price_per_share=Decimal("50.123"),
            fees=Decimal("19.9567"),  # High precision fees
            transaction_date=date(2024, 1, 15),
            notes="High precision fees"
        )

        # Act
        result = process_transaction(db_session, test_portfolio.id, transaction_data)

        # Assert
        holding = db_session.query(Holding).filter(
            Holding.portfolio_id == test_portfolio.id,
            Holding.stock_id == test_stock.id
        ).first()

        # Expected total cost: 100 * 50.123 + 19.9567 = 5032.2567
        # Expected average cost: 5032.2567 / 100 = 50.322567
        expected_total_cost = Decimal("5032.2567")
        expected_average_cost = Decimal("50.322567")

        assert result.total_amount == expected_total_cost
        # Average cost should be stored with appropriate precision
        assert abs(holding.average_cost - expected_average_cost) < Decimal("0.000001")
"""
TDD Tests for Admin User BHP Transaction Failure
Tests the specific scenario where admin user attempts to buy BHP shares and encounters transaction failures.
"""

import pytest
from decimal import Decimal
from datetime import date
from uuid import uuid4

from src.models import User, Portfolio, Stock, Transaction, Holding
from src.models.transaction import TransactionType, SourceType
from src.models.stock import StockStatus
from src.schemas.transaction import TransactionCreate
from src.services.transaction_service import process_transaction
from src.core.auth import get_password_hash


class TestAdminBHPTransaction:
    """Test admin user BHP transaction scenarios."""

    @pytest.fixture
    def admin_user(self, db):
        """Create admin test user matching the one from setup."""
        admin = User(
            email="admin@example.com",
            password_hash=get_password_hash("admin123"),
            first_name="Admin",
            last_name="User",
            role="ADMIN"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin

    @pytest.fixture
    def regular_user(self, db):
        """Create regular test user matching the one from setup."""
        user = User(
            email="test@example.com",
            password_hash=get_password_hash("test123"),
            first_name="Test",
            last_name="User",
            role="USER"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @pytest.fixture
    def admin_portfolio(self, db, admin_user):
        """Create admin portfolio matching setup."""
        portfolio = Portfolio(
            name="Admin Portfolio",
            description="Admin's investment portfolio",
            owner_id=admin_user.id
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
        return portfolio

    @pytest.fixture
    def bhp_stock(self, db):
        """Create BHP stock matching ASX setup."""
        bhp = Stock(
            symbol="BHP",
            company_name="BHP Group Limited",
            exchange="ASX",
            current_price=Decimal("42.50"),
            status=StockStatus.ACTIVE
        )
        db.add(bhp)
        db.commit()
        db.refresh(bhp)
        return bhp

    def test_admin_user_has_correct_privileges(self, db, admin_user):
        """Test that admin user is properly configured with admin role."""
        # Assert
        assert admin_user.role.value == "admin"
        assert admin_user.email == "admin@example.com"
        assert admin_user.first_name == "Admin"
        assert admin_user.last_name == "User"

        # Verify admin can be authenticated
        from src.core.auth import verify_password
        assert verify_password("admin123", admin_user.password_hash)

    def test_admin_portfolio_exists_and_accessible(self, db, admin_user, admin_portfolio):
        """Test that admin user has access to their portfolio."""
        # Assert
        assert admin_portfolio.owner_id == admin_user.id
        assert admin_portfolio.name == "Admin Portfolio"
        assert admin_portfolio.is_active is True

        # Verify portfolio can be queried by admin user
        found_portfolio = db.query(Portfolio).filter(
            Portfolio.owner_id == admin_user.id,
            Portfolio.is_active.is_(True)
        ).first()

        assert found_portfolio is not None
        assert found_portfolio.id == admin_portfolio.id

    def test_bhp_stock_exists_and_active(self, db, bhp_stock):
        """Test that BHP stock is properly configured and active."""
        # Assert
        assert bhp_stock.symbol == "BHP"
        assert bhp_stock.company_name == "BHP Group Limited"
        assert bhp_stock.exchange == "ASX"
        assert bhp_stock.status == StockStatus.ACTIVE
        assert bhp_stock.current_price == Decimal("42.50")

        # Verify BHP can be found by symbol
        found_stock = db.query(Stock).filter(
            Stock.symbol == "BHP",
            Stock.status == StockStatus.ACTIVE
        ).first()

        assert found_stock is not None
        assert found_stock.id == bhp_stock.id

    def test_admin_can_buy_bhp_shares_basic_transaction(self, db, admin_portfolio, bhp_stock):
        """Test that admin user can successfully buy BHP shares with basic transaction."""
        # Arrange
        transaction_data = TransactionCreate(
            stock_symbol="BHP",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("10"),
            price_per_share=Decimal("42.50"),
            fees=Decimal("19.95"),
            transaction_date=date(2024, 1, 15),
            notes="Admin buying BHP shares"
        )

        # Act
        result = process_transaction(db, admin_portfolio.id, transaction_data)

        # Assert
        assert result is not None
        assert result.stock_symbol == "BHP"
        assert result.transaction_type == TransactionType.BUY
        assert result.quantity == Decimal("10.0000")
        assert result.price_per_share == Decimal("42.50")
        assert result.fees == Decimal("19.95")
        assert result.total_amount == Decimal("444.95")  # 10 * 42.50 + 19.95

        # Verify holding was created
        holding = db.query(Holding).filter(
            Holding.portfolio_id == admin_portfolio.id,
            Holding.stock_id == bhp_stock.id
        ).first()

        assert holding is not None
        assert holding.quantity == Decimal("10.0000")
        # Average cost should include fees: (10 * 42.50 + 19.95) / 10 = 44.495
        assert holding.average_cost == Decimal("44.495")

    def test_admin_bhp_transaction_with_fee_calculations(self, db, admin_portfolio, bhp_stock):
        """Test BHP transaction with proper fee inclusion in cost basis."""
        # Arrange
        transaction_data = TransactionCreate(
            stock_symbol="BHP",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("10"),
            price_per_share=Decimal("42.50"),
            fees=Decimal("19.95"),
            transaction_date=date(2024, 1, 15),
            notes="BHP purchase with fees"
        )

        # Act
        result = process_transaction(db, admin_portfolio.id, transaction_data)

        # Assert
        holding = db.query(Holding).filter(
            Holding.portfolio_id == admin_portfolio.id,
            Holding.stock_id == bhp_stock.id
        ).first()

        # Verify fee calculations
        expected_total_cost = Decimal("444.95")  # 10 * 42.50 + 19.95
        expected_average_cost = Decimal("44.495")  # 444.95 / 10
        expected_current_value = Decimal("425.00")  # 10 * 42.50 (market price)
        expected_unrealized_loss = expected_current_value - expected_total_cost  # -19.95

        assert result.total_amount == expected_total_cost
        assert holding.average_cost == expected_average_cost
        assert holding.current_value == expected_current_value
        assert holding.unrealized_gain_loss == expected_unrealized_loss

        # Verify fees reduced the gain by exactly the fee amount
        gain_without_fees = Decimal("0.00")  # Would be 0 if no fees
        actual_loss_due_to_fees = gain_without_fees - holding.unrealized_gain_loss
        assert actual_loss_due_to_fees == Decimal("19.95")

    def test_multiple_bhp_transactions_weighted_average_cost(self, db, admin_portfolio, bhp_stock):
        """Test multiple BHP transactions calculate correct weighted average cost."""
        # Arrange - First transaction
        first_transaction = TransactionCreate(
            stock_symbol="BHP",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("10"),
            price_per_share=Decimal("42.50"),
            fees=Decimal("19.95"),
            transaction_date=date(2024, 1, 15),
            notes="First BHP purchase"
        )

        # Act - First transaction
        process_transaction(db, admin_portfolio.id, first_transaction)

        # Arrange - Second transaction
        second_transaction = TransactionCreate(
            stock_symbol="BHP",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("5"),
            price_per_share=Decimal("43.00"),
            fees=Decimal("15.00"),
            transaction_date=date(2024, 2, 15),
            notes="Second BHP purchase"
        )

        # Act - Second transaction
        process_transaction(db, admin_portfolio.id, second_transaction)

        # Assert
        holding = db.query(Holding).filter(
            Holding.portfolio_id == admin_portfolio.id,
            Holding.stock_id == bhp_stock.id
        ).first()

        assert holding.quantity == Decimal("15.0000")  # 10 + 5

        # Calculate expected weighted average cost:
        # First: 10 * 42.50 + 19.95 = 444.95
        # Second: 5 * 43.00 + 15.00 = 230.00
        # Total cost: 444.95 + 230.00 = 674.95
        # Total quantity: 15
        # Weighted average: 674.95 / 15 = 44.996666...
        expected_average_cost = Decimal("44.996667")
        assert abs(holding.average_cost - expected_average_cost) < Decimal("0.000001")

    def test_bhp_transaction_validation_errors_handling(self, db, admin_portfolio, bhp_stock):
        """Test proper error handling for invalid BHP transaction data."""
        # Test negative quantity
        with pytest.raises(Exception):
            invalid_transaction = TransactionCreate(
                stock_symbol="BHP",
                transaction_type=TransactionType.BUY,
                quantity=Decimal("-10"),  # Invalid negative quantity
                price_per_share=Decimal("42.50"),
                fees=Decimal("19.95"),
                transaction_date=date(2024, 1, 15),
                notes="Invalid negative quantity"
            )
            process_transaction(db, admin_portfolio.id, invalid_transaction)

        # Test zero price
        with pytest.raises(Exception):
            invalid_transaction = TransactionCreate(
                stock_symbol="BHP",
                transaction_type=TransactionType.BUY,
                quantity=Decimal("10"),
                price_per_share=Decimal("0.00"),  # Invalid zero price
                fees=Decimal("19.95"),
                transaction_date=date(2024, 1, 15),
                notes="Invalid zero price"
            )
            process_transaction(db, admin_portfolio.id, invalid_transaction)

    def test_bhp_transaction_with_nonexistent_portfolio(self, db, bhp_stock):
        """Test transaction fails gracefully with nonexistent portfolio."""
        # Arrange
        fake_portfolio_id = uuid4()
        transaction_data = TransactionCreate(
            stock_symbol="BHP",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("10"),
            price_per_share=Decimal("42.50"),
            fees=Decimal("19.95"),
            transaction_date=date(2024, 1, 15),
            notes="Transaction with fake portfolio"
        )

        # Act & Assert
        with pytest.raises(Exception):
            process_transaction(db, fake_portfolio_id, transaction_data)

    def test_bhp_transaction_with_nonexistent_stock(self, db, admin_portfolio):
        """Test transaction fails gracefully with nonexistent stock symbol."""
        # Arrange
        transaction_data = TransactionCreate(
            stock_symbol="FAKE",  # Non-existent stock
            transaction_type=TransactionType.BUY,
            quantity=Decimal("10"),
            price_per_share=Decimal("42.50"),
            fees=Decimal("19.95"),
            transaction_date=date(2024, 1, 15),
            notes="Transaction with fake stock"
        )

        # Act & Assert
        with pytest.raises(Exception):
            process_transaction(db, admin_portfolio.id, transaction_data)

    def test_bhp_sell_transaction_after_buy(self, db, admin_portfolio, bhp_stock):
        """Test selling BHP shares after buying them."""
        # Arrange - Buy first
        buy_transaction = TransactionCreate(
            stock_symbol="BHP",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("20"),
            price_per_share=Decimal("42.50"),
            fees=Decimal("19.95"),
            transaction_date=date(2024, 1, 15),
            notes="Buy BHP for later sale"
        )

        process_transaction(db, admin_portfolio.id, buy_transaction)

        # Arrange - Sell transaction
        sell_transaction = TransactionCreate(
            stock_symbol="BHP",
            transaction_type=TransactionType.SELL,
            quantity=Decimal("10"),
            price_per_share=Decimal("45.00"),
            fees=Decimal("15.00"),
            transaction_date=date(2024, 2, 15),
            notes="Sell half BHP position"
        )

        # Act
        result = process_transaction(db, admin_portfolio.id, sell_transaction)

        # Assert
        assert result.total_amount == Decimal("435.00")  # 10 * 45.00 - 15.00

        holding = db.query(Holding).filter(
            Holding.portfolio_id == admin_portfolio.id,
            Holding.stock_id == bhp_stock.id
        ).first()

        assert holding.quantity == Decimal("10.0000")  # 20 - 10
        # Average cost should remain the same from original purchase
        original_avg_cost = Decimal("42.9975")  # (20 * 42.50 + 19.95) / 20
        assert holding.average_cost == original_avg_cost

    def test_bhp_transaction_precision_maintained(self, db, admin_portfolio, bhp_stock):
        """Test that high precision values are maintained in BHP transactions."""
        # Arrange
        transaction_data = TransactionCreate(
            stock_symbol="BHP",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("13.75"),  # Fractional shares
            price_per_share=Decimal("42.567"),  # High precision price
            fees=Decimal("19.9567"),  # High precision fees
            transaction_date=date(2024, 1, 15),
            notes="High precision BHP transaction"
        )

        # Act
        result = process_transaction(db, admin_portfolio.id, transaction_data)

        # Assert
        expected_total_cost = Decimal("13.75") * Decimal("42.567") + Decimal("19.9567")
        expected_total_cost = Decimal("605.23275")  # 585.29625 + 19.9567

        assert result.total_amount == expected_total_cost

        holding = db.query(Holding).filter(
            Holding.portfolio_id == admin_portfolio.id,
            Holding.stock_id == bhp_stock.id
        ).first()

        # Average cost: 605.23275 / 13.75 = 44.016927...
        expected_avg_cost = expected_total_cost / Decimal("13.75")
        assert abs(holding.average_cost - expected_avg_cost) < Decimal("0.000001")

    def test_bhp_transaction_database_rollback_on_error(self, db, admin_portfolio, bhp_stock):
        """Test that database changes are rolled back properly on transaction errors."""
        # Arrange - Get initial state
        initial_holding_count = db.query(Holding).filter(
            Holding.portfolio_id == admin_portfolio.id
        ).count()

        initial_transaction_count = db.query(Transaction).filter(
            Transaction.portfolio_id == admin_portfolio.id
        ).count()

        # Arrange - Create a transaction that should fail (invalid data after initial validation)
        transaction_data = TransactionCreate(
            stock_symbol="BHP",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("10"),
            price_per_share=Decimal("42.50"),
            fees=Decimal("19.95"),
            transaction_date=date(2024, 1, 15),
            notes="Transaction that may fail during processing"
        )

        try:
            # Simulate a failure scenario by temporarily modifying the stock to be inactive
            bhp_stock.status = StockStatus.DELISTED
            db.commit()

            # Act - This should fail
            with pytest.raises(Exception):
                process_transaction(db, admin_portfolio.id, transaction_data)

        finally:
            # Restore stock status
            bhp_stock.status = StockStatus.ACTIVE
            db.commit()

        # Assert - Database should be in original state
        final_holding_count = db.query(Holding).filter(
            Holding.portfolio_id == admin_portfolio.id
        ).count()

        final_transaction_count = db.query(Transaction).filter(
            Transaction.portfolio_id == admin_portfolio.id
        ).count()

        assert final_holding_count == initial_holding_count
        assert final_transaction_count == initial_transaction_count
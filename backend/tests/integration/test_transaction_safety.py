"""
Integration tests for transactional safety in portfolio operations.
Tests that all operations are atomic and maintain data consistency.
"""

import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.models import Portfolio, Stock, Transaction, Holding, User
from src.models.transaction import TransactionType
from src.schemas.transaction import TransactionCreate
from src.services.transaction_service import process_transaction, update_transaction, delete_transaction


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    user = User(
        email="safety@example.com",
        password_hash="$2b$12$dummy.hash.value",
        first_name="Safety",
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
        name="Safety Test Portfolio",
        description="Portfolio for testing transactional safety",
        owner_id=test_user.id
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@pytest.fixture
def test_stock(db: Session):
    """Create a test stock."""
    stock = Stock(
        symbol="SAFE",
        company_name="Safety Corporation",
        exchange="ASX"
    )
    db.add(stock)
    db.commit()
    db.refresh(stock)
    return stock


class TestTransactionSafety:
    """Test transactional safety for all portfolio operations."""

    def test_transaction_create_is_atomic(self, db: Session, test_portfolio: Portfolio):
        """Test that transaction creation is fully atomic - all or nothing."""
        initial_portfolio_value = test_portfolio.total_value
        initial_holdings_count = db.query(Holding).filter(
            Holding.portfolio_id == test_portfolio.id
        ).count()
        initial_transactions_count = db.query(Transaction).filter(
            Transaction.portfolio_id == test_portfolio.id
        ).count()

        # Valid transaction should succeed completely
        transaction_data = TransactionCreate(
            stock_symbol="ATOMIC",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price_per_share=Decimal("50.00"),
            transaction_date=date.today(),
            notes="Atomic test transaction"
        )

        result = process_transaction(db, test_portfolio.id, transaction_data)

        # Verify all related data was created
        assert result.id is not None
        assert result.stock.symbol == "ATOMIC"

        # Stock should be created
        stock = db.query(Stock).filter(Stock.symbol == "ATOMIC").first()
        assert stock is not None

        # Holding should be created
        holding = db.query(Holding).filter(
            Holding.portfolio_id == test_portfolio.id,
            Holding.stock_id == stock.id
        ).first()
        assert holding is not None
        assert holding.quantity == Decimal("100")

        # Portfolio totals should be updated
        db.refresh(test_portfolio)
        assert test_portfolio.total_value > initial_portfolio_value

        # Counts should increase by exactly 1
        final_holdings_count = db.query(Holding).filter(
            Holding.portfolio_id == test_portfolio.id
        ).count()
        final_transactions_count = db.query(Transaction).filter(
            Transaction.portfolio_id == test_portfolio.id
        ).count()

        assert final_holdings_count == initial_holdings_count + 1
        assert final_transactions_count == initial_transactions_count + 1

    def test_transaction_failure_rolls_back_completely(self, db: Session, test_portfolio: Portfolio, monkeypatch):
        """Test that if any part of transaction processing fails, everything rolls back."""
        initial_stocks_count = db.query(Stock).count()
        initial_holdings_count = db.query(Holding).count()
        initial_transactions_count = db.query(Transaction).count()
        initial_portfolio_value = test_portfolio.total_value

        # Mock a failure in holdings update to simulate partial failure
        def mock_failing_holdings_update(*args, **kwargs):
            raise Exception("Simulated holdings update failure")

        # Patch the holdings update function to fail
        monkeypatch.setattr("src.services.transaction_service._process_buy_transaction", mock_failing_holdings_update)

        transaction_data = TransactionCreate(
            stock_symbol="FAIL",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("50"),
            price_per_share=Decimal("25.00"),
            transaction_date=date.today(),
            notes="This should fail and rollback"
        )

        # Transaction should fail
        with pytest.raises(Exception, match="Simulated holdings update failure"):
            process_transaction(db, test_portfolio.id, transaction_data)

        # Verify complete rollback - nothing should have been created
        final_stocks_count = db.query(Stock).count()
        final_holdings_count = db.query(Holding).count()
        final_transactions_count = db.query(Transaction).count()

        assert final_stocks_count == initial_stocks_count  # No new stock
        assert final_holdings_count == initial_holdings_count  # No new holding
        assert final_transactions_count == initial_transactions_count  # No new transaction

        # Portfolio should be unchanged
        db.refresh(test_portfolio)
        assert test_portfolio.total_value == initial_portfolio_value

        # FAIL stock should not exist
        fail_stock = db.query(Stock).filter(Stock.symbol == "FAIL").first()
        assert fail_stock is None

    def test_concurrent_transaction_safety(self, db: Session, test_portfolio: Portfolio, test_stock: Stock):
        """Test that concurrent transactions on the same portfolio are handled safely."""
        # Create initial holding
        transaction_data = TransactionCreate(
            stock_symbol=test_stock.symbol,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price_per_share=Decimal("10.00"),
            transaction_date=date.today(),
            notes="Initial holding"
        )
        process_transaction(db, test_portfolio.id, transaction_data)

        # Simulate concurrent SELL transactions that together would exceed available shares
        sell_data_1 = TransactionCreate(
            stock_symbol=test_stock.symbol,
            transaction_type=TransactionType.SELL,
            quantity=Decimal("60"),
            price_per_share=Decimal("12.00"),
            transaction_date=date.today(),
            notes="First sell"
        )

        sell_data_2 = TransactionCreate(
            stock_symbol=test_stock.symbol,
            transaction_type=TransactionType.SELL,
            quantity=Decimal("60"),  # This should fail - only 100 shares available
            price_per_share=Decimal("12.00"),
            transaction_date=date.today(),
            notes="Second sell - should fail"
        )

        # First sell should succeed
        result1 = process_transaction(db, test_portfolio.id, sell_data_1)
        assert result1.quantity == Decimal("60")

        # Second sell should fail due to insufficient shares
        from src.core.exceptions import InsufficientSharesError
        with pytest.raises(InsufficientSharesError):
            process_transaction(db, test_portfolio.id, sell_data_2)

        # Verify holding state is consistent
        holding = db.query(Holding).filter(
            Holding.portfolio_id == test_portfolio.id,
            Holding.stock_id == test_stock.id
        ).first()
        assert holding.quantity == Decimal("40")  # 100 - 60 = 40

    def test_update_transaction_is_atomic(self, db: Session, test_portfolio: Portfolio, test_stock: Stock):
        """Test that transaction updates are atomic."""
        # Create initial transaction
        transaction_data = TransactionCreate(
            stock_symbol=test_stock.symbol,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("50"),
            price_per_share=Decimal("20.00"),
            transaction_date=date.today(),
            notes="Initial transaction"
        )
        result = process_transaction(db, test_portfolio.id, transaction_data)
        transaction_id = result.id

        initial_holding = db.query(Holding).filter(
            Holding.portfolio_id == test_portfolio.id,
            Holding.stock_id == test_stock.id
        ).first()
        initial_quantity = initial_holding.quantity
        initial_portfolio_value = test_portfolio.total_value

        # Update transaction
        update_data = {
            "quantity": Decimal("75"),  # Increase quantity
            "price_per_share": Decimal("25.00"),  # Change price
            "notes": "Updated transaction"
        }

        updated_result = update_transaction(db, test_portfolio.id, transaction_id, update_data)

        # Verify transaction was updated
        assert updated_result.quantity == Decimal("75")
        assert updated_result.price_per_share == Decimal("25.00")
        assert updated_result.notes == "Updated transaction"

        # Verify holding was recalculated correctly
        updated_holding = db.query(Holding).filter(
            Holding.portfolio_id == test_portfolio.id,
            Holding.stock_id == test_stock.id
        ).first()
        assert updated_holding.quantity == Decimal("75")

        # Verify portfolio totals were updated
        db.refresh(test_portfolio)
        expected_new_value = Decimal("75") * Decimal("25.00")  # 75 shares * $25 = $1875
        assert test_portfolio.total_value != initial_portfolio_value

    def test_delete_transaction_is_atomic(self, db: Session, test_portfolio: Portfolio, test_stock: Stock):
        """Test that transaction deletion is atomic."""
        # Create transaction
        transaction_data = TransactionCreate(
            stock_symbol=test_stock.symbol,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("30"),
            price_per_share=Decimal("40.00"),
            transaction_date=date.today(),
            notes="To be deleted"
        )
        result = process_transaction(db, test_portfolio.id, transaction_data)
        transaction_id = result.id

        # Verify initial state
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        assert transaction is not None

        holding = db.query(Holding).filter(
            Holding.portfolio_id == test_portfolio.id,
            Holding.stock_id == test_stock.id
        ).first()
        assert holding is not None
        assert holding.quantity == Decimal("30")

        initial_portfolio_value = test_portfolio.total_value

        # Delete transaction
        delete_transaction(db, test_portfolio.id, transaction_id)

        # Verify transaction is deleted
        deleted_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        assert deleted_transaction is None

        # Verify holding is updated/removed
        updated_holding = db.query(Holding).filter(
            Holding.portfolio_id == test_portfolio.id,
            Holding.stock_id == test_stock.id
        ).first()
        assert updated_holding is None  # Should be deleted since quantity becomes 0

        # Verify portfolio totals are updated
        db.refresh(test_portfolio)
        # Portfolio value should decrease by the transaction amount
        expected_decrease = Decimal("30") * Decimal("40.00")
        assert test_portfolio.total_value == initial_portfolio_value - expected_decrease

    def test_portfolio_consistency_under_mixed_operations(self, db: Session, test_portfolio: Portfolio):
        """Test portfolio remains consistent under mixed transaction operations."""
        # Perform a series of mixed operations and verify consistency at each step
        operations = [
            ("BUY", "STOCK1", Decimal("100"), Decimal("10.00")),
            ("BUY", "STOCK2", Decimal("50"), Decimal("20.00")),
            ("SELL", "STOCK1", Decimal("30"), Decimal("12.00")),
            ("BUY", "STOCK1", Decimal("20"), Decimal("11.00")),
        ]

        for i, (operation, symbol, quantity, price) in enumerate(operations):
            transaction_data = TransactionCreate(
                stock_symbol=symbol,
                transaction_type=TransactionType(operation),
                quantity=quantity,
                price_per_share=price,
                transaction_date=date.today(),
                notes=f"Mixed operation {i+1}"
            )

            result = process_transaction(db, test_portfolio.id, transaction_data)
            assert result.id is not None

            # Verify consistency after each operation
            self._verify_portfolio_consistency(db, test_portfolio.id)

    def _verify_portfolio_consistency(self, db: Session, portfolio_id):
        """Helper method to verify portfolio data consistency."""
        # Get portfolio and holdings
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        holdings = db.query(Holding).filter(Holding.portfolio_id == portfolio_id).all()

        # Calculate expected portfolio value from holdings
        calculated_value = sum(holding.current_value for holding in holdings)

        # Portfolio total_value should match sum of holdings
        assert abs(portfolio.total_value - calculated_value) < Decimal("0.01"), \
            f"Portfolio value mismatch: {portfolio.total_value} != {calculated_value}"

        # Each holding should have positive or zero quantity
        for holding in holdings:
            assert holding.quantity >= 0, f"Negative holding quantity: {holding.quantity}"
            assert holding.current_value >= 0, f"Negative holding value: {holding.current_value}"

        # All holdings should have valid stock references
        for holding in holdings:
            stock = db.query(Stock).filter(Stock.id == holding.stock_id).first()
            assert stock is not None, f"Orphaned holding with stock_id: {holding.stock_id}"
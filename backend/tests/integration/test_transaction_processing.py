"""
Integration tests for transaction processing that includes holdings updates.
Tests the complete flow of transaction creation and portfolio position updates.
"""

import pytest
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.orm import Session

from src.models import Portfolio, Stock, Transaction, Holding
from src.models.transaction import TransactionType
from src.schemas.transaction import TransactionCreate


@pytest.mark.integration
class TestTransactionProcessing:
    """Test transaction processing with holdings updates."""

    def test_buy_transaction_creates_new_holding(self, db: Session):
        """
        When a BUY transaction is created for a stock not yet held,
        it should create a new holding with correct quantity and average cost.
        """
        # Arrange: Create portfolio and stock
        portfolio = Portfolio(name="Test Portfolio", owner_id=uuid4())
        stock = Stock(symbol="AAPL", company_name="Apple Inc.", exchange="NASDAQ")
        db.add_all([portfolio, stock])
        db.flush()
        
        # Verify no holdings exist initially
        initial_holdings = db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.stock_id == stock.id
        ).first()
        assert initial_holdings is None
        
        # Act: Create transaction
        transaction_data = TransactionCreate(
            stock_symbol="AAPL",
            transaction_type=TransactionType.BUY,
            quantity=100,
            price_per_share=Decimal("150.00"),
            transaction_date="2025-09-13",
            fees=Decimal("5.00")
        )
        
        # This should be the function we implement
        from src.services.transaction_service import process_transaction
        result = process_transaction(db, portfolio.id, transaction_data)
        
        # Assert: Transaction created
        assert result.transaction_type == TransactionType.BUY
        assert result.quantity == Decimal("100.0000")
        assert result.price_per_share == Decimal("150.0000")
        
        # Assert: Holding created with correct values
        holding = db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.stock_id == stock.id
        ).first()
        
        assert holding is not None
        assert holding.quantity == Decimal("100.0000")
        assert holding.average_cost == Decimal("150.0000")
        # Current value calculation: quantity * current_price (use purchase price as current for now)
        assert holding.current_value == Decimal("15000.00")
        assert holding.unrealized_gain_loss == Decimal("0.00")
        assert holding.unrealized_gain_loss_percent == Decimal("0.00")

    def test_additional_buy_transaction_updates_existing_holding(self, db: Session):
        """
        When a BUY transaction is created for a stock already held,
        it should update the existing holding with new average cost and quantity.
        """
        # Arrange: Create portfolio, stock, and existing holding
        portfolio = Portfolio(name="Test Portfolio", owner_id=uuid4())
        stock = Stock(symbol="AAPL", company_name="Apple Inc.", exchange="NASDAQ")
        existing_holding = Holding(
            portfolio_id=portfolio.id,
            stock_id=stock.id,
            quantity=Decimal("50.0000"),
            average_cost=Decimal("140.0000"),
            current_value=Decimal("7000.00")
        )
        db.add_all([portfolio, stock, existing_holding])
        db.flush()
        
        # Act: Create additional BUY transaction
        transaction_data = TransactionCreate(
            stock_symbol="AAPL",
            transaction_type=TransactionType.BUY,
            quantity=50,
            price_per_share=Decimal("160.00"),
            transaction_date="2025-09-13",
            fees=Decimal("5.00")
        )
        
        from src.services.transaction_service import process_transaction
        result = process_transaction(db, portfolio.id, transaction_data)
        
        # Assert: Transaction created
        assert result.transaction_type == TransactionType.BUY
        
        # Assert: Existing holding updated
        updated_holding = db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.stock_id == stock.id
        ).first()
        
        assert updated_holding is not None
        # Total quantity: 50 + 50 = 100
        assert updated_holding.quantity == Decimal("100.0000")
        # Average cost: (50 * 140 + 50 * 160) / 100 = (7000 + 8000) / 100 = 150
        assert updated_holding.average_cost == Decimal("150.0000")
        # Current value: 100 * 160 = 16000 (using latest price as current)
        assert updated_holding.current_value == Decimal("16000.00")

    def test_sell_transaction_reduces_holding_quantity(self, db: Session):
        """
        When a SELL transaction is created for a held stock,
        it should reduce the holding quantity and update values accordingly.
        """
        # Arrange: Create portfolio, stock, and existing holding
        portfolio = Portfolio(name="Test Portfolio", owner_id=uuid4())
        stock = Stock(symbol="AAPL", company_name="Apple Inc.", exchange="NASDAQ")
        existing_holding = Holding(
            portfolio_id=portfolio.id,
            stock_id=stock.id,
            quantity=Decimal("100.0000"),
            average_cost=Decimal("150.0000"),
            current_value=Decimal("15000.00")
        )
        db.add_all([portfolio, stock, existing_holding])
        db.flush()
        
        # Act: Create SELL transaction
        transaction_data = TransactionCreate(
            stock_symbol="AAPL",
            transaction_type=TransactionType.SELL,
            quantity=30,
            price_per_share=Decimal("170.00"),
            transaction_date="2025-09-13",
            fees=Decimal("5.00")
        )
        
        from src.services.transaction_service import process_transaction
        result = process_transaction(db, portfolio.id, transaction_data)
        
        # Assert: Transaction created
        assert result.transaction_type == TransactionType.SELL
        
        # Assert: Holding quantity reduced
        updated_holding = db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.stock_id == stock.id
        ).first()
        
        assert updated_holding is not None
        # Remaining quantity: 100 - 30 = 70
        assert updated_holding.quantity == Decimal("70.0000")
        # Average cost remains the same: 150.00
        assert updated_holding.average_cost == Decimal("150.0000")
        # Current value: 70 * 170 = 11900
        assert updated_holding.current_value == Decimal("11900.00")

    def test_sell_all_shares_removes_holding(self, db: Session):
        """
        When a SELL transaction sells all remaining shares,
        the holding should be removed from the portfolio.
        """
        # Arrange: Create portfolio, stock, and existing holding
        portfolio = Portfolio(name="Test Portfolio", owner_id=uuid4())
        stock = Stock(symbol="AAPL", company_name="Apple Inc.", exchange="NASDAQ")
        existing_holding = Holding(
            portfolio_id=portfolio.id,
            stock_id=stock.id,
            quantity=Decimal("50.0000"),
            average_cost=Decimal("150.0000"),
            current_value=Decimal("7500.00")
        )
        db.add_all([portfolio, stock, existing_holding])
        db.flush()
        
        # Act: Sell all shares
        transaction_data = TransactionCreate(
            stock_symbol="AAPL",
            transaction_type=TransactionType.SELL,
            quantity=50,
            price_per_share=Decimal("170.00"),
            transaction_date="2025-09-13",
            fees=Decimal("5.00")
        )
        
        from src.services.transaction_service import process_transaction
        result = process_transaction(db, portfolio.id, transaction_data)
        
        # Assert: Transaction created
        assert result.transaction_type == TransactionType.SELL
        
        # Assert: Holding removed
        remaining_holding = db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.stock_id == stock.id
        ).first()
        
        assert remaining_holding is None

    def test_transaction_processing_is_atomic(self, db: Session):
        """
        If holdings update fails, the entire transaction should be rolled back.
        This ensures data consistency.
        """
        # This test will be implemented once we have the service that can fail
        # For now, we'll leave this as a placeholder for the atomic requirement
        pass

    def test_sell_more_than_held_raises_error(self, db: Session):
        """
        Attempting to sell more shares than held should raise an error
        and not create any transaction or modify holdings.
        """
        # Arrange: Create portfolio, stock, and existing holding
        portfolio = Portfolio(name="Test Portfolio", owner_id=uuid4())
        stock = Stock(symbol="AAPL", company_name="Apple Inc.", exchange="NASDAQ")
        existing_holding = Holding(
            portfolio_id=portfolio.id,
            stock_id=stock.id,
            quantity=Decimal("50.0000"),
            average_cost=Decimal("150.0000"),
            current_value=Decimal("7500.00")
        )
        db.add_all([portfolio, stock, existing_holding])
        db.flush()
        
        initial_transaction_count = db.query(Transaction).count()
        
        # Act & Assert: Attempt to sell more than held
        transaction_data = TransactionCreate(
            stock_symbol="AAPL",
            transaction_type=TransactionType.SELL,
            quantity=100,  # More than the 50 held
            price_per_share=Decimal("170.00"),
            transaction_date="2025-09-13",
            fees=Decimal("5.00")
        )
        
        from src.services.transaction_service import process_transaction
        from src.core.exceptions import InsufficientSharesError
        
        with pytest.raises(InsufficientSharesError):
            process_transaction(db, portfolio.id, transaction_data)
        
        # Assert: No transaction created
        final_transaction_count = db.query(Transaction).count()
        assert final_transaction_count == initial_transaction_count
        
        # Assert: Holding unchanged
        unchanged_holding = db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.stock_id == stock.id
        ).first()
        
        assert unchanged_holding is not None
        assert unchanged_holding.quantity == Decimal("50.0000")
        assert unchanged_holding.average_cost == Decimal("150.0000")
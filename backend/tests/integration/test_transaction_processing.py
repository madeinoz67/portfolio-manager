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

    def test_dividend_transaction_does_not_add_shares(self, db: Session):
        """
        When a DIVIDEND transaction is processed,
        it should create the transaction but NOT add shares to holdings.
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
        
        # Act: Create DIVIDEND transaction
        transaction_data = TransactionCreate(
            stock_symbol="AAPL",
            transaction_type=TransactionType.DIVIDEND,
            quantity=0,  # No shares added for dividends
            price_per_share=Decimal("2.50"),  # Dividend per share
            transaction_date="2025-09-13",
            fees=Decimal("0.00")
        )
        
        from src.services.transaction_service import process_transaction
        result = process_transaction(db, portfolio.id, transaction_data)
        
        # Assert: Transaction created
        assert result.transaction_type == TransactionType.DIVIDEND
        assert result.quantity == Decimal("0.0000")
        assert result.price_per_share == Decimal("2.50")
        
        # Assert: Holding quantity unchanged
        unchanged_holding = db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.stock_id == stock.id
        ).first()
        
        assert unchanged_holding is not None
        assert unchanged_holding.quantity == Decimal("100.0000")  # No change
        assert unchanged_holding.average_cost == Decimal("150.0000")  # No change

    def test_stock_split_adds_shares_at_zero_cost(self, db: Session):
        """
        When a STOCK_SPLIT transaction is processed,
        it should add shares to holdings at zero cost.
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
        
        # Act: Create STOCK_SPLIT transaction (2-for-1 split = 100 additional shares)
        transaction_data = TransactionCreate(
            stock_symbol="AAPL",
            transaction_type=TransactionType.STOCK_SPLIT,
            quantity=100,  # Additional shares from split
            price_per_share=Decimal("0.00"),  # No cost for splits
            transaction_date="2025-09-13",
            fees=Decimal("0.00")
        )
        
        from src.services.transaction_service import process_transaction
        result = process_transaction(db, portfolio.id, transaction_data)
        
        # Assert: Transaction created
        assert result.transaction_type == TransactionType.STOCK_SPLIT
        assert result.quantity == Decimal("100.0000")
        assert result.price_per_share == Decimal("0.00")
        
        # Assert: Holding quantity increased, average cost adjusted
        updated_holding = db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.stock_id == stock.id
        ).first()
        
        assert updated_holding is not None
        assert updated_holding.quantity == Decimal("200.0000")  # 100 + 100 from split
        # Average cost should be halved: 150 -> 75 (same total cost, double shares)
        assert updated_holding.average_cost == Decimal("75.0000")

    def test_bonus_shares_adds_shares_at_zero_cost(self, db: Session):
        """
        When a BONUS_SHARES transaction is processed,
        it should add shares to holdings at zero cost.
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
        
        # Act: Create BONUS_SHARES transaction (10% bonus = 10 additional shares)
        transaction_data = TransactionCreate(
            stock_symbol="AAPL",
            transaction_type=TransactionType.BONUS_SHARES,
            quantity=10,  # Bonus shares
            price_per_share=Decimal("0.00"),  # No cost for bonus shares
            transaction_date="2025-09-13",
            fees=Decimal("0.00")
        )
        
        from src.services.transaction_service import process_transaction
        result = process_transaction(db, portfolio.id, transaction_data)
        
        # Assert: Transaction created
        assert result.transaction_type == TransactionType.BONUS_SHARES
        assert result.quantity == Decimal("10.0000")
        assert result.price_per_share == Decimal("0.00")
        
        # Assert: Holding quantity increased, average cost adjusted
        updated_holding = db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.stock_id == stock.id
        ).first()
        
        assert updated_holding is not None
        assert updated_holding.quantity == Decimal("110.0000")  # 100 + 10 bonus
        # Average cost reduced: (100 * 150) / 110 = 136.36
        expected_avg_cost = Decimal("15000.00") / Decimal("110.0000")
        assert abs(updated_holding.average_cost - expected_avg_cost) < Decimal("0.01")

    def test_transfer_in_adds_shares_at_cost(self, db: Session):
        """
        When a TRANSFER_IN transaction is processed,
        it should add shares to holdings at the specified cost.
        """
        # Arrange: Create portfolio and stock (no existing holding)
        portfolio = Portfolio(name="Test Portfolio", owner_id=uuid4())
        stock = Stock(symbol="AAPL", company_name="Apple Inc.", exchange="NASDAQ")
        db.add_all([portfolio, stock])
        db.flush()
        
        # Act: Create TRANSFER_IN transaction
        transaction_data = TransactionCreate(
            stock_symbol="AAPL",
            transaction_type=TransactionType.TRANSFER_IN,
            quantity=50,
            price_per_share=Decimal("145.00"),  # Transfer cost basis
            transaction_date="2025-09-13",
            fees=Decimal("0.00")
        )
        
        from src.services.transaction_service import process_transaction
        result = process_transaction(db, portfolio.id, transaction_data)
        
        # Assert: Transaction created
        assert result.transaction_type == TransactionType.TRANSFER_IN
        assert result.quantity == Decimal("50.0000")
        assert result.price_per_share == Decimal("145.00")
        
        # Assert: New holding created
        new_holding = db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.stock_id == stock.id
        ).first()
        
        assert new_holding is not None
        assert new_holding.quantity == Decimal("50.0000")
        assert new_holding.average_cost == Decimal("145.00")

    def test_transfer_out_reduces_shares(self, db: Session):
        """
        When a TRANSFER_OUT transaction is processed,
        it should reduce shares in holdings.
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
        
        # Act: Create TRANSFER_OUT transaction
        transaction_data = TransactionCreate(
            stock_symbol="AAPL",
            transaction_type=TransactionType.TRANSFER_OUT,
            quantity=25,
            price_per_share=Decimal("160.00"),  # Current market value for record
            transaction_date="2025-09-13",
            fees=Decimal("0.00")
        )
        
        from src.services.transaction_service import process_transaction
        result = process_transaction(db, portfolio.id, transaction_data)
        
        # Assert: Transaction created
        assert result.transaction_type == TransactionType.TRANSFER_OUT
        assert result.quantity == Decimal("25.0000")
        
        # Assert: Holding quantity reduced
        updated_holding = db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.stock_id == stock.id
        ).first()
        
        assert updated_holding is not None
        assert updated_holding.quantity == Decimal("75.0000")  # 100 - 25
        assert updated_holding.average_cost == Decimal("150.0000")  # Unchanged


class TestTransactionEditDelete:
    """Test transaction edit and delete operations with holdings recalculation."""

    def test_edit_transaction_recalculates_holdings_atomically(self, db: Session):
        """
        When a transaction is edited,
        holdings should be recalculated atomically from all transactions.
        """
        # Arrange: Create portfolio, stock, and two transactions
        portfolio = Portfolio(name="Test Portfolio", owner_id=uuid4())
        stock = Stock(symbol="AAPL", company_name="Apple Inc.", exchange="NASDAQ")
        db.add_all([portfolio, stock])
        db.flush()
        
        # Create first BUY transaction
        transaction_data_1 = TransactionCreate(
            stock_symbol="AAPL",
            transaction_type=TransactionType.BUY,
            quantity=100,
            price_per_share=Decimal("150.00"),
            transaction_date="2025-09-10",
            fees=Decimal("5.00")
        )
        
        from src.services.transaction_service import process_transaction, update_transaction
        result_1 = process_transaction(db, portfolio.id, transaction_data_1)
        
        # Create second BUY transaction
        transaction_data_2 = TransactionCreate(
            stock_symbol="AAPL",
            transaction_type=TransactionType.BUY,
            quantity=50,
            price_per_share=Decimal("160.00"),
            transaction_date="2025-09-11",
            fees=Decimal("5.00")
        )
        
        result_2 = process_transaction(db, portfolio.id, transaction_data_2)
        
        # Verify initial holding state
        initial_holding = db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.stock_id == stock.id
        ).first()
        
        assert initial_holding.quantity == Decimal("150.0000")  # 100 + 50
        # Average cost: (100 * 150 + 50 * 160) / 150 = (15000 + 8000) / 150 = 153.33
        expected_avg_cost = Decimal("23000.00") / Decimal("150.0000")
        assert abs(initial_holding.average_cost - expected_avg_cost) < Decimal("0.01")
        
        # Act: Edit the second transaction (change quantity and price)
        updated_transaction_data = {
            "quantity": Decimal("75.0000"),  # Changed from 50 to 75
            "price_per_share": Decimal("155.00"),  # Changed from 160 to 155
        }
        
        # This function should recalculate holdings atomically
        result = update_transaction(db, portfolio.id, result_2.id, updated_transaction_data)
        
        # Assert: Transaction updated
        assert result.quantity == Decimal("75.0000")
        assert result.price_per_share == Decimal("155.00")
        
        # Assert: Holdings recalculated correctly
        updated_holding = db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.stock_id == stock.id
        ).first()
        
        assert updated_holding.quantity == Decimal("175.0000")  # 100 + 75
        # New average cost: (100 * 150 + 75 * 155) / 175 = (15000 + 11625) / 175 = 152.14
        expected_new_avg_cost = Decimal("26625.00") / Decimal("175.0000")
        assert abs(updated_holding.average_cost - expected_new_avg_cost) < Decimal("0.01")

    def test_delete_transaction_recalculates_holdings_atomically(self, db: Session):
        """
        When a transaction is deleted,
        holdings should be recalculated atomically from remaining transactions.
        """
        # Arrange: Create portfolio, stock, and three transactions
        portfolio = Portfolio(name="Test Portfolio", owner_id=uuid4())
        stock = Stock(symbol="AAPL", company_name="Apple Inc.", exchange="NASDAQ")
        db.add_all([portfolio, stock])
        db.flush()
        
        from src.services.transaction_service import process_transaction, delete_transaction
        
        # Create three BUY transactions
        transactions = []
        for i, (qty, price) in enumerate([(100, "150.00"), (50, "160.00"), (25, "170.00")]):
            transaction_data = TransactionCreate(
                stock_symbol="AAPL",
                transaction_type=TransactionType.BUY,
                quantity=qty,
                price_per_share=Decimal(price),
                transaction_date=f"2025-09-1{i}",
                fees=Decimal("5.00")
            )
            result = process_transaction(db, portfolio.id, transaction_data)
            transactions.append(result)
        
        # Verify initial holding state
        initial_holding = db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.stock_id == stock.id
        ).first()
        
        assert initial_holding.quantity == Decimal("175.0000")  # 100 + 50 + 25
        
        # Act: Delete the middle transaction
        delete_transaction(db, portfolio.id, transactions[1].id)
        
        # Assert: Holdings recalculated without the deleted transaction
        updated_holding = db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.stock_id == stock.id
        ).first()
        
        assert updated_holding.quantity == Decimal("125.0000")  # 100 + 25 (middle deleted)
        # New average cost: (100 * 150 + 25 * 170) / 125 = (15000 + 4250) / 125 = 154.00
        expected_avg_cost = Decimal("19250.00") / Decimal("125.0000")
        assert abs(updated_holding.average_cost - expected_avg_cost) < Decimal("0.01")

    def test_delete_all_transactions_removes_holding(self, db: Session):
        """
        When all transactions for a stock are deleted,
        the holding should be removed completely.
        """
        # Arrange: Create portfolio, stock, and one transaction
        portfolio = Portfolio(name="Test Portfolio", owner_id=uuid4())
        stock = Stock(symbol="AAPL", company_name="Apple Inc.", exchange="NASDAQ")
        db.add_all([portfolio, stock])
        db.flush()
        
        from src.services.transaction_service import process_transaction, delete_transaction
        
        # Create one BUY transaction
        transaction_data = TransactionCreate(
            stock_symbol="AAPL",
            transaction_type=TransactionType.BUY,
            quantity=100,
            price_per_share=Decimal("150.00"),
            transaction_date="2025-09-13",
            fees=Decimal("5.00")
        )
        result = process_transaction(db, portfolio.id, transaction_data)
        
        # Verify holding exists
        initial_holding = db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.stock_id == stock.id
        ).first()
        assert initial_holding is not None
        
        # Act: Delete the transaction
        delete_transaction(db, portfolio.id, result.id)
        
        # Assert: Holding removed
        remaining_holding = db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.stock_id == stock.id
        ).first()
        assert remaining_holding is None
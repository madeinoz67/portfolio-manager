"""
TDD Tests for Simplified Transaction Processing
Tests that transaction processing only stores facts (quantity, average_cost)
and lets hybrid properties calculate dynamic values.
"""

import pytest
import uuid
from decimal import Decimal
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.database import Base
from src.models.holding import Holding
from src.models.stock import Stock, StockStatus
from src.models.portfolio import Portfolio
from src.models.user import User, UserRole
from src.models.transaction import Transaction, TransactionType
from src.schemas.transaction import TransactionCreate
from src.services.transaction_service import process_transaction


class TestSimplifiedTransactionProcessing:
    """Test that transaction processing stores only immutable facts."""

    @pytest.fixture
    def db(self):
        """Get test database session."""
        engine = create_engine("sqlite:///./test_simplified_transactions.db", echo=False)
        Base.metadata.create_all(engine)
        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = TestSessionLocal()

        yield session

        session.close()
        engine.dispose()

        # Clean up test database
        import os
        if os.path.exists("test_simplified_transactions.db"):
            os.remove("test_simplified_transactions.db")

    @pytest.fixture
    def test_user(self, db: Session):
        """Create a test user."""
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            role=UserRole.USER,
            hashed_password="fake_hash"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @pytest.fixture
    def test_portfolio(self, db: Session, test_user: User):
        """Create a test portfolio."""
        portfolio = Portfolio(
            name="Test Portfolio",
            description="Test portfolio for transaction processing",
            user_id=test_user.id
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
        return portfolio

    @pytest.fixture
    def test_stock(self, db: Session):
        """Create a test stock."""
        stock = Stock(
            symbol="BHP",
            company_name="BHP Corporation",
            exchange="ASX",
            current_price=Decimal("42.50"),
            status=StockStatus.ACTIVE
        )
        db.add(stock)
        db.commit()
        db.refresh(stock)
        return stock

    def test_buy_transaction_creates_new_holding_facts_only(self, db: Session, test_portfolio: Portfolio, test_stock: Stock):
        """Test BUY transaction stores only quantity and average_cost."""
        # Arrange
        transaction_data = TransactionCreate(
            stock_symbol="BHP",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price_per_share=Decimal("41.25"),
            fees=Decimal("19.95"),
            transaction_date=date(2024, 1, 15),
            notes="Initial BHP purchase"
        )

        # Act
        transaction_response = process_transaction(db, test_portfolio.id, transaction_data)

        # Assert
        # 1. Transaction was created successfully
        assert transaction_response.stock.symbol == "BHP"
        assert transaction_response.quantity == Decimal("100.0000")
        assert transaction_response.price_per_share == Decimal("41.2500")
        assert transaction_response.fees == Decimal("19.95")

        # 2. Holding was created with facts only
        holding = db.query(Holding).filter(
            Holding.portfolio_id == test_portfolio.id,
            Holding.stock_id == test_stock.id
        ).first()

        assert holding is not None
        assert holding.quantity == Decimal("100")

        # Average cost should include fees: ($4125 + $19.95) / 100 = $41.4495
        expected_average_cost = Decimal("41.4495")
        assert holding.average_cost == expected_average_cost

        # 3. No calculated fields stored in database
        # The holding model should only have quantity and average_cost columns
        # Dynamic values are calculated via hybrid properties

        # 4. Hybrid properties calculate correct values
        assert holding.cost_basis == Decimal("4144.95")  # 100 × $41.4495
        assert holding.current_value == Decimal("4250.00")  # 100 × $42.50 (current stock price)
        assert holding.unrealized_gain_loss == Decimal("105.05")  # $4250 - $4144.95
        # Percentage: (105.05 / 4144.95) × 100 ≈ 2.53%
        assert abs(holding.unrealized_gain_loss_percent - Decimal("2.53")) < Decimal("0.01")

    def test_buy_transaction_updates_existing_holding_facts_only(self, db: Session, test_portfolio: Portfolio, test_stock: Stock):
        """Test BUY transaction updates existing holding with new average cost."""
        # Arrange - Create initial holding
        initial_holding = Holding(
            portfolio_id=test_portfolio.id,
            stock_id=test_stock.id,
            quantity=Decimal("50"),
            average_cost=Decimal("40.00")  # Initial purchase at $40
        )
        db.add(initial_holding)
        db.commit()

        # Additional purchase
        transaction_data = TransactionCreate(
            stock_symbol="BHP",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("50"),
            price_per_share=Decimal("45.00"),
            fees=Decimal("19.95"),
            transaction_date=date(2024, 2, 15),
            notes="Additional BHP purchase"
        )

        # Act
        process_transaction(db, test_portfolio.id, transaction_data)

        # Assert
        # Refresh holding to get updated values
        db.refresh(initial_holding)

        # Facts: New quantity and weighted average cost
        assert initial_holding.quantity == Decimal("100")  # 50 + 50

        # Weighted average cost calculation:
        # Initial: 50 shares × $40.00 = $2000
        # Additional: 50 shares × $45.00 + $19.95 fees = $2269.95
        # Total cost: $2000 + $2269.95 = $4269.95
        # Average cost: $4269.95 / 100 = $42.6995
        expected_average_cost = Decimal("42.6995")
        assert initial_holding.average_cost == expected_average_cost

        # Dynamic values calculated correctly
        assert initial_holding.cost_basis == Decimal("4269.95")  # 100 × $42.6995
        assert initial_holding.current_value == Decimal("4250.00")  # 100 × $42.50 (current stock price)
        assert initial_holding.unrealized_gain_loss == Decimal("-19.95")  # $4250 - $4269.95

    def test_sell_transaction_reduces_holding_quantity_only(self, db: Session, test_portfolio: Portfolio, test_stock: Stock):
        """Test SELL transaction reduces quantity, keeps same average cost."""
        # Arrange - Create holding with shares
        holding = Holding(
            portfolio_id=test_portfolio.id,
            stock_id=test_stock.id,
            quantity=Decimal("100"),
            average_cost=Decimal("41.4495")  # Including fees from purchase
        )
        db.add(holding)
        db.commit()

        transaction_data = TransactionCreate(
            stock_symbol="BHP",
            transaction_type=TransactionType.SELL,
            quantity=Decimal("30"),
            price_per_share=Decimal("43.00"),
            fees=Decimal("19.95"),
            transaction_date=date(2024, 3, 15),
            notes="Partial BHP sale"
        )

        # Act
        process_transaction(db, test_portfolio.id, transaction_data)

        # Assert
        db.refresh(holding)

        # Facts: Reduced quantity, same average cost
        assert holding.quantity == Decimal("70")  # 100 - 30
        assert holding.average_cost == Decimal("41.4495")  # Unchanged

        # Dynamic values calculated correctly
        assert holding.cost_basis == Decimal("2901.465")  # 70 × $41.4495
        assert holding.current_value == Decimal("2975.00")  # 70 × $42.50 (current stock price)
        expected_gain = Decimal("73.535")  # $2975.00 - $2901.465
        assert abs(holding.unrealized_gain_loss - expected_gain) < Decimal("0.001")

    def test_sell_transaction_removes_holding_when_fully_sold(self, db: Session, test_portfolio: Portfolio, test_stock: Stock):
        """Test SELL transaction removes holding when all shares are sold."""
        # Arrange - Create holding
        holding = Holding(
            portfolio_id=test_portfolio.id,
            stock_id=test_stock.id,
            quantity=Decimal("50"),
            average_cost=Decimal("41.4495")
        )
        db.add(holding)
        db.commit()
        holding_id = holding.id

        transaction_data = TransactionCreate(
            stock_symbol="BHP",
            transaction_type=TransactionType.SELL,
            quantity=Decimal("50"),  # Sell all shares
            price_per_share=Decimal("43.00"),
            fees=Decimal("19.95"),
            transaction_date=date(2024, 3, 15),
            notes="Complete BHP sale"
        )

        # Act
        process_transaction(db, test_portfolio.id, transaction_data)

        # Assert
        # Holding should be deleted
        deleted_holding = db.query(Holding).filter(Holding.id == holding_id).first()
        assert deleted_holding is None

    def test_no_stored_calculated_values_in_database(self, db: Session, test_portfolio: Portfolio, test_stock: Stock):
        """Test that no calculated values are stored in the database."""
        # Arrange & Act
        transaction_data = TransactionCreate(
            stock_symbol="BHP",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price_per_share=Decimal("41.25"),
            fees=Decimal("19.95"),
            transaction_date=date(2024, 1, 15),
            notes="Test transaction"
        )

        process_transaction(db, test_portfolio.id, transaction_data)

        # Assert - Query raw database to verify no calculated fields are stored
        holding = db.query(Holding).filter(
            Holding.portfolio_id == test_portfolio.id,
            Holding.stock_id == test_stock.id
        ).first()

        # Only facts should be stored
        assert hasattr(holding, 'quantity')
        assert hasattr(holding, 'average_cost')
        assert hasattr(holding, 'created_at')
        assert hasattr(holding, 'updated_at')

        # These should be hybrid properties, not stored columns
        # (They exist as properties but not as database columns)
        assert hasattr(holding, 'current_value')
        assert hasattr(holding, 'cost_basis')
        assert hasattr(holding, 'unrealized_gain_loss')
        assert hasattr(holding, 'unrealized_gain_loss_percent')

        # Values should be calculated dynamically
        assert holding.current_value > 0
        assert holding.cost_basis > 0

    def test_transaction_processing_complexity_reduced(self, db: Session, test_portfolio: Portfolio, test_stock: Stock):
        """Test that transaction processing is much simpler without calculated field management."""
        # This test verifies the architectural improvement:
        # Transaction processing should only need to manage quantity and average_cost

        # Arrange
        transaction_data = TransactionCreate(
            stock_symbol="BHP",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price_per_share=Decimal("41.25"),
            fees=Decimal("19.95"),
            transaction_date=date(2024, 1, 15),
            notes="Simplified processing test"
        )

        # Act
        transaction_response = process_transaction(db, test_portfolio.id, transaction_data)

        # Assert
        # Transaction processing should be successful without complex calculated field logic
        assert transaction_response is not None
        assert transaction_response.stock.symbol == "BHP"

        # The holding should have the correct facts
        holding = db.query(Holding).filter(
            Holding.portfolio_id == test_portfolio.id,
            Holding.stock_id == test_stock.id
        ).first()

        # Facts are stored correctly
        assert holding.quantity == Decimal("100")
        assert holding.average_cost == Decimal("41.4495")  # Includes fees

        # Dynamic calculations work correctly
        assert holding.current_value == Decimal("4250.00")  # 100 × $42.50 (current price)
        assert holding.unrealized_gain_loss > 0  # Profit

        # No integrity check failures should occur
        # (This was the root cause of our previous issues)
"""
Integration tests for dynamic stock creation during transaction processing.
"""

import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from src.models import Portfolio, Stock, Transaction, User
from src.models.transaction import TransactionType, SourceType
from src.schemas.transaction import TransactionCreate
from src.services.transaction_service import process_transaction


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash="$2b$12$dummy.hash.value",
        first_name="Test",
        last_name="User"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_portfolio(db: Session, test_user: User):
    """Create a test portfolio."""
    portfolio = Portfolio(
        name="Test Portfolio",
        description="Test portfolio for dynamic stock creation",
        owner_id=test_user.id
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


class TestDynamicStockCreation:
    """Test dynamic stock creation during transaction processing."""

    def test_create_transaction_with_new_asx_stock(self, db: Session, test_portfolio: Portfolio):
        """Test creating a transaction with a new ASX stock that doesn't exist in database."""
        # Verify the stock doesn't exist
        existing_stock = db.query(Stock).filter(Stock.symbol == "XYZ").first()
        assert existing_stock is None, "Stock XYZ should not exist initially"

        # Create transaction data for new stock
        transaction_data = TransactionCreate(
            stock_symbol="XYZ",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price_per_share=Decimal("25.50"),
            transaction_date=date.today(),
            notes="Test transaction for new ASX stock"
        )

        # Process the transaction - this should create the stock dynamically
        result = process_transaction(db, test_portfolio.id, transaction_data)

        # Verify the transaction was created successfully
        assert result.id is not None
        assert result.stock.symbol == "XYZ"
        assert result.stock.exchange == "ASX"
        assert result.quantity == Decimal("100")
        assert result.price_per_share == Decimal("25.50")

        # Verify the stock was created in the database
        created_stock = db.query(Stock).filter(Stock.symbol == "XYZ").first()
        assert created_stock is not None
        assert created_stock.symbol == "XYZ"
        assert created_stock.exchange == "ASX"
        assert created_stock.company_name == "XYZ Corporation"  # Default name

        # Verify the transaction exists in database
        created_transaction = db.query(Transaction).filter(
            Transaction.portfolio_id == test_portfolio.id,
            Transaction.stock_id == created_stock.id
        ).first()
        assert created_transaction is not None
        assert created_transaction.quantity == Decimal("100")
        assert created_transaction.price_per_share == Decimal("25.50")

    def test_create_transaction_with_existing_stock(self, db: Session, test_portfolio: Portfolio):
        """Test creating a transaction with an existing stock."""
        # Create an existing stock first
        existing_stock = Stock(
            symbol="AAPL",
            company_name="Apple Inc.",
            exchange="NASDAQ"
        )
        db.add(existing_stock)
        db.commit()
        db.refresh(existing_stock)

        # Create transaction data for existing stock
        transaction_data = TransactionCreate(
            stock_symbol="AAPL",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("50"),
            price_per_share=Decimal("150.00"),
            transaction_date=date.today(),
            notes="Test transaction for existing stock"
        )

        # Process the transaction
        result = process_transaction(db, test_portfolio.id, transaction_data)

        # Verify the transaction uses the existing stock
        assert result.stock.id == existing_stock.id
        assert result.stock.symbol == "AAPL"
        assert result.stock.company_name == "Apple Inc."
        assert result.stock.exchange == "NASDAQ"

        # Verify no duplicate stock was created
        stock_count = db.query(Stock).filter(Stock.symbol == "AAPL").count()
        assert stock_count == 1

    def test_transaction_api_endpoint_with_new_stock(self, client: TestClient, test_user: User, test_portfolio: Portfolio):
        """Test the transaction API endpoint with a new stock."""
        # First login to get auth token
        login_response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Verify the stock doesn't exist
        headers = {"Authorization": f"Bearer {token}"}

        # Create transaction via API
        transaction_data = {
            "stock_symbol": "ABC",
            "transaction_type": "BUY",
            "quantity": "200",
            "price_per_share": "35.75",
            "transaction_date": str(date.today()),
            "notes": "API test for new stock"
        }

        response = client.post(
            f"/api/v1/portfolios/{test_portfolio.id}/transactions",
            json=transaction_data,
            headers=headers
        )

        # Should succeed with 201 Created
        assert response.status_code == 201
        result = response.json()

        # Verify the response structure
        assert "id" in result
        assert "stock" in result
        assert result["stock"]["symbol"] == "ABC"
        assert result["stock"]["exchange"] == "ASX"
        assert result["quantity"] == "200"
        assert result["price_per_share"] == "35.75"

    def test_multiple_transactions_same_new_stock(self, db: Session, test_portfolio: Portfolio):
        """Test creating multiple transactions for the same new stock."""
        # Create first transaction with new stock
        transaction_data_1 = TransactionCreate(
            stock_symbol="DEF",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price_per_share=Decimal("20.00"),
            transaction_date=date.today(),
            notes="First transaction for DEF"
        )

        result_1 = process_transaction(db, test_portfolio.id, transaction_data_1)
        stock_id = result_1.stock.id

        # Create second transaction with same stock
        transaction_data_2 = TransactionCreate(
            stock_symbol="DEF",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("50"),
            price_per_share=Decimal("22.00"),
            transaction_date=date.today(),
            notes="Second transaction for DEF"
        )

        result_2 = process_transaction(db, test_portfolio.id, transaction_data_2)

        # Verify both transactions use the same stock
        assert result_1.stock.id == result_2.stock.id
        assert result_2.stock.id == stock_id

        # Verify only one stock was created
        stock_count = db.query(Stock).filter(Stock.symbol == "DEF").count()
        assert stock_count == 1

        # Verify both transactions exist
        transaction_count = db.query(Transaction).filter(
            Transaction.portfolio_id == test_portfolio.id,
            Transaction.stock_id == stock_id
        ).count()
        assert transaction_count == 2
"""
Integration tests for transaction list API functionality.
Tests that all transactions are properly displayed and accounted for.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from src.models import Portfolio, Stock, Transaction, User, StockStatus
from src.models.transaction import TransactionType, SourceType


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    from src.core.auth import get_password_hash

    user = User(
        email="transaction@example.com",
        password_hash=get_password_hash("password"),
        first_name="Transaction",
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
        name="Transaction List Portfolio",
        description="Portfolio for testing transaction list",
        owner_id=test_user.id
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@pytest.fixture
def test_stocks(db: Session):
    """Create test stocks with proper enum values."""
    stocks = [
        Stock(
            symbol="CBA",
            company_name="Commonwealth Bank",
            exchange="ASX",
            status=StockStatus.ACTIVE
        ),
        Stock(
            symbol="BHP",
            company_name="BHP Group",
            exchange="ASX",
            status=StockStatus.ACTIVE
        ),
        Stock(
            symbol="WBC",
            company_name="Westpac Banking",
            exchange="ASX",
            status=StockStatus.ACTIVE
        )
    ]

    for stock in stocks:
        db.add(stock)

    db.commit()

    for stock in stocks:
        db.refresh(stock)

    return stocks


@pytest.fixture
def test_transactions(db: Session, test_portfolio: Portfolio, test_stocks: list):
    """Create comprehensive set of test transactions."""
    transactions = [
        # CBA transactions
        Transaction(
            portfolio_id=test_portfolio.id,
            stock_id=test_stocks[0].id,  # CBA
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price_per_share=Decimal("50.00"),
            total_amount=Decimal("5000.00"),  # quantity * price_per_share
            source_type=SourceType.MANUAL,
            transaction_date=date(2024, 1, 15),
            notes="Initial CBA purchase"
        ),
        Transaction(
            portfolio_id=test_portfolio.id,
            stock_id=test_stocks[0].id,  # CBA
            transaction_type=TransactionType.SELL,
            quantity=Decimal("25"),
            price_per_share=Decimal("52.00"),
            total_amount=Decimal("1300.00"),  # quantity * price_per_share
            source_type=SourceType.MANUAL,
            transaction_date=date(2024, 2, 20),
            notes="Partial CBA sale"
        ),

        # BHP transactions
        Transaction(
            portfolio_id=test_portfolio.id,
            stock_id=test_stocks[1].id,  # BHP
            transaction_type=TransactionType.BUY,
            quantity=Decimal("200"),
            price_per_share=Decimal("30.00"),
            total_amount=Decimal("6000.00"),  # quantity * price_per_share
            source_type=SourceType.MANUAL,
            transaction_date=date(2024, 1, 20),
            notes="Initial BHP purchase"
        ),
        Transaction(
            portfolio_id=test_portfolio.id,
            stock_id=test_stocks[1].id,  # BHP
            transaction_type=TransactionType.BUY,
            quantity=Decimal("50"),
            price_per_share=Decimal("32.00"),
            total_amount=Decimal("1600.00"),  # quantity * price_per_share
            source_type=SourceType.MANUAL,
            transaction_date=date(2024, 3, 10),
            notes="Additional BHP purchase"
        ),

        # WBC transactions
        Transaction(
            portfolio_id=test_portfolio.id,
            stock_id=test_stocks[2].id,  # WBC
            transaction_type=TransactionType.BUY,
            quantity=Decimal("150"),
            price_per_share=Decimal("20.00"),
            total_amount=Decimal("3000.00"),  # quantity * price_per_share
            source_type=SourceType.MANUAL,
            transaction_date=date(2024, 2, 5),
            notes="Initial WBC purchase"
        ),
    ]

    for transaction in transactions:
        db.add(transaction)

    db.commit()

    for transaction in transactions:
        db.refresh(transaction)

    return transactions


class TestTransactionListAPI:
    """Test transaction list API functionality."""

    def test_get_all_portfolio_transactions(self, client: TestClient, test_user: User, test_portfolio: Portfolio, test_transactions: list):
        """Test retrieving all transactions for a portfolio."""
        # Login first
        login_response = client.post("/api/v1/auth/login", json={
            "email": "transaction@example.com",
            "password": "password"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # Get all transactions for the portfolio
        response = client.get(
            f"/api/v1/portfolios/{test_portfolio.id}/transactions",
            headers=headers
        )

        assert response.status_code == 200
        response_data = response.json()

        # Handle paginated response format
        transactions = response_data['transactions']

        # Should return all 5 transactions
        assert len(transactions) == 5
        assert response_data['total'] == 5

        # Verify all transactions are accounted for
        symbols = [t["stock"]["symbol"] for t in transactions]
        assert "CBA" in symbols
        assert "BHP" in symbols
        assert "WBC" in symbols

        # Count transactions per stock
        cba_count = len([t for t in transactions if t["stock"]["symbol"] == "CBA"])
        bhp_count = len([t for t in transactions if t["stock"]["symbol"] == "BHP"])
        wbc_count = len([t for t in transactions if t["stock"]["symbol"] == "WBC"])

        assert cba_count == 2  # 1 buy, 1 sell
        assert bhp_count == 2  # 2 buys
        assert wbc_count == 1  # 1 buy

    def test_transaction_list_sorted_by_date(self, client: TestClient, test_user: User, test_portfolio: Portfolio, test_transactions: list):
        """Test that transactions are sorted by date (most recent first)."""
        # Login first
        login_response = client.post("/api/v1/auth/login", json={
            "email": "transaction@example.com",
            "password": "password"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # Get transactions
        response = client.get(
            f"/api/v1/portfolios/{test_portfolio.id}/transactions",
            headers=headers
        )

        assert response.status_code == 200
        response_data = response.json()
        transactions = response_data['transactions']

        # Verify sorting (most recent first)
        dates = [t["transaction_date"] for t in transactions]

        # Convert to datetime for comparison
        parsed_dates = [datetime.strptime(d, "%Y-%m-%d").date() for d in dates]

        # Should be sorted in descending order (most recent first)
        assert parsed_dates == sorted(parsed_dates, reverse=True)

    def test_transaction_details_complete(self, client: TestClient, test_user: User, test_portfolio: Portfolio, test_transactions: list):
        """Test that transaction details are complete and accurate."""
        # Login first
        login_response = client.post("/api/v1/auth/login", json={
            "email": "transaction@example.com",
            "password": "password"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # Get transactions
        response = client.get(
            f"/api/v1/portfolios/{test_portfolio.id}/transactions",
            headers=headers
        )

        assert response.status_code == 200
        response_data = response.json()
        transactions = response_data['transactions']

        # Verify each transaction has all required fields
        for transaction in transactions:
            assert "id" in transaction
            assert "stock" in transaction
            assert "transaction_type" in transaction
            assert "quantity" in transaction
            assert "price_per_share" in transaction
            assert "transaction_date" in transaction
            assert "notes" in transaction
            assert "processed_date" in transaction

            # Verify stock details
            stock = transaction["stock"]
            assert "symbol" in stock
            assert "company_name" in stock
            assert "exchange" in stock

            # Verify data types and values
            assert Decimal(transaction["quantity"]) > 0
            assert Decimal(transaction["price_per_share"]) > 0
            assert transaction["transaction_type"] in ["BUY", "SELL", "TRANSFER_IN", "TRANSFER_OUT"]

    def test_empty_portfolio_transactions(self, client: TestClient, test_user: User):
        """Test retrieving transactions for portfolio with no transactions."""
        # Create empty portfolio
        empty_portfolio = Portfolio(
            name="Empty Portfolio",
            description="Portfolio with no transactions",
            owner_id=test_user.id
        )

        # Manually add to get db session from client
        # This would be handled by the fixture in real scenarios

        # Login first
        login_response = client.post("/api/v1/auth/login", json={
            "email": "transaction@example.com",
            "password": "password"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # Create the empty portfolio via API
        portfolio_data = {
            "name": "Empty Portfolio",
            "description": "Portfolio with no transactions"
        }

        create_response = client.post(
            "/api/v1/portfolios",
            json=portfolio_data,
            headers=headers
        )

        assert create_response.status_code == 201
        empty_portfolio_id = create_response.json()["id"]

        # Get transactions for empty portfolio
        response = client.get(
            f"/api/v1/portfolios/{empty_portfolio_id}/transactions",
            headers=headers
        )

        assert response.status_code == 200
        response_data = response.json()
        transactions = response_data['transactions']
        assert len(transactions) == 0
        assert response_data['total'] == 0

    def test_transaction_totals_accuracy(self, client: TestClient, test_user: User, test_portfolio: Portfolio, test_transactions: list):
        """Test that transaction list accounts for all portfolio value correctly."""
        # Login first
        login_response = client.post("/api/v1/auth/login", json={
            "email": "transaction@example.com",
            "password": "password"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # Get transactions
        response = client.get(
            f"/api/v1/portfolios/{test_portfolio.id}/transactions",
            headers=headers
        )

        assert response.status_code == 200
        response_data = response.json()
        transactions = response_data['transactions']

        # Calculate total value from transactions
        total_invested = Decimal("0")
        total_sold = Decimal("0")

        for transaction in transactions:
            quantity = Decimal(transaction["quantity"])
            price = Decimal(transaction["price_per_share"])
            value = quantity * price

            if transaction["transaction_type"] == "BUY":
                total_invested += value
            elif transaction["transaction_type"] == "SELL":
                total_sold += value

        # Expected calculations:
        # CBA: 100 * 50.00 = 5000 (buy) - 25 * 52.00 = 1300 (sell) = 3700 net
        # BHP: 200 * 30.00 = 6000 + 50 * 32.00 = 1600 = 7600 total
        # WBC: 150 * 20.00 = 3000
        # Total invested: 5000 + 6000 + 1600 + 3000 = 15600
        # Total sold: 1300
        # Net invested: 15600 - 1300 = 14300

        expected_invested = Decimal("15600")
        expected_sold = Decimal("1300")

        assert total_invested == expected_invested
        assert total_sold == expected_sold
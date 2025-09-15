"""
TDD Test: Transaction API datetime validation
Test that transaction_date validation works correctly for frontend datetime inputs.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.models import User, Portfolio, Stock
from src.models.user import UserRole
from src.core.auth import get_password_hash, create_access_token
from uuid import uuid4


def create_test_user(db_session: Session, email: str, role: UserRole = UserRole.USER) -> User:
    """Create a test user."""
    user = User(
        id=uuid4(),
        email=email,
        password_hash=get_password_hash("testpassword"),
        first_name="Test",
        last_name="User",
        role=role,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_auth_headers(user: User) -> dict:
    """Create authentication headers for a user."""
    access_token = create_access_token(data={"sub": user.email})
    return {"Authorization": f"Bearer {access_token}"}


def create_test_portfolio(db_session: Session, user_id: str, name: str) -> Portfolio:
    """Create a test portfolio."""
    portfolio = Portfolio(
        id=uuid4(),
        name=name,
        description=f"Test description for {name}",
        owner_id=user_id,
        is_active=True
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)
    return portfolio


def create_test_stock(db_session: Session, symbol: str = "AAPL") -> Stock:
    """Create a test stock."""
    stock = Stock(
        symbol=symbol,
        company_name=f"Test Stock {symbol}",
        current_price=150.00
    )
    db_session.add(stock)
    db_session.commit()
    db_session.refresh(stock)
    return stock


class TestTransactionDatetimeValidation:
    """Test transaction API datetime validation issues."""

    def test_transaction_with_datetime_string_succeeds(self, db_session: Session, client: TestClient):
        """Test that sending datetime string (as frontend does) should work after fix."""
        # Create test user, portfolio, and stock
        user = create_test_user(db_session, email="datetime_test@example.com")
        auth_headers = create_auth_headers(user)
        portfolio = create_test_portfolio(db_session, user_id=user.id, name="Datetime Test Portfolio")
        stock = create_test_stock(db_session, symbol="TSLA")

        # Frontend correctly sends datetime strings - backend should handle this
        transaction_data = {
            "stock_symbol": stock.symbol,
            "transaction_type": "BUY",
            "quantity": 10,
            "price_per_share": 250.00,
            "transaction_date": "2025-09-14T16:00:00.000Z"  # This is what frontend sends
        }

        response = client.post(
            f"/api/v1/portfolios/{portfolio.id}/transactions",
            json=transaction_data,
            headers=auth_headers
        )

        print(f"Response status: {response.status_code}")
        if response.status_code != 201:
            print(f"Response body: {response.text}")

        # After fix, this should work - backend should extract date from datetime string
        assert response.status_code == 201
        transaction_response = response.json()
        assert transaction_response["stock"]["symbol"] == "TSLA"
        assert transaction_response["transaction_type"] == "BUY"
        # The response should contain the date part (2025-09-14)
        assert "2025-09-14" in transaction_response["transaction_date"]

    def test_transaction_with_date_string_succeeds(self, db_session: Session, client: TestClient):
        """Test that sending date-only string works correctly."""
        # Create test user, portfolio, and stock
        user = create_test_user(db_session, email="date_test@example.com")
        auth_headers = create_auth_headers(user)
        portfolio = create_test_portfolio(db_session, user_id=user.id, name="Date Test Portfolio")
        stock = create_test_stock(db_session, symbol="AAPL")

        # This is the correct format that currently works
        transaction_data = {
            "stock_symbol": stock.symbol,
            "transaction_type": "BUY",
            "quantity": 10,
            "price_per_share": 250.00,
            "transaction_date": "2025-09-14"  # Date-only format
        }

        response = client.post(
            f"/api/v1/portfolios/{portfolio.id}/transactions",
            json=transaction_data,
            headers=auth_headers
        )

        # This should work
        assert response.status_code == 201
        transaction_response = response.json()
        assert transaction_response["stock"]["symbol"] == "AAPL"
        assert transaction_response["transaction_type"] == "BUY"
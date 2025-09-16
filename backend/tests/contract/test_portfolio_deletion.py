"""
Contract tests for Portfolio Deletion API endpoints.
Tests portfolio deletion with confirmation and data cleanup.
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import Portfolio, Holding, Transaction, User, Stock
from src.models.transaction import TransactionType, SourceType
from src.core.auth import get_password_hash, create_access_token
from datetime import datetime


def create_test_user(db: Session, email: str) -> User:
    """Create a test user."""
    user = User(
        email=email,
        first_name="Test",
        last_name="User",
        password_hash=get_password_hash("testpassword")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_test_token(user: User) -> str:
    """Create a test JWT token for user."""
    return create_access_token(data={"sub": user.email})


@pytest.mark.contract
class TestPortfolioDeletionAPI:
    """Test Portfolio deletion API endpoints with confirmation."""

    def test_delete_portfolio_with_confirmation_requires_exact_name_match(
        self, client: TestClient, db: Session
    ):
        """DELETE with confirmation should require exact portfolio name match."""
        # Create test user and portfolio
        user = create_test_user(db, "test@example.com")
        token = create_test_token(user)

        portfolio = Portfolio(
            name="My Test Portfolio",
            description="Test portfolio for deletion",
            owner_id=user.id
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)

        headers = {"Authorization": f"Bearer {token}"}

        # Test with wrong confirmation name
        wrong_confirmation = {
            "confirmation_name": "Wrong Portfolio Name"
        }
        response = client.post(
            f"/api/v1/portfolios/{portfolio.id}/delete",
            json=wrong_confirmation,
            headers=headers
        )
        assert response.status_code == 400
        assert "confirmation name" in response.json()["detail"].lower()

        # Test with correct confirmation name
        correct_confirmation = {
            "confirmation_name": "My Test Portfolio"
        }
        response = client.post(
            f"/api/v1/portfolios/{portfolio.id}/delete",
            json=correct_confirmation,
            headers=headers
        )
        assert response.status_code == 200

        # Verify portfolio is soft deleted
        db.refresh(portfolio)
        assert portfolio.is_active is False

    def test_hard_delete_portfolio_removes_all_related_data(
        self, client: TestClient, db: Session
    ):
        """Hard delete should remove portfolio, holdings, and transactions."""
        # Create test user and portfolio with data
        user = create_test_user(db, "test@example.com")
        token = create_test_token(user)

        # Create stock for holdings
        stock = Stock(
            symbol="AAPL",
            company_name="Apple Inc.",
            current_price=Decimal("150.00")
        )
        db.add(stock)

        portfolio = Portfolio(
            name="Portfolio to Delete",
            description="Test portfolio with holdings",
            owner_id=user.id
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
        db.refresh(stock)

        # Add holding
        holding = Holding(
            portfolio_id=portfolio.id,
            stock_id=stock.id,
            quantity=Decimal("10"),
            average_cost=Decimal("145.00")
        )
        db.add(holding)

        # Add transaction
        transaction = Transaction(
            portfolio_id=portfolio.id,
            stock_id=stock.id,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("10"),
            price_per_share=Decimal("145.00"),
            total_amount=Decimal("1450.00"),
            transaction_date=datetime.utcnow(),
            source_type=SourceType.MANUAL
        )
        db.add(transaction)
        db.commit()

        headers = {"Authorization": f"Bearer {token}"}
        confirmation = {
            "confirmation_name": "Portfolio to Delete"
        }

        # Perform hard delete
        response = client.post(
            f"/api/v1/portfolios/{portfolio.id}/hard-delete",
            json=confirmation,
            headers=headers
        )
        assert response.status_code == 200

        # Verify complete removal
        assert db.query(Portfolio).filter(Portfolio.id == portfolio.id).first() is None
        assert db.query(Holding).filter(Holding.portfolio_id == portfolio.id).first() is None
        assert db.query(Transaction).filter(Transaction.portfolio_id == portfolio.id).first() is None

    def test_delete_portfolio_unauthorized_access(
        self, client: TestClient, db: Session
    ):
        """Users cannot delete portfolios they don't own."""
        # Create two users
        user1 = create_test_user(db, "user1@example.com")
        user2 = create_test_user(db, "user2@example.com")
        token2 = create_test_token(user2)

        # User1 creates portfolio
        portfolio = Portfolio(
            name="User1 Portfolio",
            description="Portfolio owned by user1",
            owner_id=user1.id
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)

        # User2 tries to delete user1's portfolio
        headers = {"Authorization": f"Bearer {token2}"}
        confirmation = {
            "confirmation_name": "User1 Portfolio"
        }

        response = client.post(
            f"/api/v1/portfolios/{portfolio.id}/delete",
            json=confirmation,
            headers=headers
        )
        assert response.status_code == 404  # Portfolio not found for this user

    def test_delete_nonexistent_portfolio(
        self, client: TestClient, db: Session
    ):
        """Deleting non-existent portfolio should return 404."""
        user = create_test_user(db, "test@example.com")
        token = create_test_token(user)

        fake_uuid = "00000000-0000-0000-0000-000000000000"
        headers = {"Authorization": f"Bearer {token}"}
        confirmation = {
            "confirmation_name": "Nonexistent Portfolio"
        }

        response = client.post(
            f"/api/v1/portfolios/{fake_uuid}/delete",
            json=confirmation,
            headers=headers
        )
        assert response.status_code == 404

    def test_delete_portfolio_missing_confirmation_name(
        self, client: TestClient, db: Session
    ):
        """Deletion should require confirmation_name field."""
        user = create_test_user(db, "test@example.com")
        token = create_test_token(user)

        portfolio = Portfolio(
            name="Test Portfolio",
            description="Test portfolio",
            owner_id=user.id
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)

        headers = {"Authorization": f"Bearer {token}"}

        # Missing confirmation_name
        response = client.post(
            f"/api/v1/portfolios/{portfolio.id}/delete",
            json={},
            headers=headers
        )
        assert response.status_code == 422

    def test_soft_delete_preserves_data_for_recovery(
        self, client: TestClient, db: Session
    ):
        """Soft delete should preserve holdings and transactions."""
        user = create_test_user(db, "test@example.com")
        token = create_test_token(user)

        # Create stock for holdings
        stock = Stock(
            symbol="TSLA",
            company_name="Tesla Inc.",
            current_price=Decimal("250.00")
        )
        db.add(stock)

        portfolio = Portfolio(
            name="Soft Delete Test",
            description="Test portfolio for soft deletion",
            owner_id=user.id
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
        db.refresh(stock)

        # Add data
        holding = Holding(
            portfolio_id=portfolio.id,
            stock_id=stock.id,
            quantity=Decimal("5"),
            average_cost=Decimal("240.00")
        )
        db.add(holding)

        transaction = Transaction(
            portfolio_id=portfolio.id,
            stock_id=stock.id,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("5"),
            price_per_share=Decimal("240.00"),
            total_amount=Decimal("1200.00"),
            transaction_date=datetime.utcnow(),
            source_type=SourceType.MANUAL
        )
        db.add(transaction)
        db.commit()

        headers = {"Authorization": f"Bearer {token}"}
        confirmation = {
            "confirmation_name": "Soft Delete Test"
        }

        # Perform soft delete
        response = client.post(
            f"/api/v1/portfolios/{portfolio.id}/delete",
            json=confirmation,
            headers=headers
        )
        assert response.status_code == 200

        # Verify portfolio is soft deleted but data remains
        db.refresh(portfolio)
        assert portfolio.is_active is False

        # Holdings and transactions should still exist
        assert db.query(Holding).filter(Holding.portfolio_id == portfolio.id).first() is not None
        assert db.query(Transaction).filter(Transaction.portfolio_id == portfolio.id).first() is not None
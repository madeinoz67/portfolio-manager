"""
TDD Test: Comprehensive Audit Events Integration
Test that all major audit events are properly logged across the system.
"""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.models import User, Portfolio, AuditLog, Transaction, Stock
from src.models.audit_log import AuditEventType
from src.models.user import UserRole
from src.models.transaction import TransactionType
from src.core.auth import get_password_hash, create_access_token


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


class TestComprehensiveAuditEvents:
    """Test comprehensive audit logging across all major system events."""

    def test_portfolio_creation_audit_event(self, db_session: Session, client: TestClient):
        """Test that portfolio creation creates audit log entry."""
        # Create test user
        user = create_test_user(db_session, email="portfolio_create@example.com")
        auth_headers = create_auth_headers(user)

        # Verify no audit logs initially
        initial_audit_count = db_session.query(AuditLog).count()
        assert initial_audit_count == 0

        # Create portfolio via API
        portfolio_data = {
            "name": "Audit Test Portfolio",
            "description": "Portfolio created for audit testing"
        }
        response = client.post(
            "/api/v1/portfolios",
            json=portfolio_data,
            headers=auth_headers
        )

        # Verify creation was successful
        assert response.status_code == 201
        portfolio_response = response.json()
        assert portfolio_response["name"] == "Audit Test Portfolio"

        # Verify audit log was created
        db_session.commit()
        audit_logs = db_session.query(AuditLog).all()
        assert len(audit_logs) == 1

        audit_log = audit_logs[0]
        assert audit_log.event_type == AuditEventType.PORTFOLIO_CREATED
        assert audit_log.entity_type == "portfolio"
        assert audit_log.entity_id == portfolio_response["id"]
        assert audit_log.user_id == user.id
        assert "created" in audit_log.event_description
        assert "Audit Test Portfolio" in audit_log.event_description

        # Check metadata
        assert audit_log.event_metadata is not None
        assert audit_log.event_metadata["portfolio_name"] == "Audit Test Portfolio"
        assert audit_log.event_metadata["portfolio_description"] == "Portfolio created for audit testing"

    def test_portfolio_update_audit_event(self, db_session: Session, client: TestClient):
        """Test that portfolio updates create audit log entries."""
        # Create test user and portfolio
        user = create_test_user(db_session, email="portfolio_update@example.com")
        auth_headers = create_auth_headers(user)
        portfolio = create_test_portfolio(db_session, user_id=user.id, name="Original Portfolio Name")

        # Clear initial audit logs from portfolio creation
        db_session.query(AuditLog).delete()
        db_session.commit()

        # Update portfolio via API
        update_data = {
            "name": "Updated Portfolio Name",
            "description": "Updated description for audit testing"
        }
        response = client.put(
            f"/api/v1/portfolios/{portfolio.id}",
            json=update_data,
            headers=auth_headers
        )

        # Verify update was successful
        assert response.status_code == 200
        updated_portfolio = response.json()
        assert updated_portfolio["name"] == "Updated Portfolio Name"

        # Verify audit log was created
        db_session.commit()
        audit_logs = db_session.query(AuditLog).all()
        assert len(audit_logs) == 1

        audit_log = audit_logs[0]
        assert audit_log.event_type == AuditEventType.PORTFOLIO_UPDATED
        assert audit_log.entity_type == "portfolio"
        assert audit_log.entity_id == str(portfolio.id)
        assert audit_log.user_id == user.id
        assert "updated" in audit_log.event_description
        assert "Updated Portfolio Name" in audit_log.event_description

    def test_transaction_creation_audit_event(self, db_session: Session, client: TestClient):
        """Test that transaction creation creates audit log entries."""
        # Create test user, portfolio, and stock
        user = create_test_user(db_session, email="transaction_create@example.com")
        auth_headers = create_auth_headers(user)
        portfolio = create_test_portfolio(db_session, user_id=user.id, name="Transaction Test Portfolio")
        stock = create_test_stock(db_session, symbol="TSLA")

        # Clear initial audit logs
        db_session.query(AuditLog).delete()
        db_session.commit()

        # Create transaction via API
        transaction_data = {
            "stock_symbol": stock.symbol,
            "transaction_type": "BUY",
            "quantity": 10,
            "price_per_share": 250.00,
            "transaction_date": "2023-12-01"
        }
        response = client.post(
            f"/api/v1/portfolios/{portfolio.id}/transactions",
            json=transaction_data,
            headers=auth_headers
        )

        # Verify transaction was successful
        assert response.status_code == 201
        transaction_response = response.json()

        # Verify audit log was created
        db_session.commit()
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.event_type == AuditEventType.TRANSACTION_CREATED
        ).all()
        assert len(audit_logs) == 1

        audit_log = audit_logs[0]
        assert audit_log.event_type == AuditEventType.TRANSACTION_CREATED
        assert audit_log.entity_type == "transaction"
        assert audit_log.entity_id == transaction_response["id"]
        assert audit_log.user_id == user.id
        assert "transaction" in audit_log.event_description.lower()
        assert "created" in audit_log.event_description.lower()

    def test_transaction_update_audit_event(self, db_session: Session, client: TestClient):
        """Test that transaction updates create audit log entries."""
        # Create test user, portfolio, stock, and transaction
        user = create_test_user(db_session, email="transaction_update@example.com")
        auth_headers = create_auth_headers(user)
        portfolio = create_test_portfolio(db_session, user_id=user.id, name="Transaction Update Test")
        stock = create_test_stock(db_session, symbol="GOOGL")

        # Create transaction first
        transaction_data = {
            "stock_symbol": stock.symbol,
            "transaction_type": "BUY",
            "quantity": 5,
            "price_per_share": 2800.00,
            "transaction_date": "2023-12-01"
        }
        create_response = client.post(f"/api/v1/portfolios/{portfolio.id}/transactions", json=transaction_data, headers=auth_headers)
        assert create_response.status_code == 201
        transaction_id = create_response.json()["id"]

        # Clear audit logs to focus on update event
        db_session.query(AuditLog).delete()
        db_session.commit()

        # Update transaction
        update_data = {
            "quantity": 8,
            "price_per_share": 2750.00
        }
        response = client.put(
            f"/api/v1/portfolios/{portfolio.id}/transactions/{transaction_id}",
            json=update_data,
            headers=auth_headers
        )

        # Verify update was successful
        assert response.status_code == 200

        # Verify audit log was created
        db_session.commit()
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.event_type == AuditEventType.TRANSACTION_UPDATED
        ).all()
        assert len(audit_logs) == 1

        audit_log = audit_logs[0]
        assert audit_log.event_type == AuditEventType.TRANSACTION_UPDATED
        assert audit_log.entity_type == "transaction"
        assert audit_log.entity_id == transaction_id
        assert audit_log.user_id == user.id

    def test_transaction_deletion_audit_event(self, db_session: Session, client: TestClient):
        """Test that transaction deletion creates audit log entries."""
        # Create test user, portfolio, stock, and transaction
        user = create_test_user(db_session, email="transaction_delete@example.com")
        auth_headers = create_auth_headers(user)
        portfolio = create_test_portfolio(db_session, user_id=user.id, name="Transaction Delete Test")
        stock = create_test_stock(db_session, symbol="MSFT")

        # Create transaction first
        transaction_data = {
            "stock_symbol": stock.symbol,
            "transaction_type": "BUY",
            "quantity": 15,
            "price_per_share": 350.00,
            "transaction_date": "2023-12-01"
        }
        create_response = client.post(f"/api/v1/portfolios/{portfolio.id}/transactions", json=transaction_data, headers=auth_headers)
        assert create_response.status_code == 201
        transaction_id = create_response.json()["id"]

        # Clear audit logs to focus on deletion event
        db_session.query(AuditLog).delete()
        db_session.commit()

        # Delete transaction
        response = client.delete(f"/api/v1/portfolios/{portfolio.id}/transactions/{transaction_id}", headers=auth_headers)

        # Verify deletion was successful
        assert response.status_code == 204

        # Verify audit log was created
        db_session.commit()
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.event_type == AuditEventType.TRANSACTION_DELETED
        ).all()
        assert len(audit_logs) == 1

        audit_log = audit_logs[0]
        assert audit_log.event_type == AuditEventType.TRANSACTION_DELETED
        assert audit_log.entity_type == "transaction"
        assert audit_log.entity_id == transaction_id
        assert audit_log.user_id == user.id

    def test_user_login_audit_event(self, db_session: Session, client: TestClient):
        """Test that user login creates audit log entries."""
        # Create test user
        user = create_test_user(db_session, email="login_test@example.com")

        # Clear initial audit logs
        db_session.query(AuditLog).delete()
        db_session.commit()

        # Login via API
        login_data = {
            "email": "login_test@example.com",
            "password": "testpassword"
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        # Verify login was successful
        assert response.status_code == 200
        login_response = response.json()
        assert "access_token" in login_response

        # Verify audit log was created
        db_session.commit()
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.event_type == AuditEventType.USER_LOGIN
        ).all()
        assert len(audit_logs) == 1

        audit_log = audit_logs[0]
        assert audit_log.event_type == AuditEventType.USER_LOGIN
        assert audit_log.entity_type == "user"
        assert audit_log.entity_id == str(user.id)
        assert audit_log.user_id == user.id
        assert "logged in" in audit_log.event_description

    def test_user_registration_audit_event(self, db_session: Session, client: TestClient):
        """Test that user registration creates audit log entries."""
        # Clear initial audit logs
        db_session.query(AuditLog).delete()
        db_session.commit()

        # Register new user via API
        registration_data = {
            "email": "newuser@example.com",
            "password": "newpassword123",
            "first_name": "New",
            "last_name": "User"
        }
        response = client.post("/api/v1/auth/register", json=registration_data)

        # Verify registration was successful
        assert response.status_code == 201
        registration_response = response.json()
        new_user_id = registration_response["id"]

        # Verify audit log was created
        db_session.commit()
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.event_type == AuditEventType.USER_CREATED
        ).all()
        assert len(audit_logs) == 1

        audit_log = audit_logs[0]
        assert audit_log.event_type == AuditEventType.USER_CREATED
        assert audit_log.entity_type == "user"
        assert audit_log.entity_id == new_user_id
        assert str(audit_log.user_id) == new_user_id  # User creates themselves
        assert "registered" in audit_log.event_description.lower() or "created" in audit_log.event_description.lower()

    def test_audit_events_include_request_metadata(self, db_session: Session, client: TestClient):
        """Test that all audit events include proper request metadata."""
        # Create test user
        user = create_test_user(db_session, email="metadata_test@example.com")
        auth_headers = create_auth_headers(user)
        auth_headers["User-Agent"] = "TestClient/AuditTest/1.0"

        # Clear initial audit logs
        db_session.query(AuditLog).delete()
        db_session.commit()

        # Create portfolio to generate audit event
        portfolio_data = {"name": "Metadata Test Portfolio", "description": "Testing metadata"}
        response = client.post("/api/v1/portfolios", json=portfolio_data, headers=auth_headers)
        assert response.status_code == 201

        # Verify audit log includes metadata
        db_session.commit()
        audit_logs = db_session.query(AuditLog).all()
        assert len(audit_logs) == 1

        audit_log = audit_logs[0]
        # IP address should be captured
        assert audit_log.ip_address is not None
        # User agent should be captured
        assert audit_log.user_agent == "TestClient/AuditTest/1.0"
        # Timestamp should be recent
        assert audit_log.timestamp is not None
        assert audit_log.created_at is not None

    def test_audit_events_chronological_order(self, db_session: Session, client: TestClient):
        """Test that audit events maintain chronological order."""
        # Create test user
        user = create_test_user(db_session, email="chronology_test@example.com")
        auth_headers = create_auth_headers(user)

        # Clear initial audit logs
        db_session.query(AuditLog).delete()
        db_session.commit()

        # Create multiple events in sequence
        # 1. Create portfolio
        portfolio_response = client.post(
            "/api/v1/portfolios",
            json={"name": "Chronology Test", "description": "Test"},
            headers=auth_headers
        )
        assert portfolio_response.status_code == 201
        portfolio_id = portfolio_response.json()["id"]

        # 2. Update portfolio
        client.put(
            f"/api/v1/portfolios/{portfolio_id}",
            json={"name": "Updated Chronology Test"},
            headers=auth_headers
        )

        # 3. Delete portfolio
        client.post(
            f"/api/v1/portfolios/{portfolio_id}/delete",
            json={"confirmation_name": "Updated Chronology Test"},
            headers=auth_headers
        )

        # Verify all events were created in chronological order
        db_session.commit()
        audit_logs = db_session.query(AuditLog).order_by(AuditLog.timestamp).all()
        assert len(audit_logs) == 3

        # Check event types in order
        assert audit_logs[0].event_type == AuditEventType.PORTFOLIO_CREATED
        assert audit_logs[1].event_type == AuditEventType.PORTFOLIO_UPDATED
        assert audit_logs[2].event_type == AuditEventType.PORTFOLIO_SOFT_DELETED

        # Check timestamps are in order
        assert audit_logs[0].timestamp <= audit_logs[1].timestamp
        assert audit_logs[1].timestamp <= audit_logs[2].timestamp
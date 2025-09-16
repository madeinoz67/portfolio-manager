"""
TDD Test: Portfolio Deletion Audit Integration
Test that portfolio deletion actually creates audit log entries.
"""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.models import User, Portfolio, AuditLog
from src.models.audit_log import AuditEventType
from src.models.user import UserRole
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


class TestPortfolioDeletionAuditIntegration:
    """Test portfolio deletion audit logging in real API calls."""

    def test_portfolio_soft_delete_creates_audit_event(self, db_session: Session, client: TestClient):
        """Test that portfolio soft deletion creates audit log entry."""
        # Create test user
        user = create_test_user(db_session, email="test@example.com", role=UserRole.USER)
        auth_headers = create_auth_headers(user)

        # Create test portfolio
        portfolio = create_test_portfolio(db_session, user_id=user.id, name="Test Portfolio for Audit")

        # Verify no audit logs initially
        initial_audit_count = db_session.query(AuditLog).count()
        assert initial_audit_count == 0

        # Delete portfolio via API
        response = client.post(
            f"/api/v1/portfolios/{portfolio.id}/delete",
            json={"confirmation_name": "Test Portfolio for Audit"},
            headers=auth_headers
        )

        # Verify deletion was successful
        assert response.status_code == 200
        assert response.json()["message"] == "Portfolio deleted successfully"

        # Verify audit log was created (this is our main test)
        db_session.commit()  # Ensure we see the latest data
        audit_logs = db_session.query(AuditLog).all()
        assert len(audit_logs) == 1

        # Verify portfolio is soft deleted
        db_session.refresh(portfolio)  # Refresh to get latest state
        assert portfolio.is_active is False

        audit_log = audit_logs[0]
        assert audit_log.event_type == AuditEventType.PORTFOLIO_SOFT_DELETED
        assert audit_log.entity_type == "portfolio"
        assert audit_log.entity_id == str(portfolio.id)
        assert audit_log.user_id == user.id
        assert "soft deleted" in audit_log.event_description
        assert "Test Portfolio for Audit" in audit_log.event_description

        # Check metadata
        assert audit_log.event_metadata is not None
        assert audit_log.event_metadata["portfolio_name"] == "Test Portfolio for Audit"
        assert audit_log.event_metadata["is_hard_delete"] is False

    def test_portfolio_hard_delete_creates_audit_event(self, db_session: Session, client: TestClient):
        """Test that portfolio hard deletion creates audit log entry."""
        # Create test user
        user = create_test_user(db_session, email="test2@example.com", role=UserRole.USER)
        auth_headers = create_auth_headers(user)

        # Create test portfolio
        portfolio = create_test_portfolio(db_session, user_id=user.id, name="Test Portfolio for Hard Delete")

        # Verify no audit logs initially
        initial_audit_count = db_session.query(AuditLog).count()
        assert initial_audit_count == 0

        # Hard delete portfolio via API
        response = client.post(
            f"/api/v1/portfolios/{portfolio.id}/hard-delete",
            json={"confirmation_name": "Test Portfolio for Hard Delete"},
            headers=auth_headers
        )

        # Verify deletion was successful
        assert response.status_code == 200
        assert response.json()["message"] == "Portfolio permanently deleted"

        # Verify portfolio is completely removed
        deleted_portfolio = db_session.query(Portfolio).filter(Portfolio.id == portfolio.id).first()
        assert deleted_portfolio is None

        # Verify audit log was created
        audit_logs = db_session.query(AuditLog).all()
        assert len(audit_logs) == 1

        audit_log = audit_logs[0]
        assert audit_log.event_type == AuditEventType.PORTFOLIO_HARD_DELETED
        assert audit_log.entity_type == "portfolio"
        assert audit_log.entity_id == str(portfolio.id)
        assert audit_log.user_id == user.id
        assert "hard deleted" in audit_log.event_description
        assert "Test Portfolio for Hard Delete" in audit_log.event_description

        # Check metadata
        assert audit_log.event_metadata is not None
        assert audit_log.event_metadata["portfolio_name"] == "Test Portfolio for Hard Delete"
        assert audit_log.event_metadata["is_hard_delete"] is True

    def test_portfolio_deletion_audit_includes_request_context(self, db_session: Session, client: TestClient):
        """Test that audit logs include IP address and user agent from request."""
        # Create test user
        user = create_test_user(db_session, email="test3@example.com", role=UserRole.USER)
        auth_headers = create_auth_headers(user)

        # Add user agent to headers
        auth_headers["User-Agent"] = "TestClient/1.0"

        # Create test portfolio
        portfolio = create_test_portfolio(db_session, user_id=user.id, name="Test Portfolio Context")

        # Delete portfolio via API
        response = client.post(
            f"/api/v1/portfolios/{portfolio.id}/delete",
            json={"confirmation_name": "Test Portfolio Context"},
            headers=auth_headers
        )

        assert response.status_code == 200

        # Verify audit log includes request context
        audit_log = db_session.query(AuditLog).first()
        assert audit_log is not None

        # IP address should be captured (testclient typically uses localhost)
        assert audit_log.ip_address is not None

        # User agent should be captured
        assert audit_log.user_agent == "TestClient/1.0"

    def test_failed_portfolio_deletion_no_audit_log(self, db_session: Session, client: TestClient):
        """Test that failed deletion attempts don't create audit logs."""
        # Create test user
        user = create_test_user(db_session, email="test4@example.com", role=UserRole.USER)
        auth_headers = create_auth_headers(user)

        # Create test portfolio
        portfolio = create_test_portfolio(db_session, user_id=user.id, name="Test Portfolio Fail")

        # Attempt deletion with wrong confirmation name
        response = client.post(
            f"/api/v1/portfolios/{portfolio.id}/delete",
            json={"confirmation_name": "Wrong Name"},
            headers=auth_headers
        )

        # Verify deletion failed
        assert response.status_code == 400

        # Verify no audit log was created
        audit_count = db_session.query(AuditLog).count()
        assert audit_count == 0

    def test_nonexistent_portfolio_deletion_no_audit_log(self, db_session: Session, client: TestClient):
        """Test that attempting to delete nonexistent portfolio doesn't create audit logs."""
        # Create test user
        user = create_test_user(db_session, email="test5@example.com", role=UserRole.USER)
        auth_headers = create_auth_headers(user)

        # Attempt to delete nonexistent portfolio
        fake_portfolio_id = uuid4()
        response = client.post(
            f"/api/v1/portfolios/{fake_portfolio_id}/delete",
            json={"confirmation_name": "Fake Portfolio"},
            headers=auth_headers
        )

        # Verify deletion failed
        assert response.status_code == 404

        # Verify no audit log was created
        audit_count = db_session.query(AuditLog).count()
        assert audit_count == 0
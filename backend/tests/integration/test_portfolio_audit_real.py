"""
Real integration tests for portfolio audit logging.
Tests that audit logs are actually created when portfolio operations occur.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from src.main import app
from src.models.user import User, UserRole
from src.models.portfolio import Portfolio
from src.models.audit_log import AuditLog, AuditEventType
from src.core.auth import create_access_token
from src.database import get_db


@pytest.fixture
def test_db():
    """Get test database session."""
    # Use the test database
    from src.database import engine
    from sqlalchemy.orm import sessionmaker

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(test_db):
    """Create a test user in the database."""
    user = User(
        id=uuid4(),
        email="audit_test@example.com",
        password_hash="hashed_password",
        first_name="Audit",
        last_name="Test",
        role=UserRole.USER,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user):
    """Create an auth token for the test user."""
    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
def auth_headers(auth_token):
    """Create auth headers."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestPortfolioAuditRealIntegration:
    """Real integration tests for portfolio audit logging."""

    def test_portfolio_creation_creates_audit_log(self, client, auth_headers, test_user, test_db):
        """Test that creating a portfolio actually creates an audit log entry."""
        # Count initial audit logs
        initial_audit_count = test_db.query(AuditLog).count()

        # Create a portfolio
        response = client.post(
            "/api/v1/portfolios",
            json={
                "name": "Test Audit Portfolio",
                "description": "Testing audit logging"
            },
            headers=auth_headers
        )

        # Should succeed
        assert response.status_code == 201
        portfolio_data = response.json()

        # Check that an audit log was created
        final_audit_count = test_db.query(AuditLog).count()

        # This will fail initially because audit logging is not integrated
        assert final_audit_count == initial_audit_count + 1, "Audit log should be created for portfolio creation"

        # Verify audit log details
        audit_log = test_db.query(AuditLog).filter(
            AuditLog.event_type == AuditEventType.PORTFOLIO_CREATED,
            AuditLog.entity_id == portfolio_data["id"]
        ).first()

        assert audit_log is not None, "Audit log entry should exist"
        assert audit_log.user_id == test_user.id
        assert audit_log.entity_type == "portfolio"
        assert "Test Audit Portfolio" in audit_log.event_description

    def test_portfolio_update_creates_audit_log(self, client, auth_headers, test_user, test_db):
        """Test that updating a portfolio creates an audit log entry."""
        # First create a portfolio
        create_response = client.post(
            "/api/v1/portfolios",
            json={
                "name": "Original Name",
                "description": "Original Description"
            },
            headers=auth_headers
        )
        assert create_response.status_code == 201
        portfolio_data = create_response.json()
        portfolio_id = portfolio_data["id"]

        # Count audit logs before update
        initial_update_audit_count = test_db.query(AuditLog).filter(
            AuditLog.event_type == AuditEventType.PORTFOLIO_UPDATED
        ).count()

        # Update the portfolio
        response = client.put(
            f"/api/v1/portfolios/{portfolio_id}",
            json={
                "name": "Updated Name",
                "description": "Updated Description"
            },
            headers=auth_headers
        )

        assert response.status_code == 200

        # Check that an audit log was created for the update
        final_update_audit_count = test_db.query(AuditLog).filter(
            AuditLog.event_type == AuditEventType.PORTFOLIO_UPDATED
        ).count()

        # This will fail initially because audit logging is not integrated
        assert final_update_audit_count == initial_update_audit_count + 1, "Audit log should be created for portfolio update"

    def test_portfolio_deletion_creates_audit_log(self, client, auth_headers, test_user, test_db):
        """Test that deleting a portfolio creates an audit log entry."""
        # First create a portfolio
        create_response = client.post(
            "/api/v1/portfolios",
            json={
                "name": "To Be Deleted",
                "description": "Will be deleted for testing"
            },
            headers=auth_headers
        )
        assert create_response.status_code == 201
        portfolio_data = create_response.json()
        portfolio_id = portfolio_data["id"]

        # Count audit logs before deletion
        initial_delete_audit_count = test_db.query(AuditLog).filter(
            AuditLog.event_type == AuditEventType.PORTFOLIO_SOFT_DELETED
        ).count()

        # Delete the portfolio (soft delete)
        response = client.post(
            f"/api/v1/portfolios/{portfolio_id}/delete",
            json={
                "confirmation_name": "To Be Deleted"
            },
            headers=auth_headers
        )

        assert response.status_code == 200

        # Check that an audit log was created for the deletion
        final_delete_audit_count = test_db.query(AuditLog).filter(
            AuditLog.event_type == AuditEventType.PORTFOLIO_SOFT_DELETED
        ).count()

        # This will fail initially because audit logging is not integrated
        assert final_delete_audit_count == initial_delete_audit_count + 1, "Audit log should be created for portfolio deletion"
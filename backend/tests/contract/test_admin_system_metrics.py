"""
Contract test for GET /api/v1/admin/system/metrics endpoint.

Tests the API contract as defined in admin-api.openapi.yaml:
- Response format matches SystemMetrics schema
- All required fields are present with correct types
- System status enum values are valid
- Admin authentication is enforced
- HTTP status codes match specification
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from tests.conftest import get_admin_jwt_token, get_user_jwt_token


client = TestClient(app)


class TestAdminSystemMetricsContract:
    """Contract tests for admin system metrics endpoint."""

    def test_admin_system_metrics_success_response_structure(self, admin_jwt_token: str, db_session: Session):
        """Test successful response matches SystemMetrics schema from contract."""
        response = client.get(
            "/api/v1/admin/system/metrics",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Contract requires all SystemMetrics fields
        assert "totalUsers" in data
        assert "totalPortfolios" in data
        assert "activeUsers" in data
        assert "adminUsers" in data
        assert "systemStatus" in data
        assert "lastUpdated" in data

        # Validate field types per contract
        assert isinstance(data["totalUsers"], int)
        assert data["totalUsers"] >= 0

        assert isinstance(data["totalPortfolios"], int)
        assert data["totalPortfolios"] >= 0

        assert isinstance(data["activeUsers"], int)
        assert data["activeUsers"] >= 0

        assert isinstance(data["adminUsers"], int)
        assert data["adminUsers"] >= 0

        # System status must be one of the enum values
        assert data["systemStatus"] in ["healthy", "warning", "error"]

        # lastUpdated should be a valid datetime string
        assert isinstance(data["lastUpdated"], str)
        # Basic ISO format check (will be more thorough in actual validation)
        assert "T" in data["lastUpdated"] or "Z" in data["lastUpdated"]

    def test_admin_system_metrics_logical_constraints(self, admin_jwt_token: str, db_session: Session):
        """Test that metrics follow logical business constraints."""
        response = client.get(
            "/api/v1/admin/system/metrics",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Active users cannot exceed total users
        assert data["activeUsers"] <= data["totalUsers"]

        # Admin users cannot exceed total users
        assert data["adminUsers"] <= data["totalUsers"]

        # There should be at least one admin user (the one making the request)
        assert data["adminUsers"] >= 1

    def test_admin_system_metrics_data_accuracy(self, admin_jwt_token: str, db_session: Session):
        """Test that metrics reflect actual database state."""
        from src.models.user import User
        from src.models.user_role import UserRole
        from src.models.portfolio import Portfolio

        # Get actual counts from database
        total_users_actual = db_session.query(User).count()
        admin_users_actual = db_session.query(User).filter(User.role == UserRole.ADMIN).count()
        active_users_actual = db_session.query(User).filter(User.is_active == True).count()
        total_portfolios_actual = db_session.query(Portfolio).count()

        response = client.get(
            "/api/v1/admin/system/metrics",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Metrics should match actual database state
        assert data["totalUsers"] == total_users_actual
        assert data["adminUsers"] == admin_users_actual
        assert data["activeUsers"] == active_users_actual
        assert data["totalPortfolios"] == total_portfolios_actual

    def test_admin_system_metrics_unauthorized_access_contract(self, db_session: Session):
        """Test unauthorized access returns 401 per contract."""
        response = client.get("/api/v1/admin/system/metrics")

        assert response.status_code == 401
        data = response.json()

        # Contract specifies error response structure
        assert "error" in data
        assert "message" in data
        assert data["error"] == "unauthorized"
        assert data["message"] == "Authentication required"

    def test_admin_system_metrics_forbidden_access_contract(self, user_jwt_token: str, db_session: Session):
        """Test non-admin access returns 403 per contract."""
        response = client.get(
            "/api/v1/admin/system/metrics",
            headers={"Authorization": f"Bearer {user_jwt_token}"}
        )

        assert response.status_code == 403
        data = response.json()

        # Contract specifies error response structure
        assert "error" in data
        assert "message" in data
        assert data["error"] == "forbidden"
        assert data["message"] == "Admin role required"

    def test_admin_system_metrics_timestamp_freshness(self, admin_jwt_token: str, db_session: Session):
        """Test that lastUpdated timestamp is recent."""
        from datetime import datetime, timedelta

        response = client.get(
            "/api/v1/admin/system/metrics",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Parse the timestamp (assuming ISO format)
        last_updated_str = data["lastUpdated"].replace("Z", "+00:00")
        last_updated = datetime.fromisoformat(last_updated_str)

        # Should be within the last 5 minutes (allowing for processing time)
        now = datetime.now(last_updated.tzinfo)
        time_diff = now - last_updated

        assert time_diff < timedelta(minutes=5), f"Metrics timestamp too old: {time_diff}"

    def test_admin_system_metrics_system_status_determination(self, admin_jwt_token: str, db_session: Session):
        """Test that system status is determined logically."""
        response = client.get(
            "/api/v1/admin/system/metrics",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        status = data["systemStatus"]

        # For a basic system with users and no errors, should be healthy
        # (This test may need adjustment based on actual business logic)
        if data["totalUsers"] > 0 and data["adminUsers"] > 0:
            # At minimum, should not be "error" status
            assert status in ["healthy", "warning"]


@pytest.fixture
def admin_jwt_token(db_session: Session) -> str:
    """Fixture to get JWT token for admin user."""
    return get_admin_jwt_token(db_session)


@pytest.fixture
def user_jwt_token(db_session: Session) -> str:
    """Fixture to get JWT token for regular user."""
    return get_user_jwt_token(db_session)
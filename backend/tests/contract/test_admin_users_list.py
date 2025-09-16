"""
Contract test for GET /api/v1/admin/users endpoint.

Tests the API contract as defined in admin-api.openapi.yaml:
- Response format matches AdminUserListItem schema
- Pagination parameters work correctly
- Role-based filtering functions
- Admin authentication is enforced
- HTTP status codes match specification
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.models.user import User
from src.models.user_role import UserRole
from tests.conftest import get_admin_jwt_token, get_user_jwt_token


client = TestClient(app)


class TestAdminUsersListContract:
    """Contract tests for admin users list endpoint."""

    def test_admin_users_list_success_response_structure(self, admin_jwt_token: str, db_session: Session):
        """Test successful response matches AdminUserListItem schema from contract."""
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Contract requires pagination structure
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data

        # Verify AdminUserListItem structure for each user
        for user in data["users"]:
            # Required fields per contract
            assert "id" in user
            assert "email" in user
            assert "role" in user
            assert "isActive" in user
            assert "createdAt" in user
            assert "portfolioCount" in user

            # Optional fields per contract
            assert "firstName" in user or user.get("firstName") is None
            assert "lastName" in user or user.get("lastName") is None
            assert "lastLoginAt" in user or user.get("lastLoginAt") is None

            # Validate field types and values
            assert isinstance(user["id"], str)
            assert isinstance(user["email"], str)
            assert user["role"] in ["admin", "user"]
            assert isinstance(user["isActive"], bool)
            assert isinstance(user["createdAt"], str)
            assert isinstance(user["portfolioCount"], int)
            assert user["portfolioCount"] >= 0

    def test_admin_users_list_pagination_contract(self, admin_jwt_token: str, db_session: Session):
        """Test pagination parameters work per contract specification."""
        # Test page parameter
        response = client.get(
            "/api/v1/admin/users?page=1&size=2",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert len(data["users"]) <= 2
        assert data["total"] >= 0
        assert data["pages"] >= 1

    def test_admin_users_list_role_filter_contract(self, admin_jwt_token: str, db_session: Session):
        """Test role filtering per contract specification."""
        # Test admin role filter
        response = client.get(
            "/api/v1/admin/users?role=admin",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # All returned users should have admin role
        for user in data["users"]:
            assert user["role"] == "admin"

        # Test user role filter
        response = client.get(
            "/api/v1/admin/users?role=user",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # All returned users should have user role
        for user in data["users"]:
            assert user["role"] == "user"

    def test_admin_users_list_active_filter_contract(self, admin_jwt_token: str, db_session: Session):
        """Test active status filtering per contract specification."""
        response = client.get(
            "/api/v1/admin/users?active=true",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # All returned users should be active
        for user in data["users"]:
            assert user["isActive"] is True

    def test_admin_users_list_unauthorized_access_contract(self, db_session: Session):
        """Test unauthorized access returns 401 per contract."""
        response = client.get("/api/v1/admin/users")

        assert response.status_code == 401
        data = response.json()

        # Contract specifies error response structure
        assert "error" in data
        assert "message" in data
        assert data["error"] == "unauthorized"
        assert data["message"] == "Authentication required"

    def test_admin_users_list_forbidden_access_contract(self, user_jwt_token: str, db_session: Session):
        """Test non-admin access returns 403 per contract."""
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {user_jwt_token}"}
        )

        assert response.status_code == 403
        data = response.json()

        # Contract specifies error response structure
        assert "error" in data
        assert "message" in data
        assert data["error"] == "forbidden"
        assert data["message"] == "Admin role required"

    def test_admin_users_list_pagination_bounds_contract(self, admin_jwt_token: str, db_session: Session):
        """Test pagination parameter validation per contract."""
        # Test invalid page (less than 1)
        response = client.get(
            "/api/v1/admin/users?page=0",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should return 422 for validation error
        assert response.status_code == 422

        # Test invalid size (greater than 100)
        response = client.get(
            "/api/v1/admin/users?size=101",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should return 422 for validation error
        assert response.status_code == 422

    def test_admin_users_list_portfolio_count_accuracy_contract(self, admin_jwt_token: str, db_session: Session):
        """Test that portfolioCount field is accurate per contract requirements."""
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify portfolio counts are not hardcoded and reflect actual data
        for user in data["users"]:
            user_id = user["id"]

            # Query actual portfolio count for this user
            from src.models.portfolio import Portfolio
            import uuid
            user_uuid = uuid.UUID(user_id)
            actual_count = db_session.query(Portfolio).filter(Portfolio.owner_id == user_uuid).count()

            # Contract requires accurate portfolio count
            assert user["portfolioCount"] == actual_count, f"Portfolio count mismatch for user {user_id}"


@pytest.fixture
def admin_jwt_token(db_session: Session) -> str:
    """Fixture to get JWT token for admin user."""
    return get_admin_jwt_token(db_session)


@pytest.fixture
def user_jwt_token(db_session: Session) -> str:
    """Fixture to get JWT token for regular user."""
    return get_user_jwt_token(db_session)
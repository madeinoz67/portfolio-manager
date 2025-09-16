"""
Contract test for GET /api/v1/admin/users/{user_id} endpoint.

Tests the API contract as defined in admin-api.openapi.yaml:
- Response format matches AdminUserDetails schema
- Includes portfolio information and asset totals
- Admin authentication is enforced
- HTTP status codes match specification
- Error handling for invalid user IDs
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.models.user import User
from src.models.user_role import UserRole
from tests.conftest import get_admin_jwt_token, get_user_jwt_token


client = TestClient(app)


class TestAdminUsersDetailContract:
    """Contract tests for admin user detail endpoint."""

    def test_admin_user_detail_success_response_structure(self, admin_jwt_token: str, db_session: Session):
        """Test successful response matches AdminUserDetails schema from contract."""
        # Get a user from the database
        user = db_session.query(User).filter(User.role == UserRole.USER).first()
        if not user:
            # Create a test user if none exists
            user = User(
                email="testuser@test.com",
                first_name="Test",
                last_name="User",
                password_hash="dummy_hash",
                role=UserRole.USER,
                is_active=True
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)

        response = client.get(
            f"/api/v1/admin/users/{user.id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Basic AdminUserListItem fields (inherited)
        assert "id" in data
        assert "email" in data
        assert "role" in data
        assert "isActive" in data
        assert "createdAt" in data
        assert "portfolioCount" in data

        # Optional fields per contract
        assert "firstName" in data or data.get("firstName") is None
        assert "lastName" in data or data.get("lastName") is None
        assert "lastLoginAt" in data or data.get("lastLoginAt") is None

        # Enhanced AdminUserDetails fields per contract
        assert "totalAssets" in data
        assert "portfolios" in data

        # Validate field types and values
        assert isinstance(data["id"], str)
        assert isinstance(data["email"], str)
        assert data["role"] in ["admin", "user"]
        assert isinstance(data["isActive"], bool)
        assert isinstance(data["createdAt"], str)
        assert isinstance(data["portfolioCount"], int)
        assert data["portfolioCount"] >= 0

        # Enhanced fields validation
        assert isinstance(data["totalAssets"], (int, float))
        assert data["totalAssets"] >= 0
        assert isinstance(data["portfolios"], list)

        # Validate portfolio structure
        for portfolio in data["portfolios"]:
            assert "id" in portfolio
            assert "name" in portfolio
            assert "value" in portfolio
            assert "lastUpdated" in portfolio

            assert isinstance(portfolio["id"], str)
            assert isinstance(portfolio["name"], str)
            assert isinstance(portfolio["value"], (int, float))
            assert portfolio["value"] >= 0
            assert isinstance(portfolio["lastUpdated"], str)

    def test_admin_user_detail_portfolio_count_accuracy(self, admin_jwt_token: str, db_session: Session):
        """Test that portfolioCount matches actual portfolios array length."""
        user = db_session.query(User).first()

        response = client.get(
            f"/api/v1/admin/users/{user.id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Portfolio count should match portfolios array length
        assert data["portfolioCount"] == len(data["portfolios"])

    def test_admin_user_detail_total_assets_calculation(self, admin_jwt_token: str, db_session: Session):
        """Test that totalAssets equals sum of all portfolio values."""
        user = db_session.query(User).first()

        response = client.get(
            f"/api/v1/admin/users/{user.id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Calculate expected total from portfolio values
        expected_total = sum(portfolio["value"] for portfolio in data["portfolios"])

        # Allow for small floating-point precision differences
        assert abs(data["totalAssets"] - expected_total) < 0.01

    def test_admin_user_detail_invalid_user_id_contract(self, admin_jwt_token: str, db_session: Session):
        """Test invalid user ID returns 404 per contract."""
        invalid_user_id = "00000000-0000-0000-0000-000000000000"

        response = client.get(
            f"/api/v1/admin/users/{invalid_user_id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 404
        data = response.json()

        # Contract specifies error response structure
        assert "error" in data
        assert "message" in data
        assert data["error"] == "not_found"
        assert data["message"] == "User not found"

    def test_admin_user_detail_malformed_user_id_contract(self, admin_jwt_token: str, db_session: Session):
        """Test malformed user ID returns validation error."""
        malformed_user_id = "not-a-uuid"

        response = client.get(
            f"/api/v1/admin/users/{malformed_user_id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should return 422 for validation error (malformed UUID)
        assert response.status_code == 422

    def test_admin_user_detail_unauthorized_access_contract(self, db_session: Session):
        """Test unauthorized access returns 401 per contract."""
        user = db_session.query(User).first()
        if not user:
            # Create a test user if none exists
            user = User(
                email="testuser@unauthorized.com",
                first_name="Test",
                last_name="User",
                password_hash="dummy_hash",
                role=UserRole.USER,
                is_active=True
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)

        response = client.get(f"/api/v1/admin/users/{user.id}")

        assert response.status_code == 401
        data = response.json()

        # Contract specifies error response structure
        assert "error" in data
        assert "message" in data
        assert data["error"] == "unauthorized"
        assert data["message"] == "Authentication required"

    def test_admin_user_detail_forbidden_access_contract(self, user_jwt_token: str, db_session: Session):
        """Test non-admin access returns 403 per contract."""
        user = db_session.query(User).first()

        response = client.get(
            f"/api/v1/admin/users/{user.id}",
            headers={"Authorization": f"Bearer {user_jwt_token}"}
        )

        assert response.status_code == 403
        data = response.json()

        # Contract specifies error response structure
        assert "error" in data
        assert "message" in data
        assert data["error"] == "forbidden"
        assert data["message"] == "Admin role required"

    def test_admin_user_detail_self_reference(self, admin_jwt_token: str, db_session: Session):
        """Test admin can view their own detailed information."""
        admin_user = db_session.query(User).filter(User.role == UserRole.ADMIN).first()

        response = client.get(
            f"/api/v1/admin/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(admin_user.id)
        assert data["email"] == admin_user.email
        assert data["role"] == "admin"


@pytest.fixture
def admin_jwt_token(db_session: Session) -> str:
    """Fixture to get JWT token for admin user."""
    return get_admin_jwt_token(db_session)


@pytest.fixture
def user_jwt_token(db_session: Session) -> str:
    """Fixture to get JWT token for regular user."""
    return get_user_jwt_token(db_session)
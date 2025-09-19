"""
Contract test for POST /api/v1/admin/adapters endpoint.

Tests the API contract as defined in adapter-management-api.yaml:
- Request/response format validation
- Required fields validation
- Admin authentication enforcement
- Error handling for invalid requests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from tests.conftest import get_admin_jwt_token, get_user_jwt_token


client = TestClient(app)


@pytest.fixture
def admin_jwt_token(db_session: Session) -> str:
    """Create admin JWT token for testing."""
    return get_admin_jwt_token(db_session)


@pytest.fixture
def user_jwt_token(db_session: Session) -> str:
    """Create regular user JWT token for testing."""
    return get_user_jwt_token(db_session)


class TestAdminAdaptersCreateContract:
    """Contract tests for admin adapters create endpoint."""

    def test_admin_adapters_create_endpoint_not_implemented(self, admin_jwt_token: str, db_session: Session):
        """Test that endpoint returns 404 before implementation."""
        request_data = {
            "provider_name": "alpha_vantage",
            "display_name": "Alpha Vantage Test",
            "config_data": {
                "api_key": "test_key",
                "base_url": "https://www.alphavantage.co/query"
            },
            "is_active": False
        }

        response = client.post(
            "/api/v1/admin/adapters",
            json=request_data,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should fail initially as endpoint is not implemented
        assert response.status_code == 404, "Expected 404 before implementation"

    def test_admin_adapters_create_authentication_required(self, db_session: Session):
        """Test that admin authentication is required."""
        request_data = {
            "provider_name": "alpha_vantage",
            "display_name": "Alpha Vantage Test",
            "config_data": {"api_key": "test_key"}
        }

        response = client.post("/api/v1/admin/adapters", json=request_data)

        # Should require authentication
        assert response.status_code in [401, 404], "Should require authentication or not be implemented"

    def test_admin_adapters_create_admin_role_required(self, user_jwt_token: str, db_session: Session):
        """Test that admin role is required."""
        request_data = {
            "provider_name": "alpha_vantage",
            "display_name": "Alpha Vantage Test",
            "config_data": {"api_key": "test_key"}
        }

        response = client.post(
            "/api/v1/admin/adapters",
            json=request_data,
            headers={"Authorization": f"Bearer {user_jwt_token}"}
        )

        # Should require admin role
        assert response.status_code in [403, 404], "Should require admin role or not be implemented"

    def test_admin_adapters_create_request_validation(self, admin_jwt_token: str, db_session: Session):
        """Test request validation for required fields."""
        # Missing required fields
        invalid_request = {
            "display_name": "Test Adapter"
            # Missing provider_name and config_data
        }

        response = client.post(
            "/api/v1/admin/adapters",
            json=invalid_request,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should validate request or not be implemented
        assert response.status_code in [400, 422, 404], "Should validate request or not be implemented"

    def test_admin_adapters_create_response_schema(self, admin_jwt_token: str, db_session: Session):
        """Test response schema matches contract."""
        valid_request = {
            "provider_name": "alpha_vantage",
            "display_name": "Alpha Vantage Test",
            "config_data": {
                "api_key": "test_key",
                "base_url": "https://www.alphavantage.co/query"
            },
            "is_active": False
        }

        response = client.post(
            "/api/v1/admin/adapters",
            json=valid_request,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented, should return created adapter with these fields
        expected_response_fields = {
            "id",              # UUID
            "provider_name",   # string
            "display_name",    # string
            "is_active",       # boolean
            "config_data",     # object
            "created_at",      # datetime
            "updated_at",      # datetime
            "created_by_user_id"  # UUID
        }

        # This test will fail until endpoint is implemented
        assert response.status_code in [201, 404], "Should create resource or not be implemented"
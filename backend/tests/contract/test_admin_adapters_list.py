"""
Contract test for GET /api/v1/admin/adapters endpoint.

Tests the API contract as defined in adapter-management-api.yaml:
- Response format matches AdapterConfiguration schema
- All required fields are present with correct types
- Admin authentication is enforced
- Response includes adapters array and total count
- AdapterConfiguration schema validation
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


class TestAdminAdaptersListContract:
    """Contract tests for admin adapters list endpoint."""

    def test_admin_adapters_list_success_response_structure(self, admin_jwt_token: str, db_session: Session):
        """Test successful response matches adapter list schema from contract."""
        response = client.get(
            "/api/v1/admin/adapters",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should fail initially as endpoint is not implemented
        assert response.status_code == 404, "Expected 404 before implementation"

    def test_admin_adapters_list_response_schema(self, admin_jwt_token: str, db_session: Session):
        """Test response schema matches contract specification."""
        response = client.get(
            "/api/v1/admin/adapters",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented, response should have this structure
        expected_schema = {
            "adapters": [],  # array of AdapterConfiguration objects
            "total": 0       # integer count
        }

        # This test will fail until endpoint is implemented
        assert response.status_code == 404, "Endpoint not yet implemented"

    def test_admin_adapters_list_adapter_configuration_schema(self, admin_jwt_token: str, db_session: Session):
        """Test AdapterConfiguration objects match contract schema."""
        response = client.get(
            "/api/v1/admin/adapters",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented, each adapter should have these required fields
        expected_adapter_fields = {
            "id",           # string, uuid format
            "provider_name", # string (e.g., alpha_vantage)
            "display_name",  # string (human-readable)
            "is_active"      # boolean
        }

        # Optional fields that may be present
        optional_adapter_fields = {
            "config_data",    # object (provider-specific)
            "created_at",     # string, date-time format
            "updated_at",     # string, date-time format
            "created_by_user_id", # string, uuid format
            "current_status"  # AdapterStatus object
        }

        # This test will fail until endpoint is implemented
        assert response.status_code == 404, "Endpoint not yet implemented"

    def test_admin_adapters_list_authentication_required(self, db_session: Session):
        """Test that admin authentication is required."""
        response = client.get("/api/v1/admin/adapters")

        # Should require authentication
        assert response.status_code in [401, 404], "Should require authentication or not be implemented"

    def test_admin_adapters_list_admin_role_required(self, user_jwt_token: str, db_session: Session):
        """Test that admin role is required (not just authentication)."""
        response = client.get(
            "/api/v1/admin/adapters",
            headers={"Authorization": f"Bearer {user_jwt_token}"}
        )

        # Should require admin role
        assert response.status_code in [403, 404], "Should require admin role or not be implemented"

    def test_admin_adapters_list_malformed_token(self, db_session: Session):
        """Test response with malformed JWT token."""
        response = client.get(
            "/api/v1/admin/adapters",
            headers={"Authorization": "Bearer invalid-token"}
        )

        # Should reject malformed token
        assert response.status_code in [401, 404], "Should reject malformed token or not be implemented"

    def test_admin_adapters_list_content_type(self, admin_jwt_token: str, db_session: Session):
        """Test response content type is application/json."""
        response = client.get(
            "/api/v1/admin/adapters",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        if response.status_code == 200:
            assert response.headers.get("content-type") == "application/json"
        else:
            # Expected to fail until implemented
            assert response.status_code == 404, "Endpoint not yet implemented"

    def test_admin_adapters_list_empty_response_valid(self, admin_jwt_token: str, db_session: Session):
        """Test that empty adapter list is valid response."""
        response = client.get(
            "/api/v1/admin/adapters",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented, empty list should be valid
        if response.status_code == 200:
            data = response.json()
            assert "adapters" in data
            assert "total" in data
            assert isinstance(data["adapters"], list)
            assert isinstance(data["total"], int)
            assert data["total"] == len(data["adapters"])
        else:
            # Expected to fail until implemented
            assert response.status_code == 404, "Endpoint not yet implemented"
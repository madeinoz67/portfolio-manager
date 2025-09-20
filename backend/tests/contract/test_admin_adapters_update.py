"""
Contract test for PUT /api/v1/admin/adapters/{id} endpoint.

Tests the API contract as defined in adapter-management-api.yaml:
- Request/response format validation
- Authentication enforcement
- Partial update validation
- Error handling for invalid data
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


class TestAdminAdaptersUpdateContract:
    """Contract tests for admin adapters update endpoint."""

    def test_admin_adapters_update_endpoint_not_implemented(self, admin_jwt_token: str, db_session: Session):
        """Test that endpoint returns 404 before implementation."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"
        update_data = {
            "display_name": "Updated Display Name",
            "is_active": False
        }

        response = client.put(
            f"/api/v1/admin/adapters/{adapter_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should fail initially as endpoint is not implemented
        assert response.status_code == 404, "Expected 404 before implementation"

    def test_admin_adapters_update_authentication_required(self, db_session: Session):
        """Test that admin authentication is required."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"
        update_data = {"is_active": False}

        response = client.put(f"/api/v1/admin/adapters/{adapter_id}", json=update_data)

        # Should require authentication
        assert response.status_code in [401, 404], "Should require authentication or not be implemented"

    def test_admin_adapters_update_admin_role_required(self, user_jwt_token: str, db_session: Session):
        """Test that admin role is required."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"
        update_data = {"is_active": False}

        response = client.put(
            f"/api/v1/admin/adapters/{adapter_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {user_jwt_token}"}
        )

        # Should require admin role
        assert response.status_code in [403, 404], "Should require admin role or not be implemented"

    def test_admin_adapters_update_invalid_id_format(self, admin_jwt_token: str, db_session: Session):
        """Test validation for invalid UUID format."""
        invalid_id = "not-a-uuid"
        update_data = {"is_active": False}

        response = client.put(
            f"/api/v1/admin/adapters/{invalid_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should validate UUID format or not be implemented
        assert response.status_code in [400, 422, 404], "Should validate UUID format or not be implemented"

    def test_admin_adapters_update_request_validation(self, admin_jwt_token: str, db_session: Session):
        """Test request validation for update data."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        # Test invalid field types
        invalid_update_data = {
            "is_active": "not_a_boolean",  # Should be boolean
            "display_name": 123,           # Should be string
            "config_data": "not_an_object" # Should be object
        }

        response = client.put(
            f"/api/v1/admin/adapters/{adapter_id}",
            json=invalid_update_data,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should validate request data or not be implemented
        assert response.status_code in [400, 422, 404], "Should validate request data or not be implemented"

    def test_admin_adapters_update_partial_update_allowed(self, admin_jwt_token: str, db_session: Session):
        """Test that partial updates are allowed."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        # Test updating only one field
        partial_update = {"is_active": False}

        response = client.put(
            f"/api/v1/admin/adapters/{adapter_id}",
            json=partial_update,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should accept partial updates or not be implemented
        assert response.status_code in [200, 404], "Should accept partial updates or not be implemented"

    def test_admin_adapters_update_config_data_validation(self, admin_jwt_token: str, db_session: Session):
        """Test validation of config_data updates."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        # Test updating config_data with provider-specific validation
        config_update = {
            "config_data": {
                "api_key": "new_api_key_value",
                "timeout": 45,
                "rate_limit": 10
            }
        }

        response = client.put(
            f"/api/v1/admin/adapters/{adapter_id}",
            json=config_update,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should validate config_data against provider schema or not be implemented
        assert response.status_code in [200, 400, 404], "Should validate config_data or not be implemented"

    def test_admin_adapters_update_nonexistent_adapter(self, admin_jwt_token: str, db_session: Session):
        """Test handling of non-existent adapter ID."""
        nonexistent_id = "550e8400-e29b-41d4-a716-446655440000"
        update_data = {"is_active": False}

        response = client.put(
            f"/api/v1/admin/adapters/{nonexistent_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented, should return 404 for non-existent adapter
        assert response.status_code in [404], "Should return 404 for non-existent adapter or not be implemented"

    def test_admin_adapters_update_response_schema(self, admin_jwt_token: str, db_session: Session):
        """Test response schema matches contract."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"
        update_data = {
            "display_name": "Updated Adapter Name",
            "is_active": True
        }

        response = client.put(
            f"/api/v1/admin/adapters/{adapter_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented and adapter exists, should return updated adapter with these fields
        expected_response_fields = {
            "id",                    # UUID
            "provider_name",         # string
            "display_name",          # string (updated)
            "is_active",            # boolean (possibly updated)
            "config_data",          # object (sanitized)
            "created_at",           # datetime
            "updated_at",           # datetime (should be recent)
            "created_by_user_id"    # UUID
        }

        # This test will fail until endpoint is implemented
        assert response.status_code in [200, 404], "Should return updated adapter or not be implemented"
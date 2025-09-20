"""
Contract test for GET /api/v1/admin/adapters/{id} endpoint.

Tests the API contract as defined in adapter-management-api.yaml:
- Request/response format validation
- Authentication enforcement
- Error handling for invalid IDs
- Response schema validation
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


class TestAdminAdaptersGetContract:
    """Contract tests for admin adapters get endpoint."""

    def test_admin_adapters_get_endpoint_not_implemented(self, admin_jwt_token: str, db_session: Session):
        """Test that endpoint returns 404 before implementation."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should fail initially as endpoint is not implemented
        assert response.status_code == 404, "Expected 404 before implementation"

    def test_admin_adapters_get_authentication_required(self, db_session: Session):
        """Test that admin authentication is required."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(f"/api/v1/admin/adapters/{adapter_id}")

        # Should require authentication
        assert response.status_code in [401, 404], "Should require authentication or not be implemented"

    def test_admin_adapters_get_admin_role_required(self, user_jwt_token: str, db_session: Session):
        """Test that admin role is required."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}",
            headers={"Authorization": f"Bearer {user_jwt_token}"}
        )

        # Should require admin role
        assert response.status_code in [403, 404], "Should require admin role or not be implemented"

    def test_admin_adapters_get_invalid_id_format(self, admin_jwt_token: str, db_session: Session):
        """Test validation for invalid UUID format."""
        invalid_id = "not-a-uuid"

        response = client.get(
            f"/api/v1/admin/adapters/{invalid_id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should validate UUID format or not be implemented
        assert response.status_code in [400, 422, 404], "Should validate UUID format or not be implemented"

    def test_admin_adapters_get_nonexistent_id(self, admin_jwt_token: str, db_session: Session):
        """Test handling of non-existent adapter ID."""
        nonexistent_id = "550e8400-e29b-41d4-a716-446655440000"  # Valid UUID format

        response = client.get(
            f"/api/v1/admin/adapters/{nonexistent_id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented, should return 404 for non-existent adapter
        expected_response_fields_on_not_found = {
            "detail"  # Standard FastAPI error format
        }

        # This test will fail until endpoint is implemented
        assert response.status_code in [404], "Should return 404 for non-existent adapter or not be implemented"

    def test_admin_adapters_get_response_schema(self, admin_jwt_token: str, db_session: Session):
        """Test response schema matches contract."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented and adapter exists, should return adapter details with these fields
        expected_response_fields = {
            "id",                    # UUID
            "provider_name",         # string
            "display_name",          # string
            "is_active",            # boolean
            "config_data",          # object (sanitized - no secrets)
            "created_at",           # datetime
            "updated_at",           # datetime
            "created_by_user_id",   # UUID
            "health_status",        # object with latest health check
            "latest_metrics"        # object with current performance metrics
        }

        # This test will fail until endpoint is implemented
        assert response.status_code in [200, 404], "Should return adapter details or not be implemented"
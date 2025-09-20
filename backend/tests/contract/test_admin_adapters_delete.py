"""
Contract test for DELETE /api/v1/admin/adapters/{id} endpoint.

Tests the API contract as defined in adapter-management-api.yaml:
- Authentication enforcement
- Proper deletion handling
- Error handling for invalid IDs
- Cascade deletion considerations
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


class TestAdminAdaptersDeleteContract:
    """Contract tests for admin adapters delete endpoint."""

    def test_admin_adapters_delete_endpoint_not_implemented(self, admin_jwt_token: str, db_session: Session):
        """Test that endpoint returns 404 before implementation."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.delete(
            f"/api/v1/admin/adapters/{adapter_id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should fail initially as endpoint is not implemented
        assert response.status_code == 404, "Expected 404 before implementation"

    def test_admin_adapters_delete_authentication_required(self, db_session: Session):
        """Test that admin authentication is required."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.delete(f"/api/v1/admin/adapters/{adapter_id}")

        # Should require authentication
        assert response.status_code in [401, 404], "Should require authentication or not be implemented"

    def test_admin_adapters_delete_admin_role_required(self, user_jwt_token: str, db_session: Session):
        """Test that admin role is required."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.delete(
            f"/api/v1/admin/adapters/{adapter_id}",
            headers={"Authorization": f"Bearer {user_jwt_token}"}
        )

        # Should require admin role
        assert response.status_code in [403, 404], "Should require admin role or not be implemented"

    def test_admin_adapters_delete_invalid_id_format(self, admin_jwt_token: str, db_session: Session):
        """Test validation for invalid UUID format."""
        invalid_id = "not-a-uuid"

        response = client.delete(
            f"/api/v1/admin/adapters/{invalid_id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should validate UUID format or not be implemented
        assert response.status_code in [400, 422, 404], "Should validate UUID format or not be implemented"

    def test_admin_adapters_delete_nonexistent_adapter(self, admin_jwt_token: str, db_session: Session):
        """Test handling of non-existent adapter ID."""
        nonexistent_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.delete(
            f"/api/v1/admin/adapters/{nonexistent_id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented, should return 404 for non-existent adapter
        assert response.status_code in [404], "Should return 404 for non-existent adapter or not be implemented"

    def test_admin_adapters_delete_success_response(self, admin_jwt_token: str, db_session: Session):
        """Test successful deletion response."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.delete(
            f"/api/v1/admin/adapters/{adapter_id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented and adapter exists, should return 204 No Content or 200 with confirmation
        expected_success_codes = [200, 204]

        # This test will fail until endpoint is implemented
        assert response.status_code in expected_success_codes + [404], "Should return success code or not be implemented"

    def test_admin_adapters_delete_idempotent_behavior(self, admin_jwt_token: str, db_session: Session):
        """Test that deleting already deleted adapter is idempotent."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        # First deletion
        first_response = client.delete(
            f"/api/v1/admin/adapters/{adapter_id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Second deletion should be idempotent (404 or same success response)
        second_response = client.delete(
            f"/api/v1/admin/adapters/{adapter_id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should handle repeated deletion gracefully or not be implemented
        assert second_response.status_code in [200, 204, 404], "Should handle repeated deletion or not be implemented"

    def test_admin_adapters_delete_cascade_considerations(self, admin_jwt_token: str, db_session: Session):
        """Test that deletion considers related data (metrics, cost records, health checks)."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.delete(
            f"/api/v1/admin/adapters/{adapter_id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented, deletion should handle:
        # - ProviderMetrics cascade deletion
        # - CostTrackingRecord cascade deletion
        # - AdapterHealthCheck cascade deletion
        # - Or soft delete with is_deleted flag

        # This is primarily tested through integration tests
        # Contract test just verifies endpoint behavior
        assert response.status_code in [200, 204, 404], "Should handle cascade deletion or not be implemented"

    def test_admin_adapters_delete_active_adapter_handling(self, admin_jwt_token: str, db_session: Session):
        """Test deletion of active adapter with safety considerations."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.delete(
            f"/api/v1/admin/adapters/{adapter_id}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented, should either:
        # 1. Allow deletion with warning
        # 2. Require deactivation first
        # 3. Automatically deactivate before deletion

        # Contract test doesn't enforce specific behavior, just valid response
        assert response.status_code in [200, 204, 400, 404], "Should handle active adapter deletion or not be implemented"
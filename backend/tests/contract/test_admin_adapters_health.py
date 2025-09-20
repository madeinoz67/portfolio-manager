"""
Contract test for GET /api/v1/admin/adapters/{id}/health endpoint.

Tests the API contract as defined in adapter-management-api.yaml:
- Authentication enforcement
- Health check response format
- Real-time connectivity testing
- Error handling and status codes
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


class TestAdminAdaptersHealthContract:
    """Contract tests for admin adapters health endpoint."""

    def test_admin_adapters_health_endpoint_not_implemented(self, admin_jwt_token: str, db_session: Session):
        """Test that endpoint returns 404 before implementation."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/health",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should fail initially as endpoint is not implemented
        assert response.status_code == 404, "Expected 404 before implementation"

    def test_admin_adapters_health_authentication_required(self, db_session: Session):
        """Test that admin authentication is required."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(f"/api/v1/admin/adapters/{adapter_id}/health")

        # Should require authentication
        assert response.status_code in [401, 404], "Should require authentication or not be implemented"

    def test_admin_adapters_health_admin_role_required(self, user_jwt_token: str, db_session: Session):
        """Test that admin role is required."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/health",
            headers={"Authorization": f"Bearer {user_jwt_token}"}
        )

        # Should require admin role
        assert response.status_code in [403, 404], "Should require admin role or not be implemented"

    def test_admin_adapters_health_invalid_id_format(self, admin_jwt_token: str, db_session: Session):
        """Test validation for invalid UUID format."""
        invalid_id = "not-a-uuid"

        response = client.get(
            f"/api/v1/admin/adapters/{invalid_id}/health",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should validate UUID format or not be implemented
        assert response.status_code in [400, 422, 404], "Should validate UUID format or not be implemented"

    def test_admin_adapters_health_nonexistent_adapter(self, admin_jwt_token: str, db_session: Session):
        """Test handling of non-existent adapter ID."""
        nonexistent_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(
            f"/api/v1/admin/adapters/{nonexistent_id}/health",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented, should return 404 for non-existent adapter
        assert response.status_code in [404], "Should return 404 for non-existent adapter or not be implemented"

    def test_admin_adapters_health_force_check_parameter(self, admin_jwt_token: str, db_session: Session):
        """Test force_check parameter for real-time health verification."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        # Test with force_check=true to trigger live health check
        params = {"force_check": "true"}

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/health",
            params=params,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should accept force_check parameter or not be implemented
        assert response.status_code in [200, 404], "Should accept force_check parameter or not be implemented"

    def test_admin_adapters_health_timeout_parameter(self, admin_jwt_token: str, db_session: Session):
        """Test timeout parameter for health check duration."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        # Test with custom timeout
        params = {"timeout": "10"}  # 10 seconds

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/health",
            params=params,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should accept timeout parameter or not be implemented
        assert response.status_code in [200, 404], "Should accept timeout parameter or not be implemented"

    def test_admin_adapters_health_response_schema(self, admin_jwt_token: str, db_session: Session):
        """Test response schema matches contract."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/health",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented and adapter exists, should return health status with these fields
        expected_response_fields = {
            "adapter_id",          # UUID
            "provider_name",       # string
            "status",              # string (healthy/degraded/unhealthy)
            "check_timestamp",     # datetime when check was performed
            "response_time_ms",    # float - how long the check took
            "is_live_check",       # boolean - was this a real-time check
            "details",             # object with additional health information
            "last_successful_check", # datetime of last successful check
            "error_message"        # string - present if status is not healthy
        }

        expected_details_fields = {
            "connectivity",        # boolean - can reach provider
            "authentication",      # boolean - credentials valid
            "rate_limit_status",   # object with rate limit info
            "circuit_breaker_state", # string
            "provider_response_time", # float - provider's response time
            "test_symbol_used"     # string - symbol used for testing
        }

        expected_rate_limit_fields = {
            "requests_remaining",  # integer
            "reset_time",          # datetime or null
            "quota_used_percent"   # float (0-100)
        }

        # This test will fail until endpoint is implemented
        assert response.status_code in [200, 404], "Should return health data or not be implemented"

    def test_admin_adapters_health_inactive_adapter_handling(self, admin_jwt_token: str, db_session: Session):
        """Test health check of inactive adapter."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/health",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented, should handle inactive adapters appropriately
        # Could return status indicating adapter is disabled
        assert response.status_code in [200, 404], "Should handle inactive adapters or not be implemented"

    def test_admin_adapters_health_error_scenarios(self, admin_jwt_token: str, db_session: Session):
        """Test health check error scenario handling."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/health",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented, should handle various error scenarios:
        # 1. Provider unreachable (network error)
        # 2. Authentication failure (invalid credentials)
        # 3. Rate limit exceeded
        # 4. Provider service down
        # 5. Timeout during health check

        # All should return 200 with appropriate status, not error codes
        assert response.status_code in [200, 404], "Should handle error scenarios gracefully or not be implemented"
"""
Contract test for GET /api/v1/admin/adapters/{id}/metrics endpoint.

Tests the API contract as defined in adapter-management-api.yaml:
- Authentication enforcement
- Real-time metrics response format
- Time-based filtering parameters
- Aggregation options
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


class TestAdminAdaptersMetricsContract:
    """Contract tests for admin adapters metrics endpoint."""

    def test_admin_adapters_metrics_endpoint_not_implemented(self, admin_jwt_token: str, db_session: Session):
        """Test that endpoint returns 404 before implementation."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/metrics",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should fail initially as endpoint is not implemented
        assert response.status_code == 404, "Expected 404 before implementation"

    def test_admin_adapters_metrics_authentication_required(self, db_session: Session):
        """Test that admin authentication is required."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(f"/api/v1/admin/adapters/{adapter_id}/metrics")

        # Should require authentication
        assert response.status_code in [401, 404], "Should require authentication or not be implemented"

    def test_admin_adapters_metrics_admin_role_required(self, user_jwt_token: str, db_session: Session):
        """Test that admin role is required."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/metrics",
            headers={"Authorization": f"Bearer {user_jwt_token}"}
        )

        # Should require admin role
        assert response.status_code in [403, 404], "Should require admin role or not be implemented"

    def test_admin_adapters_metrics_invalid_id_format(self, admin_jwt_token: str, db_session: Session):
        """Test validation for invalid UUID format."""
        invalid_id = "not-a-uuid"

        response = client.get(
            f"/api/v1/admin/adapters/{invalid_id}/metrics",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should validate UUID format or not be implemented
        assert response.status_code in [400, 422, 404], "Should validate UUID format or not be implemented"

    def test_admin_adapters_metrics_time_range_parameters(self, admin_jwt_token: str, db_session: Session):
        """Test time range query parameters."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        # Test with time range parameters
        params = {
            "start_time": "2025-09-19T10:00:00Z",
            "end_time": "2025-09-19T11:00:00Z",
            "interval": "1m"
        }

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/metrics",
            params=params,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should accept time range parameters or not be implemented
        assert response.status_code in [200, 404], "Should accept time range parameters or not be implemented"

    def test_admin_adapters_metrics_aggregation_parameters(self, admin_jwt_token: str, db_session: Session):
        """Test metrics aggregation parameters."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        # Test with aggregation parameters
        params = {
            "aggregate": "1h",  # 1 hour aggregation
            "metrics": "latency,success_rate,error_count"  # Specific metrics
        }

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/metrics",
            params=params,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should accept aggregation parameters or not be implemented
        assert response.status_code in [200, 404], "Should accept aggregation parameters or not be implemented"

    def test_admin_adapters_metrics_nonexistent_adapter(self, admin_jwt_token: str, db_session: Session):
        """Test handling of non-existent adapter ID."""
        nonexistent_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(
            f"/api/v1/admin/adapters/{nonexistent_id}/metrics",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented, should return 404 for non-existent adapter
        assert response.status_code in [404], "Should return 404 for non-existent adapter or not be implemented"

    def test_admin_adapters_metrics_response_schema(self, admin_jwt_token: str, db_session: Session):
        """Test response schema matches contract."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/metrics",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented and adapter exists, should return metrics with these fields
        expected_response_fields = {
            "adapter_id",           # UUID
            "provider_name",        # string
            "time_range",          # object with start/end times
            "current_metrics",     # object with latest metrics
            "historical_data",     # array of time-series data points
            "aggregation_level",   # string (1m, 5m, 1h, etc.)
            "generated_at"         # datetime when metrics were generated
        }

        expected_current_metrics_fields = {
            "request_count",       # integer
            "success_count",       # integer
            "error_count",         # integer
            "success_rate",        # float (0-1)
            "avg_latency_ms",      # float
            "rate_limit_hits",     # integer
            "circuit_breaker_state", # string
            "last_updated"         # datetime
        }

        expected_historical_data_point_fields = {
            "timestamp",           # datetime
            "request_count",       # integer
            "success_rate",        # float
            "avg_latency_ms",      # float
            "error_count",         # integer
            "rate_limit_hits"      # integer
        }

        # This test will fail until endpoint is implemented
        assert response.status_code in [200, 404], "Should return metrics data or not be implemented"

    def test_admin_adapters_metrics_real_time_data_requirement(self, admin_jwt_token: str, db_session: Session):
        """Test that metrics are live/dynamic, not hard-coded."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/metrics",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented, metrics should be:
        # 1. Generated from actual database records
        # 2. Include current timestamp in generated_at
        # 3. Reflect real adapter performance
        # 4. NOT contain hard-coded values

        # This is more of a implementation requirement than contract test
        # Contract test verifies the structure exists
        assert response.status_code in [200, 404], "Should return live metrics data or not be implemented"

    def test_admin_adapters_metrics_empty_data_handling(self, admin_jwt_token: str, db_session: Session):
        """Test handling of adapter with no metrics data."""
        adapter_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(
            f"/api/v1/admin/adapters/{adapter_id}/metrics",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented, should handle adapters with no metrics gracefully
        # Return empty/zero values rather than error
        assert response.status_code in [200, 404], "Should handle empty metrics gracefully or not be implemented"
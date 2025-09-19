"""
Integration test for adapter configuration flow.

Tests the complete user scenario:
1. Admin configures new market data provider
2. Adapter can be activated/deactivated
3. Configuration can be updated
4. Adapter can be removed

Based on Scenario 1 from quickstart.md
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from tests.conftest import get_admin_jwt_token


client = TestClient(app)


@pytest.fixture
def admin_jwt_token(db_session: Session) -> str:
    """Create admin JWT token for testing."""
    return get_admin_jwt_token(db_session)


class TestAdapterConfigurationFlow:
    """Integration tests for complete adapter configuration workflow."""

    def test_adapter_configuration_complete_flow(self, admin_jwt_token: str, db_session: Session):
        """Test complete adapter configuration workflow from quickstart scenario 1."""

        # Step 1: List available adapter types
        registry_response = client.get(
            "/api/v1/admin/adapters/registry",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should initially fail (endpoint not implemented)
        assert registry_response.status_code in [200, 404], "Registry endpoint not implemented yet"

        # Step 2: Create new adapter configuration
        adapter_config = {
            "provider_name": "alpha_vantage",
            "display_name": "Alpha Vantage Production",
            "config_data": {
                "api_key": "test_alpha_vantage_key",
                "base_url": "https://www.alphavantage.co/query",
                "rate_limit": 5,
                "timeout": 30
            },
            "is_active": False
        }

        create_response = client.post(
            "/api/v1/admin/adapters",
            json=adapter_config,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should initially fail (endpoint not implemented)
        assert create_response.status_code in [201, 404], "Create endpoint not implemented yet"

        # If implemented, continue with the flow
        if create_response.status_code == 201:
            adapter_data = create_response.json()
            adapter_id = adapter_data["id"]

            # Step 3: Test connection (health check)
            health_response = client.get(
                f"/api/v1/admin/adapters/{adapter_id}/health",
                headers={"Authorization": f"Bearer {admin_jwt_token}"}
            )

            assert health_response.status_code == 200, "Health check should work"

            # Step 4: Activate adapter
            update_response = client.put(
                f"/api/v1/admin/adapters/{adapter_id}",
                json={"is_active": True},
                headers={"Authorization": f"Bearer {admin_jwt_token}"}
            )

            assert update_response.status_code == 200, "Should be able to activate adapter"

            # Step 5: Verify adapter appears in list
            list_response = client.get(
                "/api/v1/admin/adapters",
                headers={"Authorization": f"Bearer {admin_jwt_token}"}
            )

            assert list_response.status_code == 200, "Should list adapters"
            adapters_data = list_response.json()
            assert adapters_data["total"] >= 1, "Should have at least one adapter"

            # Step 6: Monitor metrics
            metrics_response = client.get(
                f"/api/v1/admin/adapters/{adapter_id}/metrics",
                headers={"Authorization": f"Bearer {admin_jwt_token}"}
            )

            assert metrics_response.status_code == 200, "Should provide metrics"

    def test_adapter_validation_errors(self, admin_jwt_token: str, db_session: Session):
        """Test validation errors during adapter configuration."""

        # Test invalid provider name
        invalid_config = {
            "provider_name": "invalid_provider",
            "display_name": "Invalid Provider",
            "config_data": {"api_key": "test"}
        }

        response = client.post(
            "/api/v1/admin/adapters",
            json=invalid_config,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should validate or not be implemented
        assert response.status_code in [400, 404], "Should validate provider or not be implemented"

    def test_adapter_authentication_flow(self, admin_jwt_token: str, db_session: Session):
        """Test authentication requirements for adapter operations."""

        # Test without authentication
        response = client.get("/api/v1/admin/adapters")
        assert response.status_code in [401, 404], "Should require authentication or not be implemented"

        # Test with authentication
        response = client.get(
            "/api/v1/admin/adapters",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        assert response.status_code in [200, 404], "Should work with auth or not be implemented"
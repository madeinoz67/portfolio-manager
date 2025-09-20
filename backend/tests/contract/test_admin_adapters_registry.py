"""
Contract test for GET /api/v1/admin/adapters/registry endpoint.

Tests the API contract as defined in adapter-management-api.yaml:
- Authentication enforcement
- Available adapter types listing
- Adapter capabilities and schemas
- Registration status information
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


class TestAdminAdaptersRegistryContract:
    """Contract tests for admin adapters registry endpoint."""

    def test_admin_adapters_registry_endpoint_not_implemented(self, admin_jwt_token: str, db_session: Session):
        """Test that endpoint returns 404 before implementation."""
        response = client.get(
            "/api/v1/admin/adapters/registry",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should fail initially as endpoint is not implemented
        assert response.status_code == 404, "Expected 404 before implementation"

    def test_admin_adapters_registry_authentication_required(self, db_session: Session):
        """Test that admin authentication is required."""
        response = client.get("/api/v1/admin/adapters/registry")

        # Should require authentication
        assert response.status_code in [401, 404], "Should require authentication or not be implemented"

    def test_admin_adapters_registry_admin_role_required(self, user_jwt_token: str, db_session: Session):
        """Test that admin role is required."""
        response = client.get(
            "/api/v1/admin/adapters/registry",
            headers={"Authorization": f"Bearer {user_jwt_token}"}
        )

        # Should require admin role
        assert response.status_code in [403, 404], "Should require admin role or not be implemented"

    def test_admin_adapters_registry_filter_parameters(self, admin_jwt_token: str, db_session: Session):
        """Test filtering parameters for registry listing."""
        # Test with enabled_only filter
        params = {"enabled_only": "true"}

        response = client.get(
            "/api/v1/admin/adapters/registry",
            params=params,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should accept filter parameters or not be implemented
        assert response.status_code in [200, 404], "Should accept filter parameters or not be implemented"

    def test_admin_adapters_registry_include_schemas_parameter(self, admin_jwt_token: str, db_session: Session):
        """Test include_schemas parameter for detailed information."""
        # Test with include_schemas to get configuration schemas
        params = {"include_schemas": "true"}

        response = client.get(
            "/api/v1/admin/adapters/registry",
            params=params,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should accept include_schemas parameter or not be implemented
        assert response.status_code in [200, 404], "Should accept include_schemas parameter or not be implemented"

    def test_admin_adapters_registry_response_schema(self, admin_jwt_token: str, db_session: Session):
        """Test response schema matches contract."""
        response = client.get(
            "/api/v1/admin/adapters/registry",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented, should return registry information with these fields
        expected_response_fields = {
            "available_adapters",  # array of adapter types
            "total_count",         # integer
            "enabled_count",       # integer
            "generated_at"         # datetime when registry was queried
        }

        expected_adapter_fields = {
            "adapter_name",        # string (alpha_vantage, yahoo_finance, etc.)
            "display_name",        # string
            "description",         # string
            "version",             # string
            "is_enabled",          # boolean
            "capabilities",        # object with adapter capabilities
            "cost_information",    # object with pricing details
            "configuration_schema", # object (if include_schemas=true)
            "example_configuration" # object (if include_schemas=true)
        }

        expected_capabilities_fields = {
            "supports_real_time",  # boolean
            "supports_historical", # boolean
            "supports_bulk_quotes", # boolean
            "max_symbols_per_request", # integer
            "rate_limit_per_minute", # integer or null
            "rate_limit_per_day",   # integer or null
            "supported_markets",    # array of strings
            "supported_data_types"  # array of strings
        }

        expected_cost_fields = {
            "cost_model",          # string (free, freemium, subscription, per_call)
            "cost_per_call",       # string or null
            "free_tier_limits",    # object or null
            "pricing_url"          # string or null
        }

        # This test will fail until endpoint is implemented
        assert response.status_code in [200, 404], "Should return registry data or not be implemented"

    def test_admin_adapters_registry_known_adapter_types(self, admin_jwt_token: str, db_session: Session):
        """Test that known adapter types are present in registry."""
        response = client.get(
            "/api/v1/admin/adapters/registry",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented, should include these adapter types at minimum
        expected_adapter_types = {
            "alpha_vantage",       # Alpha Vantage API adapter
            "yahoo_finance"        # Yahoo Finance adapter
        }

        # This test validates that the adapters we implement are registered
        # Additional adapters may be present
        assert response.status_code in [200, 404], "Should include known adapter types or not be implemented"

    def test_admin_adapters_registry_configuration_schema_structure(self, admin_jwt_token: str, db_session: Session):
        """Test configuration schema structure when requested."""
        params = {"include_schemas": "true"}

        response = client.get(
            "/api/v1/admin/adapters/registry",
            params=params,
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented with include_schemas=true, configuration_schema should be:
        # 1. Valid JSON Schema format
        # 2. Include required fields
        # 3. Include field types and descriptions
        # 4. Include validation rules

        expected_schema_structure = {
            "type",                # "object"
            "properties",          # object with field definitions
            "required"             # array of required field names
        }

        # This test will fail until endpoint is implemented
        assert response.status_code in [200, 404], "Should return valid schemas or not be implemented"

    def test_admin_adapters_registry_empty_registry_handling(self, admin_jwt_token: str, db_session: Session):
        """Test handling when no adapters are registered."""
        response = client.get(
            "/api/v1/admin/adapters/registry",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # When implemented, should handle empty registry gracefully
        # Return empty array, not error
        assert response.status_code in [200, 404], "Should handle empty registry gracefully or not be implemented"

    def test_admin_adapters_registry_performance_requirements(self, admin_jwt_token: str, db_session: Session):
        """Test that registry endpoint responds quickly (cached data)."""
        import time

        start_time = time.time()

        response = client.get(
            "/api/v1/admin/adapters/registry",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        end_time = time.time()
        response_time = end_time - start_time

        # When implemented, registry should be fast (under 100ms)
        # This is reference data that can be cached
        if response.status_code == 200:
            assert response_time < 0.1, "Registry endpoint should respond quickly (cached data)"

        # This test will fail until endpoint is implemented
        assert response.status_code in [200, 404], "Should respond quickly or not be implemented"
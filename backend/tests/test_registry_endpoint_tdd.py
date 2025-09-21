"""
TDD Test for Registry Endpoint Serialization Issue

This test reproduces the "unhashable type: 'RegisteredProvider'" error
and validates the fix for the registry endpoint serialization problem.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch, MagicMock

from src.main import app
from src.services.adapters.registry import get_provider_registry
# ProviderRegistryResponse schema not created yet - test raw response structure


class TestRegistryEndpointSerialization:
    """Test class for registry endpoint serialization issues."""

    @pytest.fixture
    def admin_client(self, test_admin_user, test_db):
        """Create authenticated admin client."""
        with TestClient(app) as client:
            # Login admin user
            login_response = client.post(
                "/api/v1/auth/login",
                json={"email": test_admin_user.email, "password": "admin123"}
            )
            assert login_response.status_code == status.HTTP_200_OK
            token = login_response.json()["access_token"]

            # Set authorization header
            client.headers = {"Authorization": f"Bearer {token}"}
            yield client

    def test_registry_endpoint_serialization_error_reproduction(self, admin_client):
        """
        TDD Test: Reproduce the 'unhashable type: RegisteredProvider' error.

        This test should initially FAIL with the serialization error,
        then PASS after the fix is implemented.
        """
        # Act: Call the registry endpoint
        response = admin_client.get("/api/v1/admin/adapters/registry")

        # Assert: Should return 200 OK without serialization errors
        # Initially this will fail with 500 Internal Server Error
        assert response.status_code == status.HTTP_200_OK, \
            f"Registry endpoint failed with status {response.status_code}: {response.text}"

        # Validate response structure
        data = response.json()
        assert "available_adapters" in data
        assert "total_adapters" in data
        assert isinstance(data["available_adapters"], list)
        assert isinstance(data["total_adapters"], int)

        # Validate that providers are returned
        assert data["total_adapters"] > 0, "Should have at least one registered provider"

        # Validate adapter structure
        for adapter in data["available_adapters"]:
            assert "name" in adapter
            assert "display_name" in adapter
            assert "description" in adapter
            assert "capabilities" in adapter
            assert "is_available" in adapter

            # Validate capabilities structure
            capabilities = adapter["capabilities"]
            assert isinstance(capabilities, dict)

            # These fields should be serializable (not complex objects)
            for key, value in capabilities.items():
                assert self._is_json_serializable(value), \
                    f"Capability {key} with value {value} is not JSON serializable"

    def test_registry_endpoint_handles_provider_objects(self, admin_client):
        """
        Test that the registry endpoint properly converts RegisteredProvider objects
        to JSON-serializable dictionaries.
        """
        # Mock the provider registry to return complex objects that might cause issues
        with patch('src.api.admin_adapters.get_provider_registry') as mock_registry:
            # Create a mock provider that might have unhashable objects
            mock_provider_info = MagicMock()
            mock_provider_info.display_name = "Test Provider"
            mock_provider_info.description = "Test Description"
            mock_provider_info.adapter_class = MagicMock()

            # Mock capabilities that could be problematic
            mock_adapter = MagicMock()
            mock_capabilities = MagicMock()
            mock_capabilities.supports_bulk_quotes = True
            mock_capabilities.rate_limit_per_minute = 60
            mock_capabilities.supported_data_types = ["quotes", "historical"]
            mock_capabilities.requires_api_key = True
            mock_adapter.capabilities = mock_capabilities
            mock_adapter.get_configuration_schema.return_value = {"api_key": "string"}
            mock_adapter.get_example_configuration.return_value = {"api_key": "test_key"}

            mock_provider_info.adapter_class.return_value = mock_adapter

            # Setup registry mock
            mock_registry_instance = MagicMock()
            mock_registry_instance.list_providers.return_value = ["test_provider"]
            mock_registry_instance.get_provider_info.return_value = mock_provider_info
            mock_registry.return_value = mock_registry_instance

            # Act: Call endpoint
            response = admin_client.get("/api/v1/admin/adapters/registry")

            # Assert: Should succeed even with complex mock objects
            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["total_adapters"] == 1
            assert len(data["available_adapters"]) == 1

            adapter = data["available_adapters"][0]
            assert adapter["name"] == "test_provider"
            assert adapter["display_name"] == "Test Provider"
            assert adapter["description"] == "Test Description"

    def test_registry_response_schema_validation(self, admin_client):
        """
        Test that the registry response matches the expected structure.
        """
        # Act
        response = admin_client.get("/api/v1/admin/adapters/registry")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Validate response structure without Pydantic schema
        assert 'available_adapters' in data
        assert 'total_adapters' in data
        assert isinstance(data['available_adapters'], list)
        assert isinstance(data['total_adapters'], int)

    def _is_json_serializable(self, obj):
        """Check if an object is JSON serializable."""
        import json
        try:
            json.dumps(obj)
            return True
        except (TypeError, ValueError):
            return False

    def test_registry_endpoint_error_handling(self, admin_client):
        """
        Test that registry endpoint handles errors gracefully without exposing
        internal implementation details.
        """
        with patch('src.api.admin_adapters.get_provider_registry') as mock_registry:
            # Force an exception to test error handling
            mock_registry.side_effect = Exception("Registry unavailable")

            # Act
            response = admin_client.get("/api/v1/admin/adapters/registry")

            # Assert: Should return 500 with generic error message
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            error_data = response.json()
            assert error_data["detail"] == "Internal server error"
            # Should not expose internal error details
            assert "Registry unavailable" not in error_data["detail"]
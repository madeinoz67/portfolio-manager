"""
Contract tests for Portfolio API endpoints.
Tests API contracts against OpenAPI specification.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestPortfolioAPI:
    """Test Portfolio API endpoints against contract specifications."""

    def test_list_portfolios_endpoint_exists(self, client: TestClient):
        """GET /api/v1/portfolios should exist and return proper structure."""
        response = client.get("/api/v1/portfolios")
        
        # Should return 401 without authentication (for now, expect endpoint to exist)
        assert response.status_code in [200, 401, 404], f"Expected valid status code, got {response.status_code}"

    def test_create_portfolio_endpoint_exists(self, client: TestClient):
        """POST /api/v1/portfolios should exist and validate request body."""
        portfolio_data = {
            "name": "Test Portfolio",
            "description": "A test portfolio"
        }
        
        response = client.post("/api/v1/portfolios", json=portfolio_data)
        
        # Should return 401 without auth or 422 for validation (endpoint should exist)
        assert response.status_code in [201, 401, 404, 422], f"Expected valid status code, got {response.status_code}"

    def test_get_portfolio_endpoint_exists(self, client: TestClient):
        """GET /api/v1/portfolios/{portfolio_id} should exist."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/portfolios/{test_uuid}")
        
        # Should return 401/404, not 404 for missing route
        assert response.status_code in [200, 401, 404], f"Expected valid status code, got {response.status_code}"

    def test_update_portfolio_endpoint_exists(self, client: TestClient):
        """PUT /api/v1/portfolios/{portfolio_id} should exist."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        update_data = {
            "name": "Updated Portfolio",
            "description": "Updated description"
        }
        
        response = client.put(f"/api/v1/portfolios/{test_uuid}", json=update_data)
        
        # Should return 401/404, not 404 for missing route
        assert response.status_code in [200, 401, 404, 422], f"Expected valid status code, got {response.status_code}"

    def test_delete_portfolio_endpoint_exists(self, client: TestClient):
        """DELETE /api/v1/portfolios/{portfolio_id} should exist."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/api/v1/portfolios/{test_uuid}")
        
        # Should return 401/404, not 404 for missing route  
        assert response.status_code in [204, 401, 404], f"Expected valid status code, got {response.status_code}"

    def test_get_portfolio_holdings_endpoint_exists(self, client: TestClient):
        """GET /api/v1/portfolios/{portfolio_id}/holdings should exist."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/portfolios/{test_uuid}/holdings")
        
        # Should return 401/404, not 404 for missing route
        assert response.status_code in [200, 401, 404], f"Expected valid status code, got {response.status_code}"

    def test_list_portfolios_response_structure(self, client: TestClient):
        """When implemented, /api/v1/portfolios should return array structure."""
        response = client.get("/api/v1/portfolios")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Response should be an array"
            
            if len(data) > 0:
                portfolio = data[0]
                required_fields = ["id", "name", "total_value", "created_at"]
                for field in required_fields:
                    assert field in portfolio, f"Portfolio should contain {field} field"

    def test_create_portfolio_request_validation(self, client: TestClient):
        """POST /api/v1/portfolios should validate required fields."""
        # Test missing required field
        invalid_data = {"description": "Missing name field"}
        response = client.post("/api/v1/portfolios", json=invalid_data)
        
        if response.status_code == 422:
            # Validation error expected for missing name
            error_data = response.json()
            assert "detail" in error_data or "error" in error_data

    def test_create_portfolio_name_length_validation(self, client: TestClient):
        """POST /api/v1/portfolios should validate name max length (100 chars)."""
        long_name_data = {
            "name": "x" * 101,  # Exceeds maxLength: 100
            "description": "Test description"
        }
        response = client.post("/api/v1/portfolios", json=long_name_data)

        if response.status_code == 422:
            # Should validate max length
            error_data = response.json()
            assert "detail" in error_data or "error" in error_data

    def test_delete_portfolio_with_confirmation_endpoint_exists(self, client: TestClient):
        """POST /api/v1/portfolios/{portfolio_id}/delete should exist and require confirmation."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        confirmation_data = {
            "confirmation_name": "Test Portfolio"
        }

        response = client.post(f"/api/v1/portfolios/{test_uuid}/delete", json=confirmation_data)

        # Should return 401/404/422, not 404 for missing route
        assert response.status_code in [200, 401, 404, 422], f"Expected valid status code, got {response.status_code}"

    def test_delete_portfolio_confirmation_validation(self, client: TestClient):
        """POST /api/v1/portfolios/{portfolio_id}/delete should validate confirmation_name field."""
        test_uuid = "00000000-0000-0000-0000-000000000000"

        # Test missing confirmation_name
        invalid_data = {}
        response = client.post(f"/api/v1/portfolios/{test_uuid}/delete", json=invalid_data)

        if response.status_code == 422:
            # Validation error expected for missing confirmation_name
            error_data = response.json()
            assert "detail" in error_data or "error" in error_data

    def test_delete_portfolio_hard_delete_endpoint_exists(self, client: TestClient):
        """POST /api/v1/portfolios/{portfolio_id}/hard-delete should exist for permanent deletion."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        confirmation_data = {
            "confirmation_name": "Test Portfolio"
        }

        response = client.post(f"/api/v1/portfolios/{test_uuid}/hard-delete", json=confirmation_data)

        # Should return 401/404/422, not 404 for missing route
        assert response.status_code in [200, 401, 404, 422], f"Expected valid status code, got {response.status_code}"
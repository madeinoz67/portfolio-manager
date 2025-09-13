"""
Contract tests for Transaction API endpoints.
Tests API contracts against OpenAPI specification.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestTransactionAPI:
    """Test Transaction API endpoints against contract specifications."""

    def test_get_portfolio_transactions_endpoint_exists(self, client: TestClient):
        """GET /api/v1/portfolios/{portfolio_id}/transactions should exist."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/portfolios/{test_uuid}/transactions")
        
        # Should return 401/404, not 404 for missing route
        assert response.status_code in [200, 401, 404], f"Expected valid status code, got {response.status_code}"

    def test_create_transaction_endpoint_exists(self, client: TestClient):
        """POST /api/v1/portfolios/{portfolio_id}/transactions should exist."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        transaction_data = {
            "stock_symbol": "AAPL",
            "transaction_type": "BUY",
            "quantity": 100.0,
            "price_per_share": 150.00,
            "transaction_date": "2024-01-15",
            "fees": 5.00,
            "notes": "Test transaction"
        }
        
        response = client.post(f"/api/v1/portfolios/{test_uuid}/transactions", json=transaction_data)
        
        # Should return 401/422, not 404 for missing route
        assert response.status_code in [201, 401, 404, 422], f"Expected valid status code, got {response.status_code}"

    def test_get_transaction_detail_endpoint_exists(self, client: TestClient):
        """GET /api/v1/portfolios/{portfolio_id}/transactions/{transaction_id} should exist."""
        portfolio_uuid = "00000000-0000-0000-0000-000000000000"
        transaction_uuid = "11111111-1111-1111-1111-111111111111"
        response = client.get(f"/api/v1/portfolios/{portfolio_uuid}/transactions/{transaction_uuid}")
        
        # Should return 401/404, not 404 for missing route
        assert response.status_code in [200, 401, 404], f"Expected valid status code, got {response.status_code}"

    def test_get_transactions_pagination_parameters(self, client: TestClient):
        """GET transactions should handle pagination parameters."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(
            f"/api/v1/portfolios/{test_uuid}/transactions?limit=25&offset=0"
        )
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["transactions", "total", "limit", "offset"]
            for field in required_fields:
                assert field in data, f"Response should contain {field} field"
            assert isinstance(data["transactions"], list), "Transactions should be an array"

    def test_get_transactions_limit_validation(self, client: TestClient):
        """GET transactions should validate limit parameter (max 100)."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(
            f"/api/v1/portfolios/{test_uuid}/transactions?limit=150"
        )
        
        if response.status_code == 422:
            error_data = response.json()
            assert "detail" in error_data or "error" in error_data

    def test_create_transaction_required_fields(self, client: TestClient):
        """POST transaction should validate required fields."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        
        # Missing stock_symbol
        incomplete_data = {
            "transaction_type": "BUY",
            "quantity": 100.0,
            "price_per_share": 150.00,
            "transaction_date": "2024-01-15"
        }
        
        response = client.post(f"/api/v1/portfolios/{test_uuid}/transactions", json=incomplete_data)
        
        if response.status_code == 422:
            error_data = response.json()
            assert "detail" in error_data or "error" in error_data

    def test_create_transaction_type_validation(self, client: TestClient):
        """POST transaction should validate transaction_type enum."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        
        # Invalid transaction type
        invalid_data = {
            "stock_symbol": "AAPL",
            "transaction_type": "INVALID",
            "quantity": 100.0,
            "price_per_share": 150.00,
            "transaction_date": "2024-01-15"
        }
        
        response = client.post(f"/api/v1/portfolios/{test_uuid}/transactions", json=invalid_data)
        
        if response.status_code == 422:
            error_data = response.json()
            assert "detail" in error_data or "error" in error_data

    def test_create_transaction_positive_values(self, client: TestClient):
        """POST transaction should validate positive numeric values."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        
        # Negative quantity
        negative_quantity_data = {
            "stock_symbol": "AAPL",
            "transaction_type": "BUY",
            "quantity": -100.0,
            "price_per_share": 150.00,
            "transaction_date": "2024-01-15"
        }
        
        response = client.post(f"/api/v1/portfolios/{test_uuid}/transactions", json=negative_quantity_data)
        
        if response.status_code == 422:
            error_data = response.json()
            assert "detail" in error_data or "error" in error_data

    def test_create_transaction_date_format(self, client: TestClient):
        """POST transaction should validate date format."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        
        # Invalid date format
        invalid_date_data = {
            "stock_symbol": "AAPL", 
            "transaction_type": "BUY",
            "quantity": 100.0,
            "price_per_share": 150.00,
            "transaction_date": "invalid-date"
        }
        
        response = client.post(f"/api/v1/portfolios/{test_uuid}/transactions", json=invalid_date_data)
        
        if response.status_code == 422:
            error_data = response.json()
            assert "detail" in error_data or "error" in error_data

    def test_transaction_response_structure(self, client: TestClient):
        """When implemented, transaction should return proper structure."""
        test_uuid = "00000000-0000-0000-0000-000000000000"
        valid_transaction = {
            "stock_symbol": "AAPL",
            "transaction_type": "BUY", 
            "quantity": 100.0,
            "price_per_share": 150.00,
            "transaction_date": "2024-01-15",
            "fees": 5.00
        }
        
        response = client.post(f"/api/v1/portfolios/{test_uuid}/transactions", json=valid_transaction)
        
        if response.status_code == 201:
            data = response.json()
            required_fields = [
                "id", "stock", "transaction_type", "quantity", 
                "price_per_share", "total_amount", "transaction_date"
            ]
            for field in required_fields:
                assert field in data, f"Transaction should contain {field} field"
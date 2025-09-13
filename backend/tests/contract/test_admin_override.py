"""
Contract tests for POST /api/v1/admin/market-data/override endpoint.

These tests verify the API contract for administrative data overrides.
They MUST FAIL until the admin_market_data_router is implemented.
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from src.main import app


class TestAdminOverrideContract:
    """Contract tests for admin data override endpoint."""

    def test_override_endpoint_exists(self, client: TestClient, valid_jwt_token: str):
        """Test that the override endpoint exists and accepts requests."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        payload = {
            "symbol": "AAPL",
            "price": "150.25",
            "reason": "Market closure - setting end of day price",
            "duration_minutes": 60
        }
        
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=payload)
        
        # Should return 200 for successful override
        assert response.status_code == 200
        
        # Should return JSON content
        assert response.headers["content-type"] == "application/json"

    def test_override_requires_authentication(self, client: TestClient):
        """Test that override endpoint requires valid authentication."""
        # This test MUST FAIL until the endpoint is implemented
        
        payload = {
            "symbol": "AAPL",
            "price": "150.25",
            "reason": "Test without auth",
            "duration_minutes": 60
        }
        
        response = client.post("/api/v1/admin/market-data/override", json=payload)
        
        assert response.status_code == 401

    def test_override_request_validation(self, client: TestClient, valid_jwt_token: str):
        """Test that request payload is properly validated."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Test missing required fields
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json={})
        assert response.status_code == 422  # Validation error
        
        # Test missing symbol
        invalid_payload = {
            "price": "150.25",
            "reason": "Test missing symbol",
            "duration_minutes": 60
        }
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=invalid_payload)
        assert response.status_code == 422
        
        # Test missing price
        invalid_payload = {
            "symbol": "AAPL",
            "reason": "Test missing price",
            "duration_minutes": 60
        }
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=invalid_payload)
        assert response.status_code == 422
        
        # Test missing reason
        invalid_payload = {
            "symbol": "AAPL",
            "price": "150.25",
            "duration_minutes": 60
        }
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=invalid_payload)
        assert response.status_code == 422

    def test_override_symbol_validation(self, client: TestClient, valid_jwt_token: str):
        """Test that symbol field is properly validated."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Test empty symbol
        invalid_payload = {
            "symbol": "",
            "price": "150.25",
            "reason": "Test empty symbol",
            "duration_minutes": 60
        }
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=invalid_payload)
        assert response.status_code == 422
        
        # Test invalid symbol format
        invalid_payload = {
            "symbol": "invalid-symbol-123!@#",
            "price": "150.25",
            "reason": "Test invalid symbol",
            "duration_minutes": 60
        }
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=invalid_payload)
        assert response.status_code == 422
        
        # Test valid symbol formats
        valid_symbols = ["AAPL", "GOOGL", "TSLA", "BRK.A", "CBA.AX"]
        for symbol in valid_symbols:
            valid_payload = {
                "symbol": symbol,
                "price": "150.25",
                "reason": f"Test valid symbol {symbol}",
                "duration_minutes": 60
            }
            response = client.post("/api/v1/admin/market-data/override", headers=headers, json=valid_payload)
            assert response.status_code == 200

    def test_override_price_validation(self, client: TestClient, valid_jwt_token: str):
        """Test that price field is properly validated."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Test negative price
        invalid_payload = {
            "symbol": "AAPL",
            "price": "-10.50",
            "reason": "Test negative price",
            "duration_minutes": 60
        }
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=invalid_payload)
        assert response.status_code == 422
        
        # Test zero price
        invalid_payload = {
            "symbol": "AAPL",
            "price": "0.00",
            "reason": "Test zero price",
            "duration_minutes": 60
        }
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=invalid_payload)
        assert response.status_code == 422
        
        # Test invalid price format
        invalid_payload = {
            "symbol": "AAPL",
            "price": "not-a-number",
            "reason": "Test invalid price format",
            "duration_minutes": 60
        }
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=invalid_payload)
        assert response.status_code == 422
        
        # Test valid price formats
        valid_prices = ["150.25", "1.00", "999.99", "1234.5678"]
        for price in valid_prices:
            valid_payload = {
                "symbol": "AAPL",
                "price": price,
                "reason": f"Test valid price {price}",
                "duration_minutes": 60
            }
            response = client.post("/api/v1/admin/market-data/override", headers=headers, json=valid_payload)
            assert response.status_code == 200

    def test_override_duration_validation(self, client: TestClient, valid_jwt_token: str):
        """Test that duration field is properly validated."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Test negative duration
        invalid_payload = {
            "symbol": "AAPL",
            "price": "150.25",
            "reason": "Test negative duration",
            "duration_minutes": -30
        }
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=invalid_payload)
        assert response.status_code == 422
        
        # Test zero duration (should be valid - immediate expiry)
        valid_payload = {
            "symbol": "AAPL",
            "price": "150.25",
            "reason": "Test zero duration",
            "duration_minutes": 0
        }
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=valid_payload)
        assert response.status_code == 200
        
        # Test very long duration (should be limited)
        invalid_payload = {
            "symbol": "AAPL",
            "price": "150.25",
            "reason": "Test excessive duration",
            "duration_minutes": 100000
        }
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=invalid_payload)
        assert response.status_code == 422

    def test_override_response_structure(self, client: TestClient, valid_jwt_token: str):
        """Test that response has correct structure."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        payload = {
            "symbol": "AAPL",
            "price": "175.50",
            "reason": "Emergency price correction due to system error",
            "duration_minutes": 120
        }
        
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required response fields
        assert "success" in data
        assert "override_id" in data
        assert "symbol" in data
        assert "override_price" in data
        assert "previous_price" in data
        assert "effective_time" in data
        assert "expires_at" in data
        assert "admin_user" in data
        assert "reason" in data
        assert "status" in data
        
        # Verify data types
        assert isinstance(data["success"], bool)
        assert isinstance(data["override_id"], str)
        assert isinstance(data["symbol"], str)
        assert isinstance(data["override_price"], str)
        assert isinstance(data["effective_time"], str)
        assert isinstance(data["expires_at"], str)
        assert isinstance(data["admin_user"], str)
        assert isinstance(data["reason"], str)
        assert isinstance(data["status"], str)
        
        # Verify values
        assert data["success"] is True
        assert data["symbol"] == "AAPL"
        assert data["override_price"] == "175.50"
        assert data["reason"] == "Emergency price correction due to system error"
        assert data["status"] in ["active", "pending", "expired"]

    def test_override_reason_validation(self, client: TestClient, valid_jwt_token: str):
        """Test that reason field is properly validated."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Test empty reason
        invalid_payload = {
            "symbol": "AAPL",
            "price": "150.25",
            "reason": "",
            "duration_minutes": 60
        }
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=invalid_payload)
        assert response.status_code == 422
        
        # Test very short reason
        invalid_payload = {
            "symbol": "AAPL",
            "price": "150.25",
            "reason": "x",
            "duration_minutes": 60
        }
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=invalid_payload)
        assert response.status_code == 422
        
        # Test reasonable reason length
        valid_payload = {
            "symbol": "AAPL",
            "price": "150.25",
            "reason": "Market anomaly detected, setting corrected price",
            "duration_minutes": 60
        }
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=valid_payload)
        assert response.status_code == 200

    def test_override_timestamp_format(self, client: TestClient, valid_jwt_token: str):
        """Test that timestamps follow ISO 8601 format."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        payload = {
            "symbol": "GOOGL",
            "price": "2500.00",
            "reason": "Testing timestamp format",
            "duration_minutes": 90
        }
        
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify timestamp formats (ISO 8601)
        from datetime import datetime
        datetime.fromisoformat(data["effective_time"].replace("Z", "+00:00"))
        datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))

    def test_override_expiry_calculation(self, client: TestClient, valid_jwt_token: str):
        """Test that expiry time is correctly calculated."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        payload = {
            "symbol": "TSLA",
            "price": "800.00",
            "reason": "Testing expiry calculation",
            "duration_minutes": 30
        }
        
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify expiry is calculated correctly
        from datetime import datetime, timedelta
        effective_time = datetime.fromisoformat(data["effective_time"].replace("Z", "+00:00"))
        expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
        
        # Should be 30 minutes later (allowing small tolerance for processing time)
        expected_expiry = effective_time + timedelta(minutes=30)
        time_diff = abs((expires_at - expected_expiry).total_seconds())
        assert time_diff < 60  # Within 1 minute tolerance

    def test_override_admin_authorization(self, client: TestClient):
        """Test that only admin users can create overrides."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": "Bearer non_admin_token"}
        
        payload = {
            "symbol": "AAPL",
            "price": "150.25",
            "reason": "Test admin authorization",
            "duration_minutes": 60
        }
        
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=payload)
        
        # Should return 401 (unauthorized) or 403 (forbidden)
        assert response.status_code in [401, 403]

    def test_override_duplicate_handling(self, client: TestClient, valid_jwt_token: str):
        """Test handling of duplicate overrides for same symbol."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Create first override
        payload1 = {
            "symbol": "MSFT",
            "price": "300.00",
            "reason": "First override",
            "duration_minutes": 60
        }
        response1 = client.post("/api/v1/admin/market-data/override", headers=headers, json=payload1)
        assert response1.status_code == 200
        
        # Create second override for same symbol
        payload2 = {
            "symbol": "MSFT",
            "price": "305.00",
            "reason": "Second override - should replace first",
            "duration_minutes": 30
        }
        response2 = client.post("/api/v1/admin/market-data/override", headers=headers, json=payload2)
        assert response2.status_code == 200
        
        data2 = response2.json()
        
        # Should succeed and provide new override
        assert data2["success"] is True
        assert data2["override_price"] == "305.00"

    def test_override_price_precision(self, client: TestClient, valid_jwt_token: str):
        """Test that price precision is maintained."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        payload = {
            "symbol": "AAPL",
            "price": "123.4567",
            "reason": "Testing price precision",
            "duration_minutes": 60
        }
        
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify price precision is maintained
        assert data["override_price"] == "123.4567"
        
        # Should be convertible to Decimal for precision checking
        price_decimal = Decimal(data["override_price"])
        assert price_decimal == Decimal("123.4567")

    def test_override_audit_trail(self, client: TestClient, valid_jwt_token: str):
        """Test that overrides are properly logged for audit."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        payload = {
            "symbol": "NVDA",
            "price": "450.00",
            "reason": "Audit trail test - correcting erroneous price feed",
            "duration_minutes": 45
        }
        
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        
        # Response should include audit information
        assert data["admin_user"] is not None
        assert data["reason"] == payload["reason"]
        assert data["effective_time"] is not None
        assert data["override_id"] is not None
        
        # Admin user should be identifiable (not empty)
        assert len(data["admin_user"]) > 0
        
        # Override ID should be unique identifier
        assert len(data["override_id"]) > 0

    def test_override_immediate_effect(self, client: TestClient, valid_jwt_token: str):
        """Test that overrides take effect immediately."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Create override with zero duration (immediate expiry)
        payload = {
            "symbol": "AMD",
            "price": "95.00",
            "reason": "Testing immediate effect",
            "duration_minutes": 0
        }
        
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        
        # Should succeed even with zero duration
        assert data["success"] is True
        assert data["override_price"] == "95.00"
        
        # Effective time and expires at should be very close or same
        from datetime import datetime
        effective_time = datetime.fromisoformat(data["effective_time"].replace("Z", "+00:00"))
        expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
        
        time_diff = (expires_at - effective_time).total_seconds()
        assert time_diff <= 60  # Should expire within a minute

    def test_override_previous_price_capture(self, client: TestClient, valid_jwt_token: str):
        """Test that previous price is captured for rollback."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        payload = {
            "symbol": "AAPL",
            "price": "200.00",
            "reason": "Testing previous price capture",
            "duration_minutes": 60
        }
        
        response = client.post("/api/v1/admin/market-data/override", headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        
        # Should include previous price (if available)
        if data["previous_price"] is not None:
            # Previous price should be a valid decimal string
            previous_price = Decimal(data["previous_price"])
            assert previous_price > Decimal("0")
        
        # Previous price can be None if no previous data exists
        assert data["previous_price"] is None or isinstance(data["previous_price"], str)
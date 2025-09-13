"""
Contract tests for DELETE /api/v1/admin/market-data/override/{override_id} endpoint.

These tests verify the API contract for removing administrative data overrides.
They MUST FAIL until the admin_market_data_router is implemented.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


class TestAdminOverrideDeleteContract:
    """Contract tests for admin override deletion endpoint."""

    def test_override_delete_endpoint_exists(self, client: TestClient, valid_jwt_token: str):
        """Test that the override delete endpoint exists and accepts requests."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        override_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = client.delete(f"/api/v1/admin/market-data/override/{override_id}", headers=headers)
        
        # Should return 200 for successful deletion or 404 if not found
        assert response.status_code in [200, 404]
        
        # Should return JSON content
        assert response.headers["content-type"] == "application/json"

    def test_override_delete_requires_authentication(self, client: TestClient):
        """Test that override delete endpoint requires valid authentication."""
        # This test MUST FAIL until the endpoint is implemented
        
        override_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = client.delete(f"/api/v1/admin/market-data/override/{override_id}")
        
        assert response.status_code == 401

    def test_override_delete_invalid_uuid(self, client: TestClient, valid_jwt_token: str):
        """Test that invalid UUID format returns appropriate error."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        invalid_id = "not-a-valid-uuid"
        
        response = client.delete(f"/api/v1/admin/market-data/override/{invalid_id}", headers=headers)
        
        # Should return 422 for invalid UUID format
        assert response.status_code == 422

    def test_override_delete_nonexistent_id(self, client: TestClient, valid_jwt_token: str):
        """Test that nonexistent override ID returns 404."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        nonexistent_id = "987fcdeb-51a2-43d1-b789-123456789abc"
        
        response = client.delete(f"/api/v1/admin/market-data/override/{nonexistent_id}", headers=headers)
        
        # Should return 404 for nonexistent override
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data or "error" in data

    def test_override_delete_success_response(self, client: TestClient, valid_jwt_token: str):
        """Test successful deletion response structure."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # First create an override to delete
        create_payload = {
            "symbol": "AAPL",
            "price": "150.00",
            "reason": "Creating override for deletion test",
            "duration_minutes": 120
        }
        
        create_response = client.post("/api/v1/admin/market-data/override", headers=headers, json=create_payload)
        assert create_response.status_code == 200
        
        create_data = create_response.json()
        override_id = create_data["override_id"]
        
        # Now delete the override
        delete_response = client.delete(f"/api/v1/admin/market-data/override/{override_id}", headers=headers)
        assert delete_response.status_code == 200
        
        delete_data = delete_response.json()
        
        # Verify required response fields
        assert "success" in delete_data
        assert "override_id" in delete_data
        assert "symbol" in delete_data
        assert "previous_price" in delete_data
        assert "removed_at" in delete_data
        assert "admin_user" in delete_data
        assert "reason" in delete_data
        
        # Verify data types
        assert isinstance(delete_data["success"], bool)
        assert isinstance(delete_data["override_id"], str)
        assert isinstance(delete_data["symbol"], str)
        assert isinstance(delete_data["removed_at"], str)
        assert isinstance(delete_data["admin_user"], str)
        
        # Verify values
        assert delete_data["success"] is True
        assert delete_data["override_id"] == override_id
        assert delete_data["symbol"] == "AAPL"

    def test_override_delete_with_reason(self, client: TestClient, valid_jwt_token: str):
        """Test deletion with optional reason parameter."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Create override
        create_payload = {
            "symbol": "GOOGL",
            "price": "2500.00",
            "reason": "Override for reason deletion test",
            "duration_minutes": 60
        }
        
        create_response = client.post("/api/v1/admin/market-data/override", headers=headers, json=create_payload)
        assert create_response.status_code == 200
        override_id = create_response.json()["override_id"]
        
        # Delete with reason
        deletion_reason = "Market correction no longer needed"
        delete_response = client.delete(
            f"/api/v1/admin/market-data/override/{override_id}?reason={deletion_reason}",
            headers=headers
        )
        
        assert delete_response.status_code == 200
        
        delete_data = delete_response.json()
        assert delete_data["reason"] == deletion_reason

    def test_override_delete_timestamp_format(self, client: TestClient, valid_jwt_token: str):
        """Test that timestamps follow ISO 8601 format."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Create override
        create_payload = {
            "symbol": "TSLA",
            "price": "800.00",
            "reason": "Override for timestamp test",
            "duration_minutes": 30
        }
        
        create_response = client.post("/api/v1/admin/market-data/override", headers=headers, json=create_payload)
        assert create_response.status_code == 200
        override_id = create_response.json()["override_id"]
        
        # Delete override
        delete_response = client.delete(f"/api/v1/admin/market-data/override/{override_id}", headers=headers)
        assert delete_response.status_code == 200
        
        delete_data = delete_response.json()
        
        # Verify timestamp format (ISO 8601)
        from datetime import datetime
        datetime.fromisoformat(delete_data["removed_at"].replace("Z", "+00:00"))

    def test_override_delete_admin_authorization(self, client: TestClient):
        """Test that only admin users can delete overrides."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": "Bearer non_admin_token"}
        override_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = client.delete(f"/api/v1/admin/market-data/override/{override_id}", headers=headers)
        
        # Should return 401 (unauthorized) or 403 (forbidden)
        assert response.status_code in [401, 403]

    def test_override_delete_already_expired(self, client: TestClient, valid_jwt_token: str):
        """Test deletion of already expired override."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Create override with very short duration
        create_payload = {
            "symbol": "NVDA",
            "price": "450.00",
            "reason": "Short-lived override for expiry test",
            "duration_minutes": 0  # Immediate expiry
        }
        
        create_response = client.post("/api/v1/admin/market-data/override", headers=headers, json=create_payload)
        assert create_response.status_code == 200
        override_id = create_response.json()["override_id"]
        
        # Wait a moment for expiry (in real implementation)
        # Then attempt deletion
        delete_response = client.delete(f"/api/v1/admin/market-data/override/{override_id}", headers=headers)
        
        # Should handle expired overrides gracefully
        assert delete_response.status_code in [200, 404, 410]  # 410 = Gone
        
        if delete_response.status_code == 200:
            delete_data = delete_response.json()
            assert delete_data["success"] is True

    def test_override_delete_price_restoration(self, client: TestClient, valid_jwt_token: str):
        """Test that original price is restored after deletion."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Create override
        create_payload = {
            "symbol": "AMD",
            "price": "100.00",
            "reason": "Override for price restoration test",
            "duration_minutes": 60
        }
        
        create_response = client.post("/api/v1/admin/market-data/override", headers=headers, json=create_payload)
        assert create_response.status_code == 200
        
        create_data = create_response.json()
        override_id = create_data["override_id"]
        original_price = create_data["previous_price"]
        
        # Delete override
        delete_response = client.delete(f"/api/v1/admin/market-data/override/{override_id}", headers=headers)
        assert delete_response.status_code == 200
        
        delete_data = delete_response.json()
        
        # Should indicate restoration to previous price
        if original_price is not None:
            assert delete_data["previous_price"] == original_price

    def test_override_delete_audit_trail(self, client: TestClient, valid_jwt_token: str):
        """Test that deletions are properly logged for audit."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Create override
        create_payload = {
            "symbol": "INTC",
            "price": "60.00",
            "reason": "Override for audit test",
            "duration_minutes": 90
        }
        
        create_response = client.post("/api/v1/admin/market-data/override", headers=headers, json=create_payload)
        assert create_response.status_code == 200
        override_id = create_response.json()["override_id"]
        
        # Delete with audit reason
        audit_reason = "Manual removal due to market correction"
        delete_response = client.delete(
            f"/api/v1/admin/market-data/override/{override_id}?reason={audit_reason}",
            headers=headers
        )
        assert delete_response.status_code == 200
        
        delete_data = delete_response.json()
        
        # Response should include audit information
        assert delete_data["admin_user"] is not None
        assert delete_data["reason"] == audit_reason
        assert delete_data["removed_at"] is not None
        assert delete_data["override_id"] == override_id
        
        # Admin user should be identifiable
        assert len(delete_data["admin_user"]) > 0

    def test_override_delete_double_deletion(self, client: TestClient, valid_jwt_token: str):
        """Test that deleting already deleted override returns appropriate error."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Create override
        create_payload = {
            "symbol": "CRM",
            "price": "200.00",
            "reason": "Override for double deletion test",
            "duration_minutes": 60
        }
        
        create_response = client.post("/api/v1/admin/market-data/override", headers=headers, json=create_payload)
        assert create_response.status_code == 200
        override_id = create_response.json()["override_id"]
        
        # First deletion
        delete_response1 = client.delete(f"/api/v1/admin/market-data/override/{override_id}", headers=headers)
        assert delete_response1.status_code == 200
        
        # Second deletion attempt
        delete_response2 = client.delete(f"/api/v1/admin/market-data/override/{override_id}", headers=headers)
        
        # Should return 404 (not found) or 410 (gone)
        assert delete_response2.status_code in [404, 410]

    def test_override_delete_unauthorized_user(self, client: TestClient):
        """Test deletion with invalid token."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": "Bearer invalid_token"}
        override_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = client.delete(f"/api/v1/admin/market-data/override/{override_id}", headers=headers)
        
        assert response.status_code == 401

    def test_override_delete_concurrent_requests(self, client: TestClient, valid_jwt_token: str):
        """Test handling of concurrent deletion requests."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Create override
        create_payload = {
            "symbol": "ORCL",
            "price": "80.00",
            "reason": "Override for concurrency test",
            "duration_minutes": 60
        }
        
        create_response = client.post("/api/v1/admin/market-data/override", headers=headers, json=create_payload)
        assert create_response.status_code == 200
        override_id = create_response.json()["override_id"]
        
        # Simulate concurrent deletion attempts
        delete_response1 = client.delete(f"/api/v1/admin/market-data/override/{override_id}", headers=headers)
        delete_response2 = client.delete(f"/api/v1/admin/market-data/override/{override_id}", headers=headers)
        
        # One should succeed, one should fail
        status_codes = [delete_response1.status_code, delete_response2.status_code]
        assert 200 in status_codes
        assert any(code in [404, 410] for code in status_codes)

    def test_override_delete_path_parameter_validation(self, client: TestClient, valid_jwt_token: str):
        """Test various invalid path parameters."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        invalid_ids = [
            "",  # Empty
            "123",  # Too short
            "not-uuid-format",  # Invalid format
            "123e4567-e89b-12d3-a456-42661417400X",  # Invalid character
            "123E4567-E89B-12D3-A456-426614174000",  # Uppercase (should be handled)
        ]
        
        for invalid_id in invalid_ids:
            response = client.delete(f"/api/v1/admin/market-data/override/{invalid_id}", headers=headers)
            
            # Should return validation error or not found
            assert response.status_code in [404, 422]

    def test_override_delete_effect_on_system(self, client: TestClient, valid_jwt_token: str):
        """Test that deletion affects system state appropriately."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Create override
        create_payload = {
            "symbol": "MSFT",
            "price": "300.00",
            "reason": "Override for system effect test",
            "duration_minutes": 60
        }
        
        create_response = client.post("/api/v1/admin/market-data/override", headers=headers, json=create_payload)
        assert create_response.status_code == 200
        override_id = create_response.json()["override_id"]
        
        # Delete override
        delete_response = client.delete(f"/api/v1/admin/market-data/override/{override_id}", headers=headers)
        assert delete_response.status_code == 200
        
        delete_data = delete_response.json()
        
        # Deletion should be immediate and affect system state
        assert delete_data["success"] is True
        
        # System should reflect the change immediately
        from datetime import datetime
        removed_at = datetime.fromisoformat(delete_data["removed_at"].replace("Z", "+00:00"))
        now = datetime.now(removed_at.tzinfo)
        
        # Removal timestamp should be recent (within last minute)
        time_diff = abs((now - removed_at).total_seconds())
        assert time_diff < 60
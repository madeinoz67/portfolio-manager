"""
Contract tests for POST /api/v1/admin/poll-intervals endpoint.

These tests verify the API contract for creating poll interval configurations.
They MUST FAIL until the admin_market_data_router is implemented.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


class TestAdminPollIntervalsCreateContract:
    """Contract tests for admin poll intervals creation endpoint."""

    def test_create_poll_interval_endpoint_exists(self, client: TestClient, valid_jwt_token: str):
        """Test that the create poll interval endpoint exists and accepts requests."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {
            "Authorization": f"Bearer {valid_jwt_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "interval_minutes": 10,
            "reason": "Test poll interval creation"
        }
        
        response = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload)
        
        # Should return 201 for successful creation
        assert response.status_code == 201
        
        # Should return JSON content
        assert response.headers["content-type"] == "application/json"

    def test_create_poll_interval_requires_authentication(self, client: TestClient):
        """Test that create poll interval endpoint requires valid authentication."""
        # This test MUST FAIL until the endpoint is implemented
        
        payload = {
            "interval_minutes": 10,
            "reason": "Test without auth"
        }
        
        response = client.post("/api/v1/admin/poll-intervals", json=payload)
        
        assert response.status_code == 401

    def test_create_poll_interval_response_structure(self, client: TestClient, valid_jwt_token: str):
        """Test that create poll interval endpoint returns correct response structure."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {
            "Authorization": f"Bearer {valid_jwt_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "interval_minutes": 15,
            "reason": "Testing response structure"
        }
        
        response = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload)
        assert response.status_code == 201
        
        data = response.json()
        
        # Verify required response fields
        assert "id" in data
        assert "interval_minutes" in data
        assert "reason" in data
        assert "created_at" in data
        assert "created_by" in data
        assert "is_active" in data
        
        # Verify data types
        assert isinstance(data["id"], str)
        assert isinstance(data["interval_minutes"], int)
        assert isinstance(data["reason"], str)
        assert isinstance(data["created_at"], str)
        assert isinstance(data["created_by"], str)
        assert isinstance(data["is_active"], bool)
        
        # Verify values match request
        assert data["interval_minutes"] == payload["interval_minutes"]
        assert data["reason"] == payload["reason"]
        assert data["is_active"] is True  # New intervals should be active

    def test_create_poll_interval_id_format(self, client: TestClient, valid_jwt_token: str):
        """Test that created poll interval ID follows UUID format."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {
            "Authorization": f"Bearer {valid_jwt_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "interval_minutes": 20,
            "reason": "Testing UUID format"
        }
        
        response = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload)
        assert response.status_code == 201
        
        data = response.json()
        
        # Verify UUID format
        import uuid
        uuid.UUID(data["id"])  # Should not raise exception for valid UUID

    def test_create_poll_interval_timestamp_format(self, client: TestClient, valid_jwt_token: str):
        """Test that created poll interval timestamps follow ISO 8601 format."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {
            "Authorization": f"Bearer {valid_jwt_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "interval_minutes": 25,
            "reason": "Testing timestamp format"
        }
        
        response = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload)
        assert response.status_code == 201
        
        data = response.json()
        
        # Verify timestamp format (ISO 8601)
        from datetime import datetime
        datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))

    def test_create_poll_interval_validation_required_fields(self, client: TestClient, valid_jwt_token: str):
        """Test that required fields are validated."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {
            "Authorization": f"Bearer {valid_jwt_token}",
            "Content-Type": "application/json"
        }
        
        # Test missing interval_minutes
        payload_missing_interval = {"reason": "Missing interval"}
        response = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload_missing_interval)
        assert response.status_code == 422
        
        # Test missing reason
        payload_missing_reason = {"interval_minutes": 30}
        response = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload_missing_reason)
        assert response.status_code == 422
        
        # Test empty payload
        response = client.post("/api/v1/admin/poll-intervals", headers=headers, json={})
        assert response.status_code == 422

    def test_create_poll_interval_validation_interval_range(self, client: TestClient, valid_jwt_token: str):
        """Test that interval_minutes is validated for reasonable ranges."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {
            "Authorization": f"Bearer {valid_jwt_token}",
            "Content-Type": "application/json"
        }
        
        # Test interval too small (less than 1 minute)
        payload_too_small = {
            "interval_minutes": 0,
            "reason": "Testing minimum interval"
        }
        response = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload_too_small)
        assert response.status_code == 422
        
        # Test negative interval
        payload_negative = {
            "interval_minutes": -5,
            "reason": "Testing negative interval"
        }
        response = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload_negative)
        assert response.status_code == 422
        
        # Test interval too large (more than 24 hours)
        payload_too_large = {
            "interval_minutes": 1500,  # 25 hours
            "reason": "Testing maximum interval"
        }
        response = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload_too_large)
        assert response.status_code == 422

    def test_create_poll_interval_validation_reason_length(self, client: TestClient, valid_jwt_token: str):
        """Test that reason field is validated for length."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {
            "Authorization": f"Bearer {valid_jwt_token}",
            "Content-Type": "application/json"
        }
        
        # Test empty reason
        payload_empty_reason = {
            "interval_minutes": 15,
            "reason": ""
        }
        response = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload_empty_reason)
        assert response.status_code == 422
        
        # Test reason too long (more than 500 characters)
        payload_long_reason = {
            "interval_minutes": 15,
            "reason": "a" * 501
        }
        response = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload_long_reason)
        assert response.status_code == 422

    def test_create_poll_interval_deactivates_previous(self, client: TestClient, valid_jwt_token: str):
        """Test that creating a new poll interval deactivates the previous one."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {
            "Authorization": f"Bearer {valid_jwt_token}",
            "Content-Type": "application/json"
        }
        
        # Create first interval
        payload1 = {
            "interval_minutes": 10,
            "reason": "First interval"
        }
        response1 = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload1)
        assert response1.status_code == 201
        data1 = response1.json()
        assert data1["is_active"] is True
        
        # Create second interval
        payload2 = {
            "interval_minutes": 20,
            "reason": "Second interval"
        }
        response2 = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload2)
        assert response2.status_code == 201
        data2 = response2.json()
        assert data2["is_active"] is True
        
        # Verify that only one active interval exists by checking the list
        list_response = client.get("/api/v1/admin/poll-intervals?active=true", headers={"Authorization": f"Bearer {valid_jwt_token}"})
        if list_response.status_code == 200:
            active_intervals = list_response.json()
            assert len(active_intervals) == 1
            assert active_intervals[0]["id"] == data2["id"]  # Latest should be active

    def test_create_poll_interval_unauthorized_user(self, client: TestClient):
        """Test create poll interval endpoint with invalid token."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {
            "Authorization": "Bearer invalid_token",
            "Content-Type": "application/json"
        }
        
        payload = {
            "interval_minutes": 15,
            "reason": "Test with invalid token"
        }
        
        response = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload)
        
        assert response.status_code == 401

    def test_create_poll_interval_content_type_validation(self, client: TestClient, valid_jwt_token: str):
        """Test that endpoint requires proper content type."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Test without content-type header
        payload = {
            "interval_minutes": 15,
            "reason": "Test content type"
        }
        
        response = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload)
        
        # Should still work with json parameter, but test that content-type is handled
        assert response.status_code in [201, 415]  # 201 if accepted, 415 if content-type required

    def test_create_poll_interval_duplicate_handling(self, client: TestClient, valid_jwt_token: str):
        """Test that duplicate intervals are handled appropriately."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {
            "Authorization": f"Bearer {valid_jwt_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "interval_minutes": 15,
            "reason": "Testing duplicate creation"
        }
        
        # Create first interval
        response1 = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload)
        assert response1.status_code == 201
        
        # Create second interval with same data
        response2 = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload)
        
        # Should either succeed (creating new record) or return appropriate status
        assert response2.status_code in [201, 409]  # 201 for new record, 409 for conflict

    def test_create_poll_interval_location_header(self, client: TestClient, valid_jwt_token: str):
        """Test that response includes Location header for created resource."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {
            "Authorization": f"Bearer {valid_jwt_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "interval_minutes": 15,
            "reason": "Test location header"
        }
        
        response = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload)
        assert response.status_code == 201
        
        data = response.json()
        
        # Should include Location header pointing to the created resource
        assert "location" in response.headers
        expected_location = f"/api/v1/admin/poll-intervals/{data['id']}"
        assert response.headers["location"].endswith(expected_location)

    def test_create_poll_interval_error_response_format(self, client: TestClient, valid_jwt_token: str):
        """Test that error responses follow consistent format."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {
            "Authorization": f"Bearer {valid_jwt_token}",
            "Content-Type": "application/json"
        }
        
        # Send invalid payload to trigger error
        payload = {
            "interval_minutes": "invalid",  # Should be integer
            "reason": "Test error format"
        }
        
        response = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload)
        
        # Should return validation error
        assert response.status_code == 422
        
        data = response.json()
        # Should follow FastAPI validation error format
        assert "detail" in data
        assert isinstance(data["detail"], list)

    def test_create_poll_interval_valid_ranges(self, client: TestClient, valid_jwt_token: str):
        """Test that valid interval ranges are accepted."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {
            "Authorization": f"Bearer {valid_jwt_token}",
            "Content-Type": "application/json"
        }
        
        # Test minimum valid interval (1 minute)
        payload_min = {
            "interval_minutes": 1,
            "reason": "Testing minimum interval"
        }
        response = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload_min)
        assert response.status_code == 201
        
        # Test maximum valid interval (24 hours = 1440 minutes)
        payload_max = {
            "interval_minutes": 1440,
            "reason": "Testing maximum interval"
        }
        response = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload_max)
        assert response.status_code == 201
        
        # Test common intervals
        common_intervals = [5, 10, 15, 30, 60, 120]  # 5 min, 10 min, 15 min, 30 min, 1 hour, 2 hours
        for interval in common_intervals:
            payload_common = {
                "interval_minutes": interval,
                "reason": f"Testing {interval} minute interval"
            }
            response = client.post("/api/v1/admin/poll-intervals", headers=headers, json=payload_common)
            assert response.status_code == 201
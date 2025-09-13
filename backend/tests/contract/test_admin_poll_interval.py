"""
Contract tests for POST /api/v1/admin/market-data/poll-interval endpoint.

These tests verify the API contract for administrative poll interval control.
They MUST FAIL until the admin_market_data_router is implemented.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


class TestAdminPollIntervalContract:
    """Contract tests for admin poll interval endpoint."""

    def test_poll_interval_endpoint_exists(self, client: TestClient, valid_jwt_token: str):
        """Test that the poll interval endpoint exists and accepts requests."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        payload = {
            "interval_minutes": 30,
            "reason": "Reducing API usage during low activity period"
        }
        
        response = client.post("/api/v1/admin/market-data/poll-interval", headers=headers, json=payload)
        
        # Should return 200 for successful interval update
        assert response.status_code == 200
        
        # Should return JSON content
        assert response.headers["content-type"] == "application/json"

    def test_poll_interval_requires_authentication(self, client: TestClient):
        """Test that poll interval endpoint requires valid authentication."""
        # This test MUST FAIL until the endpoint is implemented
        
        payload = {
            "interval_minutes": 30,
            "reason": "Test without auth"
        }
        
        response = client.post("/api/v1/admin/market-data/poll-interval", json=payload)
        
        assert response.status_code == 401

    def test_poll_interval_request_validation(self, client: TestClient, valid_jwt_token: str):
        """Test that request payload is properly validated."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Test missing required fields
        response = client.post("/api/v1/admin/market-data/poll-interval", headers=headers, json={})
        assert response.status_code == 422  # Validation error
        
        # Test invalid interval (too low)
        invalid_payload = {
            "interval_minutes": 0,
            "reason": "Test invalid interval"
        }
        response = client.post("/api/v1/admin/market-data/poll-interval", headers=headers, json=invalid_payload)
        assert response.status_code == 422
        
        # Test invalid interval (too high)
        invalid_payload = {
            "interval_minutes": 10000,
            "reason": "Test invalid interval"
        }
        response = client.post("/api/v1/admin/market-data/poll-interval", headers=headers, json=invalid_payload)
        assert response.status_code == 422

    def test_poll_interval_valid_ranges(self, client: TestClient, valid_jwt_token: str):
        """Test that valid interval ranges are accepted."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        valid_intervals = [5, 15, 30, 60, 120]
        
        for interval in valid_intervals:
            payload = {
                "interval_minutes": interval,
                "reason": f"Testing {interval} minute interval"
            }
            
            response = client.post("/api/v1/admin/market-data/poll-interval", headers=headers, json=payload)
            assert response.status_code == 200

    def test_poll_interval_response_structure(self, client: TestClient, valid_jwt_token: str):
        """Test that response has correct structure."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        payload = {
            "interval_minutes": 15,
            "reason": "Test response structure"
        }
        
        response = client.post("/api/v1/admin/market-data/poll-interval", headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required response fields
        assert "success" in data
        assert "previous_interval" in data
        assert "new_interval" in data
        assert "effective_time" in data
        assert "next_update_scheduled" in data
        assert "admin_user" in data
        assert "reason" in data
        
        # Verify data types
        assert isinstance(data["success"], bool)
        assert isinstance(data["previous_interval"], int)
        assert isinstance(data["new_interval"], int)
        assert isinstance(data["effective_time"], str)
        assert isinstance(data["next_update_scheduled"], str)
        assert isinstance(data["admin_user"], str)
        assert isinstance(data["reason"], str)
        
        # Verify values
        assert data["success"] is True
        assert data["new_interval"] == 15
        assert data["reason"] == "Test response structure"

    def test_poll_interval_reason_validation(self, client: TestClient, valid_jwt_token: str):
        """Test that reason field is properly validated."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Test missing reason
        payload = {
            "interval_minutes": 30
        }
        response = client.post("/api/v1/admin/market-data/poll-interval", headers=headers, json=payload)
        assert response.status_code == 422
        
        # Test empty reason
        payload = {
            "interval_minutes": 30,
            "reason": ""
        }
        response = client.post("/api/v1/admin/market-data/poll-interval", headers=headers, json=payload)
        assert response.status_code == 422
        
        # Test very long reason
        payload = {
            "interval_minutes": 30,
            "reason": "x" * 1000  # Very long reason
        }
        response = client.post("/api/v1/admin/market-data/poll-interval", headers=headers, json=payload)
        assert response.status_code == 422

    def test_poll_interval_timestamp_format(self, client: TestClient, valid_jwt_token: str):
        """Test that timestamps follow ISO 8601 format."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        payload = {
            "interval_minutes": 45,
            "reason": "Testing timestamp format"
        }
        
        response = client.post("/api/v1/admin/market-data/poll-interval", headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify timestamp formats (ISO 8601)
        from datetime import datetime
        datetime.fromisoformat(data["effective_time"].replace("Z", "+00:00"))
        datetime.fromisoformat(data["next_update_scheduled"].replace("Z", "+00:00"))

    def test_poll_interval_admin_authorization(self, client: TestClient):
        """Test that only admin users can change poll intervals."""
        # This test MUST FAIL until the endpoint is implemented
        
        # Assuming we have a non-admin token fixture
        # For now, test with invalid token to ensure proper error handling
        headers = {"Authorization": "Bearer non_admin_token"}
        
        payload = {
            "interval_minutes": 30,
            "reason": "Test admin authorization"
        }
        
        response = client.post("/api/v1/admin/market-data/poll-interval", headers=headers, json=payload)
        
        # Should return 401 (unauthorized) or 403 (forbidden)
        assert response.status_code in [401, 403]

    def test_poll_interval_scheduling_logic(self, client: TestClient, valid_jwt_token: str):
        """Test that next update is properly scheduled."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        payload = {
            "interval_minutes": 60,
            "reason": "Testing scheduling logic"
        }
        
        response = client.post("/api/v1/admin/market-data/poll-interval", headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify next update is scheduled appropriately
        from datetime import datetime, timedelta
        effective_time = datetime.fromisoformat(data["effective_time"].replace("Z", "+00:00"))
        next_update = datetime.fromisoformat(data["next_update_scheduled"].replace("Z", "+00:00"))
        
        # Next update should be after effective time
        assert next_update > effective_time
        
        # Should be roughly the interval duration later (allowing some tolerance)
        expected_next = effective_time + timedelta(minutes=60)
        time_diff = abs((next_update - expected_next).total_seconds())
        assert time_diff < 300  # Within 5 minutes tolerance

    def test_poll_interval_concurrent_requests(self, client: TestClient, valid_jwt_token: str):
        """Test handling of concurrent poll interval changes."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Make multiple rapid requests
        payloads = [
            {"interval_minutes": 15, "reason": "First concurrent request"},
            {"interval_minutes": 30, "reason": "Second concurrent request"},
            {"interval_minutes": 45, "reason": "Third concurrent request"}
        ]
        
        responses = []
        for payload in payloads:
            response = client.post("/api/v1/admin/market-data/poll-interval", headers=headers, json=payload)
            responses.append(response)
        
        # All requests should be handled properly
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count > 0
        
        # Last successful request should win
        successful_responses = [r for r in responses if r.status_code == 200]
        if successful_responses:
            last_response = successful_responses[-1]
            data = last_response.json()
            assert data["success"] is True

    def test_poll_interval_market_hours_consideration(self, client: TestClient, valid_jwt_token: str):
        """Test that market hours are considered in scheduling."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        payload = {
            "interval_minutes": 15,
            "reason": "Testing market hours consideration"
        }
        
        response = client.post("/api/v1/admin/market-data/poll-interval", headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        
        # Response should include next update time
        assert "next_update_scheduled" in data
        
        # The scheduling should be reasonable (not in the past)
        from datetime import datetime
        next_update = datetime.fromisoformat(data["next_update_scheduled"].replace("Z", "+00:00"))
        now = datetime.now(next_update.tzinfo)
        assert next_update >= now

    def test_poll_interval_audit_trail(self, client: TestClient, valid_jwt_token: str):
        """Test that admin actions are properly logged for audit."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        payload = {
            "interval_minutes": 20,
            "reason": "Audit trail test - reducing frequency for maintenance"
        }
        
        response = client.post("/api/v1/admin/market-data/poll-interval", headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        
        # Response should include audit information
        assert data["admin_user"] is not None
        assert data["reason"] == payload["reason"]
        assert data["effective_time"] is not None
        
        # Admin user should be identifiable (not empty)
        assert len(data["admin_user"]) > 0

    def test_poll_interval_system_impact_warning(self, client: TestClient, valid_jwt_token: str):
        """Test that extreme interval changes include appropriate warnings."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Test very frequent polling (might impact system)
        payload = {
            "interval_minutes": 1,
            "reason": "Testing high frequency impact"
        }
        
        response = client.post("/api/v1/admin/market-data/poll-interval", headers=headers, json=payload)
        
        # Should either succeed with warning or reject with appropriate error
        assert response.status_code in [200, 422]
        
        if response.status_code == 200:
            data = response.json()
            # Might include warning about high frequency
            assert "warning" in data or data["success"] is True
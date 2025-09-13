"""
Contract tests for GET /api/v1/admin/poll-intervals endpoint.

These tests verify the API contract for retrieving poll interval configurations.
They MUST FAIL until the admin_market_data_router is implemented.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


class TestAdminPollIntervalsContract:
    """Contract tests for admin poll intervals endpoint."""

    def test_poll_intervals_endpoint_exists(self, client: TestClient, valid_jwt_token: str):
        """Test that the poll intervals endpoint exists and accepts requests."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/poll-intervals", headers=headers)
        
        # Should return 200 for successful retrieval
        assert response.status_code == 200
        
        # Should return JSON content
        assert response.headers["content-type"] == "application/json"

    def test_poll_intervals_requires_authentication(self, client: TestClient):
        """Test that poll intervals endpoint requires valid authentication."""
        # This test MUST FAIL until the endpoint is implemented
        
        response = client.get("/api/v1/admin/poll-intervals")
        
        assert response.status_code == 401

    def test_poll_intervals_response_structure(self, client: TestClient, valid_jwt_token: str):
        """Test that poll intervals endpoint returns correct response structure."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/poll-intervals", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Should return a list of poll interval configurations
        assert isinstance(data, list)
        
        # If there are any configs, verify structure
        if len(data) > 0:
            config = data[0]
            
            # Verify required fields
            assert "id" in config
            assert "interval_minutes" in config
            assert "reason" in config
            assert "created_at" in config
            assert "created_by" in config
            assert "is_active" in config
            
            # Verify data types
            assert isinstance(config["id"], str)
            assert isinstance(config["interval_minutes"], int)
            assert isinstance(config["reason"], str)
            assert isinstance(config["created_at"], str)
            assert isinstance(config["created_by"], str)
            assert isinstance(config["is_active"], bool)

    def test_poll_intervals_timestamp_format(self, client: TestClient, valid_jwt_token: str):
        """Test that timestamps follow ISO 8601 format."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/poll-intervals", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify timestamp format for each config
        for config in data:
            from datetime import datetime
            datetime.fromisoformat(config["created_at"].replace("Z", "+00:00"))
            
            # If expired_at exists, verify its format too
            if "expired_at" in config and config["expired_at"]:
                datetime.fromisoformat(config["expired_at"].replace("Z", "+00:00"))

    def test_poll_intervals_id_format(self, client: TestClient, valid_jwt_token: str):
        """Test that poll interval IDs follow UUID format."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/poll-intervals", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify UUID format for each config ID
        for config in data:
            import uuid
            uuid.UUID(config["id"])  # Should not raise exception for valid UUID

    def test_poll_intervals_interval_validation(self, client: TestClient, valid_jwt_token: str):
        """Test that interval values are within reasonable ranges."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/poll-intervals", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify interval ranges are reasonable
        for config in data:
            interval = config["interval_minutes"]
            
            # Should be positive and reasonable (1 minute to 24 hours)
            assert interval > 0
            assert interval <= 1440  # 24 hours in minutes

    def test_poll_intervals_unauthorized_user(self, client: TestClient):
        """Test poll intervals endpoint with invalid token."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/api/v1/admin/poll-intervals", headers=headers)
        
        assert response.status_code == 401

    def test_poll_intervals_ordering(self, client: TestClient, valid_jwt_token: str):
        """Test that poll intervals are returned in a logical order."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/poll-intervals", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # If multiple configs exist, verify ordering
        if len(data) > 1:
            from datetime import datetime
            
            # Should be ordered by creation time (newest first) or active status
            timestamps = []
            for config in data:
                created_at = datetime.fromisoformat(config["created_at"].replace("Z", "+00:00"))
                timestamps.append(created_at)
            
            # Verify descending order (newest first)
            for i in range(1, len(timestamps)):
                assert timestamps[i-1] >= timestamps[i]

    def test_poll_intervals_active_status_consistency(self, client: TestClient, valid_jwt_token: str):
        """Test that active status is logically consistent."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/poll-intervals", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        active_configs = [config for config in data if config["is_active"]]
        
        # Should have at most one active configuration
        assert len(active_configs) <= 1
        
        # If there's an active config, verify it doesn't have expired_at
        for config in active_configs:
            assert config.get("expired_at") is None or config.get("expired_at") == ""

    def test_poll_intervals_response_caching(self, client: TestClient, valid_jwt_token: str):
        """Test that poll intervals responses include appropriate caching headers."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/poll-intervals", headers=headers)
        assert response.status_code == 200
        
        # Should include cache control headers
        assert "cache-control" in response.headers
        # Admin data should be short-lived cache or no-cache
        cache_control = response.headers["cache-control"]
        assert "max-age" in cache_control or "no-cache" in cache_control

    def test_poll_intervals_pagination_support(self, client: TestClient, valid_jwt_token: str):
        """Test that endpoint supports pagination parameters."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Test with limit parameter
        response = client.get("/api/v1/admin/poll-intervals?limit=5", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Should respect limit
        assert len(data) <= 5
        
        # Test with offset parameter
        response_offset = client.get("/api/v1/admin/poll-intervals?offset=0&limit=2", headers=headers)
        assert response_offset.status_code == 200

    def test_poll_intervals_filtering_support(self, client: TestClient, valid_jwt_token: str):
        """Test that endpoint supports filtering by active status."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Test filtering by active status
        response_active = client.get("/api/v1/admin/poll-intervals?active=true", headers=headers)
        assert response_active.status_code == 200
        
        data_active = response_active.json()
        
        # All returned configs should be active
        for config in data_active:
            assert config["is_active"] is True
        
        # Test filtering by inactive status
        response_inactive = client.get("/api/v1/admin/poll-intervals?active=false", headers=headers)
        assert response_inactive.status_code == 200
        
        data_inactive = response_inactive.json()
        
        # All returned configs should be inactive
        for config in data_inactive:
            assert config["is_active"] is False

    def test_poll_intervals_empty_response(self, client: TestClient, valid_jwt_token: str):
        """Test endpoint behavior when no poll intervals exist."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        response = client.get("/api/v1/admin/poll-intervals", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Should return empty list, not null
        assert isinstance(data, list)

    def test_poll_intervals_cors_headers(self, client: TestClient, valid_jwt_token: str):
        """Test that poll intervals endpoint includes proper CORS headers."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {
            "Authorization": f"Bearer {valid_jwt_token}",
            "Origin": "http://localhost:3000"
        }
        
        response = client.get("/api/v1/admin/poll-intervals", headers=headers)
        assert response.status_code == 200
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers

    def test_poll_intervals_content_encoding(self, client: TestClient, valid_jwt_token: str):
        """Test that responses are properly encoded."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {
            "Authorization": f"Bearer {valid_jwt_token}",
            "Accept-Encoding": "gzip"
        }
        
        response = client.get("/api/v1/admin/poll-intervals", headers=headers)
        assert response.status_code == 200
        
        # Should handle encoding properly
        data = response.json()
        assert isinstance(data, list)

    def test_poll_intervals_error_responses(self, client: TestClient, valid_jwt_token: str):
        """Test error response format for invalid query parameters."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Test with invalid limit parameter
        response = client.get("/api/v1/admin/poll-intervals?limit=invalid", headers=headers)
        
        # Should return appropriate error status
        assert response.status_code in [400, 422]
        
        if response.status_code != 404:  # 404 might not have JSON body
            data = response.json()
            # Should follow FastAPI error format
            assert "detail" in data or "error" in data
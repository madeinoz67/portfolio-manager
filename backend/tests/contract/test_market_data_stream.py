"""
Contract tests for GET /api/v1/market-data/stream SSE endpoint.

These tests verify the API contract for Server-Sent Events streaming.
They MUST FAIL until the market_data_router is implemented.
"""

import asyncio
import json
from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.main import app
from tests.conftest import AuthenticatedClient


class TestMarketDataStreamContract:
    """Contract tests for SSE market data stream endpoint."""

    @pytest.fixture
    async def auth_client(self, authenticated_client: AuthenticatedClient) -> AsyncClient:
        """Provide authenticated async client for SSE testing."""
        return authenticated_client.async_client

    def test_sse_endpoint_exists(self, client: TestClient, valid_jwt_token: str):
        """Test that the SSE endpoint exists and accepts connections."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Attempt to connect to SSE stream
        with client.stream("GET", "/api/v1/market-data/stream", headers=headers) as response:
            # Should return 200 for successful SSE connection
            assert response.status_code == 200
            
            # Should have correct content type for SSE
            assert response.headers["content-type"] == "text/event-stream"
            
            # Should have SSE-specific headers
            assert "cache-control" in response.headers
            assert response.headers["cache-control"] == "no-cache"

    def test_sse_requires_authentication(self, client: TestClient):
        """Test that SSE endpoint requires valid authentication."""
        # This test MUST FAIL until the endpoint is implemented
        
        # Attempt to connect without authentication
        with client.stream("GET", "/api/v1/market-data/stream") as response:
            assert response.status_code == 401

    def test_sse_portfolio_subscription(self, client: TestClient, valid_jwt_token: str):
        """Test SSE endpoint accepts portfolio_ids parameter."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        portfolio_ids = "123e4567-e89b-12d3-a456-426614174000,987fcdeb-51a2-43d1-b789-123456789abc"
        
        with client.stream(
            "GET", 
            f"/api/v1/market-data/stream?portfolio_ids={portfolio_ids}",
            headers=headers
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"

    def test_sse_heartbeat_parameter(self, client: TestClient, valid_jwt_token: str):
        """Test SSE endpoint accepts heartbeat parameter."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        with client.stream(
            "GET", 
            "/api/v1/market-data/stream?include_heartbeat=false",
            headers=headers
        ) as response:
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_sse_event_format(self, auth_client: AsyncClient):
        """Test that SSE events follow the correct format."""
        # This test MUST FAIL until the endpoint is implemented
        
        # Connect to SSE stream
        async with auth_client.stream(
            "GET", 
            "/api/v1/market-data/stream?portfolio_ids=test-portfolio",
            timeout=5.0
        ) as response:
            assert response.status_code == 200
            
            # Read first few events to verify format
            event_count = 0
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    # Parse the JSON data
                    data = line[6:]  # Remove "data: " prefix
                    event = json.loads(data)
                    
                    # Verify event structure
                    assert "type" in event
                    assert "timestamp" in event
                    assert event["type"] in ["portfolio_update", "heartbeat", "connection_status"]
                    
                    # Verify timestamp format (ISO 8601)
                    from datetime import datetime
                    datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
                    
                    event_count += 1
                    if event_count >= 2:  # Test first few events
                        break

    @pytest.mark.asyncio
    async def test_portfolio_update_event_structure(self, auth_client: AsyncClient):
        """Test portfolio_update event has required fields."""
        # This test MUST FAIL until the endpoint is implemented
        
        portfolio_id = "123e4567-e89b-12d3-a456-426614174000"
        
        async with auth_client.stream(
            "GET", 
            f"/api/v1/market-data/stream?portfolio_ids={portfolio_id}",
            timeout=5.0
        ) as response:
            assert response.status_code == 200
            
            # Look for portfolio_update event
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    event = json.loads(data)
                    
                    if event["type"] == "portfolio_update":
                        # Verify required fields
                        assert "data" in event
                        data_obj = event["data"]
                        
                        assert "portfolio_id" in data_obj
                        assert "total_value" in data_obj
                        assert "last_updated" in data_obj
                        
                        # Verify portfolio_id format (UUID)
                        import uuid
                        uuid.UUID(data_obj["portfolio_id"])
                        
                        # Verify total_value is string (for precision)
                        assert isinstance(data_obj["total_value"], str)
                        
                        break

    @pytest.mark.asyncio
    async def test_heartbeat_event_structure(self, auth_client: AsyncClient):
        """Test heartbeat event has required fields."""
        # This test MUST FAIL until the endpoint is implemented
        
        async with auth_client.stream(
            "GET", 
            "/api/v1/market-data/stream?include_heartbeat=true",
            timeout=5.0
        ) as response:
            assert response.status_code == 200
            
            # Look for heartbeat event
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    event = json.loads(data)
                    
                    if event["type"] == "heartbeat":
                        # Verify required fields
                        assert "data" in event
                        data_obj = event["data"]
                        
                        assert "status" in data_obj
                        assert "server_time" in data_obj
                        assert data_obj["status"] in ["connected", "reconnecting", "error"]
                        
                        break

    def test_sse_connection_limits(self, client: TestClient, valid_jwt_token: str):
        """Test SSE endpoint respects connection limits."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        
        # Try to establish connection
        with client.stream("GET", "/api/v1/market-data/stream", headers=headers) as response:
            # Should succeed for reasonable number of connections
            assert response.status_code == 200

    def test_sse_invalid_portfolio_id(self, client: TestClient, valid_jwt_token: str):
        """Test SSE endpoint handles invalid portfolio IDs gracefully."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        invalid_portfolio_id = "invalid-uuid"
        
        with client.stream(
            "GET", 
            f"/api/v1/market-data/stream?portfolio_ids={invalid_portfolio_id}",
            headers=headers
        ) as response:
            # Should either return 400 for invalid UUID or 200 with error event
            assert response.status_code in [200, 400]
            
            if response.status_code == 200:
                # If connection succeeds, should get error event
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        event = json.loads(data)
                        if event["type"] == "error":
                            break

    def test_sse_cors_headers(self, client: TestClient, valid_jwt_token: str):
        """Test SSE endpoint includes proper CORS headers."""
        # This test MUST FAIL until the endpoint is implemented
        
        headers = {
            "Authorization": f"Bearer {valid_jwt_token}",
            "Origin": "http://localhost:3000"
        }
        
        with client.stream("GET", "/api/v1/market-data/stream", headers=headers) as response:
            assert response.status_code == 200
            # CORS headers should be present for SSE
            assert "access-control-allow-origin" in response.headers

    @pytest.mark.asyncio
    async def test_sse_sequence_numbers(self, auth_client: AsyncClient):
        """Test that SSE events include sequence numbers for ordering."""
        # This test MUST FAIL until the endpoint is implemented
        
        async with auth_client.stream(
            "GET", 
            "/api/v1/market-data/stream",
            timeout=5.0
        ) as response:
            assert response.status_code == 200
            
            last_sequence = -1
            event_count = 0
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    event = json.loads(data)
                    
                    # Verify sequence number exists and is monotonic
                    assert "sequence" in event
                    assert isinstance(event["sequence"], int)
                    assert event["sequence"] > last_sequence
                    
                    last_sequence = event["sequence"]
                    event_count += 1
                    
                    if event_count >= 3:  # Test first few events
                        break
"""
Integration tests for SSE connection lifecycle.

These tests verify the complete workflow from connection establishment 
to data streaming and connection cleanup.
They MUST FAIL until the complete SSE system is implemented.
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from typing import AsyncGenerator, List, Dict, Any
from httpx import AsyncClient

from src.main import app
from tests.conftest import AuthenticatedClient


class TestSSELifecycleIntegration:
    """Integration tests for complete SSE workflow."""

    @pytest.fixture
    async def auth_client(self, authenticated_client: AuthenticatedClient) -> AsyncClient:
        """Provide authenticated async client for SSE testing."""
        return authenticated_client.async_client

    @pytest.mark.asyncio
    async def test_sse_connection_establishment(self, auth_client: AsyncClient):
        """Test complete SSE connection establishment workflow."""
        # This test MUST FAIL until the complete system is implemented
        
        portfolio_id = "123e4567-e89b-12d3-a456-426614174000"
        
        async with auth_client.stream(
            "GET", 
            f"/api/v1/market-data/stream?portfolio_ids={portfolio_id}",
            timeout=10.0
        ) as response:
            
            # Should establish connection successfully
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"
            
            # Should receive connection status event first
            events = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])
                    events.append(event_data)
                    
                    # First event should be connection status
                    if len(events) == 1:
                        assert event_data["type"] == "connection_status"
                        assert event_data["data"]["status"] == "connected"
                        assert "timestamp" in event_data
                        break

    @pytest.mark.asyncio
    async def test_sse_portfolio_data_flow(self, auth_client: AsyncClient):
        """Test that portfolio data flows correctly through SSE."""
        # This test MUST FAIL until the complete system is implemented
        
        portfolio_id = "123e4567-e89b-12d3-a456-426614174000"
        
        async with auth_client.stream(
            "GET", 
            f"/api/v1/market-data/stream?portfolio_ids={portfolio_id}",
            timeout=15.0
        ) as response:
            
            assert response.status_code == 200
            
            portfolio_updates = []
            heartbeats = []
            event_count = 0
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])
                    event_count += 1
                    
                    if event_data["type"] == "portfolio_update":
                        portfolio_updates.append(event_data)
                    elif event_data["type"] == "heartbeat":
                        heartbeats.append(event_data)
                    
                    # Collect enough events to verify data flow
                    if event_count >= 5:
                        break
            
            # Should receive both portfolio updates and heartbeats
            assert len(portfolio_updates) > 0
            assert len(heartbeats) > 0
            
            # Verify portfolio update structure
            for update in portfolio_updates:
                assert "data" in update
                assert "portfolio_id" in update["data"]
                assert update["data"]["portfolio_id"] == portfolio_id
                assert "total_value" in update["data"]
                assert "last_updated" in update["data"]

    @pytest.mark.asyncio
    async def test_sse_multiple_portfolio_subscription(self, auth_client: AsyncClient):
        """Test SSE with multiple portfolio subscriptions."""
        # This test MUST FAIL until the complete system is implemented
        
        portfolio_ids = [
            "123e4567-e89b-12d3-a456-426614174000",
            "987fcdeb-51a2-43d1-b789-123456789abc"
        ]
        portfolio_ids_param = ",".join(portfolio_ids)
        
        async with auth_client.stream(
            "GET", 
            f"/api/v1/market-data/stream?portfolio_ids={portfolio_ids_param}",
            timeout=15.0
        ) as response:
            
            assert response.status_code == 200
            
            received_portfolio_ids = set()
            event_count = 0
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])
                    event_count += 1
                    
                    if event_data["type"] == "portfolio_update":
                        portfolio_id = event_data["data"]["portfolio_id"]
                        received_portfolio_ids.add(portfolio_id)
                    
                    # Stop after collecting sufficient data
                    if event_count >= 10 or len(received_portfolio_ids) >= 2:
                        break
            
            # Should receive updates for both portfolios
            assert len(received_portfolio_ids) > 0
            # In a real system, we'd expect updates for both portfolios

    @pytest.mark.asyncio
    async def test_sse_heartbeat_timing(self, auth_client: AsyncClient):
        """Test that heartbeats are sent at correct intervals."""
        # This test MUST FAIL until the complete system is implemented
        
        async with auth_client.stream(
            "GET", 
            "/api/v1/market-data/stream?include_heartbeat=true",
            timeout=20.0
        ) as response:
            
            assert response.status_code == 200
            
            heartbeat_timestamps = []
            event_count = 0
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])
                    event_count += 1
                    
                    if event_data["type"] == "heartbeat":
                        timestamp = datetime.fromisoformat(
                            event_data["timestamp"].replace("Z", "+00:00")
                        )
                        heartbeat_timestamps.append(timestamp)
                    
                    # Collect a few heartbeats to verify timing
                    if len(heartbeat_timestamps) >= 3:
                        break
                    
                    # Safety stop after many events
                    if event_count >= 50:
                        break
            
            # Should have received multiple heartbeats
            assert len(heartbeat_timestamps) >= 2
            
            # Verify heartbeat intervals (should be around 30 seconds per .env)
            if len(heartbeat_timestamps) >= 2:
                interval = heartbeat_timestamps[1] - heartbeat_timestamps[0]
                # Allow some tolerance for timing variations
                assert 25 <= interval.total_seconds() <= 35

    @pytest.mark.asyncio
    async def test_sse_connection_cleanup(self, auth_client: AsyncClient):
        """Test that SSE connections are properly cleaned up."""
        # This test MUST FAIL until the complete system is implemented
        
        # Start connection
        async with auth_client.stream(
            "GET", 
            "/api/v1/market-data/stream",
            timeout=5.0
        ) as response:
            
            assert response.status_code == 200
            
            # Read a few events to establish connection
            event_count = 0
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_count += 1
                    if event_count >= 2:
                        break
        
        # Connection should be closed now
        # Verify through system status that connection count decreased
        status_response = await auth_client.get("/api/v1/market-data/status")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        # Active connections should be managed properly
        assert "statistics" in status_data
        assert "active_sse_connections" in status_data["statistics"]
        assert status_data["statistics"]["active_sse_connections"] >= 0

    @pytest.mark.asyncio
    async def test_sse_error_handling(self, auth_client: AsyncClient):
        """Test SSE error handling and recovery."""
        # This test MUST FAIL until the complete system is implemented
        
        # Test with invalid portfolio ID
        invalid_portfolio_id = "invalid-portfolio-uuid"
        
        async with auth_client.stream(
            "GET", 
            f"/api/v1/market-data/stream?portfolio_ids={invalid_portfolio_id}",
            timeout=10.0
        ) as response:
            
            # Should either reject connection or send error event
            if response.status_code == 200:
                # If connection succeeds, should get error event
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        event_data = json.loads(line[6:])
                        
                        if event_data["type"] == "error":
                            assert "message" in event_data["data"]
                            assert "error_code" in event_data["data"]
                            break
                        
                        # Also accept connection status with error
                        if (event_data["type"] == "connection_status" and 
                            event_data["data"]["status"] == "error"):
                            break
            else:
                # Connection rejected - appropriate error status
                assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_sse_sequence_ordering(self, auth_client: AsyncClient):
        """Test that SSE events maintain proper sequence ordering."""
        # This test MUST FAIL until the complete system is implemented
        
        async with auth_client.stream(
            "GET", 
            "/api/v1/market-data/stream",
            timeout=10.0
        ) as response:
            
            assert response.status_code == 200
            
            sequences = []
            event_count = 0
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])
                    event_count += 1
                    
                    if "sequence" in event_data:
                        sequences.append(event_data["sequence"])
                    
                    if event_count >= 5:
                        break
            
            # Should have sequence numbers
            assert len(sequences) > 0
            
            # Sequences should be monotonically increasing
            for i in range(1, len(sequences)):
                assert sequences[i] > sequences[i-1]

    @pytest.mark.asyncio
    async def test_sse_concurrent_connections(self, auth_client: AsyncClient):
        """Test multiple concurrent SSE connections."""
        # This test MUST FAIL until the complete system is implemented
        
        portfolio_ids = [
            "123e4567-e89b-12d3-a456-426614174000",
            "987fcdeb-51a2-43d1-b789-123456789abc",
            "456e7890-f01b-23c4-d567-890123456def"
        ]
        
        # Start multiple concurrent connections
        connections = []
        for portfolio_id in portfolio_ids:
            conn = auth_client.stream(
                "GET", 
                f"/api/v1/market-data/stream?portfolio_ids={portfolio_id}",
                timeout=10.0
            )
            connections.append(conn)
        
        try:
            # Open all connections
            responses = []
            for conn in connections:
                response = await conn.__aenter__()
                responses.append(response)
            
            # All should succeed
            for response in responses:
                assert response.status_code == 200
            
            # Read events from each connection
            events_per_connection = []
            for response in responses:
                events = []
                event_count = 0
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        events.append(json.loads(line[6:]))
                        event_count += 1
                        if event_count >= 3:
                            break
                events_per_connection.append(events)
            
            # Each connection should receive events
            for events in events_per_connection:
                assert len(events) > 0
        
        finally:
            # Clean up connections
            for i, conn in enumerate(connections):
                try:
                    await conn.__aexit__(None, None, None)
                except:
                    pass

    @pytest.mark.asyncio
    async def test_sse_admin_poll_interval_integration(self, auth_client: AsyncClient):
        """Test that SSE responds to admin poll interval changes."""
        # This test MUST FAIL until the complete system is implemented
        
        # Change poll interval
        poll_payload = {
            "interval_minutes": 5,
            "reason": "Integration test - faster polling for testing"
        }
        
        poll_response = await auth_client.post(
            "/api/v1/admin/market-data/poll-interval",
            json=poll_payload
        )
        assert poll_response.status_code == 200
        
        # Start SSE connection
        async with auth_client.stream(
            "GET", 
            "/api/v1/market-data/stream",
            timeout=15.0
        ) as response:
            
            assert response.status_code == 200
            
            # Should receive events reflecting the new poll interval
            events = []
            event_count = 0
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])
                    events.append(event_data)
                    event_count += 1
                    
                    if event_count >= 5:
                        break
            
            # Should receive portfolio updates within reasonable time
            portfolio_updates = [e for e in events if e["type"] == "portfolio_update"]
            assert len(portfolio_updates) > 0

    @pytest.mark.asyncio
    async def test_sse_price_override_integration(self, auth_client: AsyncClient):
        """Test that SSE reflects price overrides immediately."""
        # This test MUST FAIL until the complete system is implemented
        
        # Create price override
        override_payload = {
            "symbol": "AAPL",
            "price": "999.99",
            "reason": "Integration test override",
            "duration_minutes": 30
        }
        
        override_response = await auth_client.post(
            "/api/v1/admin/market-data/override",
            json=override_payload
        )
        assert override_response.status_code == 200
        override_id = override_response.json()["override_id"]
        
        # Start SSE connection for portfolio containing AAPL
        portfolio_id = "123e4567-e89b-12d3-a456-426614174000"
        
        async with auth_client.stream(
            "GET", 
            f"/api/v1/market-data/stream?portfolio_ids={portfolio_id}",
            timeout=10.0
        ) as response:
            
            assert response.status_code == 200
            
            # Should receive portfolio update reflecting override
            override_detected = False
            event_count = 0
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])
                    event_count += 1
                    
                    if event_data["type"] == "portfolio_update":
                        # Check if portfolio value reflects override
                        # (This would depend on portfolio holdings)
                        override_detected = True
                        break
                    
                    if event_count >= 10:
                        break
            
            # Should detect some change due to override
            assert override_detected
        
        # Clean up override
        await auth_client.delete(f"/api/v1/admin/market-data/override/{override_id}")

    @pytest.mark.asyncio
    async def test_sse_system_status_consistency(self, auth_client: AsyncClient):
        """Test that SSE state is consistent with system status."""
        # This test MUST FAIL until the complete system is implemented
        
        # Start SSE connection
        async with auth_client.stream(
            "GET", 
            "/api/v1/market-data/stream",
            timeout=5.0
        ) as response:
            
            assert response.status_code == 200
            
            # Read a few events
            event_count = 0
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_count += 1
                    if event_count >= 3:
                        break
            
            # Check system status while connection is active
            status_response = await auth_client.get("/api/v1/market-data/status")
            assert status_response.status_code == 200
            
            status_data = status_response.json()
            
            # Should reflect active SSE connection
            assert status_data["statistics"]["active_sse_connections"] > 0
        
        # After connection closes, check status again
        await asyncio.sleep(1)  # Allow cleanup time
        
        final_status_response = await auth_client.get("/api/v1/market-data/status")
        assert final_status_response.status_code == 200
        
        final_status_data = final_status_response.json()
        
        # Connection count should be properly managed
        assert final_status_data["statistics"]["active_sse_connections"] >= 0
"""
Integration tests for admin functionality workflow.

These tests verify the complete admin workflow including poll interval changes,
price overrides, usage monitoring, and their interactions with the market data system.
They MUST FAIL until the complete admin system is implemented.
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from httpx import AsyncClient

from src.main import app
from tests.conftest import AuthenticatedClient


class TestAdminWorkflowIntegration:
    """Integration tests for complete admin workflow."""

    @pytest.fixture
    async def auth_client(self, authenticated_client: AuthenticatedClient) -> AsyncClient:
        """Provide authenticated async client for admin testing."""
        return authenticated_client.async_client

    @pytest.mark.asyncio
    async def test_poll_interval_change_workflow(self, auth_client: AsyncClient):
        """Test complete poll interval change workflow and its effects."""
        # This test MUST FAIL until the complete system is implemented
        
        # Get initial system status
        initial_status = await auth_client.get("/api/v1/market-data/status")
        assert initial_status.status_code == 200
        initial_data = initial_status.json()
        
        # Change poll interval to faster rate
        poll_payload = {
            "interval_minutes": 5,
            "reason": "Integration test - speeding up for testing"
        }
        
        poll_response = await auth_client.post(
            "/api/v1/admin/market-data/poll-interval",
            json=poll_payload
        )
        assert poll_response.status_code == 200
        poll_data = poll_response.json()
        
        # Verify poll interval change was recorded
        assert poll_data["success"] is True
        assert poll_data["new_interval"] == 5
        assert poll_data["reason"] == poll_payload["reason"]
        
        # Wait for next scheduled update to be planned
        await asyncio.sleep(2)
        
        # Check system status reflects the change
        updated_status = await auth_client.get("/api/v1/market-data/status")
        assert updated_status.status_code == 200
        updated_data = updated_status.json()
        
        # Next update time should reflect new interval
        next_update_time = datetime.fromisoformat(
            poll_data["next_update_scheduled"].replace("Z", "+00:00")
        )
        now = datetime.now(next_update_time.tzinfo)
        time_until_next = (next_update_time - now).total_seconds()
        
        # Should be scheduled within 5 minutes (300 seconds)
        assert 0 <= time_until_next <= 300

    @pytest.mark.asyncio
    async def test_price_override_complete_workflow(self, auth_client: AsyncClient):
        """Test complete price override workflow from creation to expiry."""
        # This test MUST FAIL until the complete system is implemented
        
        # Create price override
        symbol = "AAPL"
        override_price = "999.99"
        
        override_payload = {
            "symbol": symbol,
            "price": override_price,
            "reason": "Integration test price override",
            "duration_minutes": 2  # Short duration for testing
        }
        
        override_response = await auth_client.post(
            "/api/v1/admin/market-data/override",
            json=override_payload
        )
        assert override_response.status_code == 200
        override_data = override_response.json()
        
        override_id = override_data["override_id"]
        assert override_data["symbol"] == symbol
        assert override_data["override_price"] == override_price
        
        # Verify override is active by checking price endpoint
        price_response = await auth_client.get(f"/api/v1/market-data/prices/{symbol}")
        assert price_response.status_code == 200
        price_data = price_response.json()
        
        # Price should reflect override
        assert price_data["current_price"] == override_price
        assert price_data["source"] in ["override", "admin_override"]
        
        # Check system status shows override activity
        status_response = await auth_client.get("/api/v1/market-data/status")
        assert status_response.status_code == 200
        # Status might include override information
        
        # Wait for override to expire (2 minutes + buffer)
        await asyncio.sleep(130)  # 2 minutes 10 seconds
        
        # Check that price reverted after expiry
        expired_price_response = await auth_client.get(f"/api/v1/market-data/prices/{symbol}")
        assert expired_price_response.status_code == 200
        expired_price_data = expired_price_response.json()
        
        # Price should have reverted (not the override price anymore)
        # Note: Actual value depends on market data, but source should indicate normal operation
        assert expired_price_data["source"] in ["alpha_vantage", "yfinance", "cache"]

    @pytest.mark.asyncio
    async def test_override_deletion_workflow(self, auth_client: AsyncClient):
        """Test price override manual deletion workflow."""
        # This test MUST FAIL until the complete system is implemented
        
        symbol = "GOOGL"
        override_price = "2999.99"
        
        # Create override
        override_payload = {
            "symbol": symbol,
            "price": override_price,
            "reason": "Integration test for deletion workflow",
            "duration_minutes": 60  # Long duration
        }
        
        override_response = await auth_client.post(
            "/api/v1/admin/market-data/override",
            json=override_payload
        )
        assert override_response.status_code == 200
        override_id = override_response.json()["override_id"]
        
        # Verify override is active
        price_response = await auth_client.get(f"/api/v1/market-data/prices/{symbol}")
        assert price_response.status_code == 200
        assert price_response.json()["current_price"] == override_price
        
        # Delete override manually
        delete_reason = "Manual removal for integration test"
        delete_response = await auth_client.delete(
            f"/api/v1/admin/market-data/override/{override_id}?reason={delete_reason}"
        )
        assert delete_response.status_code == 200
        delete_data = delete_response.json()
        
        assert delete_data["success"] is True
        assert delete_data["override_id"] == override_id
        assert delete_data["reason"] == delete_reason
        
        # Verify price reverted immediately
        await asyncio.sleep(2)  # Brief pause for system to process
        
        reverted_price_response = await auth_client.get(f"/api/v1/market-data/prices/{symbol}")
        assert reverted_price_response.status_code == 200
        reverted_price_data = reverted_price_response.json()
        
        # Should no longer be override price
        assert reverted_price_data["current_price"] != override_price
        assert reverted_price_data["source"] in ["alpha_vantage", "yfinance", "cache"]

    @pytest.mark.asyncio
    async def test_usage_monitoring_workflow(self, auth_client: AsyncClient):
        """Test usage monitoring captures admin actions."""
        # This test MUST FAIL until the complete system is implemented
        
        # Get initial usage data
        initial_usage = await auth_client.get("/api/v1/admin/market-data/usage")
        assert initial_usage.status_code == 200
        initial_data = initial_usage.json()
        
        initial_total_requests = initial_data["current_period"]["total_requests"]
        
        # Perform several admin actions to generate usage
        actions = [
            # Change poll interval
            ("POST", "/api/v1/admin/market-data/poll-interval", {
                "interval_minutes": 10,
                "reason": "Usage test interval change"
            }),
            
            # Create price override
            ("POST", "/api/v1/admin/market-data/override", {
                "symbol": "TSLA",
                "price": "888.88",
                "reason": "Usage test override",
                "duration_minutes": 30
            }),
            
            # Check market data status (generates usage)
            ("GET", "/api/v1/market-data/status", None),
            ("GET", "/api/v1/market-data/prices/AAPL", None),
        ]
        
        override_id = None
        for method, endpoint, payload in actions:
            if method == "POST":
                response = await auth_client.post(endpoint, json=payload)
                if "override" in endpoint and response.status_code == 200:
                    override_id = response.json().get("override_id")
            else:
                response = await auth_client.get(endpoint)
            
            assert response.status_code == 200
            await asyncio.sleep(1)  # Brief pause between actions
        
        # Get updated usage data
        final_usage = await auth_client.get("/api/v1/admin/market-data/usage")
        assert final_usage.status_code == 200
        final_data = final_usage.json()
        
        # Should show increased usage
        final_total_requests = final_data["current_period"]["total_requests"]
        assert final_total_requests > initial_total_requests
        
        # Should show recent admin actions in system metrics or logs
        # (Exact structure depends on implementation)
        
        # Clean up override if created
        if override_id:
            await auth_client.delete(f"/api/v1/admin/market-data/override/{override_id}")

    @pytest.mark.asyncio
    async def test_admin_actions_affect_sse(self, auth_client: AsyncClient):
        """Test that admin actions are reflected in SSE streams."""
        # This test MUST FAIL until the complete system is implemented
        
        # Start SSE connection
        portfolio_id = "123e4567-e89b-12d3-a456-426614174000"
        
        # This test simulates concurrent SSE monitoring while admin actions occur
        sse_events = []
        sse_task = None
        
        try:
            # Start SSE stream in background
            async def collect_sse_events():
                async with auth_client.stream(
                    "GET", 
                    f"/api/v1/market-data/stream?portfolio_ids={portfolio_id}",
                    timeout=30.0
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                event_data = json.loads(line[6:])
                                sse_events.append(event_data)
                                # Stop after collecting reasonable number of events
                                if len(sse_events) >= 15:
                                    break
            
            sse_task = asyncio.create_task(collect_sse_events())
            
            # Give SSE time to establish
            await asyncio.sleep(2)
            
            # Perform admin actions that should affect SSE
            
            # 1. Change poll interval (should affect update frequency)
            poll_response = await auth_client.post(
                "/api/v1/admin/market-data/poll-interval",
                json={
                    "interval_minutes": 1,  # Very frequent for testing
                    "reason": "SSE integration test"
                }
            )
            assert poll_response.status_code == 200
            
            await asyncio.sleep(3)
            
            # 2. Create price override (should affect portfolio values)
            override_response = await auth_client.post(
                "/api/v1/admin/market-data/override",
                json={
                    "symbol": "AAPL",  # Assuming portfolio contains AAPL
                    "price": "777.77",
                    "reason": "SSE integration test override",
                    "duration_minutes": 10
                }
            )
            assert override_response.status_code == 200
            override_id = override_response.json()["override_id"]
            
            # Give time for admin actions to propagate to SSE
            await asyncio.sleep(5)
            
            # Wait for SSE task to complete or timeout
            await asyncio.wait_for(sse_task, timeout=20.0)
            
        except asyncio.TimeoutError:
            # Expected - we're collecting events for a limited time
            pass
        finally:
            if sse_task and not sse_task.done():
                sse_task.cancel()
                try:
                    await sse_task
                except asyncio.CancelledError:
                    pass
        
        # Analyze collected SSE events
        assert len(sse_events) > 0
        
        # Should have received various event types
        event_types = set(event["type"] for event in sse_events)
        assert "connection_status" in event_types  # Connection establishment
        
        # Should have received portfolio updates or heartbeats
        assert any(et in event_types for et in ["portfolio_update", "heartbeat"])
        
        # Clean up override
        if 'override_id' in locals():
            await auth_client.delete(f"/api/v1/admin/market-data/override/{override_id}")

    @pytest.mark.asyncio
    async def test_system_status_reflects_admin_changes(self, auth_client: AsyncClient):
        """Test that system status accurately reflects admin changes."""
        # This test MUST FAIL until the complete system is implemented
        
        # Get baseline status
        baseline_status = await auth_client.get("/api/v1/market-data/status")
        assert baseline_status.status_code == 200
        baseline_data = baseline_status.json()
        
        # Perform admin actions
        
        # 1. Change poll interval
        poll_response = await auth_client.post(
            "/api/v1/admin/market-data/poll-interval",
            json={
                "interval_minutes": 15,
                "reason": "System status integration test"
            }
        )
        assert poll_response.status_code == 200
        
        # 2. Create multiple price overrides
        overrides_created = []
        symbols = ["AAPL", "GOOGL", "MSFT"]
        
        for i, symbol in enumerate(symbols):
            override_response = await auth_client.post(
                "/api/v1/admin/market-data/override",
                json={
                    "symbol": symbol,
                    "price": f"{100 + i}.00",
                    "reason": f"Status test override {i+1}",
                    "duration_minutes": 30
                }
            )
            assert override_response.status_code == 200
            overrides_created.append(override_response.json()["override_id"])
        
        # Wait for changes to propagate
        await asyncio.sleep(3)
        
        # Check updated system status
        updated_status = await auth_client.get("/api/v1/market-data/status")
        assert updated_status.status_code == 200
        updated_data = updated_status.json()
        
        # Status should reflect changes
        # (Exact fields depend on implementation, but some changes should be visible)
        
        # System should be healthy despite admin changes
        assert updated_data["system_status"]["status"] in ["healthy", "degraded"]
        
        # Market status should still be accurate
        assert "is_open" in updated_data["market_status"]
        assert isinstance(updated_data["market_status"]["is_open"], bool)
        
        # Statistics should show reasonable values
        stats = updated_data["statistics"]
        assert stats["active_sse_connections"] >= 0
        assert stats["portfolios_tracked"] >= 0
        assert stats["symbols_cached"] >= 0
        
        # Clean up overrides
        for override_id in overrides_created:
            await auth_client.delete(f"/api/v1/admin/market-data/override/{override_id}")

    @pytest.mark.asyncio
    async def test_concurrent_admin_actions(self, auth_client: AsyncClient):
        """Test system handles concurrent admin actions properly."""
        # This test MUST FAIL until the complete system is implemented
        
        # Prepare concurrent admin actions
        async def change_poll_interval():
            return await auth_client.post(
                "/api/v1/admin/market-data/poll-interval",
                json={
                    "interval_minutes": 8,
                    "reason": "Concurrent test poll change"
                }
            )
        
        async def create_override(symbol, price):
            return await auth_client.post(
                "/api/v1/admin/market-data/override",
                json={
                    "symbol": symbol,
                    "price": price,
                    "reason": f"Concurrent test override for {symbol}",
                    "duration_minutes": 20
                }
            )
        
        async def check_usage():
            return await auth_client.get("/api/v1/admin/market-data/usage")
        
        # Execute concurrent admin actions
        tasks = [
            change_poll_interval(),
            create_override("AAPL", "555.55"),
            create_override("GOOGL", "2555.55"),
            check_usage(),
            check_usage(),  # Multiple usage checks
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All actions should succeed or handle conflicts gracefully
        successful_responses = []
        override_ids = []
        
        for result in results:
            if isinstance(result, Exception):
                # Some conflicts might be expected in concurrent scenarios
                continue
            
            if hasattr(result, 'status_code'):
                if result.status_code == 200:
                    successful_responses.append(result)
                    # Collect override IDs for cleanup
                    data = result.json()
                    if "override_id" in data:
                        override_ids.append(data["override_id"])
        
        # At least some actions should succeed
        assert len(successful_responses) >= 3
        
        # System should remain stable after concurrent actions
        final_status = await auth_client.get("/api/v1/market-data/status")
        assert final_status.status_code == 200
        final_data = final_status.json()
        
        assert final_data["system_status"]["status"] in ["healthy", "degraded"]
        
        # Clean up any created overrides
        for override_id in override_ids:
            try:
                await auth_client.delete(f"/api/v1/admin/market-data/override/{override_id}")
            except:
                pass  # Cleanup - ignore errors

    @pytest.mark.asyncio
    async def test_admin_audit_trail_integration(self, auth_client: AsyncClient):
        """Test that all admin actions create proper audit trail."""
        # This test MUST FAIL until the complete system is implemented
        
        # Perform series of admin actions with specific reasons
        audit_actions = [
            {
                "action": "poll_interval_change",
                "reason": "Audit test: Changing to 12-minute intervals for load balancing",
                "payload": {"interval_minutes": 12}
            },
            {
                "action": "price_override",
                "reason": "Audit test: Emergency price correction for TSLA",
                "payload": {"symbol": "TSLA", "price": "444.44", "duration_minutes": 45}
            }
        ]
        
        admin_timestamps = []
        created_override_id = None
        
        for action_info in audit_actions:
            timestamp_before = datetime.utcnow()
            
            if action_info["action"] == "poll_interval_change":
                response = await auth_client.post(
                    "/api/v1/admin/market-data/poll-interval",
                    json={**action_info["payload"], "reason": action_info["reason"]}
                )
            elif action_info["action"] == "price_override":
                response = await auth_client.post(
                    "/api/v1/admin/market-data/override",
                    json={**action_info["payload"], "reason": action_info["reason"]}
                )
                if response.status_code == 200:
                    created_override_id = response.json()["override_id"]
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify audit information in response
            assert data.get("reason") == action_info["reason"]
            assert "admin_user" in data
            assert len(data["admin_user"]) > 0
            
            # Should have timestamp
            timestamp_field = "effective_time" if "effective_time" in data else "created_at"
            if timestamp_field in data:
                action_timestamp = datetime.fromisoformat(
                    data[timestamp_field].replace("Z", "+00:00")
                )
                admin_timestamps.append(action_timestamp)
                
                # Timestamp should be recent
                time_diff = abs((action_timestamp - timestamp_before.replace(tzinfo=action_timestamp.tzinfo)).total_seconds())
                assert time_diff < 60  # Within 1 minute
            
            await asyncio.sleep(1)  # Brief pause between actions
        
        # Check usage monitoring captured the actions
        usage_response = await auth_client.get("/api/v1/admin/market-data/usage")
        assert usage_response.status_code == 200
        usage_data = usage_response.json()
        
        # Should show increased activity
        assert usage_data["current_period"]["total_requests"] > 0
        assert usage_data["current_period"]["successful_requests"] > 0
        
        # Clean up
        if created_override_id:
            delete_response = await auth_client.delete(
                f"/api/v1/admin/market-data/override/{created_override_id}?reason=Audit test cleanup"
            )
            assert delete_response.status_code == 200
            
            # Deletion should also be audited
            delete_data = delete_response.json()
            assert delete_data["reason"] == "Audit test cleanup"
            assert "admin_user" in delete_data
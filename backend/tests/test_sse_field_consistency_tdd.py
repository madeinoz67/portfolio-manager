"""
TDD Test for SSE Stream Field Name Consistency

Issue: SSE stream uses 'timestamp' field instead of 'fetched_at' field,
causing frontend staleness calculation to fail.

Expected: SSE stream should use same field names as REST API for consistency.
"""

import json
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from uuid import UUID

from src.main import app
from src.database import SessionLocal
from src.models.realtime_symbol import RealtimeSymbol


class TestSSEFieldConsistency:
    """Test SSE stream uses consistent field names with REST API."""

    @pytest.fixture
    def setup_market_data(self):
        """Setup fresh market data in database."""
        db = SessionLocal()
        try:
            # Clean existing data
            db.query(RealtimeSymbol).delete()

            # Add fresh test data
            test_symbol = RealtimeSymbol(
                symbol="TESTSSE",
                current_price=100.50,
                company_name="Test SSE Company",
                last_updated=datetime.now(),
                volume=50000,
                provider_id=UUID("9fe77c9d-8056-404d-b7ad-c88bea7f7db4")  # yfinance provider
            )
            db.add(test_symbol)
            db.commit()

            yield test_symbol
        finally:
            db.close()

    def test_sse_price_update_uses_fetched_at_field(
        self,
        client: TestClient,
        valid_jwt_token: str,
        setup_market_data
    ):
        """
        Test that SSE price_update events use 'fetched_at' field.

        This test MUST FAIL initially because SSE stream currently uses 'timestamp'
        instead of 'fetched_at' field, causing frontend staleness calculation to fail.
        """
        # Connect to SSE stream with authentication
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        with client.stream(
            "GET",
            "/api/v1/market-data/stream",
            headers=headers,
            timeout=2.0
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"

            # Read SSE events looking for price_update
            for line in response.iter_lines():
                if line and line.startswith("data: "):
                    try:
                        data = line[6:]  # Remove "data: " prefix
                        event = json.loads(data)

                        if event.get("type") == "price_update":
                            # Verify the event has price data
                            assert "data" in event
                            price_data = event["data"]

                            # Check that we have our test symbol
                            if "TESTSSE" in price_data:
                                symbol_data = price_data["TESTSSE"]

                                # CRITICAL: SSE stream must use 'fetched_at' field
                                # not 'timestamp' for frontend compatibility
                                assert "fetched_at" in symbol_data, (
                                    "SSE stream must use 'fetched_at' field for frontend compatibility. "
                                    "Currently uses 'timestamp' which breaks staleness calculation."
                                )

                                # Verify timestamp format is ISO string
                                fetched_at = symbol_data["fetched_at"]
                                assert isinstance(fetched_at, str)

                                # Verify timestamp is parseable as ISO format
                                parsed_time = datetime.fromisoformat(
                                    fetched_at.replace("Z", "+00:00")
                                )

                                # Verify timestamp is recent (within last minute)
                                now = datetime.now(parsed_time.tzinfo)
                                age_seconds = (now - parsed_time).total_seconds()
                                assert age_seconds < 60, f"Timestamp too old: {age_seconds} seconds"

                                # Test passed - SSE uses correct field name
                                return

                    except json.JSONDecodeError:
                        continue

            # If we get here, no price_update event was found
            pytest.fail("No price_update event with TESTSSE found in SSE stream")

    def test_sse_vs_rest_api_field_consistency(
        self,
        client: TestClient,
        valid_jwt_token: str,
        setup_market_data
    ):
        """
        Test that SSE stream and REST API use identical field names.

        This ensures frontend code can use same logic for both data sources.
        """
        client = authenticated_client.client

        # Get data from REST API first
        rest_response = client.get("/api/v1/market-data/prices/TESTSSE")
        assert rest_response.status_code == 200
        rest_data = rest_response.json()

        # REST API should use 'fetched_at'
        assert "fetched_at" in rest_data
        rest_timestamp = rest_data["fetched_at"]

        # Now check SSE stream uses same field name
        with client.stream(
            "GET",
            "/api/v1/market-data/stream",
            timeout=2.0
        ) as sse_response:
            assert sse_response.status_code == 200

            for line in sse_response.iter_lines():
                if line and line.startswith("data: "):
                    try:
                        data = line[6:]
                        event = json.loads(data)

                        if (event.get("type") == "price_update" and
                            "TESTSSE" in event.get("data", {})):

                            sse_symbol_data = event["data"]["TESTSSE"]

                            # CRITICAL: Both APIs must use same field names
                            assert "fetched_at" in sse_symbol_data, (
                                "SSE stream and REST API must use identical field names. "
                                "REST API uses 'fetched_at', SSE must use same field."
                            )

                            # Verify both timestamps are similar (within 30 seconds)
                            sse_timestamp = sse_symbol_data["fetched_at"]

                            rest_time = datetime.fromisoformat(
                                rest_timestamp.replace("Z", "+00:00")
                            )
                            sse_time = datetime.fromisoformat(
                                sse_timestamp.replace("Z", "+00:00")
                            )

                            time_diff = abs((rest_time - sse_time).total_seconds())
                            assert time_diff < 30, "REST and SSE timestamps should be similar"

                            return

                    except json.JSONDecodeError:
                        continue

            pytest.fail("No matching price_update event found in SSE stream")

    def test_sse_price_data_structure_matches_frontend_expectations(
        self,
        client: TestClient,
        valid_jwt_token: str,
        setup_market_data
    ):
        """
        Test that SSE price data structure matches frontend PriceResponse interface.

        Frontend expects: { symbol, price, volume?, fetched_at, cached, ... }
        """
        client = authenticated_client.client

        with client.stream(
            "GET",
            "/api/v1/market-data/stream",
            timeout=2.0
        ) as response:
            assert response.status_code == 200

            for line in response.iter_lines():
                if line and line.startswith("data: "):
                    try:
                        data = line[6:]
                        event = json.loads(data)

                        if (event.get("type") == "price_update" and
                            "TESTSSE" in event.get("data", {})):

                            symbol_data = event["data"]["TESTSSE"]

                            # Verify frontend expected fields
                            assert "price" in symbol_data
                            assert "fetched_at" in symbol_data  # CRITICAL field

                            # Optional fields that may be present
                            if "volume" in symbol_data:
                                assert isinstance(symbol_data["volume"], (int, type(None)))

                            # Verify price is numeric
                            assert isinstance(symbol_data["price"], (int, float))
                            assert symbol_data["price"] > 0

                            return

                    except json.JSONDecodeError:
                        continue

            pytest.fail("No valid price_update event found")
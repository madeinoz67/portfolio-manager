"""
TDD test for fixing Decimal JSON serialization issue in activity logging.

This test validates that Decimal values in activity metadata are properly
converted to strings before JSON serialization, preventing the scheduler
background task from failing.
"""

import pytest
from decimal import Decimal
import json
from datetime import datetime, timezone

from src.database import SessionLocal
from src.services.activity_service import log_provider_activity
from src.models.market_data_provider import ProviderActivity


class TestDecimalJSONSerializationFix:
    """Test suite for fixing Decimal JSON serialization in activity logging."""

    @pytest.fixture
    def db_session(self):
        """Create a database session for testing."""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def test_decimal_in_metadata_should_be_serializable(self, db_session):
        """
        Test that Decimal values in activity metadata are properly serialized.

        This test reproduces the exact error from the scheduler background task:
        'Object of type Decimal is not JSON serializable'
        """
        # Arrange: Create metadata with Decimal values (like price data)
        metadata_with_decimal = {
            "symbol": "TLS",
            "price": Decimal("4.93"),  # This should cause the JSON error
            "provider": "yfinance",
            "response_time_ms": 2551
        }

        # Act & Assert: This should NOT raise a JSON serialization error
        try:
            activity = log_provider_activity(
                db_session=db_session,
                provider_id="yfinance",
                activity_type="API_CALL",
                description="Successfully fetched TLS from yfinance: $4.93",
                status="success",
                metadata=metadata_with_decimal
            )

            # Verify the activity was created successfully
            assert activity is not None
            assert activity.provider_id == "yfinance"
            assert activity.activity_type == "API_CALL"
            assert activity.status == "success"

            # Verify metadata is stored and retrievable (SQLAlchemy JSON field auto-deserializes)
            stored_metadata = activity.activity_metadata
            assert stored_metadata["symbol"] == "TLS"
            assert stored_metadata["provider"] == "yfinance"
            assert stored_metadata["response_time_ms"] == 2551

            # The critical test: Decimal should be converted to string
            assert isinstance(stored_metadata["price"], str)
            assert stored_metadata["price"] == "4.93"

            # Verify database commit succeeded
            db_session.commit()

        except Exception as e:
            pytest.fail(f"Activity logging failed with Decimal metadata: {e}")

    def test_json_serialization_with_mixed_types(self, db_session):
        """Test that mixed metadata types including Decimal are properly handled."""
        # Arrange: Create metadata with various types including Decimal
        complex_metadata = {
            "symbol": "CBA",
            "price": Decimal("169.97"),
            "volume": 1234567,
            "market_cap": 123456789012.0,
            "is_enabled": True,
            "tags": ["ASX", "Banking"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "nested": {
                "previous_close": Decimal("168.50"),
                "change": Decimal("1.47")
            }
        }

        # Act: Log activity with complex metadata
        activity = log_provider_activity(
            db_session=db_session,
            provider_id="yfinance",
            activity_type="BULK_PRICE_UPDATE",
            description="Bulk fetch completed with mixed data types",
            status="success",
            metadata=complex_metadata
        )

        # Assert: All types should be properly serialized
        stored_metadata = activity.activity_metadata

        # String should remain string
        assert stored_metadata["symbol"] == "CBA"

        # Decimal should become string
        assert isinstance(stored_metadata["price"], str)
        assert stored_metadata["price"] == "169.97"

        # Numbers should remain numbers
        assert stored_metadata["volume"] == 1234567
        assert stored_metadata["market_cap"] == 123456789012.0

        # Boolean should remain boolean
        assert stored_metadata["is_enabled"] is True

        # Lists should remain lists
        assert stored_metadata["tags"] == ["ASX", "Banking"]

        # Nested Decimals should be converted
        assert isinstance(stored_metadata["nested"]["previous_close"], str)
        assert stored_metadata["nested"]["previous_close"] == "168.50"
        assert isinstance(stored_metadata["nested"]["change"], str)
        assert stored_metadata["nested"]["change"] == "1.47"

    def test_scheduler_background_task_metadata_compatibility(self, db_session):
        """
        Test that the exact metadata structure from scheduler background task works.

        This reproduces the exact metadata structure that caused the failure.
        """
        # Arrange: Use the exact metadata from the error logs
        scheduler_metadata = {
            "symbol": "TLS",
            "price": Decimal("4.93"),
            "provider": "yfinance",
            "response_time_ms": 2551
        }

        # Act: This should work without transaction rollback
        activity = log_provider_activity(
            db_session=db_session,
            provider_id="yfinance",
            activity_type="API_CALL",
            description="Successfully fetched TLS from yfinance: $4.93",
            status="success",
            metadata=scheduler_metadata
        )

        # Assert: Transaction should complete successfully
        db_session.commit()

        # Verify the activity exists in the database
        retrieved_activity = db_session.query(ProviderActivity).filter(
            ProviderActivity.id == activity.id
        ).first()

        assert retrieved_activity is not None
        assert retrieved_activity.provider_id == "yfinance"
        assert retrieved_activity.status == "success"

        # Verify metadata is properly stored
        metadata = retrieved_activity.activity_metadata
        assert metadata["symbol"] == "TLS"
        assert metadata["price"] == "4.93"  # Converted from Decimal to string
        assert metadata["provider"] == "yfinance"
        assert metadata["response_time_ms"] == 2551

    def test_activity_service_handles_none_metadata(self, db_session):
        """Test that activity service handles None metadata gracefully."""
        # Act: Log activity with None metadata
        activity = log_provider_activity(
            db_session=db_session,
            provider_id="system",
            activity_type="HEALTH_CHECK",
            description="System health check",
            status="success",
            metadata=None
        )

        # Assert: Should work without errors
        assert activity is not None
        assert activity.activity_metadata == "{}"  # Should be empty JSON object

    def test_activity_service_handles_empty_metadata(self, db_session):
        """Test that activity service handles empty metadata dict."""
        # Act: Log activity with empty metadata
        activity = log_provider_activity(
            db_session=db_session,
            provider_id="system",
            activity_type="HEALTH_CHECK",
            description="System health check",
            status="success",
            metadata={}
        )

        # Assert: Should work without errors
        assert activity is not None
        assert activity.activity_metadata == "{}"

    def test_direct_json_serialization_fails_with_decimal(self):
        """
        Verify that the problem exists: direct JSON serialization of Decimal fails.

        This test documents the root cause of the issue.
        """
        # Arrange: Create data with Decimal (what was causing the error)
        data_with_decimal = {
            "price": Decimal("4.93"),
            "symbol": "TLS"
        }

        # Assert: Direct JSON serialization should fail
        with pytest.raises(TypeError, match="Object of type Decimal is not JSON serializable"):
            json.dumps(data_with_decimal)

    def test_decimal_conversion_utility(self):
        """Test utility function for converting Decimals to strings in nested data."""
        # This test will ensure our fix handles nested structures properly
        from src.services.activity_service import _convert_decimals_to_strings

        # Arrange: Create nested data with Decimals
        data = {
            "symbol": "CBA",
            "price": Decimal("169.97"),
            "stats": {
                "high": Decimal("170.50"),
                "low": Decimal("168.20"),
                "volume": 1000000
            },
            "tags": ["ASX", "Banking"]
        }

        # Act: Convert Decimals to strings
        converted = _convert_decimals_to_strings(data)

        # Assert: Decimals should be strings, other types unchanged
        assert converted["symbol"] == "CBA"
        assert converted["price"] == "169.97"
        assert isinstance(converted["price"], str)

        assert converted["stats"]["high"] == "170.50"
        assert isinstance(converted["stats"]["high"], str)
        assert converted["stats"]["low"] == "168.20"
        assert isinstance(converted["stats"]["low"], str)
        assert converted["stats"]["volume"] == 1000000  # int unchanged

        assert converted["tags"] == ["ASX", "Banking"]  # list unchanged

        # Verify JSON serialization now works
        json_str = json.dumps(converted)
        assert json_str is not None
        assert "169.97" in json_str
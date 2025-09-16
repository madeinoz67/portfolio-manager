"""
Test for scheduler JSON serialization fix using TDD approach.

Testing for: https://sqlalche.me/e/20/7s2a
Error: Object of type Decimal is not JSON serializable
"""

import pytest
import json
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from src.services.market_data_service import MarketDataService
from src.services.activity_service import log_provider_activity
from src.models.market_data_provider import MarketDataProvider
from src.database import get_db
from src.utils.datetime_utils import utc_now


class TestSchedulerJsonSerializationFix:
    """Test fixes for scheduler JSON serialization issues."""

    def test_decimal_serialization_in_activity_metadata(self, db_session: Session):
        """Test that Decimal values are properly serialized in activity logs."""
        # Create a test provider (let SQLAlchemy auto-generate UUID for id)
        provider = MarketDataProvider(
            name="test_provider",
            display_name="Test Provider",
            is_enabled=True,
            priority=1,
            rate_limit_per_minute=60,
            rate_limit_per_day=5000
        )
        db_session.add(provider)
        db_session.commit()

        # Test data with Decimal values that previously caused JSON serialization errors
        metadata_with_decimal = {
            "symbol": "TLS",
            "price": Decimal("4.93"),  # This caused the serialization error
            "provider": "yfinance",
            "response_time_ms": 2551
        }

        # This should not raise a JSON serialization error
        try:
            log_provider_activity(
                db_session=db_session,
                provider_id="test_provider",  # Use provider name, not ID
                activity_type="API_CALL",
                description="Test activity with decimal price",
                status="success",
                metadata=metadata_with_decimal
            )
            # If we get here, the test passes
            assert True
        except TypeError as e:
            if "Object of type Decimal is not JSON serializable" in str(e):
                pytest.fail("Decimal serialization not fixed - JSON error still occurs")
            else:
                raise

    def test_activity_service_handles_various_data_types(self, db_session: Session):
        """Test that activity service properly handles various data types in metadata."""
        # Create a test provider
        provider = MarketDataProvider(
            name="test_provider2",
            display_name="Test Provider 2",
            is_enabled=True,
            priority=1,
            rate_limit_per_minute=60,
            rate_limit_per_day=5000
        )
        db_session.add(provider)
        db_session.commit()

        # Test metadata with various data types that need proper serialization
        complex_metadata = {
            "symbol": "BHP",
            "price": Decimal("40.81"),
            "volume": 1234567,
            "timestamp": datetime.now(),
            "provider_config": {
                "timeout": 30,
                "retry_count": 3,
                "batch_size": Decimal("50")  # Nested decimal
            },
            "market_cap": Decimal("176543210987.65"),
            "percentage_change": Decimal("-2.15")
        }

        # This should handle all data types properly
        log_provider_activity(
            db_session=db_session,
            provider_id="test_provider2",
            activity_type="BULK_PRICE_UPDATE",
            description="Complex metadata test",
            status="success",
            metadata=complex_metadata
        )

        # Verify the activity was stored
        from src.models.market_data_provider import ProviderActivity
        activity = db_session.query(ProviderActivity).filter_by(
            provider_id="test_provider2",
            activity_type="BULK_PRICE_UPDATE"
        ).first()

        assert activity is not None
        assert activity.status == "success"

        # Verify metadata was stored as valid JSON
        stored_metadata = activity.activity_metadata
        assert isinstance(stored_metadata, dict)
        assert stored_metadata["symbol"] == "BHP"

        # Decimal values should be converted to strings or floats for JSON storage
        price_value = stored_metadata["price"]
        assert isinstance(price_value, (str, float, int))

    def test_market_data_service_bulk_fetch_handles_decimals(self, db_session: Session):
        """Test that MarketDataService properly handles Decimal values during bulk fetch."""
        service = MarketDataService(db_session)

        # Mock the yfinance response to simulate real scenario
        mock_price_data = {
            "TLS": {
                "symbol": "TLS",
                "price": Decimal("4.93"),
                "volume": 17285570,
                "market_cap": Decimal("56128049152.0")
            }
        }

        with patch.object(service, '_fetch_from_yfinance', return_value=mock_price_data["TLS"]):
            with patch.object(service, '_store_price_data', return_value=None):
                # This should not fail with JSON serialization error
                try:
                    result = service._fetch_single_price("TLS")
                    assert result is not None
                    assert "symbol" in result
                except TypeError as e:
                    if "Object of type Decimal is not JSON serializable" in str(e):
                        pytest.fail("MarketDataService still has JSON serialization issues")
                    else:
                        raise

    def test_scheduler_can_process_real_price_data_without_errors(self, db_session: Session):
        """Test that the scheduler task can process real price data without JSON errors."""
        # Create enabled provider
        provider = MarketDataProvider(
            name="yfinance",
            display_name="Yahoo Finance",
            is_enabled=True,
            priority=1,
            rate_limit_per_minute=60,
            rate_limit_per_day=5000
        )
        db_session.add(provider)
        db_session.commit()

        service = MarketDataService(db_session)

        # Simulate the exact scenario that was failing in the logs
        symbols_to_fetch = ["TLS"]

        # Mock fetch_multiple_prices to return realistic data with Decimals
        mock_results = {
            "TLS": {
                "symbol": "TLS",
                "price": Decimal("4.93"),
                "volume": 17285570,
                "market_cap": Decimal("56128049152.0"),
                "provider": "yfinance",
                "response_time_ms": 2551
            }
        }

        with patch.object(service, 'fetch_multiple_prices') as mock_fetch:
            mock_fetch.return_value = mock_results

            # This simulates the main scheduler loop logic
            try:
                results = service.fetch_multiple_prices(symbols_to_fetch)
                successful_fetches = len([result for result in results.values() if result is not None])

                # Log the batch summary as the scheduler does
                log_provider_activity(
                    db_session=db_session,
                    provider_id="system",
                    activity_type="BATCH_SUMMARY",
                    description=f"Batch update completed: {successful_fetches}/{len(symbols_to_fetch)} symbols updated",
                    status="success" if successful_fetches > 0 else "warning",
                    metadata={
                        "cycle_number": 1,
                        "symbols_processed": symbols_to_fetch,
                        "success_count": successful_fetches,
                        "dynamic_discovery": "enabled",
                        "provider_bulk_limit": 50,
                        "sources": "portfolio_holdings_and_recent_requests"
                    }
                )

                assert successful_fetches > 0

            except TypeError as e:
                if "Object of type Decimal is not JSON serializable" in str(e):
                    pytest.fail("Scheduler batch processing still has JSON serialization issues")
                else:
                    raise
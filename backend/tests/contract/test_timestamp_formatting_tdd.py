"""
TDD tests for proper timestamp formatting in API responses.

Tests that timestamps are properly formatted for frontend consumption
to avoid "Invalid Date" and staleness detection issues.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from src.models.realtime_price_history import RealtimePriceHistory
from src.models.market_data_provider import MarketDataProvider
from src.api.market_data import build_price_response
from src.utils.datetime_utils import utc_now


class TestTimestampFormatting:
    """Test suite for timestamp formatting in API responses."""

    @pytest.fixture
    def sample_provider(self, db_session: Session):
        """Create sample market data provider."""
        provider = MarketDataProvider(
            name="test_provider",
            display_name="Test Provider",
            is_enabled=True,
            priority=1,
            rate_limit_per_day=1000
        )
        db_session.add(provider)
        db_session.commit()
        return provider

    def test_timestamp_format_is_javascript_compatible(self, sample_provider: MarketDataProvider, db_session: Session):
        """Test that timestamps are formatted in JavaScript-compatible ISO format."""
        symbol = "TIMESTAMP_TEST"
        current_price = Decimal("100.00")
        current_time = utc_now()

        # Create price record with timezone-aware datetime
        price_record = RealtimePriceHistory(
            symbol=symbol,
            price=current_price,
            volume=1000000,
            provider_id=sample_provider.id,
            source_timestamp=current_time,
            opening_price=Decimal("99.50"),
            fetched_at=current_time,
            created_at=current_time
        )
        db_session.add(price_record)
        db_session.commit()

        # Build response
        response = build_price_response(
            symbol=symbol,
            price_record=price_record,
            cached=False,
            trend_service=None
        )

        # Verify timestamp format
        fetched_at = response.fetched_at

        # Should be a valid ISO string
        assert isinstance(fetched_at, str)

        # Should end with 'Z' for UTC timezone
        assert fetched_at.endswith('Z'), f"Timestamp should end with 'Z': {fetched_at}"

        # Should NOT contain invalid patterns like '+00:00Z'
        assert '+00:00Z' not in fetched_at, f"Invalid +00:00Z pattern found: {fetched_at}"

        # Should be parseable by JavaScript Date constructor (Python equivalent)
        try:
            # This is how JavaScript would parse it: new Date(fetched_at)
            parsed_time = datetime.fromisoformat(fetched_at.replace('Z', '+00:00'))
            assert parsed_time is not None

            # Should be very recent (within last minute)
            time_diff = (utc_now() - parsed_time).total_seconds()
            assert time_diff < 60, f"Timestamp appears too old: {time_diff} seconds"

        except ValueError as e:
            pytest.fail(f"Timestamp format is not JavaScript-compatible: {fetched_at} - Error: {e}")

    def test_naive_datetime_handling(self, sample_provider: MarketDataProvider, db_session: Session):
        """Test that naive datetime objects are properly converted to UTC ISO format."""
        symbol = "NAIVE_TEST"
        current_price = Decimal("200.00")

        # Create a naive datetime (without timezone info)
        naive_time = datetime.now().replace(microsecond=0)  # Remove microseconds for cleaner test

        # Create price record with naive datetime
        price_record = RealtimePriceHistory(
            symbol=symbol,
            price=current_price,
            volume=500000,
            provider_id=sample_provider.id,
            source_timestamp=naive_time,
            opening_price=Decimal("199.75"),
            fetched_at=naive_time,  # This will be naive datetime
            created_at=naive_time
        )
        db_session.add(price_record)
        db_session.commit()

        # Build response
        response = build_price_response(
            symbol=symbol,
            price_record=price_record,
            cached=False,
            trend_service=None
        )

        # Verify timestamp is properly formatted even for naive datetime
        fetched_at = response.fetched_at

        # Should be a valid ISO string with Z suffix
        assert fetched_at.endswith('Z'), f"Naive datetime should be converted to UTC with Z: {fetched_at}"

        # Should be parseable
        try:
            parsed_time = datetime.fromisoformat(fetched_at.replace('Z', '+00:00'))
            assert parsed_time is not None
        except ValueError as e:
            pytest.fail(f"Naive datetime was not properly converted: {fetched_at} - Error: {e}")

    def test_price_data_timestamp_formatting(self, sample_provider: MarketDataProvider):
        """Test timestamp formatting when using price_data dict instead of price_record."""
        symbol = "PRICE_DATA_TEST"
        current_time = utc_now()

        # Create price_data dict (as would come from API)
        price_data = {
            "symbol": symbol,
            "price": Decimal("150.50"),
            "volume": 750000,
            "source_timestamp": current_time,  # This should be formatted properly
            "open_price": Decimal("150.00"),
        }

        # Build response using price_data instead of price_record
        response = build_price_response(
            symbol=symbol,
            price_record=None,
            price_data=price_data,
            cached=False,
            trend_service=None
        )

        # Verify timestamp formatting from price_data
        fetched_at = response.fetched_at

        assert fetched_at.endswith('Z'), f"Price data timestamp should end with Z: {fetched_at}"
        assert '+00:00Z' not in fetched_at, f"Invalid +00:00Z pattern: {fetched_at}"

        # Should be parseable
        try:
            parsed_time = datetime.fromisoformat(fetched_at.replace('Z', '+00:00'))
            time_diff = (utc_now() - parsed_time).total_seconds()
            assert time_diff < 60, f"Price data timestamp too old: {time_diff} seconds"
        except ValueError as e:
            pytest.fail(f"Price data timestamp format invalid: {fetched_at} - Error: {e}")

    def test_staleness_detection_with_correct_timestamps(self, sample_provider: MarketDataProvider, db_session: Session):
        """Test that properly formatted timestamps don't cause false staleness detection."""
        symbol = "STALENESS_TEST"
        current_price = Decimal("300.00")

        # Create fresh data (should NOT be stale)
        fresh_time = utc_now()
        fresh_record = RealtimePriceHistory(
            symbol=f"{symbol}_FRESH",
            price=current_price,
            volume=1000000,
            provider_id=sample_provider.id,
            source_timestamp=fresh_time,
            opening_price=Decimal("299.50"),
            fetched_at=fresh_time,
            created_at=fresh_time
        )

        # Create stale data (should be stale)
        stale_time = utc_now() - timedelta(minutes=45)  # 45 minutes old
        stale_record = RealtimePriceHistory(
            symbol=f"{symbol}_STALE",
            price=current_price,
            volume=1000000,
            provider_id=sample_provider.id,
            source_timestamp=stale_time,
            opening_price=Decimal("299.50"),
            fetched_at=stale_time,
            created_at=stale_time
        )

        db_session.add(fresh_record)
        db_session.add(stale_record)
        db_session.commit()

        # Build responses
        fresh_response = build_price_response(
            symbol=f"{symbol}_FRESH",
            price_record=fresh_record,
            cached=False,
            trend_service=None
        )

        stale_response = build_price_response(
            symbol=f"{symbol}_STALE",
            price_record=stale_record,
            cached=True,  # Stale data would typically be cached
            trend_service=None
        )

        # Test fresh data timestamp
        fresh_parsed = datetime.fromisoformat(fresh_response.fetched_at.replace('Z', '+00:00'))
        fresh_age_minutes = (utc_now() - fresh_parsed).total_seconds() / 60
        assert fresh_age_minutes < 30, f"Fresh data should not be stale: {fresh_age_minutes} minutes"

        # Test stale data timestamp
        stale_parsed = datetime.fromisoformat(stale_response.fetched_at.replace('Z', '+00:00'))
        stale_age_minutes = (utc_now() - stale_parsed).total_seconds() / 60
        assert stale_age_minutes > 30, f"Stale data should be old: {stale_age_minutes} minutes"
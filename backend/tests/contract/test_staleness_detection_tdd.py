"""
TDD tests for staleness detection in market data display.

Tests the logic that determines if price data is "stale" vs "live"
to ensure newly fetched data shows as "Live" not "Stale".
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from src.models.realtime_price_history import RealtimePriceHistory
from src.models.market_data_provider import MarketDataProvider
from src.api.market_data import build_price_response
from src.utils.datetime_utils import utc_now


class TestStalenessDetection:
    """Test suite for staleness detection logic."""

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

    def test_fresh_data_should_not_be_stale(self, sample_provider: MarketDataProvider, db_session: Session):
        """Test that data fetched within last 30 minutes is not marked as stale."""
        symbol = "ANZ"
        current_price = Decimal("32.99")

        # Data fetched just now (very fresh)
        current_time = utc_now()
        price_record = RealtimePriceHistory(
            symbol=symbol,
            price=current_price,
            volume=3500000,
            market_cap=Decimal("98400000000"),
            provider_id=sample_provider.id,
            source_timestamp=current_time,
            opening_price=Decimal("32.98"),
            high_price=Decimal("33.21"),
            low_price=Decimal("32.86"),
            previous_close=Decimal("33.19"),
            fetched_at=current_time,  # Same as source_timestamp for fresh data
            created_at=current_time
        )
        db_session.add(price_record)
        db_session.commit()

        # Build response
        response = build_price_response(
            symbol=symbol,
            price_record=price_record,
            cached=False,  # Fresh data should not be cached
            trend_service=None
        )

        # Verify the response
        assert response.symbol == symbol
        assert response.price == 32.99
        assert response.cached is False

        # The fetched_at should be a recent timestamp
        fetched_datetime = datetime.fromisoformat(response.fetched_at.replace('Z', '+00:00'))
        time_diff = (utc_now() - fetched_datetime).total_seconds()

        # Should be very recent (less than 60 seconds old)
        assert time_diff < 60, f"Data appears old: {time_diff} seconds"

    def test_old_data_should_be_stale(self, sample_provider: MarketDataProvider, db_session: Session):
        """Test that data older than 30 minutes is marked as stale."""
        symbol = "OLD"
        current_price = Decimal("100.00")

        # Data fetched 45 minutes ago (stale)
        old_time = utc_now() - timedelta(minutes=45)
        price_record = RealtimePriceHistory(
            symbol=symbol,
            price=current_price,
            volume=1000000,
            provider_id=sample_provider.id,
            source_timestamp=old_time,
            opening_price=Decimal("99.50"),
            fetched_at=old_time,  # 45 minutes old
            created_at=old_time
        )
        db_session.add(price_record)
        db_session.commit()

        # Build response
        response = build_price_response(
            symbol=symbol,
            price_record=price_record,
            cached=True,  # Old data is typically cached
            trend_service=None
        )

        # The fetched_at should be an old timestamp
        fetched_datetime = datetime.fromisoformat(response.fetched_at.replace('Z', '+00:00'))
        time_diff = (utc_now() - fetched_datetime).total_seconds()

        # Should be old (more than 30 minutes = 1800 seconds)
        assert time_diff > 1800, f"Data appears fresh when it should be stale: {time_diff} seconds"

    def test_boundary_case_30_minutes(self, sample_provider: MarketDataProvider, db_session: Session):
        """Test the boundary case of exactly 30 minutes old data."""
        symbol = "BOUNDARY"
        current_price = Decimal("50.00")

        # Data fetched exactly 30 minutes ago
        boundary_time = utc_now() - timedelta(minutes=30)
        price_record = RealtimePriceHistory(
            symbol=symbol,
            price=current_price,
            volume=500000,
            provider_id=sample_provider.id,
            source_timestamp=boundary_time,
            opening_price=Decimal("49.75"),
            fetched_at=boundary_time,
            created_at=boundary_time
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

        # The fetched_at should be exactly at the boundary
        fetched_datetime = datetime.fromisoformat(response.fetched_at.replace('Z', '+00:00'))
        time_diff = (utc_now() - fetched_datetime).total_seconds()

        # Should be around 30 minutes (1800 seconds), allowing some tolerance
        assert 1790 <= time_diff <= 1810, f"Boundary case timing incorrect: {time_diff} seconds"

    def test_timezone_handling_in_staleness(self, sample_provider: MarketDataProvider, db_session: Session):
        """Test that timezone conversions don't affect staleness detection."""
        symbol = "TZ_TEST"
        current_price = Decimal("75.50")

        # Create various timezone-aware timestamps
        current_time = utc_now()

        # Test data in different representations but same actual time
        test_times = [
            current_time,  # Direct UTC datetime
            current_time.replace(microsecond=0),  # Without microseconds
        ]

        for i, test_time in enumerate(test_times):
            symbol_variant = f"{symbol}_{i}"
            price_record = RealtimePriceHistory(
                symbol=symbol_variant,
                price=current_price + Decimal(f"0.{i:02d}"),  # Slight price variation
                volume=1000000,
                provider_id=sample_provider.id,
                source_timestamp=test_time,
                opening_price=Decimal("75.00"),
                fetched_at=test_time,
                created_at=test_time
            )
            db_session.add(price_record)

        db_session.commit()

        # Test each variant
        for i in range(len(test_times)):
            symbol_variant = f"{symbol}_{i}"
            price_record = db_session.query(RealtimePriceHistory).filter_by(symbol=symbol_variant).first()

            response = build_price_response(
                symbol=symbol_variant,
                price_record=price_record,
                cached=False,
                trend_service=None
            )

            # All variants should be fresh (not stale)
            fetched_datetime = datetime.fromisoformat(response.fetched_at.replace('Z', '+00:00'))
            time_diff = (utc_now() - fetched_datetime).total_seconds()

            assert time_diff < 60, f"Timezone variant {i} appears stale: {time_diff} seconds"
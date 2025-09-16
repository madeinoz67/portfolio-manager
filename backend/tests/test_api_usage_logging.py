"""
Test API usage logging without constraint errors.

This test ensures that the API usage logging system works correctly
and that datetime objects are properly stored in the database.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.models.market_data_usage_metrics import MarketDataUsageMetrics
from src.models.market_data_provider import MarketDataProvider
from src.services.market_data_service import MarketDataService


def test_api_usage_logging_without_constraint_errors(db: Session):
    """
    Test that API usage can be logged without database constraint errors.

    This test verifies that:
    1. Both recorded_at and time_bucket use datetime objects
    2. No constraint errors occur during insert
    3. The data is correctly stored and retrievable
    """
    # Create a test provider
    provider = MarketDataProvider(
        name="test_provider",
        display_name="Test Provider",
        is_enabled=True,
        priority=1,
        rate_limit_per_minute=100,
        rate_limit_per_day=1000
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)

    # Create market data service
    service = MarketDataService(db)

    # Test successful API usage logging
    service._log_api_usage(
        provider=provider,
        symbol="TEST",
        status_code=200,
        success=True
    )

    # Verify the record was created without errors
    usage_record = db.query(MarketDataUsageMetrics).filter(
        MarketDataUsageMetrics.provider_id == "test_provider"
    ).first()

    assert usage_record is not None
    assert usage_record.provider_id == "test_provider"
    assert usage_record.requests_count == 1
    assert usage_record.data_points_fetched == 1
    assert usage_record.error_count == 0

    # Verify datetime fields are properly set
    assert isinstance(usage_record.recorded_at, datetime)
    assert isinstance(usage_record.time_bucket, datetime)

    # Verify time_bucket is a rounded-down hour
    expected_time_bucket = usage_record.recorded_at.replace(minute=0, second=0, microsecond=0)
    assert usage_record.time_bucket == expected_time_bucket


def test_api_usage_logging_error_case(db: Session):
    """Test API usage logging for error cases."""
    # Create a test provider
    provider = MarketDataProvider(
        name="test_provider_error",
        display_name="Test Provider Error",
        is_enabled=True,
        priority=1,
        rate_limit_per_minute=100,
        rate_limit_per_day=1000
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)

    # Create market data service
    service = MarketDataService(db)

    # Test error API usage logging
    service._log_api_usage(
        provider=provider,
        symbol="ERROR_TEST",
        status_code=500,
        success=False,
        error_message="API rate limit exceeded"
    )

    # Verify the error record was created
    usage_record = db.query(MarketDataUsageMetrics).filter(
        MarketDataUsageMetrics.provider_id == "test_provider_error"
    ).first()

    assert usage_record is not None
    assert usage_record.provider_id == "test_provider_error"
    assert usage_record.requests_count == 1
    assert usage_record.data_points_fetched == 0  # No data on error
    assert usage_record.error_count == 1


def test_multiple_api_usage_logs_same_hour(db: Session):
    """Test that multiple API calls in the same hour work correctly."""
    # Create a test provider
    provider = MarketDataProvider(
        name="test_provider_multi",
        display_name="Test Provider Multi",
        is_enabled=True,
        priority=1,
        rate_limit_per_minute=100,
        rate_limit_per_day=1000
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)

    # Create market data service
    service = MarketDataService(db)

    # Log multiple API calls
    symbols = ["AAPL", "GOOGL", "MSFT"]
    for symbol in symbols:
        service._log_api_usage(
            provider=provider,
            symbol=symbol,
            status_code=200,
            success=True
        )

    # Verify all records were created
    usage_records = db.query(MarketDataUsageMetrics).filter(
        MarketDataUsageMetrics.provider_id == "test_provider_multi"
    ).all()

    assert len(usage_records) == 3

    # All should have the same time_bucket (same hour)
    time_buckets = [record.time_bucket for record in usage_records]
    assert len(set(time_buckets)) == 1  # All should be the same hour

    # All should have proper datetime objects
    for record in usage_records:
        assert isinstance(record.recorded_at, datetime)
        assert isinstance(record.time_bucket, datetime)
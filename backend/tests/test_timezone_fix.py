"""
Test to verify timezone handling in datetime utilities.

This test verifies that our datetime utilities properly handle UTC time
instead of incorrectly treating local time as UTC.
"""
import pytest
from datetime import datetime, timezone
from src.utils.datetime_utils import now, utc_now, to_iso_string


def test_now_returns_utc_time():
    """Test that now() returns UTC time, not local time."""
    current_time = now()
    utc_time = utc_now()

    # The times should be very close (within 1 second) if both are UTC
    time_diff = abs((current_time - utc_time).total_seconds())
    assert time_diff < 1, f"now() and utc_now() should return similar times, got diff: {time_diff}s"

    # now() should have timezone info indicating UTC
    if current_time.tzinfo is not None:
        assert current_time.tzinfo == timezone.utc, "now() should return UTC timezone-aware datetime"


def test_to_iso_string_formats_correctly():
    """Test that to_iso_string produces JavaScript-compatible ISO strings."""
    # Test with timezone-aware UTC datetime
    utc_dt = datetime(2025, 9, 14, 21, 34, 1, 217989, timezone.utc)
    iso_string = to_iso_string(utc_dt)

    # Should use the existing timezone info
    assert iso_string == "2025-09-14T21:34:01.217989+00:00"

    # Test with naive datetime (should be treated as UTC)
    naive_dt = datetime(2025, 9, 14, 21, 34, 1, 217989)
    iso_string_naive = to_iso_string(naive_dt)

    # Should add Z suffix for UTC
    assert iso_string_naive == "2025-09-14T21:34:01.217989Z"


def test_iso_string_javascript_compatibility():
    """Test that our ISO strings are compatible with JavaScript Date constructor."""
    # This would be tested in frontend, but we can verify format
    test_cases = [
        # UTC timezone-aware datetime
        (datetime(2025, 9, 14, 21, 34, 1, 217989, timezone.utc), "2025-09-14T21:34:01.217989+00:00"),
        # Naive datetime treated as UTC
        (datetime(2025, 9, 14, 13, 34, 1, 217989), "2025-09-14T13:34:01.217989Z"),
    ]

    for dt, expected in test_cases:
        result = to_iso_string(dt)
        assert result == expected

        # Verify no invalid patterns like "+00:00Z"
        assert not result.endswith("+00:00Z"), f"Invalid pattern in: {result}"
        assert not result.endswith("Z+00:00"), f"Invalid pattern in: {result}"
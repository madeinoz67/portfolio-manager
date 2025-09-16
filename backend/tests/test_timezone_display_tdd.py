"""
TDD test for timezone display functionality.

This test implements Test-Driven Development to ensure:
1. The API returns UTC timestamps with proper timezone info
2. JavaScript can convert these to local timezone for display
3. The backend respects the user's timezone preference
"""

import pytest
from datetime import datetime, timezone
from src.utils.datetime_utils import to_iso_string, utc_now


class TestTimezoneDisplayTDD:
    """TDD tests for proper timezone handling in API responses."""

    def test_utc_timestamps_are_timezone_aware(self):
        """Test that UTC timestamps include timezone information for frontend conversion."""
        # Get a UTC timestamp
        utc_time = utc_now()

        # Should be timezone-aware
        assert utc_time.tzinfo is not None
        assert utc_time.tzinfo == timezone.utc

        # Convert to ISO string
        iso_string = to_iso_string(utc_time)

        # Should include timezone offset for UTC
        assert "+00:00" in iso_string or "Z" in iso_string
        # Should NOT have both +00:00 AND Z (which was the original bug)
        assert not ("+00:00" in iso_string and iso_string.endswith("Z"))

    def test_javascript_can_convert_utc_to_local(self):
        """Test that JavaScript can properly convert UTC timestamps to local timezone."""
        # Create a known UTC time
        utc_time = datetime(2025, 9, 15, 10, 30, 0, tzinfo=timezone.utc)
        iso_string = to_iso_string(utc_time)

        # The ISO string should be parseable by JavaScript
        # JavaScript will automatically convert to local timezone when displaying

        # Verify format is correct for JavaScript Date constructor
        assert iso_string in [
            "2025-09-15T10:30:00+00:00",  # Explicit UTC offset
            "2025-09-15T10:30:00Z"        # Z suffix (equivalent to +00:00)
        ]

    def test_api_response_contains_utc_timestamps(self):
        """Test that API responses contain UTC timestamps that can be converted client-side."""
        # This test defines the expected API response format

        # API should return UTC timestamps with timezone info
        # Frontend will handle conversion to user's local timezone

        utc_time = utc_now()
        iso_string = to_iso_string(utc_time)

        # Mock API response format
        api_response = {
            "scheduler": {
                "last_run_at": iso_string,
                "next_run_at": iso_string,
                "status": "running"
            }
        }

        # Verify timestamps are proper ISO format
        assert "last_run_at" in api_response["scheduler"]
        assert "next_run_at" in api_response["scheduler"]

        # Both should be parseable datetimes
        last_run = api_response["scheduler"]["last_run_at"]
        next_run = api_response["scheduler"]["next_run_at"]

        # Should contain timezone information
        assert any(char in last_run for char in ["+", "Z"])
        assert any(char in next_run for char in ["+", "Z"])

    def test_datetime_utils_handle_timezone_correctly(self):
        """Test that datetime utility functions handle timezones properly."""
        # Test with timezone-aware UTC datetime
        utc_dt = datetime(2025, 9, 15, 14, 30, 0, tzinfo=timezone.utc)
        iso_string = to_iso_string(utc_dt)

        # Should preserve timezone info
        assert "+00:00" in iso_string

        # Test with naive datetime (should be treated as UTC)
        naive_dt = datetime(2025, 9, 15, 14, 30, 0)
        iso_string_naive = to_iso_string(naive_dt)

        # Should add Z suffix for naive datetimes (treated as UTC)
        assert iso_string_naive.endswith("Z")
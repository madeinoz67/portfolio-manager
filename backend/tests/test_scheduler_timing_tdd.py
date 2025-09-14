"""
TDD test for scheduler timing display issues.

This test implements Test-Driven Development to ensure:
1. The scheduler API returns valid date formats
2. Date parsing works correctly on frontend
3. Timing information displays properly
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from src.api.market_data import get_scheduler_status
from src.models.user import User, UserRole


class TestSchedulerTimingTDD:
    """TDD tests for scheduler timing display functionality."""

    @pytest.fixture
    def admin_user(self):
        """Create an admin user for testing."""
        user = User(
            email="admin@test.com",
            password_hash="hashed",
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            is_active=True
        )
        return user

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        mock_session = MagicMock(spec=Session)
        return mock_session

    @pytest.mark.asyncio
    async def test_scheduler_status_returns_valid_dates(self, admin_user, mock_db_session):
        """Test that scheduler status API returns properly formatted dates."""
        try:
            # Act
            result = await get_scheduler_status(
                current_admin=admin_user,
                db=mock_db_session
            )

            # Assert - check response structure
            assert "scheduler" in result
            scheduler_info = result["scheduler"]

            # Check that date fields exist
            assert "last_run" in scheduler_info
            assert "next_run" in scheduler_info
            assert "uptime_seconds" in scheduler_info

            # Test that dates are either None or valid ISO format strings
            if scheduler_info["last_run"] is not None:
                # Should be parseable as ISO datetime
                datetime.fromisoformat(scheduler_info["last_run"].replace('Z', '+00:00'))

            if scheduler_info["next_run"] is not None:
                # Should be parseable as ISO datetime
                datetime.fromisoformat(scheduler_info["next_run"].replace('Z', '+00:00'))

            # Uptime should be a number
            assert isinstance(scheduler_info["uptime_seconds"], (int, float))

        except Exception as e:
            pytest.fail(f"Scheduler status API failed: {e}")

    @pytest.mark.asyncio
    async def test_scheduler_status_with_mock_data(self, admin_user, mock_db_session):
        """Test scheduler status with known good data."""
        # This test will help us understand the current date format issues

        try:
            result = await get_scheduler_status(
                current_admin=admin_user,
                db=mock_db_session
            )

            # Print actual response for debugging
            print(f"Actual scheduler response: {result}")

            # The test should pass but give us insight into the data format
            assert "scheduler" in result

        except Exception as e:
            pytest.fail(f"Failed to get scheduler status: {e}")

    def test_date_formatting_expectations(self):
        """Test what date formats should be returned by the API."""
        # Define expected date format patterns
        now = datetime.now()
        future = now + timedelta(minutes=15)

        # ISO format with timezone (what frontend expects)
        expected_iso = now.isoformat()

        # Verify our expectations
        assert "T" in expected_iso
        parsed_back = datetime.fromisoformat(expected_iso)
        assert parsed_back == now

        # Test with timezone info
        expected_iso_tz = now.isoformat() + "Z"
        # Frontend should handle this format
        parsed_tz = datetime.fromisoformat(expected_iso_tz.replace('Z', '+00:00'))
        assert parsed_tz is not None
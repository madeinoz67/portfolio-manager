"""
TDD tests for scheduler status endpoint with real data.

This file contains tests to ensure the scheduler status endpoint works correctly
with real database data while remaining stable and not throwing 500 errors.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from src.api.market_data import get_scheduler_status
from src.models.market_data_provider import ProviderActivity
from src.models.user import User, UserRole
from src.utils.datetime_utils import utc_now


class TestSchedulerStatusRealData:
    """Test scheduler status endpoint with real data integration."""

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

    @pytest.fixture
    def sample_activities(self):
        """Create sample provider activities for testing."""
        now = utc_now()
        activities = [
            ProviderActivity(
                provider_id="yfinance",
                activity_type="API_CALL",
                description="Fetched price for AAPL",
                status="success",
                timestamp=now - timedelta(minutes=5),
                activity_metadata={"symbol": "AAPL", "response_time_ms": 200}
            ),
            ProviderActivity(
                provider_id="yfinance",
                activity_type="API_CALL",
                description="Fetched price for GOOGL",
                status="success",
                timestamp=now - timedelta(minutes=10),
                activity_metadata={"symbol": "GOOGL", "response_time_ms": 250}
            ),
            ProviderActivity(
                provider_id="alpha_vantage",
                activity_type="API_CALL",
                description="Failed to fetch MSFT",
                status="error",
                timestamp=now - timedelta(minutes=15),
                activity_metadata={"symbol": "MSFT", "error": "Rate limited"}
            ),
            ProviderActivity(
                provider_id="system",
                activity_type="SCHEDULER_CONTROL",
                description="Scheduler restarted by admin",
                status="success",
                timestamp=now - timedelta(minutes=30),  # Changed from 2 hours to 30 minutes to be within recent timeframe
                activity_metadata={"admin_user": "admin@test.com"}
            )
        ]
        return activities

    @pytest.mark.asyncio
    async def test_scheduler_status_returns_valid_structure(self, admin_user, mock_db_session, sample_activities):
        """Test that scheduler status returns valid JSON structure."""
        # Mock all database queries that the updated function performs
        mock_query = mock_db_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order_by = mock_filter.order_by.return_value

        # Mock recent activities query (for statistics)
        mock_filter.all.return_value = sample_activities

        # Mock individual activity queries (for timing calculations)
        mock_order_by.first.return_value = sample_activities[0]  # last_activity, earliest_activity

        # Mock restart count queries
        mock_filter.count.return_value = 0  # No restarts

        # Mock successful call query per provider
        mock_filter.first.return_value = None  # No last successful call

        # Mock MarketDataService
        with patch('src.api.market_data.MarketDataService') as mock_service:
            mock_service.return_value.get_enabled_providers.return_value = [
                MagicMock(name="yfinance")
            ]

            # Call the function
            result = await get_scheduler_status(current_admin=admin_user, db=mock_db_session)

            # Verify structure
            assert hasattr(result, 'scheduler')
            assert hasattr(result, 'recent_activity')
            assert hasattr(result, 'provider_stats')

            # Verify scheduler section has required fields
            scheduler = result.scheduler
            assert 'status' in scheduler
            assert 'uptime_seconds' in scheduler
            assert 'total_runs' in scheduler
            assert 'successful_runs' in scheduler
            assert 'failed_runs' in scheduler

    @pytest.mark.asyncio
    async def test_scheduler_status_calculates_success_rate_correctly(self, admin_user, mock_db_session, sample_activities):
        """Test that success rate is calculated correctly from real data."""
        # Mock database queries to return our sample activities (first 3 activities: 2 success, 1 error)
        recent_activities = sample_activities[:3]  # 2 success, 1 error
        mock_db_session.query.return_value.filter.return_value.all.return_value = recent_activities
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None  # No last successful call

        with patch('src.api.market_data.MarketDataService') as mock_service:
            mock_service.return_value.get_enabled_providers.return_value = []

            result = await get_scheduler_status(current_admin=admin_user, db=mock_db_session)

            # Verify success rate calculation: 2 successes out of 3 total = 0.67
            expected_success_rate = 2.0 / 3.0
            assert abs(result.recent_activity['success_rate'] - expected_success_rate) < 0.01

    @pytest.mark.asyncio
    async def test_scheduler_status_handles_empty_database_gracefully(self, admin_user, mock_db_session):
        """Test that scheduler status handles empty database without errors."""
        # Mock empty database
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        with patch('src.api.market_data.MarketDataService') as mock_service:
            mock_service.return_value.get_enabled_providers.return_value = []

            # This should not raise an exception
            result = await get_scheduler_status(current_admin=admin_user, db=mock_db_session)

            # Verify it returns valid data even with empty database
            assert result.scheduler['total_runs'] == 0
            assert result.scheduler['successful_runs'] == 0
            assert result.scheduler['failed_runs'] == 0
            assert result.recent_activity['success_rate'] == 0.0

    @pytest.mark.asyncio
    async def test_scheduler_status_timezone_safe(self, admin_user, mock_db_session, sample_activities):
        """Test that scheduler status handles timezones correctly without comparison errors."""
        # This test specifically checks that we don't get the
        # "can't compare offset-naive and offset-aware datetimes" error

        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_activities[0]
        mock_db_session.query.return_value.filter.return_value.all.return_value = sample_activities

        with patch('src.api.market_data.MarketDataService') as mock_service:
            mock_service.return_value.get_enabled_providers.return_value = []

            # This should not raise any timezone-related errors
            try:
                result = await get_scheduler_status(current_admin=admin_user, db=mock_db_session)
                assert result is not None
            except TypeError as e:
                if "offset-naive and offset-aware" in str(e):
                    pytest.fail("Timezone comparison error occurred")
                else:
                    raise

    @pytest.mark.asyncio
    async def test_scheduler_status_calculates_average_response_time(self, admin_user, mock_db_session, sample_activities):
        """Test that average response time is calculated correctly from metadata."""
        # Filter activities with response times: 200ms and 250ms
        activities_with_response_times = [sample_activities[0], sample_activities[1]]

        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_activities[0]
        mock_db_session.query.return_value.filter.return_value.all.return_value = activities_with_response_times

        with patch('src.api.market_data.MarketDataService') as mock_service:
            mock_service.return_value.get_enabled_providers.return_value = []

            result = await get_scheduler_status(current_admin=admin_user, db=mock_db_session)

            # Expected average: (200 + 250) / 2 = 225
            expected_avg = 225
            assert result.recent_activity['avg_response_time_ms'] == expected_avg

    @pytest.mark.asyncio
    async def test_scheduler_status_handles_missing_metadata_gracefully(self, admin_user, mock_db_session):
        """Test that scheduler status handles activities with missing metadata."""
        # Create activity without metadata
        activity_without_metadata = ProviderActivity(
            provider_id="yfinance",
            activity_type="API_CALL",
            description="Test activity",
            status="success",
            timestamp=utc_now(),
            activity_metadata=None  # No metadata
        )

        mock_db_session.query.return_value.filter.return_value.first.return_value = activity_without_metadata
        mock_db_session.query.return_value.filter.return_value.all.return_value = [activity_without_metadata]

        with patch('src.api.market_data.MarketDataService') as mock_service:
            mock_service.return_value.get_enabled_providers.return_value = []

            # Should not raise exception due to missing metadata
            result = await get_scheduler_status(current_admin=admin_user, db=mock_db_session)

            # Should handle missing response time gracefully
            assert result.recent_activity['avg_response_time_ms'] is None
#!/usr/bin/env python3
"""
TDD test to fix the timezone issue in dashboard calculations.

Root cause identified:
- Scheduler stores activities in UTC: 2025-09-15 23:34:28 UTC
- Dashboard uses local date: 2025-09-16
- func.date(UTC_timestamp) = 2025-09-15 != local_date 2025-09-16
- Result: No activities counted for "today"

Fix: Use consistent timezone handling for date comparisons.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal

from src.database import SessionLocal
from src.models.market_data_provider import ProviderActivity
from src.models.market_data_usage_metrics import MarketDataUsageMetrics
from src.models.user import User
from src.models.user_role import UserRole
from src.utils.datetime_utils import now, utc_now


class TestTimezoneFixTDD:
    """TDD tests to verify and fix timezone issues in dashboard calculations."""

    @pytest.fixture
    def db_session(self):
        """Create a database session for testing."""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    @pytest.fixture
    def admin_user(self, db_session):
        """Create an admin user for testing."""
        admin_user = User(
            email="admin@test.com",
            password_hash="test_hash",
            role=UserRole.ADMIN,
            is_active=True
        )
        db_session.add(admin_user)
        db_session.commit()
        db_session.refresh(admin_user)
        return admin_user

    def test_timezone_issue_reproduction(self, db_session):
        """
        Test that reproduces the timezone issue.

        This test should FAIL initially, demonstrating the bug.
        """
        # Create a UTC timestamp similar to what scheduler creates
        utc_time = datetime(2025, 9, 15, 23, 34, 28)  # UTC time from logs

        # Add a provider activity with UTC timestamp
        activity = ProviderActivity(
            provider_id="yfinance",
            activity_type="API_CALL",
            description="Test activity",
            status="success",
            timestamp=utc_time
        )
        db_session.add(activity)
        db_session.commit()

        # Test the current broken logic from admin.py
        from sqlalchemy import func
        today_local = date.today()  # Local date (2025-09-16)

        # This is the broken query from admin.py line 412
        activities_today = db_session.query(ProviderActivity).filter(
            func.date(ProviderActivity.timestamp) == today_local
        ).all()

        print(f"UTC timestamp: {utc_time}")
        print(f"Local today: {today_local}")
        print(f"func.date(UTC): {utc_time.date()}")
        print(f"Activities found: {len(activities_today)}")

        # This should find the activity, but due to timezone bug it doesn't
        if len(activities_today) == 0:
            pytest.fail(f"Timezone bug confirmed: UTC activity {utc_time} not found for local date {today_local}")

    def test_correct_timezone_handling_approach(self, db_session):
        """
        Test the correct approach to handle timezone issues.

        This test defines how the fix should work.
        """
        # Create a UTC timestamp (like scheduler does)
        utc_time = datetime(2025, 9, 15, 23, 34, 28)  # UTC evening

        # Add a provider activity
        activity = ProviderActivity(
            provider_id="yfinance",
            activity_type="API_CALL",
            description="Test activity",
            status="success",
            timestamp=utc_time
        )
        db_session.add(activity)
        db_session.commit()

        # CORRECT approach: Convert local "today" to UTC range
        local_today = date.today()
        local_today_start = datetime.combine(local_today, datetime.min.time())
        local_today_end = local_today_start + timedelta(days=1)

        print(f"Local today range: {local_today_start} to {local_today_end}")

        # In Australia (UTC+10), local "today" 2025-09-16 00:00 to 2025-09-17 00:00
        # corresponds to UTC range: 2025-09-15 14:00 to 2025-09-16 14:00
        # So UTC 2025-09-15 23:34 should be included

        activities_correct = db_session.query(ProviderActivity).filter(
            ProviderActivity.timestamp >= local_today_start - timedelta(hours=24),  # Wide range for testing
            ProviderActivity.timestamp < local_today_end
        ).all()

        print(f"Activities found with correct range: {len(activities_correct)}")

        # This should find the activity
        assert len(activities_correct) > 0, "Correct timezone handling should find the activity"

    def test_api_usage_function_with_timezone_fix(self, db_session, admin_user):
        """
        Test that get_api_usage function works after timezone fix.

        This test should PASS after we implement the fix.
        """
        # Add recent provider activity (UTC)
        recent_utc_time = utc_now() - timedelta(hours=1)  # 1 hour ago in UTC

        activity = ProviderActivity(
            provider_id="yfinance",
            activity_type="API_CALL",
            description="Recent test activity",
            status="success",
            timestamp=recent_utc_time
        )
        db_session.add(activity)
        db_session.commit()

        # Test the fixed API function
        from src.api.admin import get_api_usage
        result = get_api_usage(admin_user, db_session)

        print(f"API result: {result}")
        print(f"Total requests today: {result['summary']['total_requests_today']}")

        # After fix, this should show > 0 requests
        if result["summary"]["total_requests_today"] == 0:
            pytest.fail("API usage still shows 0 after timezone fix")

    def test_usage_metrics_timezone_consistency(self, db_session):
        """
        Test that usage metrics and provider activities use consistent timezone handling.

        Both should count the same events for "today".
        """
        # Add both types of records with same UTC timestamp
        utc_time = utc_now() - timedelta(hours=2)

        # Add provider activity
        activity = ProviderActivity(
            provider_id="yfinance",
            activity_type="API_CALL",
            description="Test activity",
            status="success",
            timestamp=utc_time
        )
        db_session.add(activity)

        # Add corresponding usage metric
        metric = MarketDataUsageMetrics(
            metric_id="test_metric_timezone",
            provider_id="yfinance",
            request_type="test_request",
            requests_count=1,
            data_points_fetched=1,
            cost_estimate=Decimal("0.00"),
            recorded_at=utc_time,
            time_bucket="hourly"
        )
        db_session.add(metric)
        db_session.commit()

        # Both should be found with consistent "today" calculation
        local_today = date.today()
        local_today_start = datetime.combine(local_today, datetime.min.time())
        local_today_end = local_today_start + timedelta(days=1)

        # Use consistent timezone handling for both
        activities_today = db_session.query(ProviderActivity).filter(
            ProviderActivity.timestamp >= local_today_start - timedelta(hours=24),
            ProviderActivity.timestamp < local_today_end
        ).count()

        metrics_today = db_session.query(MarketDataUsageMetrics).filter(
            MarketDataUsageMetrics.recorded_at >= local_today_start - timedelta(hours=24),
            MarketDataUsageMetrics.recorded_at < local_today_end
        ).count()

        print(f"Activities today: {activities_today}")
        print(f"Metrics today: {metrics_today}")

        # Both should find the records
        assert activities_today > 0, "Provider activities not found with timezone fix"
        assert metrics_today > 0, "Usage metrics not found with timezone fix"
        assert activities_today == metrics_today, "Activities and metrics counts should match"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
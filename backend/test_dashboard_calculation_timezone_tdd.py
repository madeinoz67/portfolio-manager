#!/usr/bin/env python3
"""
TDD test to verify dashboard calculations work correctly with timezone handling.

The scheduler is working and creating metrics, but the dashboard shows 0.
This could be due to:
1. Timezone issues (UTC vs local time)
2. "Today" calculation using wrong timeframe
3. Dashboard using old metric names after refactoring
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from src.database import SessionLocal
from src.models.market_data_usage_metrics import MarketDataUsageMetrics
from src.models.market_data_provider import ProviderActivity
from src.api.admin import get_api_usage, get_market_data_status
from src.models.user import User
from src.models.user_role import UserRole
from src.utils.datetime_utils import now, utc_now


class TestDashboardCalculationTimezone:
    """Test dashboard calculations handle timezone and timeframes correctly."""

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

    def test_recent_metrics_are_found_in_database(self, db_session):
        """
        Test that we can find the recent metrics that the scheduler just created.

        This verifies our database queries work with recent data.
        """
        # Look for metrics from the last hour (scheduler just ran)
        one_hour_ago = datetime.now() - timedelta(hours=1)

        recent_metrics = db_session.query(MarketDataUsageMetrics).filter(
            MarketDataUsageMetrics.recorded_at >= one_hour_ago
        ).all()

        print(f"Found {len(recent_metrics)} metrics in last hour")

        if len(recent_metrics) == 0:
            pytest.fail("No recent metrics found. Scheduler metrics should be visible.")

        # Show the recent metrics
        for metric in recent_metrics:
            print(f"Metric: {metric.provider_id} - {metric.requests_count} requests at {metric.recorded_at}")

    def test_todays_metrics_calculation_matches_database(self, db_session, admin_user):
        """
        Test that the dashboard's "today" calculation matches what's in the database.

        This identifies timezone/timeframe calculation issues.
        """
        # Calculate "today" the same way the dashboard should
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        print(f"Today range: {today_start} to {today_end}")

        # Count metrics for today
        today_metrics = db_session.query(MarketDataUsageMetrics).filter(
            MarketDataUsageMetrics.recorded_at >= today_start,
            MarketDataUsageMetrics.recorded_at < today_end
        ).all()

        print(f"Database shows {len(today_metrics)} metrics for today")

        # Sum requests for today
        from sqlalchemy import func
        today_requests = db_session.query(func.sum(MarketDataUsageMetrics.requests_count)).filter(
            MarketDataUsageMetrics.recorded_at >= today_start,
            MarketDataUsageMetrics.recorded_at < today_end
        ).scalar() or 0

        print(f"Database shows {today_requests} total requests for today")

        # Now test what the API returns
        api_result = get_api_usage(admin_user, db_session)
        dashboard_requests = api_result["summary"]["total_requests_today"]

        print(f"Dashboard API returns {dashboard_requests} requests for today")

        # They should match
        if today_requests > 0 and dashboard_requests == 0:
            pytest.fail(f"Database has {today_requests} requests today but dashboard shows {dashboard_requests}. "
                       "Dashboard calculation is incorrect.")

    def test_provider_activities_are_visible_to_dashboard(self, db_session, admin_user):
        """
        Test that provider activities are visible to the dashboard calculations.

        This verifies the scheduler's activities are properly recorded and accessible.
        """
        # Look for recent activities
        one_hour_ago = datetime.now() - timedelta(hours=1)

        recent_activities = db_session.query(ProviderActivity).filter(
            ProviderActivity.timestamp >= one_hour_ago
        ).all()

        print(f"Found {len(recent_activities)} activities in last hour")

        if len(recent_activities) == 0:
            pytest.fail("No recent activities found. Scheduler should create activities.")

        # Test market data status API
        market_status = get_market_data_status(admin_user, db_session)

        print(f"Market data status: {market_status}")

        # Verify the API can see recent data
        for provider_id, provider_data in market_status.get("providers", {}).items():
            print(f"Provider {provider_id}: {provider_data}")

    def test_timezone_handling_in_calculations(self, db_session):
        """
        Test that timezone handling doesn't cause issues with recent data.

        The backend logs show times like '2025-09-15 23:34:28.303030'
        which may be UTC, while dashboard might use local time.
        """
        # Check what timezone our database records use
        recent_metric = db_session.query(MarketDataUsageMetrics).order_by(
            MarketDataUsageMetrics.recorded_at.desc()
        ).first()

        if recent_metric:
            print(f"Most recent metric timestamp: {recent_metric.recorded_at}")
            print(f"Type: {type(recent_metric.recorded_at)}")
            print(f"Timezone info: {recent_metric.recorded_at.tzinfo}")

            # Compare with current time calculations
            print(f"now(): {now()}")
            print(f"utc_now(): {utc_now()}")
            print(f"datetime.now(): {datetime.now()}")

            # Check if the recent metric falls within "today" by different calculations
            today_start_local = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_start_utc = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)

            print(f"Today start (local): {today_start_local}")
            print(f"Today start (UTC): {today_start_utc}")

            is_today_local = recent_metric.recorded_at >= today_start_local
            is_today_utc = recent_metric.recorded_at >= today_start_utc

            print(f"Recent metric is 'today' by local calc: {is_today_local}")
            print(f"Recent metric is 'today' by UTC calc: {is_today_utc}")

            if not is_today_local and not is_today_utc:
                pytest.fail("Recent metrics not recognized as 'today' by either timezone calculation")

    def test_dashboard_calculation_with_fresh_data(self, db_session, admin_user):
        """
        Test dashboard calculation after adding fresh test data.

        This isolates whether the issue is with calculation logic or existing data.
        """
        # Add a fresh metric record for right now
        current_time = now()  # Use the same function the app uses

        test_metric = MarketDataUsageMetrics(
            metric_id=f"test_dashboard_{int(current_time.timestamp())}",
            provider_id="yfinance",
            request_type="test_request",
            requests_count=5,
            data_points_fetched=5,
            cost_estimate=Decimal("0.00"),
            recorded_at=current_time,
            time_bucket="hourly",
            rate_limit_hit=False,
            error_count=0,
            avg_response_time_ms=100
        )

        db_session.add(test_metric)
        db_session.commit()

        print(f"Added test metric at {current_time}")

        # Now check if dashboard sees it
        api_result = get_api_usage(admin_user, db_session)
        dashboard_requests = api_result["summary"]["total_requests_today"]

        print(f"After adding test data, dashboard shows {dashboard_requests} requests")

        if dashboard_requests == 0:
            pytest.fail("Dashboard still shows 0 even after adding fresh test data. "
                       "Dashboard calculation logic is broken.")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
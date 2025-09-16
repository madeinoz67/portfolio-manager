"""
Test-Driven Development tests for admin dashboard recent activity feed.

Tests real activity data population for the admin dashboard recent activity section,
including different activity types, providers, statuses, and time-based filtering.
"""
from datetime import datetime, timedelta
from typing import List
import pytest
from sqlalchemy.orm import Session

from src.models.market_data_provider import ProviderActivity, MarketDataProvider
from src.services.activity_service import (
    log_provider_activity,
    get_recent_activities_all_providers,
    get_activity_summary_for_provider
)


class TestAdminDashboardActivities:
    """Test suite for admin dashboard recent activity feed functionality."""

    def test_create_realistic_activity_data(self, db_session: Session):
        """Test creation of realistic activity data matching the UI design."""
        # Create providers first
        yfinance_provider = MarketDataProvider(
            name="yfinance",
            display_name="Yahoo Finance",
            is_enabled=True,
            rate_limit_per_minute=60,
            rate_limit_per_day=60000,
            priority=1
        )

        alpha_provider = MarketDataProvider(
            name="alpha_vantage",
            display_name="Alpha Vantage",
            is_enabled=False,
            rate_limit_per_minute=5,
            rate_limit_per_day=15000,
            priority=2
        )

        db_session.add_all([yfinance_provider, alpha_provider])
        db_session.commit()

        # Create activities that match the UI examples
        now = datetime.utcnow()

        activities = [
            # "Successfully updated prices for 25 symbols" - Alpha Vantage, 2 minutes ago
            {
                "provider_id": "alpha_vantage",
                "activity_type": "BULK_PRICE_UPDATE",
                "description": "Successfully updated prices for 25 symbols",
                "status": "success",
                "timestamp": now - timedelta(minutes=2),
                "metadata": {"symbols_count": 25, "duration_ms": 3420}
            },

            # "Batch price update completed for S&P 500 stocks" - Yahoo Finance, 15 minutes ago
            {
                "provider_id": "yfinance",
                "activity_type": "BATCH_UPDATE",
                "description": "Batch price update completed for S&P 500 stocks",
                "status": "success",
                "timestamp": now - timedelta(minutes=15),
                "metadata": {"batch_size": 500, "success_rate": 0.98}
            },

            # "Switched to backup provider due to rate limiting" - Alpha Vantage, 1 hour ago
            {
                "provider_id": "alpha_vantage",
                "activity_type": "PROVIDER_SWITCH",
                "description": "Switched to backup provider due to rate limiting",
                "status": "warning",
                "timestamp": now - timedelta(hours=1),
                "metadata": {"reason": "rate_limit_exceeded", "backup_provider": "yfinance"}
            },

            # "High error rate detected, increased retry intervals" - Yahoo Finance, 3 hours ago
            {
                "provider_id": "yfinance",
                "activity_type": "ERROR_THRESHOLD",
                "description": "High error rate detected, increased retry intervals",
                "status": "warning",
                "timestamp": now - timedelta(hours=3),
                "metadata": {"error_rate": 0.15, "new_interval_sec": 300}
            },

            # "Daily rate limits reset for all providers" - System, 6 hours ago
            {
                "provider_id": "system",
                "activity_type": "RATE_LIMIT_RESET",
                "description": "Daily rate limits reset for all providers",
                "status": "info",
                "timestamp": now - timedelta(hours=6),
                "metadata": {"providers_reset": ["yfinance", "alpha_vantage"]}
            }
        ]

        # Log all activities
        created_activities = []
        for activity_data in activities:
            activity = log_provider_activity(
                db_session=db_session,
                **activity_data
            )
            created_activities.append(activity)

        # Verify all activities were created
        assert len(created_activities) == 5

        # Verify activity types match expected values
        expected_types = [
            "BULK_PRICE_UPDATE", "BATCH_UPDATE", "PROVIDER_SWITCH",
            "ERROR_THRESHOLD", "RATE_LIMIT_RESET"
        ]
        actual_types = [a.activity_type for a in created_activities]
        assert set(actual_types) == set(expected_types)

        # Verify status distribution
        success_count = len([a for a in created_activities if a.status == "success"])
        warning_count = len([a for a in created_activities if a.status == "warning"])
        info_count = len([a for a in created_activities if a.status == "info"])

        assert success_count == 2
        assert warning_count == 2
        assert info_count == 1

    def test_get_recent_activities_for_dashboard(self, db_session: Session):
        """Test fetching recent activities for the admin dashboard feed."""
        # Setup test data
        self.test_create_realistic_activity_data(db_session)

        # Get recent activities (should match dashboard requirements)
        recent_activities = get_recent_activities_all_providers(
            db_session=db_session,
            limit=10,
            page=1,
            size=10
        )

        # Verify we get activities back
        assert len(recent_activities) == 5

        # Verify activities are ordered by timestamp (newest first)
        timestamps = [activity.timestamp for activity in recent_activities]
        assert timestamps == sorted(timestamps, reverse=True)

        # Verify first activity is the most recent (2 minutes ago)
        most_recent = recent_activities[0]
        assert most_recent.activity_type == "BULK_PRICE_UPDATE"
        assert most_recent.description == "Successfully updated prices for 25 symbols"
        assert most_recent.status == "success"
        assert most_recent.provider_id == "alpha_vantage"
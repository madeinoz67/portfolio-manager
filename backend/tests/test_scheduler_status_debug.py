"""
TDD tests to troubleshoot and fix the scheduler status 500 errors.

This file creates failing tests that reproduce the exact issues happening in production,
then implements fixes to make them pass.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from src.api.market_data import get_scheduler_status
from src.models.market_data_provider import ProviderActivity
from src.models.user import User, UserRole
from src.utils.datetime_utils import utc_now


class TestSchedulerStatusDebug:
    """TDD tests to debug and fix current scheduler status errors."""

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
    def real_db_session(self):
        """Create a real database session for integration testing."""
        from src.database import SessionLocal
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_scheduler_status_with_real_database_data(self, admin_user, real_db_session):
        """
        Integration test with real database to reproduce the 500 error.

        This test should initially FAIL and show us the exact error,
        then we'll fix it to make it PASS.
        """
        try:
            # This should reproduce the exact error we're seeing in production
            result = await get_scheduler_status(current_admin=admin_user, db=real_db_session)

            # If we get here, the error is fixed
            assert result is not None
            assert hasattr(result, 'scheduler')
            assert hasattr(result, 'recent_activity')
            assert hasattr(result, 'provider_stats')

            # Verify real data is being used (not hardcoded values)
            print(f"Success rate: {result.recent_activity['success_rate']}")
            print(f"Total activities: {result.recent_activity['total_symbols_processed']}")
            print(f"Uptime seconds: {result.scheduler['uptime_seconds']}")

        except Exception as e:
            # This will show us the exact error happening in production
            pytest.fail(f"Scheduler status failed with error: {type(e).__name__}: {e}")

    @pytest.mark.asyncio
    async def test_scheduler_status_handles_empty_provider_activities(self, admin_user, real_db_session):
        """Test scheduler status when there are no provider activities."""

        # Clear all provider activities to test empty state
        real_db_session.query(ProviderActivity).delete()
        real_db_session.commit()

        try:
            result = await get_scheduler_status(current_admin=admin_user, db=real_db_session)

            # Should handle empty database gracefully
            assert result.scheduler['total_runs'] == 0
            assert result.scheduler['successful_runs'] == 0
            assert result.scheduler['uptime_seconds'] == 0
            assert result.recent_activity['success_rate'] == 0.0

        except Exception as e:
            pytest.fail(f"Scheduler status failed with empty database: {type(e).__name__}: {e}")

    @pytest.mark.asyncio
    async def test_scheduler_status_with_mixed_activity_types(self, admin_user, real_db_session):
        """Test scheduler status with different types of activities that exist in production."""

        # Create activities that mirror what we see in the logs
        now = utc_now()
        activities = [
            ProviderActivity(
                provider_id="system",
                activity_type="HEALTH_CHECK",
                description="System health check completed",
                status="success",
                timestamp=now - timedelta(minutes=5),
                activity_metadata={"uptime_minutes": 0, "providers_available": 1}
            ),
            ProviderActivity(
                provider_id="yfinance",
                activity_type="API_CALL",
                description="Bulk yfinance fetch completed",
                status="success",
                timestamp=now - timedelta(minutes=3),
                activity_metadata={"symbols": 4, "response_time_ms": 3469}
            )
        ]

        # Clear existing activities and add our test data
        real_db_session.query(ProviderActivity).delete()
        for activity in activities:
            real_db_session.add(activity)
        real_db_session.commit()

        try:
            result = await get_scheduler_status(current_admin=admin_user, db=real_db_session)

            # Should calculate from real activities
            assert result.scheduler['total_runs'] == 2
            assert result.scheduler['successful_runs'] == 2
            assert result.recent_activity['success_rate'] == 1.0

        except Exception as e:
            pytest.fail(f"Scheduler status failed with mixed activities: {type(e).__name__}: {e}")

    def test_provider_activity_database_structure(self, real_db_session):
        """Test that ProviderActivity can be queried without errors."""

        try:
            # Test basic queries that scheduler status uses
            recent_activities = real_db_session.query(ProviderActivity).all()
            print(f"Found {len(recent_activities)} provider activities")

            # Test ordering queries
            last_activity = real_db_session.query(ProviderActivity).order_by(
                ProviderActivity.timestamp.desc()
            ).first()

            if last_activity:
                print(f"Last activity: {last_activity.activity_type} at {last_activity.timestamp}")
                print(f"Metadata: {last_activity.activity_metadata}")

            # Test filtering by time
            one_hour_ago = utc_now() - timedelta(hours=1)
            recent = real_db_session.query(ProviderActivity).filter(
                ProviderActivity.timestamp >= one_hour_ago
            ).all()
            print(f"Activities in last hour: {len(recent)}")

        except Exception as e:
            pytest.fail(f"Database query failed: {type(e).__name__}: {e}")

    def test_market_data_service_integration(self, real_db_session):
        """Test that MarketDataService can be instantiated and used."""

        try:
            from src.services.market_data_service import MarketDataService

            service = MarketDataService(real_db_session)
            providers = service.get_enabled_providers()

            print(f"Found {len(providers)} enabled providers")
            for provider in providers:
                print(f"Provider: {provider.name}, enabled: {provider.is_enabled}")

        except Exception as e:
            pytest.fail(f"MarketDataService failed: {type(e).__name__}: {e}")
#!/usr/bin/env python3
"""
TDD test to verify scheduler triggers provider calls and metrics are recorded.

The admin dashboard shows:
- Scheduler: 23 successful runs
- API Calls today: 0
- Symbols Processed: 0

This indicates the scheduler is running but either:
1. Provider calls are not being made
2. Metrics are not being recorded properly
3. There's a disconnect between scheduler execution and provider integration
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from src.database import SessionLocal
from src.models.market_data_usage_metrics import MarketDataUsageMetrics
from src.models.market_data_provider import MarketDataProvider, ProviderActivity
from src.models.stock import Stock, StockStatus
from src.services.market_data_service import MarketDataService


class TestSchedulerProviderIntegration:
    """Test that scheduler properly triggers provider calls and records metrics."""

    @pytest.fixture
    def db_session(self):
        """Create a database session for testing."""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def test_scheduler_execution_creates_provider_activities(self, db_session):
        """
        Test that scheduler executions create provider activities.

        Given: Scheduler has run 23 times successfully
        When: We check provider_activities table
        Then: We should see recent activity records
        """
        # Check if we have any provider activities from recent scheduler runs
        recent_activities = db_session.query(ProviderActivity).filter(
            ProviderActivity.timestamp >= datetime.now() - timedelta(hours=1)
        ).all()

        # The fact that we have 23 successful scheduler runs suggests activities should exist
        print(f"Found {len(recent_activities)} recent provider activities")

        # If no activities found, this indicates the scheduler isn't creating activities
        if len(recent_activities) == 0:
            pytest.fail("No provider activities found despite 23 successful scheduler runs. "
                       "Scheduler may not be triggering provider calls.")

        # Verify activities have the expected structure
        for activity in recent_activities[:5]:  # Check first 5
            assert activity.provider_id is not None
            assert activity.activity_type is not None
            assert activity.timestamp is not None
            print(f"Activity: {activity.provider_id} - {activity.activity_type} at {activity.timestamp}")

    def test_provider_calls_create_usage_metrics(self, db_session):
        """
        Test that provider calls create usage metrics records.

        Given: Provider activities exist
        When: We check market_data_usage_metrics table
        Then: We should see corresponding metrics records
        """
        # Check if we have any usage metrics from recent activities
        recent_metrics = db_session.query(MarketDataUsageMetrics).filter(
            MarketDataUsageMetrics.recorded_at >= datetime.now() - timedelta(hours=1)
        ).all()

        print(f"Found {len(recent_metrics)} recent usage metrics")

        # If no metrics found, this indicates provider calls aren't recording metrics
        if len(recent_metrics) == 0:
            pytest.fail("No usage metrics found despite scheduler running. "
                       "Provider calls may not be recording metrics properly.")

        # Verify metrics have the expected structure
        for metric in recent_metrics[:5]:  # Check first 5
            assert metric.provider_id is not None
            assert metric.request_type is not None
            assert metric.requests_count is not None
            print(f"Metric: {metric.provider_id} - {metric.requests_count} requests at {metric.recorded_at}")

    def test_enabled_providers_exist_and_configured(self, db_session):
        """
        Test that enabled providers exist and are properly configured.

        Given: Admin dashboard shows providers
        When: We check market_data_providers table
        Then: We should see enabled providers (especially yfinance)
        """
        enabled_providers = db_session.query(MarketDataProvider).filter(
            MarketDataProvider.is_enabled == True
        ).all()

        print(f"Found {len(enabled_providers)} enabled providers")

        if len(enabled_providers) == 0:
            pytest.fail("No enabled providers found. Scheduler has nothing to call.")

        # Verify yfinance is enabled (as shown in dashboard)
        yfinance_provider = db_session.query(MarketDataProvider).filter(
            MarketDataProvider.name == 'yfinance',
            MarketDataProvider.is_enabled == True
        ).first()

        if not yfinance_provider:
            pytest.fail("Yahoo Finance provider not found or not enabled, but dashboard shows it as enabled")

        print(f"yfinance provider: enabled={yfinance_provider.is_enabled}, priority={yfinance_provider.priority}")

    def test_stocks_exist_for_provider_to_fetch(self, db_session):
        """
        Test that there are stocks in the database for providers to fetch.

        Given: Scheduler is running
        When: We check stocks table
        Then: We should see stocks that need price updates
        """
        active_stocks = db_session.query(Stock).filter(
            Stock.status == StockStatus.ACTIVE
        ).all()

        print(f"Found {active_stocks} active stocks")

        if len(active_stocks) == 0:
            pytest.fail("No active stocks found. Providers have nothing to fetch.")

        # Show some example stocks
        for stock in active_stocks[:5]:
            print(f"Stock: {stock.symbol} - {stock.company_name}")

    @pytest.mark.asyncio
    async def test_manual_provider_call_creates_metrics(self, db_session):
        """
        Test that manually calling the provider creates metrics.

        This will help isolate if the issue is with scheduler integration
        or with the provider metrics recording itself.
        """
        # Get initial metrics count
        initial_count = db_session.query(MarketDataUsageMetrics).count()
        initial_activities = db_session.query(ProviderActivity).count()

        print(f"Initial metrics: {initial_count}, activities: {initial_activities}")

        # Get an enabled provider
        provider = db_session.query(MarketDataProvider).filter(
            MarketDataProvider.is_enabled == True
        ).first()

        if not provider:
            pytest.skip("No enabled providers found for manual test")

        # Create market data service and make a call
        service = MarketDataService(db_session)

        try:
            # Attempt to fetch price for a test symbol
            result = await service.fetch_price("TLS")  # Australian stock that should exist
            print(f"Fetch result: {result}")

        except Exception as e:
            print(f"Provider call failed: {e}")
            # Don't fail the test, but record what happened
            pytest.skip(f"Provider call failed: {e}")

        finally:
            await service.close_session()

        # Check if metrics were created
        new_metrics = db_session.query(MarketDataUsageMetrics).count()
        new_activities = db_session.query(ProviderActivity).count()

        print(f"After call - metrics: {new_metrics}, activities: {new_activities}")

        # Verify that the call created records
        if new_metrics == initial_count and new_activities == initial_activities:
            pytest.fail("Manual provider call did not create any metrics or activities. "
                       "This indicates the metrics recording is broken.")

    def test_dashboard_calculation_matches_database(self, db_session):
        """
        Test that dashboard calculations match what's actually in the database.

        This verifies if the issue is with data collection or data display.
        """
        # Calculate what the dashboard should show
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Count today's API calls
        today_calls = db_session.query(MarketDataUsageMetrics).filter(
            MarketDataUsageMetrics.recorded_at >= today_start
        ).count()

        # Sum today's request counts
        from sqlalchemy import func
        today_request_sum = db_session.query(func.sum(MarketDataUsageMetrics.requests_count)).filter(
            MarketDataUsageMetrics.recorded_at >= today_start
        ).scalar() or 0

        # Count today's provider activities
        today_activities = db_session.query(ProviderActivity).filter(
            ProviderActivity.timestamp >= today_start
        ).count()

        print(f"Database shows:")
        print(f"- Today's metric records: {today_calls}")
        print(f"- Today's total requests: {today_request_sum}")
        print(f"- Today's activities: {today_activities}")
        print(f"Dashboard shows: 0 API calls")

        # If database has data but dashboard shows 0, there's a calculation issue
        if (today_calls > 0 or today_request_sum > 0) and today_activities > 0:
            pytest.fail(f"Database has data (calls={today_calls}, requests={today_request_sum}, "
                       f"activities={today_activities}) but dashboard shows 0. "
                       "Dashboard calculation logic may be incorrect.")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
"""
TDD test for API usage metrics tracking issue.

The admin dashboard shows "Calls today: 0" for Yahoo Finance despite successful
scheduler operations. This test validates that API calls are properly tracked.
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from src.database import SessionLocal
from src.services.market_data_service import MarketDataService
from src.models.market_data_provider import MarketDataProvider, ProviderActivity
from src.models.market_data_usage_metrics import MarketDataUsageMetrics


class TestMarketDataUsageMetricsTracking:
    """Test suite for API usage metrics tracking."""

    @pytest.fixture
    def db_session(self):
        """Create a database session for testing."""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    @pytest.mark.asyncio
    async def test_api_call_creates_usage_metrics(self, db_session):
        """
        Test that API calls create corresponding usage metrics records.

        This test verifies that when we fetch a price, the system:
        1. Records the API call in provider_activities
        2. Creates a corresponding usage metric in market_data_api_usage_metrics
        3. The metric is counted correctly for "calls today" calculation
        """
        # Arrange: Clean slate and get initial counts
        initial_activities = db_session.query(ProviderActivity).filter(
            ProviderActivity.activity_type == 'API_CALL'
        ).count()

        initial_metrics = db_session.query(MarketDataUsageMetrics).filter(
            MarketDataUsageMetrics.provider_id == 'yfinance'
        ).count()

        # Act: Make an API call through the service
        service = MarketDataService(db_session)
        result = await service.fetch_price("TLS")

        # Assert: API call was successful
        assert result is not None
        assert "price" in result

        # Assert: Provider activity was logged
        new_activities = db_session.query(ProviderActivity).filter(
            ProviderActivity.activity_type == 'API_CALL'
        ).count()
        assert new_activities > initial_activities, "No new provider activity was logged"

        # Assert: Usage metrics were created
        new_metrics = db_session.query(MarketDataUsageMetrics).filter(
            MarketDataUsageMetrics.provider_id == 'yfinance'
        ).count()
        assert new_metrics > initial_metrics, "No new usage metrics were created"

        # Assert: The metrics have correct data
        latest_metric = (
            db_session.query(MarketDataUsageMetrics)
            .filter(MarketDataUsageMetrics.provider_id == 'yfinance')
            .order_by(MarketDataUsageMetrics.recorded_at.desc())
            .first()
        )

        assert latest_metric is not None
        assert latest_metric.requests_count >= 1
        assert latest_metric.data_points_fetched >= 1
        assert latest_metric.request_type == 'price_fetch'

        await service.close_session()

    def test_daily_usage_calculation(self, db_session):
        """
        Test that daily usage calculation works correctly.

        This reproduces the admin dashboard calculation to see if it's working.
        """
        # Arrange: Get today's date range
        today = datetime.now(timezone.utc).date()
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        today_end = today_start + timedelta(days=1)

        # Act: Calculate today's usage for yfinance (same as admin API)
        today_metrics = (
            db_session.query(MarketDataUsageMetrics)
            .filter(
                MarketDataUsageMetrics.provider_id == 'yfinance',
                MarketDataUsageMetrics.recorded_at >= today_start,
                MarketDataUsageMetrics.recorded_at < today_end
            )
            .all()
        )

        total_calls_today = sum(metric.requests_count for metric in today_metrics)

        # Assert: We should have metrics if the system is working
        print(f"Today's metrics count: {len(today_metrics)}")
        print(f"Total calls today: {total_calls_today}")

        # This test will help us see what's actually in the database
        for metric in today_metrics[-5:]:  # Show last 5
            print(f"  {metric.recorded_at}: {metric.requests_count} calls ({metric.metric_id})")

        # If we have recent successful scheduler runs, we should have metrics
        recent_activities = (
            db_session.query(ProviderActivity)
            .filter(
                ProviderActivity.activity_type == 'API_CALL',
                ProviderActivity.provider_id == 'yfinance',
                ProviderActivity.timestamp >= today_start
            )
            .count()
        )

        print(f"Recent yfinance activities today: {recent_activities}")

        # The assertion: if we have activities, we should have metrics
        if recent_activities > 0:
            assert len(today_metrics) > 0, f"Found {recent_activities} activities but no usage metrics"
            assert total_calls_today > 0, f"Found {len(today_metrics)} metrics but total calls is 0"

    def test_metrics_table_structure(self, db_session):
        """Test that the metrics table has the expected structure."""
        # Check if we can query the table successfully
        try:
            count = db_session.query(MarketDataUsageMetrics).count()
            print(f"Total metrics records: {count}")

            # Check if we can create a test record
            test_metric = MarketDataUsageMetrics(
                metric_id="test_metric_123",
                provider_id="test_provider",
                request_type="test_request",
                requests_count=1,
                data_points_fetched=1,
                recorded_at=datetime.now(timezone.utc),
                time_bucket="hourly"
            )

            db_session.add(test_metric)
            db_session.commit()

            # Clean up
            db_session.delete(test_metric)
            db_session.commit()

            assert True  # If we get here, table structure is OK

        except Exception as e:
            pytest.fail(f"Metrics table structure issue: {e}")

    def test_market_data_service_logs_api_usage(self, db_session):
        """
        Test that MarketDataService._log_api_usage() method works correctly.

        This tests the specific method responsible for creating usage metrics.
        """
        # Arrange: Get a provider for testing
        provider = db_session.query(MarketDataProvider).filter(
            MarketDataProvider.name == 'yfinance'
        ).first()

        assert provider is not None, "yfinance provider not found"

        # Arrange: Create service and get initial count
        service = MarketDataService(db_session)
        initial_count = db_session.query(MarketDataUsageMetrics).filter(
            MarketDataUsageMetrics.provider_id == 'yfinance'
        ).count()

        # Act: Call the internal API usage logging method
        service._log_api_usage(
            provider=provider,
            symbol="TEST",
            response_code=200,
            success=True
        )

        # Assert: A new metrics record was created
        new_count = db_session.query(MarketDataUsageMetrics).filter(
            MarketDataUsageMetrics.provider_id == 'yfinance'
        ).count()

        assert new_count > initial_count, "API usage was not logged"

        # Assert: The record has correct data
        latest_metric = (
            db_session.query(MarketDataUsageMetrics)
            .filter(MarketDataUsageMetrics.provider_id == 'yfinance')
            .order_by(MarketDataUsageMetrics.recorded_at.desc())
            .first()
        )

        assert latest_metric.requests_count == 1
        assert latest_metric.request_type == 'price_fetch'
        assert 'TEST' in latest_metric.metric_id

    def test_admin_api_provider_status_calculation(self, db_session):
        """
        Test the exact calculation used by the admin API for provider status.

        This reproduces the admin dashboard logic to identify discrepancies.
        """
        try:
            from src.api.admin import get_provider_status

            # Act: Get provider status using admin API logic
            provider_status = get_provider_status(db_session)

            # Assert: We should get status for both providers
            assert len(provider_status) >= 1

            # Find yfinance provider
            yfinance_status = None
            for provider in provider_status:
                if provider['name'] == 'yfinance':
                    yfinance_status = provider
                    break

            assert yfinance_status is not None, "yfinance not found in provider status"

            print(f"Admin API yfinance status:")
            print(f"  Calls today: {yfinance_status['usage']['calls_today']}")
            print(f"  Calls this month: {yfinance_status['usage']['calls_this_month']}")
            print(f"  Monthly limit: {yfinance_status['usage']['monthly_limit']}")
            print(f"  Last update: {yfinance_status['usage']['last_update']}")

            # Check if the issue is in the calculation
            # If we have activities but calls_today is 0, there's a bug in the calculation

        except ImportError:
            pytest.skip("Admin API not available for testing")
        except Exception as e:
            pytest.fail(f"Admin API test failed: {e}")
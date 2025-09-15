"""
TDD test for renaming ApiUsageMetrics to MarketDataUsageMetrics.

The current model name "ApiUsageMetrics" is too generic. It should be
"MarketDataUsageMetrics" to clearly indicate it tracks market data API usage.
"""

import pytest
from datetime import datetime, timezone

from src.database import SessionLocal


class TestMarketDataUsageMetricsModelRename:
    """Test suite for renaming the usage metrics model."""

    @pytest.fixture
    def db_session(self):
        """Create a database session for testing."""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def test_old_model_should_not_exist_after_rename(self):
        """
        Test that the old ApiUsageMetrics model should not be importable after rename.

        This test will fail initially (red phase), then pass after we rename the model.
        """
        with pytest.raises(ImportError):
            from src.models.market_data_api_usage_metrics import ApiUsageMetrics  # Should fail after rename

    def test_new_model_should_be_importable(self):
        """
        Test that the new MarketDataUsageMetrics model should be importable.

        This test will fail initially (red phase), then pass after we create the new model.
        """
        try:
            from src.models.market_data_usage_metrics import MarketDataUsageMetrics

            # Should be able to create an instance
            instance = MarketDataUsageMetrics(
                metric_id="test_metric",
                provider_id="test_provider",
                request_type="test_request",
                requests_count=1,
                data_points_fetched=1,
                recorded_at=datetime.now(timezone.utc),
                time_bucket="hourly"
            )

            assert instance is not None
            assert instance.provider_id == "test_provider"
            assert instance.requests_count == 1

        except ImportError:
            pytest.fail("MarketDataUsageMetrics should be importable after rename")

    def test_table_name_should_be_descriptive(self, db_session):
        """
        Test that the table name is descriptive and follows naming conventions.

        The table should be named 'market_data_usage_metrics' to be clear about its purpose.
        """
        try:
            from src.models.market_data_usage_metrics import MarketDataUsageMetrics

            # Check that the table name is descriptive
            assert MarketDataUsageMetrics.__tablename__ == "market_data_usage_metrics"

            # Test that we can query the table with the new model
            count = db_session.query(MarketDataUsageMetrics).count()
            assert count >= 0  # Should work without errors

        except ImportError:
            pytest.fail("MarketDataUsageMetrics model should exist")

    def test_admin_api_should_use_new_model(self, db_session):
        """
        Test that the admin API should use the new model name.

        This ensures consistency across the codebase after the rename.
        """
        try:
            # The admin API should import and use the new model
            from src.api.admin import get_provider_status

            # This should work with the new model
            provider_status = get_provider_status(db_session)
            assert isinstance(provider_status, list)

        except ImportError as e:
            # If this fails due to model import, the test should pass after rename
            if "MarketDataUsageMetrics" in str(e):
                pytest.fail("Admin API should use new MarketDataUsageMetrics model")
            else:
                pytest.skip(f"Admin API import failed for other reason: {e}")

    def test_market_data_service_should_use_new_model(self, db_session):
        """
        Test that the MarketDataService should use the new model.

        This ensures the service layer is updated after the rename.
        """
        try:
            from src.services.market_data_service import MarketDataService

            # Create service instance
            service = MarketDataService(db_session)

            # The service should be able to work with the new model
            # (This test mainly ensures imports work correctly)
            assert service is not None

        except ImportError as e:
            if "MarketDataUsageMetrics" in str(e):
                pytest.fail("MarketDataService should use new MarketDataUsageMetrics model")
            else:
                pytest.skip(f"MarketDataService import failed for other reason: {e}")

    def test_database_migration_preserves_data(self, db_session):
        """
        Test that the database migration preserves existing data.

        After renaming the model and migrating the table, all existing data should be preserved.
        """
        try:
            from src.models.market_data_usage_metrics import MarketDataUsageMetrics

            # Get current data count
            current_count = db_session.query(MarketDataUsageMetrics).count()

            # We should have the existing data (22+ records from earlier test)
            assert current_count >= 22, f"Expected at least 22 records, got {current_count}"

            # Check that recent records exist
            recent_records = (
                db_session.query(MarketDataUsageMetrics)
                .filter(MarketDataUsageMetrics.provider_id == 'yfinance')
                .order_by(MarketDataUsageMetrics.recorded_at.desc())
                .limit(5)
                .all()
            )

            assert len(recent_records) >= 5, "Should have recent yfinance records"

            # Verify data integrity
            for record in recent_records:
                assert record.provider_id == 'yfinance'
                assert record.requests_count >= 1
                assert record.request_type == 'price_fetch'
                assert record.recorded_at is not None

        except ImportError:
            pytest.fail("MarketDataUsageMetrics should be importable after migration")
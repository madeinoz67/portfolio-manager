"""
TDD test for system-specific metrics table naming refactor.

This test defines the requirement that we should have separate API usage metrics tables
for different systems to avoid confusion:
- market_data_api_usage_metrics: For tracking market data provider API calls
- portfolio_api_usage_metrics: For tracking portfolio-related API usage (if needed)

The current single 'api_usage_metrics' table is causing confusion.
"""

import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from src.database import engine


class TestSystemSpecificMetricsTables:
    """Test that API usage metrics are separated by system being monitored."""

    def test_market_data_api_usage_metrics_table_should_exist(self, db: Session):
        """
        Test that market_data_api_usage_metrics table exists for market data provider tracking.

        Given: Market data system with multiple providers (Alpha Vantage, yfinance, etc.)
        When: Inspecting database schema
        Then: market_data_api_usage_metrics table should exist
        And: Table should have columns specific to market data provider usage
        """
        # Get database inspector
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        # Check that market_data_api_usage_metrics table exists
        assert "market_data_api_usage_metrics" in table_names, \
            "market_data_api_usage_metrics table is missing - required for market data provider tracking"

        # Verify table has required columns for market data provider metrics
        columns = inspector.get_columns("market_data_api_usage_metrics")
        column_names = [col["name"] for col in columns]

        required_columns = [
            "id",
            "provider_id",  # 'yfinance', 'alpha_vantage', etc.
            "metric_id",
            "user_id",
            "portfolio_id",
            "request_type",  # 'price_fetch', 'bulk_fetch', etc.
            "requests_count",
            "data_points_fetched",
            "cost_estimate",
            "recorded_at",
            "time_bucket",
            "rate_limit_hit",
            "error_count",
            "avg_response_time_ms"
        ]

        for required_col in required_columns:
            assert required_col in column_names, \
                f"Column '{required_col}' missing from market_data_api_usage_metrics table"

    def test_old_api_usage_metrics_table_should_not_exist(self, db: Session):
        """
        Test that the old generic 'api_usage_metrics' table no longer exists.

        Given: System refactored to use system-specific metrics tables
        When: Inspecting database schema
        Then: The old 'api_usage_metrics' table should not exist
        And: This prevents confusion about which system the metrics belong to
        """
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        # The old confusing table should be gone
        assert "api_usage_metrics" not in table_names, \
            "Old 'api_usage_metrics' table still exists - should be renamed to system-specific tables"

    def test_portfolio_api_usage_metrics_table_optional(self, db: Session):
        """
        Test that portfolio_api_usage_metrics table may exist for portfolio-specific metrics.

        Given: Portfolio system may need its own API usage tracking
        When: Inspecting database schema
        Then: portfolio_api_usage_metrics table may exist (but is not required initially)

        Note: This table would track portfolio-related API calls if needed in the future.
        """
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        # This is optional for now - just document the expected structure if it exists
        if "portfolio_api_usage_metrics" in table_names:
            columns = inspector.get_columns("portfolio_api_usage_metrics")
            column_names = [col["name"] for col in columns]

            # Should have portfolio-specific metrics structure
            expected_columns = [
                "id",
                "portfolio_id",
                "user_id",
                "api_endpoint",  # '/api/v1/portfolios/{id}', etc.
                "request_method",  # 'GET', 'POST', etc.
                "requests_count",
                "avg_response_time_ms",
                "error_count",
                "recorded_at",
                "time_bucket"
            ]

            # Verify structure if table exists
            for col in expected_columns:
                assert col in column_names, \
                    f"Column '{col}' missing from portfolio_api_usage_metrics table"

    def test_market_data_models_use_correct_table_name(self):
        """
        Test that market data models reference the correct table name.

        Given: Market data API usage tracking
        When: Checking model definitions
        Then: Models should reference 'market_data_api_usage_metrics' table
        And: No models should reference the old 'api_usage_metrics' table
        """
        # This will be implemented after we update the models
        # For now, just ensure we have a test that will validate the refactor
        from src.models.market_data_api_usage_metrics import ApiUsageMetrics

        # The model should use the new table name
        expected_table_name = "market_data_api_usage_metrics"
        actual_table_name = ApiUsageMetrics.__tablename__

        assert actual_table_name == expected_table_name, \
            f"ApiUsageMetrics model uses table '{actual_table_name}' but should use '{expected_table_name}'"
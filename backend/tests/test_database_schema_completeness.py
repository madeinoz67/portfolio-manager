"""
Test database schema completeness for portfolio metrics functionality.

This test verifies that all required tables exist for the admin dashboard
to properly display portfolio metrics and usage statistics.
"""

import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from src.database import get_db, engine


class TestDatabaseSchemaCompleteness:
    """Test that all required database tables exist for portfolio metrics."""

    def test_portfolio_update_metrics_table_should_exist(self, db: Session):
        """
        Test that portfolio_update_metrics table exists for portfolio metrics functionality.

        Given: Portfolio management system with metrics tracking
        When: Inspecting database schema
        Then: portfolio_update_metrics table should exist
        And: Table should have required columns for update tracking
        """
        # Get database inspector
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        # Check that portfolio_update_metrics table exists
        assert "portfolio_update_metrics" in table_names, \
            "portfolio_update_metrics table is missing - required for portfolio metrics functionality"

        # Verify table has required columns
        columns = inspector.get_columns("portfolio_update_metrics")
        column_names = [col["name"] for col in columns]

        required_columns = [
            "id",
            "portfolio_id",
            "status",
            "trigger_type",
            "update_duration_ms",
            "symbols_updated",
            "error_message",
            "created_at"
        ]

        for required_col in required_columns:
            assert required_col in column_names, \
                f"Column '{required_col}' missing from portfolio_update_metrics table"

    def test_portfolio_queue_metrics_table_should_exist(self, db: Session):
        """
        Test that portfolio_queue_metrics table exists for queue monitoring.

        Given: Portfolio management system with queue processing
        When: Inspecting database schema
        Then: portfolio_queue_metrics table should exist
        And: Table should have required columns for queue tracking
        """
        # Get database inspector
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        # Check that portfolio_queue_metrics table exists
        assert "portfolio_queue_metrics" in table_names, \
            "portfolio_queue_metrics table is missing - required for portfolio queue monitoring"

        # Verify table has required columns
        columns = inspector.get_columns("portfolio_queue_metrics")
        column_names = [col["name"] for col in columns]

        required_columns = [
            "id",
            "pending_updates",
            "processing_rate",
            "avg_processing_time_ms",
            "is_processing",
            "created_at"
        ]

        for required_col in required_columns:
            assert required_col in column_names, \
                f"Column '{required_col}' missing from portfolio_queue_metrics table"

    def test_all_portfolio_related_tables_exist(self, db: Session):
        """
        Test that all tables required for portfolio functionality exist.

        Given: Complete portfolio management system
        When: Checking database schema
        Then: All core tables should exist
        """
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        required_tables = [
            "users",
            "portfolios",
            "stocks",
            "holdings",
            "transactions",
            "market_data_providers",
            "provider_activities",
            "scheduler_executions",
            "api_usage_metrics",  # Market data API metrics
            "portfolio_update_metrics",  # Portfolio update tracking
            "portfolio_queue_metrics"  # Portfolio queue monitoring
        ]

        missing_tables = []
        for table in required_tables:
            if table not in table_names:
                missing_tables.append(table)

        assert not missing_tables, \
            f"Missing required tables: {missing_tables}. " \
            f"Portfolio metrics functionality requires all tables to exist."

    def test_provider_activities_table_has_proper_relationships(self, db: Session):
        """
        Test that provider_activities table has proper foreign key relationships.

        Given: Market data provider system
        When: Checking table relationships
        Then: provider_activities should reference market_data_providers
        """
        inspector = inspect(engine)

        # Check provider_activities table exists
        table_names = inspector.get_table_names()
        assert "provider_activities" in table_names

        # Check foreign key relationships
        foreign_keys = inspector.get_foreign_keys("provider_activities")

        # Should have FK to market_data_providers
        provider_fk_exists = any(
            fk["referred_table"] == "market_data_providers"
            for fk in foreign_keys
        )

        assert provider_fk_exists, \
            "provider_activities table should have foreign key to market_data_providers"
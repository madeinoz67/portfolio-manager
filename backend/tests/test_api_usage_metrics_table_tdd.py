"""
TDD test for api_usage_metrics table existence and functionality.

This test implements Test-Driven Development to ensure:
1. The api_usage_metrics table exists in the database
2. The table can be queried without errors
3. The admin API endpoints can access the table successfully
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.database import engine
from src.models.market_data_usage_metrics import MarketDataUsageMetrics


class TestMarketDataUsageMetricsTableTDD:
    """TDD tests for api_usage_metrics table existence and functionality."""

    def test_api_usage_metrics_table_exists(self):
        """Test that the api_usage_metrics table exists in the database."""
        with Session(engine) as db:
            # This should not raise an OperationalError about missing table
            try:
                result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='api_usage_metrics'"))
                table_exists = result.fetchone() is not None
                assert table_exists, "api_usage_metrics table should exist in database"
            except Exception as e:
                pytest.fail(f"Failed to check table existence: {e}")

    def test_api_usage_metrics_table_structure(self):
        """Test that the api_usage_metrics table has the correct structure."""
        with Session(engine) as db:
            try:
                # Query table info to verify structure
                result = db.execute(text("PRAGMA table_info(api_usage_metrics)"))
                columns = result.fetchall()

                # Convert to dict for easier checking
                column_names = {col[1] for col in columns}  # col[1] is column name

                # Check required columns exist
                required_columns = {
                    'id', 'metric_id', 'provider_id', 'user_id', 'portfolio_id',
                    'request_type', 'requests_count', 'data_points_fetched',
                    'cost_estimate', 'recorded_at', 'time_bucket', 'rate_limit_hit',
                    'error_count', 'avg_response_time_ms'
                }

                missing_columns = required_columns - column_names
                assert not missing_columns, f"Missing columns: {missing_columns}"

            except Exception as e:
                pytest.fail(f"Failed to verify table structure: {e}")

    def test_api_usage_metrics_can_be_queried(self):
        """Test that the api_usage_metrics table can be queried without errors."""
        with Session(engine) as db:
            try:
                # This should not raise sqlite3.OperationalError: no such table
                result = db.query(MarketDataUsageMetrics).count()
                assert result >= 0, "Should be able to count records in api_usage_metrics table"
            except Exception as e:
                pytest.fail(f"Failed to query api_usage_metrics table: {e}")

    @pytest.mark.asyncio
    async def test_admin_api_can_access_api_usage_metrics(self):
        """Test that admin API endpoints can access api_usage_metrics table."""
        from src.api.admin import get_api_usage
        from src.models.user import User, UserRole

        # Create mock admin user
        admin_user = User(
            email="admin@test.com",
            password_hash="hashed",
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            is_active=True
        )

        with Session(engine) as db:
            try:
                # This should not fail with "no such table: api_usage_metrics"
                result = await get_api_usage(
                    current_admin=admin_user,
                    db=db
                )
                assert "by_provider" in result
                assert "summary" in result
                assert isinstance(result["by_provider"], list)

            except Exception as e:
                pytest.fail(f"Admin API failed to access api_usage_metrics: {e}")
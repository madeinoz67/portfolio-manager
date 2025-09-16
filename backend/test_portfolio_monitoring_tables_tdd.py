#!/usr/bin/env python3
"""
TDD test to fix missing portfolio monitoring tables.

The migration 26dce3bcb832 was created but skipped in the migration chain.
This causes the portfolio monitoring system to fail because the tables don't exist.
"""

import pytest
from sqlalchemy import text

from src.database import SessionLocal


class TestPortfolioMonitoringTablesTDD:
    """TDD tests to verify and fix missing portfolio monitoring tables."""

    @pytest.fixture
    def db_session(self):
        """Create a database session for testing."""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def test_portfolio_update_metrics_table_exists(self, db_session):
        """
        Test that portfolio_update_metrics table exists.

        This test should FAIL initially, demonstrating the missing table.
        """
        try:
            result = db_session.execute(text("SELECT 1 FROM portfolio_update_metrics LIMIT 1"))
            result.fetchone()
            print("portfolio_update_metrics table exists")
        except Exception as e:
            pytest.fail(f"portfolio_update_metrics table missing: {e}")

    def test_portfolio_queue_metrics_table_exists(self, db_session):
        """
        Test that portfolio_queue_metrics table exists.

        This test should FAIL initially, demonstrating the missing table.
        """
        try:
            result = db_session.execute(text("SELECT 1 FROM portfolio_queue_metrics LIMIT 1"))
            result.fetchone()
            print("portfolio_queue_metrics table exists")
        except Exception as e:
            pytest.fail(f"portfolio_queue_metrics table missing: {e}")

    def test_portfolio_update_summaries_table_exists(self, db_session):
        """
        Test that portfolio_update_summaries table exists.

        This test should FAIL initially, demonstrating the missing table.
        """
        try:
            result = db_session.execute(text("SELECT 1 FROM portfolio_update_summaries LIMIT 1"))
            result.fetchone()
            print("portfolio_update_summaries table exists")
        except Exception as e:
            pytest.fail(f"portfolio_update_summaries table missing: {e}")

    def test_portfolio_update_alerts_table_exists(self, db_session):
        """
        Test that portfolio_update_alerts table exists.

        This test should FAIL initially, demonstrating the missing table.
        """
        try:
            result = db_session.execute(text("SELECT 1 FROM portfolio_update_alerts LIMIT 1"))
            result.fetchone()
            print("portfolio_update_alerts table exists")
        except Exception as e:
            pytest.fail(f"portfolio_update_alerts table missing: {e}")

    def test_portfolio_monitoring_api_endpoints_work(self, db_session):
        """
        Test that portfolio monitoring API endpoints can query the tables.

        This test validates that the monitoring system works after tables are created.
        """
        from src.api.admin import get_portfolio_queue_health

        try:
            # This should work after we create the missing tables
            from src.models.user import User
            from src.models.user_role import UserRole

            # Create a test admin user (might already exist)
            admin_user = User(
                email="test_admin@example.com",
                password_hash="test_hash",
                role=UserRole.ADMIN,
                is_active=True
            )

            # Mock a user - we just need the admin role for this test
            class MockUser:
                def __init__(self):
                    self.role = UserRole.ADMIN
                    self.email = "test@example.com"

            mock_admin = MockUser()

            # This should not fail after tables are created
            result = get_portfolio_queue_health(mock_admin, db_session)
            print(f"Portfolio queue health API result: {result}")

            # Verify the result has expected structure
            assert "queue_status" in result, "API should return queue_status"
            assert "recent_metrics" in result, "API should return recent_metrics"

        except Exception as e:
            pytest.fail(f"Portfolio monitoring API failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
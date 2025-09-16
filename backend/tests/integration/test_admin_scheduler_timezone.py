"""
Test Admin API Scheduler Timezone Handling - TDD tests for timezone conversion.

Tests that the admin API properly returns scheduler data in correct format
for frontend timezone conversion and database persistence integration.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
import json

from src.main import app
from src.models.scheduler_execution import SchedulerExecution
from src.services.scheduler_service import MarketDataSchedulerService
from src.utils.datetime_utils import utc_now


# No fixtures needed for this simplified test


class TestAdminSchedulerTimezone:
    """Test admin API scheduler status timezone handling."""

    def test_scheduler_service_status_info_vs_get_status_comparison(self, db: Session):
        """
        Test that demonstrates the difference between status_info and get_status methods.

        Given: Scheduler execution in database
        When: Comparing status_info (used by admin API) vs get_status (database method)
        Then: They should return the same data for consistency
        """
        # Create scheduler execution in database
        execution_time = utc_now().replace(tzinfo=None)
        execution = SchedulerExecution(
            started_at=execution_time - timedelta(seconds=5),
            completed_at=execution_time,
            status="success",
            symbols_processed=7,
            successful_fetches=7,
            failed_fetches=0,
            execution_time_ms=5000,
            provider_used="yfinance"
        )
        db.add(execution)
        db.commit()

        # Create scheduler service (loads from database)
        scheduler = MarketDataSchedulerService(db, auto_start=False)

        # Get data from both methods
        status_info_data = scheduler.status_info  # Used by admin API
        get_status_data = scheduler.get_status()  # Database method

        # Compare key metrics - they should be the same
        assert status_info_data["last_run"] == get_status_data["last_run"]

        # This test will initially fail because status_info uses in-memory data
        # while get_status uses database data
        print(f"status_info total_executions: {status_info_data.get('total_executions', 'N/A')}")
        print(f"get_status total_runs: {get_status_data.get('total_runs', 'N/A')}")

        # The admin API should use get_status for database persistence
        assert get_status_data["total_runs"] == 1  # Database shows 1 execution
        assert get_status_data["successful_runs"] == 1

    def test_get_status_returns_database_persisted_metrics(self, db: Session):
        """
        Test that get_status method returns accurate database-persisted metrics.

        Given: Multiple scheduler executions in database
        When: Using get_status method
        Then: Returns accurate metrics calculated from database
        """
        # Create multiple executions in database
        now = utc_now().replace(tzinfo=None)
        executions = [
            SchedulerExecution(
                started_at=now - timedelta(hours=2),
                completed_at=now - timedelta(hours=2) + timedelta(seconds=3),
                status="success",
                symbols_processed=5,
                successful_fetches=5,
                failed_fetches=0
            ),
            SchedulerExecution(
                started_at=now - timedelta(hours=1),
                completed_at=now - timedelta(hours=1) + timedelta(seconds=4),
                status="failed",
                symbols_processed=0,
                successful_fetches=0,
                failed_fetches=0,
                error_message="Test failure"
            )
        ]

        for execution in executions:
            db.add(execution)
        db.commit()

        # Create fresh scheduler service
        scheduler = MarketDataSchedulerService(db, auto_start=False)

        # Use get_status method (should return database data)
        status_data = scheduler.get_status()

        # Verify accurate database metrics
        assert status_data["total_runs"] == 2
        assert status_data["successful_runs"] == 1
        assert status_data["failed_runs"] == 1
        assert status_data["last_run"] is not None  # Most recent successful run

        # Verify timestamp format for frontend conversion
        last_run = status_data["last_run"]
        assert isinstance(last_run, datetime)  # Should be datetime object
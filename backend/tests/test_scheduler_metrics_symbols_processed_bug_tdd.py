"""
TDD Test for Scheduler Metrics Bug: 0 symbols processed displayed in admin dashboard.

Tests to reproduce and fix the issue where the admin dashboard shows
"Symbols Processed: 0" even when batch updates are working correctly.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.services.scheduler_service import MarketDataSchedulerService, SchedulerConfiguration
from src.models.scheduler_execution import SchedulerExecution
from src.utils.datetime_utils import utc_now


class TestSchedulerMetricsSymbolsProcessedBug:
    """Test class for reproducing the scheduler metrics symbols processed bug."""

    @pytest.fixture
    def scheduler_config(self) -> SchedulerConfiguration:
        """Create a basic scheduler configuration for testing."""
        return SchedulerConfiguration(
            interval_minutes=15,
            max_concurrent_jobs=5,
            retry_attempts=3,
            enabled_providers=["yfinance"],
            bulk_mode=True,
            timeout_seconds=300
        )

    @pytest.fixture
    def scheduler_service(self, db_session: Session, scheduler_config: SchedulerConfiguration) -> MarketDataSchedulerService:
        """Create a scheduler service for testing."""
        return MarketDataSchedulerService(db_session, scheduler_config)

    def test_scheduler_execution_record_should_store_symbols_processed(
        self,
        db_session: Session,
        scheduler_service: MarketDataSchedulerService
    ):
        """
        Test that SchedulerExecution records are created and store symbols_processed correctly.
        This test should currently FAIL if the issue exists.
        """
        # Start the scheduler to create initial execution record
        scheduler_service.start()

        # Simulate a successful execution with 8 symbols processed
        symbols_processed = 8
        scheduler_service.record_execution_success(symbols_processed=symbols_processed)

        # Check that a SchedulerExecution record was created in the database
        executions = db_session.query(SchedulerExecution).all()
        assert len(executions) > 0, "No SchedulerExecution records found in database"

        # Find the completed execution
        completed_execution = None
        for execution in executions:
            if execution.status == "success" and execution.completed_at is not None:
                completed_execution = execution
                break

        assert completed_execution is not None, "No completed SchedulerExecution record found"

        # CRITICAL ASSERTION: symbols_processed should be stored correctly
        assert completed_execution.symbols_processed == symbols_processed, \
            f"Expected symbols_processed={symbols_processed}, got {completed_execution.symbols_processed}"

    def test_scheduler_get_status_should_calculate_total_symbols_correctly(
        self,
        db_session: Session,
        scheduler_service: MarketDataSchedulerService
    ):
        """
        Test that get_status() correctly calculates total_symbols_processed from database.
        This test should currently FAIL showing 0 symbols processed.
        """
        # Start scheduler and record several successful executions
        scheduler_service.start()

        # First execution: 5 symbols
        scheduler_service.record_execution_success(symbols_processed=5)

        # Start new execution record for second run
        scheduler_service.record_execution_start()

        # Second execution: 3 symbols
        scheduler_service.record_execution_success(symbols_processed=3)

        # Start new execution record for third run
        scheduler_service.record_execution_start()

        # Third execution: 7 symbols
        scheduler_service.record_execution_success(symbols_processed=7)

        # Get status from scheduler (this is what the admin API calls)
        status_info = scheduler_service.get_status()

        # CRITICAL ASSERTION: total_symbols_processed should be 5 + 3 + 7 = 15
        expected_total = 15
        actual_total = status_info.get("total_symbols_processed", 0)
        assert actual_total == expected_total, \
            f"Expected total_symbols_processed={expected_total}, got {actual_total}"

        # Verify individual metrics are also correct
        assert status_info.get("total_runs", 0) == 3, "Expected 3 total runs"
        assert status_info.get("successful_runs", 0) == 3, "Expected 3 successful runs"
        assert status_info.get("failed_runs", 0) == 0, "Expected 0 failed runs"

    def test_admin_api_scheduler_status_shows_correct_symbols_processed(
        self,
        db_session: Session,
        scheduler_service: MarketDataSchedulerService
    ):
        """
        Test that the admin API endpoint returns correct symbols_processed value.
        This simulates the exact flow from admin dashboard.
        """
        # Start scheduler and simulate batch update success
        scheduler_service.start()

        # Simulate successful batch update of 8 symbols (our recent fix)
        batch_symbols_processed = 8
        scheduler_service.record_execution_success(symbols_processed=batch_symbols_processed)

        # Get status using the same method as admin API
        status_info = scheduler_service.get_status()

        # This is exactly what admin.py line 1666 uses
        symbols_processed_from_api = status_info.get("total_symbols_processed", 0)

        # CRITICAL ASSERTION: Should match our batch update count
        assert symbols_processed_from_api == batch_symbols_processed, \
            f"Admin API shows {symbols_processed_from_api} symbols processed, expected {batch_symbols_processed}"

        # Verify success rate calculation is also correct
        expected_success_rate = 100.0  # 1 successful run out of 1 total
        actual_success_rate = status_info.get("success_rate", 0.0)
        assert actual_success_rate == expected_success_rate, \
            f"Expected success_rate={expected_success_rate}%, got {actual_success_rate}%"

    def test_multiple_executions_accumulate_symbols_processed_correctly(
        self,
        db_session: Session,
        scheduler_service: MarketDataSchedulerService
    ):
        """
        Test that multiple scheduler executions correctly accumulate symbols_processed.
        This test ensures the admin dashboard shows cumulative symbols across all runs.
        """
        scheduler_service.start()

        # Simulate multiple successful batch updates over time
        execution_data = [
            {"symbols": 8, "description": "First batch update"},
            {"symbols": 6, "description": "Second batch update"},
            {"symbols": 4, "description": "Third batch update"},
            {"symbols": 10, "description": "Fourth batch update"}
        ]

        total_expected_symbols = 0

        for i, execution in enumerate(execution_data):
            # Start new execution record for each run (except first)
            if i > 0:
                scheduler_service.record_execution_start()

            symbols = execution["symbols"]
            scheduler_service.record_execution_success(symbols_processed=symbols)
            total_expected_symbols += symbols

            # Verify cumulative total after each execution
            status = scheduler_service.get_status()
            current_total = status.get("total_symbols_processed", 0)
            assert current_total == total_expected_symbols, \
                f"After {execution['description']}: expected {total_expected_symbols} total symbols, got {current_total}"

        # Final verification: total should be 8 + 6 + 4 + 10 = 28
        final_status = scheduler_service.get_status()
        final_total = final_status.get("total_symbols_processed", 0)
        assert final_total == 28, f"Final total should be 28, got {final_total}"

    def test_scheduler_execution_database_persistence(
        self,
        db_session: Session,
        scheduler_service: MarketDataSchedulerService
    ):
        """
        Test that SchedulerExecution records are properly persisted to database.
        This verifies the database layer is working correctly.
        """
        # Clear any existing execution records
        db_session.query(SchedulerExecution).delete()
        db_session.commit()

        # Start scheduler and record execution
        scheduler_service.start()
        scheduler_service.record_execution_success(symbols_processed=12)

        # Query database directly to verify persistence
        executions = db_session.query(SchedulerExecution).all()
        assert len(executions) > 0, "No SchedulerExecution records persisted to database"

        # Verify the data integrity
        successful_executions = [ex for ex in executions if ex.status == "success"]
        assert len(successful_executions) > 0, "No successful execution records found"

        # Check the symbols_processed field specifically
        for execution in successful_executions:
            if execution.symbols_processed is not None:
                assert execution.symbols_processed == 12, \
                    f"Database shows symbols_processed={execution.symbols_processed}, expected 12"
                return  # Test passed

        # If we get here, no execution had symbols_processed set
        pytest.fail("No SchedulerExecution record has symbols_processed field populated")

    def test_recent_activity_metrics_calculation(
        self,
        db_session: Session,
        scheduler_service: MarketDataSchedulerService
    ):
        """
        Test that recent activity metrics (24 hours) are calculated correctly.
        This affects the "Recent Activity" section in the admin dashboard.
        """
        scheduler_service.start()

        # Record some executions with timestamps in last 24 hours
        scheduler_service.record_execution_success(symbols_processed=5)

        # Get status and check recent activity
        status = scheduler_service.get_status()
        recent_activity = status.get("recent_activity", {})

        # Recent activity should show symbols processed in last 24 hours
        recent_symbols = recent_activity.get("total_symbols_processed", 0)
        assert recent_symbols == 5, \
            f"Recent activity shows {recent_symbols} symbols, expected 5"

        # Recent success rate should be 100%
        recent_success_rate = recent_activity.get("success_rate", 0.0)
        assert recent_success_rate == 100.0, \
            f"Recent success rate shows {recent_success_rate}%, expected 100%"
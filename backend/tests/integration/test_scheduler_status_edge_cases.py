"""
Test Scheduler Status Edge Cases - TDD tests for scheduler status reporting accuracy.

Tests edge cases where scheduler status might report incorrectly, particularly
when there's no persisted execution data or mixed data states.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.models.scheduler_execution import SchedulerExecution
from src.services.scheduler_service import MarketDataSchedulerService
from src.utils.datetime_utils import utc_now


class TestSchedulerStatusEdgeCases:
    """Test scheduler status reporting in edge case scenarios."""

    def test_fresh_scheduler_reports_correct_empty_status(self, db: Session):
        """
        Test that a fresh scheduler with no execution history reports correct empty status.

        Given: A fresh scheduler service with no execution history in database
        When: Getting scheduler status
        Then: It reports zero metrics correctly without errors or incorrect values
        """
        # Create fresh scheduler service (no executions in database)
        scheduler = MarketDataSchedulerService(db, auto_start=False)
        scheduler.start()

        status = scheduler.get_status()

        # Verify fresh scheduler reports zeros correctly
        assert status["total_runs"] == 0
        assert status["successful_runs"] == 0
        assert status["failed_runs"] == 0
        assert status["success_rate"] == 0.0
        assert status["total_symbols_processed"] == 0
        assert status["last_run"] is None
        assert status["state"] == "running"

        # Verify recent activity is also empty
        assert status["recent_activity"]["total_symbols_processed"] == 0
        assert status["recent_activity"]["success_rate"] == 0.0

    def test_scheduler_status_after_single_execution(self, db: Session):
        """
        Test scheduler status reporting after exactly one execution.

        Given: A scheduler that has performed exactly one execution
        When: Getting status from database
        Then: All metrics reflect the single execution accurately
        """
        # Create execution record in database
        execution_time = utc_now().replace(tzinfo=None)
        execution = SchedulerExecution(
            started_at=execution_time,
            completed_at=execution_time + timedelta(seconds=3),
            status="success",
            symbols_processed=7,
            successful_fetches=6,
            failed_fetches=1,
            execution_time_ms=3000,
            provider_used="yfinance"
        )
        db.add(execution)
        db.commit()

        # Create scheduler service (should load the single execution)
        scheduler = MarketDataSchedulerService(db, auto_start=False)
        status = scheduler.get_status()

        # Verify single execution is reported correctly
        assert status["total_runs"] == 1
        assert status["successful_runs"] == 1
        assert status["failed_runs"] == 0
        assert status["success_rate"] == 100.0
        assert status["total_symbols_processed"] == 7
        assert status["last_run"] is not None

        # Verify recent activity matches total (since only one execution)
        assert status["recent_activity"]["total_symbols_processed"] == 7
        assert status["recent_activity"]["success_rate"] == 100.0

    def test_scheduler_status_with_mixed_success_failure_history(self, db: Session):
        """
        Test scheduler status calculation with mixed success/failure history.

        Given: Multiple executions with both successes and failures
        When: Calculating status metrics
        Then: Success rate and totals are calculated correctly
        """
        # Create mixed execution history
        now = utc_now().replace(tzinfo=None)
        executions = [
            # 2 successful executions
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
                status="success",
                symbols_processed=8,
                successful_fetches=7,
                failed_fetches=1
            ),
            # 1 failed execution
            SchedulerExecution(
                started_at=now - timedelta(minutes=30),
                completed_at=now - timedelta(minutes=30) + timedelta(seconds=2),
                status="failed",
                symbols_processed=0,
                successful_fetches=0,
                failed_fetches=0,
                error_message="Provider timeout"
            )
        ]

        for execution in executions:
            db.add(execution)
        db.commit()

        # Create scheduler and check status
        scheduler = MarketDataSchedulerService(db, auto_start=False)
        status = scheduler.get_status()

        # Verify mixed history calculations
        assert status["total_runs"] == 3
        assert status["successful_runs"] == 2
        assert status["failed_runs"] == 1
        assert abs(status["success_rate"] - 66.67) < 0.1  # 2/3 = 66.67%
        assert status["total_symbols_processed"] == 13  # 5 + 8 + 0
        assert status["last_run"] is not None  # Should be most recent successful run

        # Recent activity should include all 3 executions (within 24 hours)
        assert status["recent_activity"]["total_symbols_processed"] == 13
        assert abs(status["recent_activity"]["success_rate"] - 66.67) < 0.1

    def test_scheduler_status_with_old_vs_recent_executions(self, db: Session):
        """
        Test scheduler status distinguishes between old and recent executions.

        Given: Executions both within and outside the 24-hour recent window
        When: Calculating status metrics
        Then: Total includes all, recent activity only includes last 24 hours
        """
        # Use same time source as application (naive UTC)
        now = utc_now().replace(tzinfo=None)
        executions = [
            # Old execution (25 hours ago - outside recent window)
            SchedulerExecution(
                started_at=now - timedelta(hours=25),
                completed_at=now - timedelta(hours=25) + timedelta(seconds=3),
                status="success",
                symbols_processed=10,
                successful_fetches=10,
                failed_fetches=0
            ),
            # Recent execution (1 hour ago - within recent window)
            SchedulerExecution(
                started_at=now - timedelta(hours=1),
                completed_at=now - timedelta(hours=1) + timedelta(seconds=4),
                status="success",
                symbols_processed=5,
                successful_fetches=5,
                failed_fetches=0
            )
        ]

        for execution in executions:
            db.add(execution)
        db.commit()

        # Create scheduler and check status
        scheduler = MarketDataSchedulerService(db, auto_start=False)
        status = scheduler.get_status()

        # Verify total includes both old and recent
        assert status["total_runs"] == 2
        assert status["successful_runs"] == 2
        assert status["failed_runs"] == 0
        assert status["success_rate"] == 100.0
        assert status["total_symbols_processed"] == 15  # 10 + 5

        # Verify recent activity only includes the 1-hour-ago execution
        assert status["recent_activity"]["total_symbols_processed"] == 5  # Only recent execution
        assert status["recent_activity"]["success_rate"] == 100.0

    def test_scheduler_status_with_no_successful_executions(self, db: Session):
        """
        Test scheduler status when all executions have failed.

        Given: Only failed executions in history
        When: Getting scheduler status
        Then: Success rate is 0%, last_run is None, but totals are correct
        """
        # Create only failed executions
        now = utc_now().replace(tzinfo=None)
        executions = [
            SchedulerExecution(
                started_at=now - timedelta(hours=2),
                completed_at=now - timedelta(hours=2) + timedelta(seconds=1),
                status="failed",
                symbols_processed=0,
                successful_fetches=0,
                failed_fetches=0,
                error_message="Network timeout"
            ),
            SchedulerExecution(
                started_at=now - timedelta(hours=1),
                completed_at=now - timedelta(hours=1) + timedelta(seconds=2),
                status="failed",
                symbols_processed=0,
                successful_fetches=0,
                failed_fetches=0,
                error_message="API rate limit"
            )
        ]

        for execution in executions:
            db.add(execution)
        db.commit()

        # Create scheduler and check status
        scheduler = MarketDataSchedulerService(db, auto_start=False)
        status = scheduler.get_status()

        # Verify failed-only status
        assert status["total_runs"] == 2
        assert status["successful_runs"] == 0
        assert status["failed_runs"] == 2
        assert status["success_rate"] == 0.0
        assert status["total_symbols_processed"] == 0
        assert status["last_run"] is None  # No successful runs

        # Recent activity should also show failures
        assert status["recent_activity"]["total_symbols_processed"] == 0
        assert status["recent_activity"]["success_rate"] == 0.0

    def test_scheduler_last_run_only_counts_successful_executions(self, db: Session):
        """
        Test that last_run timestamp only considers successful executions.

        Given: Mixed executions with most recent being a failure
        When: Getting last_run timestamp
        Then: It returns the most recent successful execution, not the failure
        """
        now = utc_now().replace(tzinfo=None)
        executions = [
            # Successful execution 2 hours ago
            SchedulerExecution(
                started_at=now - timedelta(hours=2),
                completed_at=now - timedelta(hours=2) + timedelta(seconds=3),
                status="success",
                symbols_processed=5,
                successful_fetches=5,
                failed_fetches=0
            ),
            # Failed execution 1 hour ago (more recent than success)
            SchedulerExecution(
                started_at=now - timedelta(hours=1),
                completed_at=now - timedelta(hours=1) + timedelta(seconds=2),
                status="failed",
                symbols_processed=0,
                successful_fetches=0,
                failed_fetches=0,
                error_message="Provider error"
            )
        ]

        for execution in executions:
            db.add(execution)
        db.commit()

        # Create scheduler and check last_run
        scheduler = MarketDataSchedulerService(db, auto_start=False)
        last_run = scheduler.get_last_run()

        # last_run should be the successful execution (2 hours ago), not the failed one
        assert last_run is not None
        time_diff = abs((now - last_run).total_seconds())
        assert 7200 - 60 <= time_diff <= 7200 + 60  # 2 hours ± 1 minute tolerance

        # Also verify through status
        status = scheduler.get_status()
        assert status["last_run"] is not None
        assert status["total_runs"] == 2
        assert status["successful_runs"] == 1
        assert status["failed_runs"] == 1
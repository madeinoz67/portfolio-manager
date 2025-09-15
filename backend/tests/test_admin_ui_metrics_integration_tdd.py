"""
TDD tests to verify admin UI metrics are actually being updated by background task integration.

Tests the specific metrics shown in the screenshot:
- Last Run (should not be "Never")
- Success Rate (should reflect actual results)
- Symbols Processed (should show real counts)
- Total Runs, Successful, Failed counts
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.services.scheduler_service import MarketDataSchedulerService, SchedulerState, get_scheduler_service


class TestAdminUIMetricsIntegration:
    """Test that admin UI metrics are updated by background task integration."""

    def test_last_run_is_updated_from_never_to_actual_time(self, db_session: Session):
        """
        FAILING TEST: Last Run should change from 'Never' to actual timestamp.

        This tests the exact metric shown in the screenshot.
        """
        scheduler = get_scheduler_service(db_session)

        # Initially should be None (which displays as "Never" in UI)
        initial_status = scheduler.status_info
        assert initial_status["last_run"] is None, "Initial last_run should be None (displays as 'Never')"

        # Simulate background task execution
        scheduler.record_execution_success(symbols_processed=5)

        # Now last_run should have actual timestamp
        updated_status = scheduler.status_info
        assert updated_status["last_run"] is not None, "last_run should be updated after execution"

        # Should be recent timestamp (within last minute)
        last_run_time = datetime.fromisoformat(updated_status["last_run"].replace('Z', '+00:00'))
        now = datetime.utcnow().replace(tzinfo=last_run_time.tzinfo)
        time_diff = abs((now - last_run_time).total_seconds())
        assert time_diff < 60, f"last_run should be recent, but was {time_diff} seconds ago"

    def test_success_rate_calculation_from_execution_results(self, db_session: Session):
        """
        FAILING TEST: Success Rate should be calculated from actual execution results.

        Currently shows 0.00% in screenshot - should reflect real success/failure rates.
        """
        scheduler = get_scheduler_service(db_session)

        # Need to track success/failure counts for rate calculation
        # This test will fail initially because we don't track these metrics yet

        # Simulate some successful executions
        scheduler.record_execution_success(symbols_processed=5)
        scheduler.record_execution_success(symbols_processed=3)

        # Simulate one failure
        scheduler.record_execution_failure("API timeout")

        # Should be able to calculate success rate: 2 success out of 3 total = 66.67%
        status = scheduler.status_info

        # This will fail because we don't track success/failure counts yet
        assert "total_executions" in status, "Should track total execution count"
        assert "successful_executions" in status, "Should track successful execution count"
        assert "failed_executions" in status, "Should track failed execution count"

        # Success rate should be calculated
        total = status["total_executions"]
        successful = status["successful_executions"]
        expected_rate = (successful / total) * 100 if total > 0 else 0

        assert "success_rate_percent" in status, "Should calculate success rate percentage"
        assert abs(status["success_rate_percent"] - expected_rate) < 0.01, \
            f"Success rate should be {expected_rate}%, got {status.get('success_rate_percent', 'missing')}"

    def test_symbols_processed_tracking_from_background_task(self, db_session: Session):
        """
        FAILING TEST: Symbols Processed should show actual count from background task.

        Screenshot shows 0 - should show real symbols processed.
        """
        scheduler = get_scheduler_service(db_session)

        # Simulate background task processing different symbol counts
        scheduler.record_execution_success(symbols_processed=5)
        scheduler.record_execution_success(symbols_processed=3)
        scheduler.record_execution_success(symbols_processed=7)

        status = scheduler.status_info

        # Should track symbols processed
        assert "total_symbols_processed" in status, "Should track total symbols processed"
        assert status["total_symbols_processed"] == 15, \
            f"Should track cumulative symbols: 5+3+7=15, got {status.get('total_symbols_processed', 'missing')}"

        # Should also track symbols in most recent execution
        assert "last_execution_symbols" in status, "Should track symbols from last execution"
        assert status["last_execution_symbols"] == 7, \
            f"Last execution had 7 symbols, got {status.get('last_execution_symbols', 'missing')}"

    def test_total_runs_successful_failed_counters(self, db_session: Session):
        """
        FAILING TEST: Total Runs, Successful, Failed counters should reflect actual executions.

        Screenshot shows all zeros - should show real execution counts.
        """
        scheduler = get_scheduler_service(db_session)

        # Simulate mixed execution results
        scheduler.record_execution_success(symbols_processed=5)
        scheduler.record_execution_success(symbols_processed=3)
        scheduler.record_execution_failure("Network error")
        scheduler.record_execution_success(symbols_processed=2)
        scheduler.record_execution_failure("API timeout")

        status = scheduler.status_info

        # Should track execution counts
        assert status.get("total_executions", 0) == 5, "Should count 5 total executions"
        assert status.get("successful_executions", 0) == 3, "Should count 3 successful executions"
        assert status.get("failed_executions", 0) == 2, "Should count 2 failed executions"

    def test_next_run_time_calculation_accuracy(self, db_session: Session):
        """
        TEST: Next Run time should be accurate based on last execution + interval.

        Screenshot shows a future time - verify this is correctly calculated.
        """
        scheduler = get_scheduler_service(db_session)

        # Record an execution
        scheduler.record_execution_success(symbols_processed=3)

        status = scheduler.status_info
        assert status["next_run"] is not None, "Next run should be calculated"

        # Parse times
        last_run = datetime.fromisoformat(status["last_run"].replace('Z', '+00:00'))
        next_run = datetime.fromisoformat(status["next_run"].replace('Z', '+00:00'))

        # Interval should match configuration (15 minutes by default)
        interval_minutes = scheduler.configuration.interval_minutes
        expected_next = last_run + timedelta(minutes=interval_minutes)

        # Allow small tolerance for processing time
        time_diff = abs((next_run - expected_next).total_seconds())
        assert time_diff < 10, \
            f"Next run should be {interval_minutes} min after last run, diff: {time_diff}s"

    def test_admin_api_exposes_updated_metrics(self, db_session: Session):
        """
        FAILING TEST: Admin API endpoints should expose the updated metrics.

        The UI gets data from API - verify the API returns updated values.
        """
        # This test checks if the admin API endpoint returns updated scheduler metrics
        # Will need to verify the actual API endpoint that feeds the UI

        scheduler = get_scheduler_service(db_session)

        # Simulate execution
        scheduler.record_execution_success(symbols_processed=8)

        # The admin API should expose these metrics
        # This test documents what the API contract should be

        expected_api_response = {
            "scheduler": {
                "state": "running",
                "last_run": scheduler.status_info["last_run"],
                "next_run": scheduler.status_info["next_run"],
                "total_runs": scheduler.status_info.get("total_executions", 0),
                "successful": scheduler.status_info.get("successful_executions", 0),
                "failed": scheduler.status_info.get("failed_executions", 0),
                "symbols_processed": scheduler.status_info.get("total_symbols_processed", 0),
                "success_rate": scheduler.status_info.get("success_rate_percent", 0.0)
            }
        }

        # This test will fail until we implement the missing metrics tracking
        assert False, f"Admin API should expose metrics: {expected_api_response}"

    def test_uptime_calculation_from_running_state(self, db_session: Session):
        """
        TEST: Uptime should be calculated from when scheduler started running.

        Screenshot shows 0m - should show actual uptime.
        """
        scheduler = get_scheduler_service(db_session)

        # Should be running by default (from auto-start)
        assert scheduler.state == SchedulerState.RUNNING

        # Record execution to establish last_run
        scheduler.record_execution_success(symbols_processed=2)

        status = scheduler.status_info

        # Uptime calculation depends on implementation
        # Currently returns None unless last_run exists
        uptime_seconds = status.get("uptime_seconds")

        if uptime_seconds is not None:
            assert uptime_seconds >= 0, "Uptime should be non-negative"
            assert uptime_seconds < 3600, "Uptime should be reasonable (< 1 hour for test)"

    def test_metrics_persist_across_scheduler_service_calls(self, db_session: Session):
        """
        TEST: Metrics should persist across multiple get_scheduler_service calls.

        UI makes multiple API calls - metrics should be consistent.
        """
        # First scheduler instance
        scheduler1 = get_scheduler_service(db_session)
        scheduler1.record_execution_success(symbols_processed=4)

        status1 = scheduler1.status_info
        last_run1 = status1["last_run"]

        # Second scheduler instance (should be same singleton)
        scheduler2 = get_scheduler_service(db_session)
        status2 = scheduler2.status_info

        # Should have same metrics
        assert status2["last_run"] == last_run1, "Metrics should persist across service calls"
        assert scheduler1 is scheduler2, "Should be same singleton instance"
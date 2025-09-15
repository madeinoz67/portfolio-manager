"""
TDD tests to verify scheduler service integration with background task.

Tests that the background task properly updates scheduler service state.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from sqlalchemy.orm import Session

from src.services.scheduler_service import MarketDataSchedulerService, SchedulerState, get_scheduler_service


class TestSchedulerIntegrationFix:
    """Test that scheduler service integration bridge works."""

    def test_scheduler_has_execution_recording_methods(self, db_session: Session):
        """Test that scheduler service has new execution recording methods."""
        scheduler = MarketDataSchedulerService(db_session)

        # Should have new methods for recording executions
        assert hasattr(scheduler, 'record_execution_start')
        assert hasattr(scheduler, 'record_execution_success')
        assert hasattr(scheduler, 'record_execution_failure')

        # Methods should be callable
        assert callable(scheduler.record_execution_start)
        assert callable(scheduler.record_execution_success)
        assert callable(scheduler.record_execution_failure)

    def test_record_execution_success_updates_last_run(self, db_session: Session):
        """Test that record_execution_success updates last_run time."""
        scheduler = MarketDataSchedulerService(db_session)

        # Initially last_run should be None
        initial_status = scheduler.status_info
        assert initial_status["last_run"] is None

        # Record successful execution
        scheduler.record_execution_success(symbols_processed=5)

        # Now last_run should be set
        updated_status = scheduler.status_info
        assert updated_status["last_run"] is not None

        # Should also update next_run
        assert updated_status["next_run"] is not None

    def test_record_execution_failure_sets_error_message(self, db_session: Session):
        """Test that record_execution_failure sets error message."""
        scheduler = MarketDataSchedulerService(db_session)

        # Initially no error
        initial_status = scheduler.status_info
        assert initial_status["error_message"] is None

        # Record failure
        test_error = "API timeout error"
        scheduler.record_execution_failure(test_error)

        # Should set error message
        updated_status = scheduler.status_info
        assert updated_status["error_message"] == test_error

    def test_execution_methods_only_work_when_running(self, db_session: Session):
        """Test execution recording methods only work when scheduler is RUNNING."""
        scheduler = MarketDataSchedulerService(db_session, auto_start=False)

        # Scheduler starts as STOPPED
        assert scheduler.state == SchedulerState.STOPPED

        # Recording success shouldn't update last_run when stopped
        scheduler.record_execution_success(symbols_processed=5)
        status = scheduler.status_info
        assert status["last_run"] is None

        # Start scheduler
        scheduler.start()
        assert scheduler.state == SchedulerState.RUNNING

        # Now recording should work
        scheduler.record_execution_success(symbols_processed=5)
        updated_status = scheduler.status_info
        assert updated_status["last_run"] is not None

    @patch('src.services.scheduler_service.logger')
    def test_record_execution_success_logs_completion(self, mock_logger, db_session: Session):
        """Test that successful execution is properly logged."""
        scheduler = MarketDataSchedulerService(db_session)

        # Record successful execution
        scheduler.record_execution_success(symbols_processed=8)

        # Should log completion
        mock_logger.info.assert_called_with(
            "Scheduler execution completed successfully: 8 symbols processed"
        )

    @patch('src.services.scheduler_service.logger')
    def test_record_execution_failure_logs_error(self, mock_logger, db_session: Session):
        """Test that execution failure is properly logged."""
        scheduler = MarketDataSchedulerService(db_session)

        # Record failure
        error_msg = "Connection timeout"
        scheduler.record_execution_failure(error_msg)

        # Should log error
        mock_logger.error.assert_called_with(f"Scheduler execution failed: {error_msg}")

    def test_scheduler_service_can_track_multiple_executions(self, db_session: Session):
        """Test that scheduler service can track multiple successful executions."""
        scheduler = MarketDataSchedulerService(db_session)

        # First execution
        scheduler.record_execution_success(symbols_processed=3)
        first_run = scheduler.status_info["last_run"]
        assert first_run is not None

        # Brief pause to ensure different timestamps
        import time
        time.sleep(0.1)

        # Second execution should update last_run to new value
        scheduler.record_execution_success(symbols_processed=7)
        second_run = scheduler.status_info["last_run"]
        assert second_run is not None
        assert second_run != first_run  # Should be different timestamps

    def test_background_task_integration_imports(self):
        """Test that main.py can import the scheduler service integration."""
        # This test verifies the import works without circular dependency
        try:
            from src.main import get_scheduler_service
            assert get_scheduler_service is not None
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_scheduler_service_singleton_behavior(self, db_session: Session):
        """Test that get_scheduler_service returns consistent instance."""
        # Multiple calls should return same instance
        scheduler1 = get_scheduler_service(db_session)
        scheduler2 = get_scheduler_service(db_session)

        assert scheduler1 is scheduler2

        # Updates to one should be visible to other
        scheduler1.record_execution_success(symbols_processed=5)

        status1 = scheduler1.status_info
        status2 = scheduler2.status_info

        assert status1["last_run"] == status2["last_run"]
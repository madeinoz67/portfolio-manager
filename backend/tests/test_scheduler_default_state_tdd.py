"""
TDD tests for scheduler default state behavior.

Testing that the scheduler should always be running/active by default.
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from src.services.scheduler_service import MarketDataSchedulerService, SchedulerState, get_scheduler_service


class TestSchedulerDefaultState:
    """Test that scheduler defaults to running state on startup."""

    def test_scheduler_should_default_to_running_not_stopped(self, db_session: Session):
        """
        FAILING TEST: Scheduler should default to RUNNING state, not STOPPED.

        Current behavior: defaults to STOPPED
        Expected behavior: defaults to RUNNING
        """
        scheduler = MarketDataSchedulerService(db_session)

        # This should pass but currently fails
        assert scheduler.state == SchedulerState.RUNNING, \
            "Scheduler should default to RUNNING state for production use"

    def test_get_scheduler_service_returns_running_scheduler(self, db_session: Session):
        """Test that get_scheduler_service returns a scheduler in RUNNING state."""
        scheduler = get_scheduler_service(db_session)

        # The service should be automatically started
        assert scheduler.state == SchedulerState.RUNNING, \
            "get_scheduler_service() should return a running scheduler"

    def test_scheduler_auto_starts_with_default_configuration(self, db_session: Session):
        """Test that scheduler auto-starts with sensible default configuration."""
        scheduler = get_scheduler_service(db_session)

        # Should be running
        assert scheduler.state == SchedulerState.RUNNING

        # Should have default configuration
        config = scheduler.configuration
        assert config.interval_minutes == 15, "Default interval should be 15 minutes"
        assert config.enabled_providers == [], "Should start with empty provider list until configured"
        assert config.bulk_mode == True, "Should default to bulk mode for efficiency"

    def test_scheduler_has_next_run_time_when_started(self, db_session: Session):
        """Test that a running scheduler has a next_run time calculated."""
        scheduler = get_scheduler_service(db_session)

        if scheduler.state == SchedulerState.RUNNING:
            status = scheduler.status_info
            assert status["next_run"] is not None, \
                "Running scheduler should have next_run time calculated"

    def test_fresh_scheduler_instance_auto_starts(self, db_session: Session):
        """Test that creating a fresh scheduler instance auto-starts it."""
        # Reset the global instance to test fresh creation
        from src.services.scheduler_service import reset_scheduler_service
        reset_scheduler_service()

        # Get fresh instance
        scheduler = get_scheduler_service(db_session)

        # Should be running
        assert scheduler.state == SchedulerState.RUNNING, \
            "Fresh scheduler instance should auto-start"

    @patch('src.services.scheduler_service.logger')
    def test_scheduler_startup_is_logged(self, mock_logger, db_session: Session):
        """Test that scheduler auto-startup is properly logged."""
        from src.services.scheduler_service import reset_scheduler_service
        reset_scheduler_service()

        # Create fresh scheduler (should auto-start)
        scheduler = get_scheduler_service(db_session)

        # Should log that it started
        mock_logger.info.assert_called_with(
            "Market data scheduler auto-started with 15min intervals"
        )

    def test_stopped_scheduler_can_still_be_manually_started(self, db_session: Session):
        """Test that if scheduler is stopped, it can still be manually started."""
        scheduler = MarketDataSchedulerService(db_session)

        # Force stop it
        scheduler.stop("test_stop")
        assert scheduler.state == SchedulerState.STOPPED

        # Manual start should work
        success = scheduler.start()
        assert success == True
        assert scheduler.state == SchedulerState.RUNNING

    def test_scheduler_state_persists_across_requests(self, db_session: Session):
        """Test that scheduler state is consistent across multiple get_scheduler_service calls."""
        scheduler1 = get_scheduler_service(db_session)
        scheduler2 = get_scheduler_service(db_session)

        # Should be same instance
        assert scheduler1 is scheduler2

        # Both should show same state
        assert scheduler1.state == scheduler2.state

    def test_scheduler_default_configuration_is_production_ready(self, db_session: Session):
        """Test that default configuration is suitable for production use."""
        scheduler = get_scheduler_service(db_session)
        config = scheduler.configuration

        # Production-ready defaults
        assert config.interval_minutes >= 5, "Interval should be at least 5 minutes for API rate limits"
        assert config.max_concurrent_jobs >= 1, "Should allow concurrent jobs"
        assert config.retry_attempts >= 1, "Should have retry capability"
        assert config.timeout_seconds >= 30, "Should have reasonable timeout"
        assert isinstance(config.bulk_mode, bool), "bulk_mode should be boolean"
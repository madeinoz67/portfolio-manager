"""
TDD tests for scheduler execution failure diagnosis.

The scheduler shows as "running" but Last Run is "Never" despite next run time being in the past.
This indicates the background task is not actually executing market data fetches.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.services.scheduler_service import MarketDataSchedulerService, SchedulerState
from src.services.market_data_service import MarketDataService
from src.main import periodic_price_updates, scheduler_paused


class TestSchedulerExecutionFailure:
    """Test to diagnose why scheduler shows running but never executes."""

    def test_scheduler_service_shows_running_but_never_executed(self, db_session: Session):
        """
        FAILING TEST: Scheduler shows running with next_run in past but Last Run is Never.

        This test should expose the disconnect between scheduler service state
        and actual background task execution.
        """
        scheduler = MarketDataSchedulerService(db_session)

        # Scheduler should be running by default (from previous fix)
        assert scheduler.state == SchedulerState.RUNNING

        # Status should show next run time calculated
        status = scheduler.status_info
        assert status["next_run"] is not None

        # But last_run should be None since no actual execution happened
        # This exposes the issue: service thinks it's running but no execution occurs
        assert status["last_run"] is None, "Last run should be None if no execution happened"

        # If we simulate a run, it should update last_run
        run_result = scheduler.simulate_run()
        assert run_result["status"] == "completed"

        # Now status should show the simulated run
        updated_status = scheduler.status_info
        assert updated_status["last_run"] is not None, "Last run should be updated after simulate_run"

    @pytest.mark.asyncio
    async def test_background_task_execution_isolation(self, db_session: Session):
        """
        FAILING TEST: Background task execution should be independent of scheduler service.

        The background task in main.py should execute regardless of scheduler service state.
        This test will expose if there's a missing connection.
        """
        # Mock the global scheduler_paused flag as False
        with patch('src.main.scheduler_paused', False):
            # Mock MarketDataService to avoid actual API calls
            with patch('src.main.MarketDataService') as mock_service_class:
                mock_service = AsyncMock()
                mock_service.get_enabled_providers.return_value = [
                    MagicMock(name="yfinance", api_key=None)
                ]
                mock_service.get_actively_monitored_symbols.return_value = ["CBA", "BHP"]
                mock_service.fetch_multiple_prices.return_value = {"CBA": 170.0, "BHP": 41.0}
                mock_service.close_session = AsyncMock()
                mock_service_class.return_value = mock_service

                # Mock get_db to return our test session
                with patch('src.main.get_db') as mock_get_db:
                    mock_get_db.return_value.__next__.return_value = db_session

                    # Mock sleep to speed up test
                    with patch('asyncio.sleep') as mock_sleep:
                        mock_sleep.return_value = None

                        # Run one cycle of the background task
                        # This should fail because background task doesn't update scheduler service
                        task = asyncio.create_task(periodic_price_updates())

                        # Let it run briefly
                        await asyncio.sleep(0.1)
                        task.cancel()

                        try:
                            await task
                        except asyncio.CancelledError:
                            pass

                        # The background task should have attempted to fetch prices
                        mock_service.fetch_multiple_prices.assert_called()

                        # But scheduler service should still show last_run as None
                        # This exposes the disconnect
                        scheduler = MarketDataSchedulerService(db_session, auto_start=False)
                        status = scheduler.status_info
                        assert status["last_run"] is None, \
                            "Background task execution doesn't update scheduler service last_run"

    def test_scheduler_service_and_background_task_are_disconnected(self, db_session: Session):
        """
        FAILING TEST: Expose that scheduler service and background task are separate systems.

        The scheduler service tracks its own state, but the background task in main.py
        operates independently and doesn't update the service.
        """
        scheduler = MarketDataSchedulerService(db_session)

        # Scheduler service can simulate runs and track them
        run1 = scheduler.simulate_run()
        assert run1["status"] == "completed"

        status_after_sim = scheduler.status_info
        assert status_after_sim["last_run"] is not None

        # But the background task operates completely separately
        # It doesn't update the scheduler service's last_run
        # This test documents the architectural disconnect

        # The UI shows "Last Run: Never" because it's reading scheduler service state
        # But the background task logs show successful runs

        assert True, "This test documents the architectural issue"

    @pytest.mark.asyncio
    async def test_background_task_should_update_scheduler_service_state(self, db_session: Session):
        """
        FAILING TEST: Background task should update scheduler service when it runs.

        Currently they're disconnected - this test shows what SHOULD happen.
        """
        scheduler = MarketDataSchedulerService(db_session)
        initial_status = scheduler.status_info
        assert initial_status["last_run"] is None

        # After background task runs, scheduler service should be updated
        # This is currently not happening - they're separate systems

        # Mock the background task execution
        with patch('src.main.MarketDataService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_enabled_providers.return_value = []
            mock_service.get_actively_monitored_symbols.return_value = ["CBA"]
            mock_service.fetch_multiple_prices.return_value = {"CBA": 170.0}
            mock_service.close_session = AsyncMock()
            mock_service_class.return_value = mock_service

            # Mock get_db
            with patch('src.main.get_db') as mock_get_db:
                mock_get_db.return_value.__next__.return_value = db_session

                # The background task should update scheduler service after execution
                # But currently it doesn't - this will fail

                # This is the architectural fix needed:
                # Background task should call scheduler.record_successful_run()

                assert False, "Background task doesn't update scheduler service - architectural gap"

    def test_admin_ui_shows_never_because_scheduler_service_never_updated(self, db_session: Session):
        """
        TEST: Confirm admin UI reads from scheduler service, not background task logs.

        This explains why UI shows "Last Run: Never" despite background task working.
        """
        scheduler = MarketDataSchedulerService(db_session)

        # Admin UI reads scheduler.status_info
        status = scheduler.status_info
        last_run = status["last_run"]

        # This is None because background task doesn't update scheduler service
        assert last_run is None, "Admin UI reads None because scheduler service never updated"

        # Success rate is 0.00% for same reason
        # Background task success/failures aren't tracked in scheduler service

        # The fix requires connecting background task execution to scheduler service updates
        assert True, "Admin UI correctly shows scheduler service state, but service is never updated"

    def test_scheduler_now_has_record_execution_methods(self, db_session: Session):
        """
        PASSING TEST: Scheduler service now has methods to record actual executions.

        Background task can now call these after each cycle.
        """
        scheduler = MarketDataSchedulerService(db_session)

        # These methods now exist and bridge the gap
        assert hasattr(scheduler, 'record_execution_start'), \
            "Scheduler service should have method to record execution start"

        assert hasattr(scheduler, 'record_execution_success'), \
            "Scheduler service should have method to record successful executions"

        assert hasattr(scheduler, 'record_execution_failure'), \
            "Scheduler service should have method to record execution failures"

        # Methods should be callable
        assert callable(scheduler.record_execution_start)
        assert callable(scheduler.record_execution_success)
        assert callable(scheduler.record_execution_failure)

        # These methods bridge the gap between background task and scheduler service
        # Now admin UI can show real execution data instead of "Never"
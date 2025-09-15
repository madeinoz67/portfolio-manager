"""
Test Scheduler Persistence - TDD tests for scheduler state persistence across restarts.

This test ensures scheduler state (last run, execution counts, metrics) persists
across FastAPI auto-reload restarts during development.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.models.scheduler_execution import SchedulerExecution


class TestSchedulerPersistence:
    """Test scheduler state persistence across restarts."""

    def test_scheduler_execution_model_stores_run_history(self, db: Session):
        """
        Test that scheduler execution history is stored in database.

        Given: A scheduler execution occurs
        When: Execution details are recorded in database
        Then: Execution history persists across restarts
        """
        # Create a scheduler execution record
        execution = SchedulerExecution(
            started_at=datetime.now(),
            completed_at=datetime.now() + timedelta(seconds=5),
            status="success",
            symbols_processed=7,
            successful_fetches=5,
            failed_fetches=2,
            execution_time_ms=5000,
            provider_used="yfinance",
            execution_metadata='{"symbols": ["BHP", "CBA", "CSL", "NAB", "NEM", "TLS", "WBC"]}'
        )

        db.add(execution)
        db.commit()

        # Verify it's stored
        stored_execution = db.query(SchedulerExecution).first()
        assert stored_execution is not None
        assert stored_execution.status == "success"
        assert stored_execution.symbols_processed == 7
        assert stored_execution.successful_fetches == 5
        assert stored_execution.failed_fetches == 2
        assert stored_execution.execution_time_ms == 5000
        assert stored_execution.provider_used == "yfinance"

    def test_scheduler_service_loads_last_execution_from_database(self, db: Session):
        """
        Test that scheduler service loads last execution time from database.

        Given: Previous scheduler executions exist in database
        When: Scheduler service starts up
        Then: It loads the most recent execution as "last run"
        """
        # Create multiple execution records
        executions = [
            SchedulerExecution(
                started_at=datetime.now() - timedelta(hours=2),
                completed_at=datetime.now() - timedelta(hours=2) + timedelta(seconds=3),
                status="success",
                symbols_processed=5,
                successful_fetches=5,
                failed_fetches=0
            ),
            SchedulerExecution(
                started_at=datetime.now() - timedelta(minutes=30),
                completed_at=datetime.now() - timedelta(minutes=30) + timedelta(seconds=4),
                status="success",
                symbols_processed=7,
                successful_fetches=6,
                failed_fetches=1
            )
        ]

        for execution in executions:
            db.add(execution)
        db.commit()

        # Create scheduler service and verify it loads the most recent execution
        from src.services.scheduler_service import MarketDataSchedulerService
        scheduler_service = MarketDataSchedulerService(db, auto_start=False)

        # Should load most recent execution (30 minutes ago)
        last_run = scheduler_service.get_last_run()
        assert last_run is not None

        # Should be approximately 30 minutes ago (within 1 minute tolerance)
        time_diff = abs((datetime.now() - last_run).total_seconds())
        assert 1800 - 60 <= time_diff <= 1800 + 60  # 30 minutes ± 1 minute

    def test_scheduler_metrics_calculated_from_database_history(self, db: Session):
        """
        Test that scheduler metrics are calculated from persisted execution history.

        Given: Multiple scheduler executions in database
        When: Requesting scheduler metrics
        Then: Metrics reflect all historical executions, not just current session
        """
        # Create execution history spanning multiple "sessions"
        now = datetime.now()
        executions = [
            # Successful executions
            SchedulerExecution(
                started_at=now - timedelta(hours=5),
                completed_at=now - timedelta(hours=5) + timedelta(seconds=3),
                status="success",
                symbols_processed=7,
                successful_fetches=7,
                failed_fetches=0
            ),
            SchedulerExecution(
                started_at=now - timedelta(hours=3),
                completed_at=now - timedelta(hours=3) + timedelta(seconds=4),
                status="success",
                symbols_processed=5,
                successful_fetches=5,
                failed_fetches=0
            ),
            # Failed execution
            SchedulerExecution(
                started_at=now - timedelta(hours=1),
                completed_at=now - timedelta(hours=1) + timedelta(seconds=2),
                status="failed",
                symbols_processed=0,
                successful_fetches=0,
                failed_fetches=0,
                error_message="Provider timeout"
            ),
            # Recent successful execution
            SchedulerExecution(
                started_at=now - timedelta(minutes=20),
                completed_at=now - timedelta(minutes=20) + timedelta(seconds=5),
                status="success",
                symbols_processed=8,
                successful_fetches=6,
                failed_fetches=2
            )
        ]

        for execution in executions:
            db.add(execution)
        db.commit()

        # Create scheduler service and verify metrics from database
        from src.services.scheduler_service import MarketDataSchedulerService
        scheduler_service = MarketDataSchedulerService(db, auto_start=False)

        status = scheduler_service.get_status()

        # Verify metrics calculated from all executions
        assert status["total_runs"] == 4
        assert status["successful_runs"] == 3
        assert status["failed_runs"] == 1
        assert status["total_symbols_processed"] == 20  # 7+5+0+8

        # Verify recent activity (within last 24 hours)
        recent_activity = status["recent_activity"]
        assert recent_activity["total_symbols_processed"] == 20
        assert recent_activity["success_rate"] == 75.0  # 3/4 = 75%

    def test_scheduler_execution_persistence_survives_service_restart(self, db: Session):
        """
        Test that scheduler execution history survives service restarts.

        Given: Scheduler service records executions
        When: Service is destroyed and recreated (simulating FastAPI restart)
        Then: New service instance has access to all previous execution history
        """
        # First service instance records execution
        from src.services.scheduler_service import MarketDataSchedulerService

        scheduler_1 = MarketDataSchedulerService(db, auto_start=False)
        scheduler_1.start()

        # Simulate successful execution
        scheduler_1.record_execution_start()
        scheduler_1.record_execution_success(symbols_processed=5)

        initial_status = scheduler_1.get_status()
        assert initial_status["total_runs"] == 1
        assert initial_status["successful_runs"] == 1

        # "Restart" - create new service instance (simulating FastAPI reload)
        scheduler_2 = MarketDataSchedulerService(db, auto_start=False)
        scheduler_2.start()

        # New instance should have access to previous execution history
        reloaded_status = scheduler_2.get_status()
        assert reloaded_status["total_runs"] == 1
        assert reloaded_status["successful_runs"] == 1
        assert reloaded_status["last_run"] is not None

        # Add another execution with new service instance
        scheduler_2.record_execution_start()
        scheduler_2.record_execution_success(symbols_processed=7)

        final_status = scheduler_2.get_status()
        assert final_status["total_runs"] == 2
        assert final_status["successful_runs"] == 2
        assert final_status["total_symbols_processed"] == 12  # 5 + 7
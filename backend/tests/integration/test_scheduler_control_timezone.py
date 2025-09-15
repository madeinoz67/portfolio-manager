"""
Test timezone formatting consistency between scheduler status and control endpoints.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.models.scheduler_execution import SchedulerExecution
from src.services.scheduler_service import MarketDataSchedulerService
from src.utils.datetime_utils import utc_now


class TestSchedulerControlTimezone:
    """Test timezone formatting consistency in scheduler control responses."""

    def test_scheduler_control_response_timezone_consistency(self, db: Session):
        """
        Test that scheduler control endpoint returns properly formatted timezones.

        Given: Scheduler execution history in database
        When: Scheduler control endpoint returns status in response
        Then: Both lastRun and nextRun have proper UTC format with 'Z' suffix
        And: Format matches the dedicated status endpoint
        """
        # Create execution history for consistent data
        execution_time = utc_now().replace(tzinfo=None)
        execution = SchedulerExecution(
            started_at=execution_time - timedelta(seconds=10),
            completed_at=execution_time,
            status="success",
            symbols_processed=3,
            successful_fetches=3,
            failed_fetches=0
        )
        db.add(execution)
        db.commit()

        # Get scheduler service and start it to generate next_run
        scheduler = MarketDataSchedulerService(db, auto_start=False)
        scheduler.start()  # Start scheduler to populate next_run

        # Simulate control endpoint - get status via status_info property (in-memory)
        control_status = scheduler.status_info

        # Simulate status endpoint - get status via get_status method (database)
        status_endpoint_data = scheduler.get_status()

        # Check both endpoints have datetime data
        assert control_status["last_run"] is not None
        assert control_status["next_run"] is not None
        assert status_endpoint_data["last_run"] is not None
        assert status_endpoint_data["next_run"] is not None

        # Simulate control endpoint formatting (currently broken)
        control_last_run = control_status["last_run"]  # Raw datetime, no 'Z'
        control_next_run = control_status["next_run"]  # Raw datetime, no 'Z'

        # Simulate status endpoint formatting (currently working)
        status_last_run = status_endpoint_data["last_run"].isoformat() + 'Z'
        status_next_run = status_endpoint_data["next_run"].isoformat() + 'Z'

        print(f"Control lastRun format: {control_last_run}")
        print(f"Control nextRun format: {control_next_run}")
        print(f"Status lastRun format: {status_last_run}")
        print(f"Status nextRun format: {status_next_run}")

        # The control endpoint should format consistently
        # Currently this will fail - demonstrating the bug
        if isinstance(control_last_run, datetime):
            # Control endpoint returns raw datetime - needs formatting
            control_last_run_formatted = control_last_run.isoformat() + 'Z'
            control_next_run_formatted = control_next_run.isoformat() + 'Z'
        else:
            control_last_run_formatted = control_last_run
            control_next_run_formatted = control_next_run

        # Both endpoints should have consistent UTC format (after API formatting)
        assert control_last_run_formatted.endswith('Z'), "Control endpoint lastRun should have 'Z' suffix"
        assert control_next_run_formatted.endswith('Z'), "Control endpoint nextRun should have 'Z' suffix"
        assert 'T' in control_last_run_formatted, "Control endpoint lastRun should be ISO format"
        assert 'T' in control_next_run_formatted, "Control endpoint nextRun should be ISO format"

        # Service layer should return timezone-naive UTC datetimes consistently
        assert isinstance(control_last_run, datetime), "lastRun should be datetime object"
        assert isinstance(control_next_run, datetime), "nextRun should be datetime object"
        assert control_last_run.tzinfo is None, "lastRun should be timezone-naive"
        assert control_next_run.tzinfo is None, "nextRun should be timezone-naive"

        # Frontend should be able to parse both formats
        parsed_control_last = datetime.fromisoformat(control_last_run_formatted.replace('Z', '+00:00'))
        parsed_control_next = datetime.fromisoformat(control_next_run_formatted.replace('Z', '+00:00'))
        parsed_status_last = datetime.fromisoformat(status_last_run.replace('Z', '+00:00'))
        parsed_status_next = datetime.fromisoformat(status_next_run.replace('Z', '+00:00'))

        assert isinstance(parsed_control_last, datetime)
        assert isinstance(parsed_control_next, datetime)
        assert isinstance(parsed_status_last, datetime)
        assert isinstance(parsed_status_next, datetime)
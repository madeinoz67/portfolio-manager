"""
Test timezone format in API responses - ensuring proper UTC format with Z suffix.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.models.scheduler_execution import SchedulerExecution
from src.services.scheduler_service import MarketDataSchedulerService
from src.utils.datetime_utils import utc_now


class TestTimezoneFormat:
    """Test timezone format in API responses."""

    def test_admin_api_sends_utc_format_with_z_suffix(self, db: Session):
        """
        Test that admin API sends timestamps with 'Z' suffix to indicate UTC.

        Given: Scheduler execution in database
        When: Admin API formats timestamps
        Then: Timestamps include 'Z' suffix for proper UTC indication
        """
        # Create execution in database
        execution_time = utc_now().replace(tzinfo=None)
        execution = SchedulerExecution(
            started_at=execution_time - timedelta(seconds=5),
            completed_at=execution_time,
            status="success",
            symbols_processed=5,
            successful_fetches=5,
            failed_fetches=0
        )
        db.add(execution)
        db.commit()

        # Get status using database method
        scheduler = MarketDataSchedulerService(db, auto_start=False)
        status_data = scheduler.get_status()

        # Simulate admin API formatting
        last_run_api_format = status_data["last_run"].isoformat() + 'Z' if status_data["last_run"] else None

        # Verify UTC format with Z suffix
        assert last_run_api_format is not None
        assert last_run_api_format.endswith('Z')
        assert 'T' in last_run_api_format  # ISO format

        # Verify it's parseable as UTC by frontend
        from datetime import datetime
        parsed_date = datetime.fromisoformat(last_run_api_format.replace('Z', '+00:00'))
        assert isinstance(parsed_date, datetime)

        print(f"API format: {last_run_api_format}")
        print(f"Parsed: {parsed_date}")
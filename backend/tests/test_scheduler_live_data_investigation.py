"""
TDD test to investigate the live scheduler execution data.

The admin dashboard shows 0 symbols processed despite the scheduler running.
Need to check if SchedulerExecution records are being created and if the
metrics calculation is working correctly.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.models.scheduler_execution import SchedulerExecution
from src.services.scheduler_service import MarketDataSchedulerService


def test_check_live_scheduler_execution_records(db_session: Session):
    """
    Check what SchedulerExecution records exist in the database.
    This will help us understand if the scheduler is actually recording data.
    """
    # Get all scheduler execution records
    executions = db_session.query(SchedulerExecution).order_by(
        SchedulerExecution.created_at.desc()
    ).limit(10).all()

    print(f"\n=== LIVE SCHEDULER EXECUTION RECORDS ===")
    print(f"Total records found: {len(executions)}")

    for i, execution in enumerate(executions):
        print(f"\nRecord {i+1}:")
        print(f"  ID: {execution.id}")
        print(f"  Status: {execution.status}")
        print(f"  Symbols Processed: {execution.symbols_processed}")
        print(f"  Created: {execution.created_at}")
        print(f"  Started: {execution.started_at}")
        print(f"  Completed: {execution.completed_at}")
        print(f"  Error: {execution.error_message}")

    # Check if any records have symbols_processed > 0
    successful_with_symbols = [e for e in executions if e.symbols_processed and e.symbols_processed > 0]
    print(f"\nRecords with symbols_processed > 0: {len(successful_with_symbols)}")

    # This test documents the current state - it may pass or fail depending on live data
    # The key is to understand what's happening in the database


def test_check_scheduler_service_status_calculation(db_session: Session):
    """
    Test the scheduler service's get_status() method to see what it returns.
    This is what the admin dashboard calls.
    """
    # Create a scheduler service instance
    from src.services.scheduler_service import SchedulerConfiguration

    config = SchedulerConfiguration(
        interval_minutes=15,
        max_concurrent_jobs=5,
        retry_attempts=3,
        timeout_seconds=300
    )

    scheduler_service = MarketDataSchedulerService(db_session, config)

    # Get the status that would be returned to admin dashboard
    status = scheduler_service.get_status()

    print(f"\n=== SCHEDULER SERVICE STATUS ===")
    print(f"Total runs: {status.get('total_runs', 0)}")
    print(f"Successful runs: {status.get('successful_runs', 0)}")
    print(f"Failed runs: {status.get('failed_runs', 0)}")
    print(f"Total symbols processed: {status.get('total_symbols_processed', 0)}")
    print(f"Success rate: {status.get('success_rate', 0)}%")
    print(f"Last run: {status.get('last_run')}")
    print(f"Next run: {status.get('next_run')}")
    print(f"Recent activity: {status.get('recent_activity', {})}")

    # Document what we're seeing
    if status.get('total_symbols_processed', 0) == 0:
        print(f"\n❌ ISSUE CONFIRMED: total_symbols_processed is 0")
    else:
        print(f"\n✅ Symbols processed correctly: {status.get('total_symbols_processed', 0)}")


def test_raw_database_query_for_symbols_processed(db_session: Session):
    """
    Use raw SQL to check the scheduler_executions table directly.
    This bypasses any ORM issues and shows exactly what's in the database.
    """
    result = db_session.execute(text("""
        SELECT
            id,
            status,
            symbols_processed,
            created_at,
            started_at,
            completed_at
        FROM scheduler_executions
        ORDER BY created_at DESC
        LIMIT 10
    """))

    rows = result.fetchall()

    print(f"\n=== RAW DATABASE QUERY RESULTS ===")
    print(f"Total records: {len(rows)}")

    for i, row in enumerate(rows):
        print(f"\nRow {i+1}:")
        print(f"  ID: {row.id}")
        print(f"  Status: {row.status}")
        print(f"  Symbols Processed: {row.symbols_processed}")
        print(f"  Created: {row.created_at}")
        print(f"  Started: {row.started_at}")
        print(f"  Completed: {row.completed_at}")

    # Calculate totals manually
    total_symbols = sum(row.symbols_processed or 0 for row in rows)
    successful_runs = len([r for r in rows if r.status == 'success'])

    print(f"\nManual calculations:")
    print(f"  Total symbols (last 10 records): {total_symbols}")
    print(f"  Successful runs: {successful_runs}")
    print(f"  Total runs: {len(rows)}")


def test_check_if_scheduler_is_actually_running():
    """
    Check if the scheduler is configured and running.
    Look for signs that it should be creating execution records.
    """
    # This is a manual check - we'll look at the current time vs last run time
    # to see if the scheduler should have run recently
    now = datetime.utcnow()
    fifteen_minutes_ago = now - timedelta(minutes=15)

    print(f"\n=== SCHEDULER TIMING CHECK ===")
    print(f"Current time (UTC): {now}")
    print(f"15 minutes ago: {fifteen_minutes_ago}")
    print(f"Expected: Scheduler should have run within last 15 minutes if active")

    # This test documents expectations but doesn't assert anything
    # The goal is to understand the scheduler's behavior


if __name__ == "__main__":
    # Allow running this as a script for quick debugging
    print("Run with: uv run pytest tests/test_scheduler_live_data_investigation.py -v -s")
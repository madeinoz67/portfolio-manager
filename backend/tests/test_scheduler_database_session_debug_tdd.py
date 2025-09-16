#!/usr/bin/env python3
"""
TDD test to debug scheduler service database session issues.

The scheduler_executions table exists with 37 records showing successful runs,
but the scheduler service get_status() method returns 0 total runs.

This suggests a database session or configuration issue.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.database import SessionLocal, get_db
from src.models.scheduler_execution import SchedulerExecution
from src.services.scheduler_service import MarketDataSchedulerService, SchedulerConfiguration


class TestSchedulerDatabaseSessionDebugTDD:
    """TDD tests to debug scheduler service database session issues."""

    @pytest.fixture
    def db_session(self):
        """Create a database session for testing."""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def test_direct_scheduler_execution_query(self, db_session):
        """
        Test direct querying of SchedulerExecution records.

        This should show the actual number of records in the database.
        """
        # Direct ORM query
        executions = db_session.query(SchedulerExecution).all()

        print(f"\n=== DIRECT ORM QUERY RESULTS ===")
        print(f"Total SchedulerExecution records: {len(executions)}")

        if executions:
            recent_executions = sorted(executions, key=lambda x: x.started_at, reverse=True)[:5]
            for i, execution in enumerate(recent_executions):
                print(f"Record {i+1}: {execution.started_at} | {execution.status} | {execution.symbols_processed} symbols")

        # This should match what we saw in SQLite CLI (37 records)
        assert len(executions) > 0, f"Expected execution records but found {len(executions)}"

        # Calculate expected totals
        successful_runs = sum(1 for ex in executions if ex.status == "success")
        total_symbols = sum(ex.symbols_processed or 0 for ex in executions)

        print(f"Successful runs: {successful_runs}")
        print(f"Total symbols processed: {total_symbols}")

        assert successful_runs > 0, "Should have successful runs"
        assert total_symbols > 0, "Should have processed symbols"

    def test_scheduler_service_database_session_consistency(self, db_session):
        """
        Test that scheduler service uses the same database session.

        This test verifies if the scheduler service sees the same data.
        """
        # First, verify records exist in our test session
        direct_count = db_session.query(SchedulerExecution).count()
        print(f"\n=== DATABASE SESSION CONSISTENCY ===")
        print(f"Direct session count: {direct_count}")

        # Create scheduler service with our session
        config = SchedulerConfiguration(
            interval_minutes=15,
            max_concurrent_jobs=5,
            retry_attempts=3,
            timeout_seconds=300
        )

        scheduler_service = MarketDataSchedulerService(db_session, auto_start=False)

        # Test the problematic get_status() method
        status = scheduler_service.get_status()

        print(f"Scheduler service status:")
        print(f"  total_runs: {status.get('total_runs', 0)}")
        print(f"  successful_runs: {status.get('successful_runs', 0)}")
        print(f"  total_symbols_processed: {status.get('total_symbols_processed', 0)}")
        print(f"  success_rate: {status.get('success_rate', 0)}%")

        # These should match our direct query
        if status.get('total_runs', 0) != direct_count:
            pytest.fail(f"Session inconsistency: direct count {direct_count} != scheduler service count {status.get('total_runs', 0)}")

        # If we get here, the sessions are consistent
        assert status.get('total_runs', 0) == direct_count, "Database session should be consistent"
        assert status.get('total_symbols_processed', 0) > 0, "Should see processed symbols"

    def test_raw_sql_vs_orm_consistency(self, db_session):
        """
        Test raw SQL vs ORM query consistency.

        Verifies both approaches return the same data.
        """
        # Raw SQL query
        raw_result = db_session.execute(text("""
            SELECT
                COUNT(*) as total_count,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_count,
                SUM(symbols_processed) as total_symbols
            FROM scheduler_executions
        """)).fetchone()

        # ORM query
        all_executions = db_session.query(SchedulerExecution).all()
        orm_total = len(all_executions)
        orm_successful = sum(1 for ex in all_executions if ex.status == "success")
        orm_symbols = sum(ex.symbols_processed or 0 for ex in all_executions)

        print(f"\n=== RAW SQL vs ORM CONSISTENCY ===")
        print(f"Raw SQL - Total: {raw_result.total_count}, Successful: {raw_result.successful_count}, Symbols: {raw_result.total_symbols}")
        print(f"ORM     - Total: {orm_total}, Successful: {orm_successful}, Symbols: {orm_symbols}")

        # These should match exactly
        assert raw_result.total_count == orm_total, f"Count mismatch: SQL {raw_result.total_count} != ORM {orm_total}"
        assert raw_result.successful_count == orm_successful, f"Success count mismatch: SQL {raw_result.successful_count} != ORM {orm_successful}"
        assert raw_result.total_symbols == orm_symbols, f"Symbols mismatch: SQL {raw_result.total_symbols} != ORM {orm_symbols}"

    def test_scheduler_service_database_connection_debug(self, db_session):
        """
        Debug the scheduler service database connection specifically.

        This test examines the internal database session of the scheduler service.
        """
        config = SchedulerConfiguration(
            interval_minutes=15,
            max_concurrent_jobs=5,
            retry_attempts=3,
            timeout_seconds=300
        )

        scheduler_service = MarketDataSchedulerService(db_session, auto_start=False)

        print(f"\n=== SCHEDULER SERVICE DATABASE DEBUG ===")
        print(f"Scheduler service database session: {scheduler_service.db}")
        print(f"Our test database session: {db_session}")
        print(f"Sessions are same object: {scheduler_service.db is db_session}")

        # Test the internal database query directly
        internal_executions = scheduler_service.db.query(SchedulerExecution).all()
        external_executions = db_session.query(SchedulerExecution).all()

        print(f"Internal query count: {len(internal_executions)}")
        print(f"External query count: {len(external_executions)}")

        # If these differ, we've found the issue
        if len(internal_executions) != len(external_executions):
            print(f"❌ DATABASE SESSION MISMATCH DETECTED!")
            print(f"   Scheduler service sees {len(internal_executions)} records")
            print(f"   Test session sees {len(external_executions)} records")
            pytest.fail("Scheduler service using different database session!")
        else:
            print(f"✅ Database sessions are consistent")

    def test_scheduler_service_with_fresh_session(self):
        """
        Test scheduler service with a completely fresh database session.

        This mimics how the service would be used in production.
        """
        # Create fresh session like production would
        fresh_session = SessionLocal()

        try:
            # Verify records exist in fresh session
            fresh_count = fresh_session.query(SchedulerExecution).count()
            print(f"\n=== FRESH SESSION TEST ===")
            print(f"Fresh session record count: {fresh_count}")

            if fresh_count == 0:
                pytest.fail("Fresh session shows 0 records - database persistence issue!")

            # Create scheduler service with fresh session
            config = SchedulerConfiguration(
                interval_minutes=15,
                max_concurrent_jobs=5,
                retry_attempts=3,
                timeout_seconds=300
            )

            scheduler_service = MarketDataSchedulerService(fresh_session, auto_start=False)
            status = scheduler_service.get_status()

            print(f"Fresh session scheduler status:")
            print(f"  total_runs: {status.get('total_runs', 0)}")
            print(f"  total_symbols_processed: {status.get('total_symbols_processed', 0)}")
            print(f"  success_rate: {status.get('success_rate', 0)}%")

            # This should show the correct metrics
            assert status.get('total_runs', 0) > 0, "Fresh session should see execution records"
            assert status.get('total_symbols_processed', 0) > 0, "Fresh session should see processed symbols"

        finally:
            fresh_session.close()

    def test_admin_dashboard_scheduler_api_simulation(self, db_session):
        """
        Simulate exactly how the admin dashboard calls the scheduler API.

        This tests the exact code path used by the dashboard.
        """
        # This simulates how admin.py calls the scheduler service
        from src.services.scheduler_service import get_scheduler_service

        print(f"\n=== ADMIN DASHBOARD API SIMULATION ===")

        # Get scheduler service like admin dashboard does
        scheduler_service = get_scheduler_service(db_session)

        # Call get_status like admin dashboard does
        status = scheduler_service.get_status()

        print(f"Admin dashboard scheduler status:")
        print(f"  state: {status.get('state')}")
        print(f"  total_runs: {status.get('total_runs', 0)}")
        print(f"  successful_runs: {status.get('successful_runs', 0)}")
        print(f"  failed_runs: {status.get('failed_runs', 0)}")
        print(f"  total_symbols_processed: {status.get('total_symbols_processed', 0)}")
        print(f"  success_rate: {status.get('success_rate', 0)}%")
        print(f"  last_run: {status.get('last_run')}")
        print(f"  next_run: {status.get('next_run')}")

        # This is what should be fixed - admin dashboard should see correct metrics
        if status.get('total_symbols_processed', 0) == 0:
            print(f"❌ ADMIN DASHBOARD ISSUE REPRODUCED")
            print(f"   Admin API returns 0 symbols processed despite database having records")

            # Let's debug the scheduler service state
            print(f"\n=== SCHEDULER SERVICE DEBUG INFO ===")
            print(f"Service state: {scheduler_service.state}")
            print(f"Service database: {scheduler_service.db}")

            # Manual query through the service's database session
            manual_count = scheduler_service.db.query(SchedulerExecution).count()
            print(f"Manual query through service session: {manual_count}")

            if manual_count == 0:
                pytest.fail("Scheduler service database session sees 0 records - this is the root cause!")
            else:
                pytest.fail(f"Scheduler service sees {manual_count} records but get_status() returns 0 - logic bug in get_status()!")
        else:
            print(f"✅ Admin dashboard correctly shows {status.get('total_symbols_processed', 0)} symbols processed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
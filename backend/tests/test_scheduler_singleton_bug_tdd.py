#!/usr/bin/env python3
"""
TDD test to reproduce and fix the scheduler service singleton database session bug.

Root cause identified:
- get_scheduler_service() uses a global singleton that captures the first database session
- Subsequent calls ignore the new database session parameter
- This causes stale database sessions and incorrect metrics (0 symbols processed)

Fix: Ensure scheduler service always uses a fresh database session for queries.
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models.scheduler_execution import SchedulerExecution
from src.services.scheduler_service import get_scheduler_service, reset_scheduler_service, MarketDataSchedulerService


class TestSchedulerSingletonBugTDD:
    """TDD tests to reproduce and fix the scheduler singleton database session bug."""

    def setup_method(self):
        """Reset scheduler service before each test."""
        reset_scheduler_service()

    def test_scheduler_singleton_ignores_new_database_sessions(self):
        """
        Test that demonstrates the singleton bug.

        This test should FAIL initially, showing the singleton ignores new database sessions.
        """
        # Create first database session with some test data
        session1 = SessionLocal()

        try:
            # Add execution record in session1
            execution = SchedulerExecution(
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                status="success",
                symbols_processed=5,
                successful_fetches=5,
                failed_fetches=0,
                provider_used="test_provider"
            )
            session1.add(execution)
            session1.commit()
            session1.refresh(execution)

            # Get scheduler service with session1
            scheduler1 = get_scheduler_service(session1)
            status1 = scheduler1.get_status()

            print(f"\n=== FIRST CALL WITH SESSION1 ===")
            print(f"Scheduler service DB session: {scheduler1.db}")
            print(f"Total runs: {status1.get('total_runs', 0)}")
            print(f"Total symbols: {status1.get('total_symbols_processed', 0)}")

            # Now create a second database session
            session2 = SessionLocal()

            try:
                # Add another execution record in session2
                execution2 = SchedulerExecution(
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    status="success",
                    symbols_processed=3,
                    successful_fetches=3,
                    failed_fetches=0,
                    provider_used="test_provider2"
                )
                session2.add(execution2)
                session2.commit()

                # Get scheduler service with session2 (should use fresh session but doesn't due to singleton bug)
                scheduler2 = get_scheduler_service(session2)
                status2 = scheduler2.get_status()

                print(f"\n=== SECOND CALL WITH SESSION2 ===")
                print(f"Scheduler service DB session: {scheduler2.db}")
                print(f"Same service instance: {scheduler1 is scheduler2}")
                print(f"Same DB session: {scheduler1.db is scheduler2.db}")
                print(f"Total runs: {status2.get('total_runs', 0)}")
                print(f"Total symbols: {status2.get('total_symbols_processed', 0)}")

                # BUG: The singleton returns the same instance with the old database session
                if scheduler1 is scheduler2:
                    print(f"❌ SINGLETON BUG CONFIRMED: Same service instance returned")

                if scheduler1.db is scheduler2.db:
                    print(f"❌ DATABASE SESSION BUG CONFIRMED: Same DB session despite passing different session")

                # The scheduler should see records from both sessions but might not due to singleton bug
                direct_count_session2 = session2.query(SchedulerExecution).count()
                print(f"Direct query in session2: {direct_count_session2} records")

                # This might fail due to singleton using stale session1
                if status2.get('total_runs', 0) < direct_count_session2:
                    pytest.fail(f"Singleton bug: scheduler sees {status2.get('total_runs', 0)} but session2 has {direct_count_session2} records")

            finally:
                session2.close()

        finally:
            session1.close()

    def test_scheduler_service_should_use_provided_database_session(self):
        """
        Test that scheduler service should always use the provided database session.

        This test defines the correct behavior after the fix.
        """
        # Create two separate sessions
        session1 = SessionLocal()
        session2 = SessionLocal()

        try:
            # Add different data in each session
            execution1 = SchedulerExecution(
                started_at=datetime.utcnow(),
                status="success",
                symbols_processed=1,
                successful_fetches=1,
                failed_fetches=0
            )
            session1.add(execution1)
            session1.commit()

            execution2 = SchedulerExecution(
                started_at=datetime.utcnow(),
                status="success",
                symbols_processed=2,
                successful_fetches=2,
                failed_fetches=0
            )
            session2.add(execution2)
            session2.commit()

            # After fix: Each call should use the provided session
            scheduler1 = get_scheduler_service(session1)
            scheduler2 = get_scheduler_service(session2)

            # After fix: These should be different or use different sessions
            print(f"\n=== AFTER FIX BEHAVIOR ===")
            print(f"Service instances same: {scheduler1 is scheduler2}")
            print(f"DB sessions same: {scheduler1.db is scheduler2.db}")

            # After fix: Each should use its own session and see its own data
            status1 = scheduler1.get_status()
            status2 = scheduler2.get_status()

            print(f"Session1 scheduler sees: {status1.get('total_runs', 0)} runs")
            print(f"Session2 scheduler sees: {status2.get('total_runs', 0)} runs")

            # After fix: Both should see all committed data (since they're the same database)
            # but should use the correct session for queries
            assert status1.get('total_runs', 0) > 0, "Scheduler with session1 should see data"
            assert status2.get('total_runs', 0) > 0, "Scheduler with session2 should see data"

        finally:
            session1.close()
            session2.close()

    def test_admin_api_scheduler_session_behavior(self):
        """
        Test the specific admin API use case that's failing.

        This simulates the exact scenario where admin dashboard calls scheduler.
        """
        # Add some execution records first
        setup_session = SessionLocal()
        try:
            for i in range(3):
                execution = SchedulerExecution(
                    started_at=datetime.utcnow(),
                    status="success",
                    symbols_processed=i + 1,
                    successful_fetches=i + 1,
                    failed_fetches=0
                )
                setup_session.add(execution)
            setup_session.commit()
        finally:
            setup_session.close()

        # Simulate admin API call with fresh session (like FastAPI does)
        admin_session = SessionLocal()
        try:
            # This is exactly what admin.py does
            scheduler_service = get_scheduler_service(admin_session)
            status_info = scheduler_service.get_status()

            print(f"\n=== ADMIN API SIMULATION ===")
            print(f"Total runs: {status_info.get('total_runs', 0)}")
            print(f"Symbols processed: {status_info.get('total_symbols_processed', 0)}")
            print(f"Success rate: {status_info.get('success_rate', 0)}%")

            # This should NOT show 0 after the fix
            if status_info.get('total_symbols_processed', 0) == 0:
                pytest.fail("Admin API still shows 0 symbols processed - singleton bug not fixed!")

            # Verify against direct database query
            direct_count = admin_session.query(SchedulerExecution).count()
            direct_symbols = sum(ex.symbols_processed or 0 for ex in admin_session.query(SchedulerExecution).all())

            print(f"Direct query: {direct_count} runs, {direct_symbols} symbols")

            assert status_info.get('total_runs', 0) == direct_count, "Scheduler should match direct query"
            assert status_info.get('total_symbols_processed', 0) == direct_symbols, "Symbols should match direct query"

        finally:
            admin_session.close()

    def test_scheduler_service_database_session_refresh(self):
        """
        Test that scheduler service can handle database session refresh scenarios.

        This tests the robustness of the fix.
        """
        # Test multiple sequential calls with different sessions
        results = []

        for i in range(3):
            session = SessionLocal()
            try:
                # Add execution record
                execution = SchedulerExecution(
                    started_at=datetime.utcnow(),
                    status="success",
                    symbols_processed=i + 10,  # Different values to track
                    successful_fetches=i + 10,
                    failed_fetches=0
                )
                session.add(execution)
                session.commit()

                # Get scheduler status
                scheduler = get_scheduler_service(session)
                status = scheduler.get_status()

                results.append({
                    'call': i + 1,
                    'total_runs': status.get('total_runs', 0),
                    'total_symbols': status.get('total_symbols_processed', 0)
                })

                print(f"Call {i + 1}: {status.get('total_runs', 0)} runs, {status.get('total_symbols_processed', 0)} symbols")

            finally:
                session.close()

        # After fix: Each call should see cumulative data (since all use same database)
        # and the metrics should be non-decreasing
        for i in range(1, len(results)):
            assert results[i]['total_runs'] >= results[i-1]['total_runs'], "Total runs should not decrease"
            assert results[i]['total_symbols'] >= results[i-1]['total_symbols'], "Total symbols should not decrease"

        print(f"✅ All {len(results)} calls showed consistent, non-decreasing metrics")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
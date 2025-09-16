#!/usr/bin/env python3
"""
Test the scheduler fix directly to verify it's working.
"""

from src.database import SessionLocal
from src.services.scheduler_service import get_scheduler_service

def test_scheduler_fix():
    """Test that the scheduler service now returns correct metrics."""
    db = SessionLocal()

    try:
        print("=== Testing Scheduler Service Fix ===")

        # Get scheduler service with our fix
        scheduler_service = get_scheduler_service(db)
        status = scheduler_service.get_status()

        print(f"📊 Total runs: {status.get('total_runs', 0)}")
        print(f"📊 Successful runs: {status.get('successful_runs', 0)}")
        print(f"📊 Failed runs: {status.get('failed_runs', 0)}")
        print(f"📊 Total symbols processed: {status.get('total_symbols_processed', 0)}")
        print(f"📊 Success rate: {status.get('success_rate', 0)}%")
        print(f"📊 Last run: {status.get('last_run')}")
        print(f"📊 Next run: {status.get('next_run')}")

        # Verify against direct database query
        from src.models.scheduler_execution import SchedulerExecution
        direct_count = db.query(SchedulerExecution).count()
        direct_symbols = sum(ex.symbols_processed or 0 for ex in db.query(SchedulerExecution).all())

        print(f"\n=== Direct Database Query ===")
        print(f"📊 Direct count: {direct_count}")
        print(f"📊 Direct symbols: {direct_symbols}")

        # Check if fix is working
        if status.get('total_symbols_processed', 0) > 0:
            print(f"\n✅ FIX WORKING! Scheduler shows {status.get('total_symbols_processed', 0)} symbols processed")
        else:
            print(f"\n❌ FIX NOT WORKING! Scheduler still shows 0 symbols despite {direct_symbols} in database")

        return status

    except Exception as e:
        print(f"❌ Error testing scheduler fix: {e}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    test_scheduler_fix()
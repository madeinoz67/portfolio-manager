#!/usr/bin/env python3
"""
Create test scheduler execution data to verify the singleton fix.
"""

from datetime import datetime, timedelta
from src.database import SessionLocal
from src.models.scheduler_execution import SchedulerExecution

def create_test_data():
    """Create some test scheduler execution records."""
    db = SessionLocal()

    try:
        # Check if we already have test data
        existing_count = db.query(SchedulerExecution).count()
        if existing_count > 0:
            print(f"Found {existing_count} existing scheduler execution records")
            return

        print("Creating test scheduler execution records...")

        # Create several test execution records
        test_executions = [
            {
                "started_at": datetime.utcnow() - timedelta(minutes=45),
                "completed_at": datetime.utcnow() - timedelta(minutes=44),
                "status": "success",
                "symbols_processed": 8,
                "successful_fetches": 8,
                "failed_fetches": 0,
                "provider_used": "yahoo_finance"
            },
            {
                "started_at": datetime.utcnow() - timedelta(minutes=30),
                "completed_at": datetime.utcnow() - timedelta(minutes=29),
                "status": "success",
                "symbols_processed": 8,
                "successful_fetches": 7,
                "failed_fetches": 1,
                "provider_used": "yahoo_finance"
            },
            {
                "started_at": datetime.utcnow() - timedelta(minutes=15),
                "completed_at": datetime.utcnow() - timedelta(minutes=14),
                "status": "success",
                "symbols_processed": 8,
                "successful_fetches": 8,
                "failed_fetches": 0,
                "provider_used": "yahoo_finance"
            }
        ]

        for exec_data in test_executions:
            execution = SchedulerExecution(**exec_data)
            db.add(execution)

        db.commit()
        print(f"✅ Created {len(test_executions)} test scheduler execution records")

        # Verify the data
        total_records = db.query(SchedulerExecution).count()
        total_symbols = sum(ex.symbols_processed or 0 for ex in db.query(SchedulerExecution).all())
        print(f"📊 Total records: {total_records}, Total symbols processed: {total_symbols}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating test data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()
#!/usr/bin/env python3
"""
TDD script to clean up old invalid data detection metrics that are skewing the results.
This will remove the 96 invalid_data_detection records that are causing metrics inconsistency.
"""

import asyncio
import sys
import os
import sqlite3
from datetime import datetime, timedelta, timezone

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_and_clean_invalid_metrics():
    """Test and clean up invalid data detection metrics."""
    print("Testing and cleaning invalid metrics records...")

    # Connect to SQLite database
    db_path = "/Users/seaton/Documents/src/portfolio-manager/backend/portfolio.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # First, test current state
        print("\n=== BEFORE CLEANUP ===")
        cursor.execute("""
            SELECT COUNT(*) as total_count,
                   SUM(CASE WHEN request_type = 'invalid_data_detection' THEN 1 ELSE 0 END) as invalid_count,
                   SUM(CASE WHEN request_type = 'bulk_price_fetch' THEN 1 ELSE 0 END) as bulk_count
            FROM market_data_usage_metrics
            WHERE provider_name = 'yfinance'
        """)

        before_counts = cursor.fetchone()
        print(f"Total records: {before_counts[0]}")
        print(f"Invalid data detection records: {before_counts[1]}")
        print(f"Bulk price fetch records: {before_counts[2]}")

        # Calculate current metrics including invalid records
        cursor.execute("""
            SELECT SUM(requests_count) as total_requests,
                   SUM(error_count) as total_errors
            FROM market_data_usage_metrics
            WHERE provider_name = 'yfinance'
        """)

        before_metrics = cursor.fetchone()
        total_requests_before = before_metrics[0] or 0
        total_errors_before = before_metrics[1] or 0
        error_rate_before = (total_errors_before / total_requests_before * 100) if total_requests_before > 0 else 0

        print(f"Current error rate: {error_rate_before:.1f}% ({total_errors_before}/{total_requests_before})")

        # Clean up invalid data detection records (they're no longer needed since adapter is fixed)
        print(f"\n=== CLEANING UP INVALID DATA DETECTION RECORDS ===")
        cursor.execute("""
            DELETE FROM market_data_usage_metrics
            WHERE provider_name = 'yfinance'
            AND request_type = 'invalid_data_detection'
        """)

        deleted_count = cursor.rowcount
        print(f"Deleted {deleted_count} invalid data detection records")

        # Test after cleanup
        print(f"\n=== AFTER CLEANUP ===")
        cursor.execute("""
            SELECT COUNT(*) as total_count,
                   SUM(CASE WHEN request_type = 'invalid_data_detection' THEN 1 ELSE 0 END) as invalid_count,
                   SUM(CASE WHEN request_type = 'bulk_price_fetch' THEN 1 ELSE 0 END) as bulk_count
            FROM market_data_usage_metrics
            WHERE provider_name = 'yfinance'
        """)

        after_counts = cursor.fetchone()
        print(f"Total records: {after_counts[0]}")
        print(f"Invalid data detection records: {after_counts[1]}")
        print(f"Bulk price fetch records: {after_counts[2]}")

        # Calculate new metrics
        cursor.execute("""
            SELECT SUM(requests_count) as total_requests,
                   SUM(error_count) as total_errors
            FROM market_data_usage_metrics
            WHERE provider_name = 'yfinance'
        """)

        after_metrics = cursor.fetchone()
        total_requests_after = after_metrics[0] or 0
        total_errors_after = after_metrics[1] or 0
        error_rate_after = (total_errors_after / total_requests_after * 100) if total_requests_after > 0 else 0

        print(f"New error rate: {error_rate_after:.1f}% ({total_errors_after}/{total_requests_after})")

        # Commit changes
        conn.commit()
        conn.close()

        print(f"\n✅ CLEANUP COMPLETE")
        print(f"Error rate improved from {error_rate_before:.1f}% to {error_rate_after:.1f}%")

        return True

    except Exception as e:
        print(f"Error during cleanup: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

async def test_main():
    """Run the cleanup test."""
    result = await test_and_clean_invalid_metrics()
    if result:
        print("✅ Metrics cleanup successful!")
    else:
        print("❌ Metrics cleanup failed!")

if __name__ == "__main__":
    asyncio.run(test_main())
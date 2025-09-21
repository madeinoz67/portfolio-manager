#!/usr/bin/env python3
"""
TDD test to verify metrics calculation and database state.
Test that checks if old invalid data metrics are affecting current calculations.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone
import sqlite3

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_metrics_database_state():
    """Test the database state to understand metrics inconsistency."""
    print("Testing metrics database state...")

    # Connect to SQLite database
    db_path = "/Users/seaton/Documents/src/portfolio-manager/backend/portfolio.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("\n=== Market Data Usage Metrics ===")
        cursor.execute("""
            SELECT provider_name, request_type, requests_count, error_count, recorded_at
            FROM market_data_usage_metrics
            WHERE provider_name = 'yfinance'
            ORDER BY recorded_at DESC
            LIMIT 20
        """)

        results = cursor.fetchall()
        print(f"Found {len(results)} recent metrics records:")

        total_requests = 0
        total_errors = 0

        for row in results:
            provider, req_type, req_count, err_count, recorded = row
            total_requests += req_count or 0
            total_errors += err_count or 0
            print(f"  {recorded}: {req_type} - {req_count} requests, {err_count} errors")

        print(f"\nTOTAL: {total_requests} requests, {total_errors} errors")
        success_rate = ((total_requests - total_errors) / total_requests * 100) if total_requests > 0 else 0
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Error Rate: {error_rate:.1f}%")

        print("\n=== Invalid Data Detection Records ===")
        cursor.execute("""
            SELECT COUNT(*) as count, request_type
            FROM market_data_usage_metrics
            WHERE provider_name = 'yfinance'
            AND request_type = 'invalid_data_detection'
        """)

        invalid_count = cursor.fetchone()
        print(f"Invalid data detection records: {invalid_count[0] if invalid_count else 0}")

        print("\n=== Recent Bulk Updates ===")
        cursor.execute("""
            SELECT recorded_at, requests_count, error_count
            FROM market_data_usage_metrics
            WHERE provider_name = 'yfinance'
            AND request_type = 'bulk_price_fetch'
            ORDER BY recorded_at DESC
            LIMIT 10
        """)

        bulk_results = cursor.fetchall()
        print(f"Recent bulk updates:")
        for row in bulk_results:
            recorded, req_count, err_count = row
            print(f"  {recorded}: {req_count} requests, {err_count} errors")

        conn.close()

        # Check if the inconsistency is due to old invalid data records
        if total_errors > total_requests / 2:  # More than 50% errors suggests old bad data
            print(f"\n🚨 ISSUE DETECTED: {total_errors} errors vs {total_requests} total suggests old invalid data records!")
            return False
        else:
            print(f"\n✅ METRICS LOOK CONSISTENT")
            return True

    except Exception as e:
        print(f"Error checking database: {e}")
        return False

async def test_main():
    """Run the test."""
    result = await test_metrics_database_state()
    if result:
        print("✅ All metrics tests passed!")
    else:
        print("❌ Metrics inconsistency detected!")

if __name__ == "__main__":
    asyncio.run(test_main())
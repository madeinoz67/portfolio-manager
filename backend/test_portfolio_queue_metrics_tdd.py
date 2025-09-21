#!/usr/bin/env python3
"""
TDD test to investigate portfolio queue metrics frequency and optimize database writes.
Check if portfolio queue is writing metrics every 30 seconds and if this can be optimized.
"""

import asyncio
import sys
import os
import sqlite3
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_portfolio_queue_metrics_frequency():
    """Test portfolio queue metrics write frequency."""
    print("Testing portfolio queue metrics frequency...")

    # Connect to SQLite database
    db_path = "/Users/seaton/Documents/src/portfolio-manager/backend/portfolio.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("\n=== PORTFOLIO QUEUE METRICS ANALYSIS ===")

        # Check if portfolio_queue_metrics table exists and its recent activity
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='portfolio_queue_metrics'
        """)

        table_exists = cursor.fetchone()
        if not table_exists:
            print("❌ portfolio_queue_metrics table not found")
            return False

        # Get recent portfolio queue metrics records
        cursor.execute("""
            SELECT created_at, pending_updates, processing_rate, is_processing
            FROM portfolio_queue_metrics
            ORDER BY created_at DESC
            LIMIT 20
        """)

        records = cursor.fetchall()
        print(f"Found {len(records)} recent portfolio queue metrics records:")

        if not records:
            print("✅ No portfolio queue metrics records found - not generating excessive writes")
            return True

        # Analyze frequency
        write_intervals = []
        prev_time = None

        for i, (created_at, pending, rate, processing) in enumerate(records):
            created_dt = datetime.fromisoformat(created_at)
            print(f"  {created_at}: pending={pending}, rate={rate:.1f}, processing={processing}")

            if prev_time:
                interval = (prev_time - created_dt).total_seconds()
                write_intervals.append(interval)

            prev_time = created_dt

        if write_intervals:
            avg_interval = sum(write_intervals) / len(write_intervals)
            print(f"\nAVERAGE WRITE INTERVAL: {avg_interval:.1f} seconds")

            if avg_interval < 60:  # Less than 1 minute
                print(f"🚨 HIGH FREQUENCY DETECTED: Writing every {avg_interval:.1f}s")
                print("Recommendation: Increase interval to 5-15 minutes for production")
                return False
            else:
                print(f"✅ REASONABLE FREQUENCY: Writing every {avg_interval/60:.1f} minutes")
                return True
        else:
            print("✅ Insufficient data to determine frequency")
            return True

        conn.close()

    except Exception as e:
        print(f"Error analyzing portfolio queue metrics: {e}")
        return False

async def test_main():
    """Run the portfolio queue metrics analysis."""
    result = await test_portfolio_queue_metrics_frequency()

    if result:
        print("\n✅ Portfolio queue metrics frequency is acceptable")
    else:
        print("\n⚠️ Portfolio queue metrics frequency should be optimized")
        print("\nSUGGESTED FIXES:")
        print("1. Increase metrics_interval from 30s to 300s (5 minutes)")
        print("2. Only write metrics when queue state changes significantly")
        print("3. Implement metrics batching/aggregation")

if __name__ == "__main__":
    asyncio.run(test_main())
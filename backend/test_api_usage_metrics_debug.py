#!/usr/bin/env python3
"""
Debug script to investigate why API usage metrics aren't updating for providers.

The scheduler is working and processing symbols, but the admin dashboard shows
"Calls today: 0" for Yahoo Finance despite successful operations.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from src.database import SessionLocal
from src.services.market_data_service import MarketDataService
from src.models.market_data_provider import MarketDataProvider, ProviderActivity
from src.models.market_data_usage_metrics import MarketDataUsageMetrics


async def debug_api_usage_metrics():
    """Debug API usage metrics tracking."""
    print("=== API Usage Metrics Debug ===")

    db = SessionLocal()
    try:
        # Check if there are any usage metrics at all
        all_metrics = db.query(MarketDataUsageMetrics).all()
        print(f"Total API usage metrics records: {len(all_metrics)}")

        if all_metrics:
            print("Recent metrics:")
            for metric in all_metrics[-5:]:
                print(f"  {metric.provider_id}: {metric.requests_count} calls at {metric.recorded_at}")

        # Check recent provider activities
        recent_activities = (
            db.query(ProviderActivity)
            .filter(ProviderActivity.activity_type == 'API_CALL')
            .order_by(ProviderActivity.timestamp.desc())
            .limit(5)
            .all()
        )

        print(f"\nRecent API_CALL activities: {len(recent_activities)}")
        for activity in recent_activities:
            print(f"  {activity.provider_id}: {activity.description} at {activity.timestamp}")

        # Test if manual API call creates metrics
        print("\n=== Testing Manual API Call ===")
        service = MarketDataService(db)

        # Fetch a single price manually
        result = await service.fetch_price("TLS")
        print(f"Manual fetch result: {result}")

        # Check if metrics were created
        new_metrics = (
            db.query(MarketDataUsageMetrics)
            .filter(MarketDataUsageMetrics.recorded_at >= datetime.now(timezone.utc) - timedelta(minutes=1))
            .all()
        )

        print(f"New metrics created: {len(new_metrics)}")
        for metric in new_metrics:
            print(f"  {metric.provider_id}: {metric.requests_count} calls, {metric.data_points_fetched} points")

        # Check if the admin API calculation is correct
        print("\n=== Testing Admin API Calculation ===")

        # Get today's usage for yfinance
        today = datetime.now(timezone.utc).date()
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        today_end = today_start + timedelta(days=1)

        yfinance_today = (
            db.query(MarketDataUsageMetrics)
            .filter(
                MarketDataUsageMetrics.provider_id == 'yfinance',
                MarketDataUsageMetrics.recorded_at >= today_start,
                MarketDataUsageMetrics.recorded_at < today_end
            )
            .all()
        )

        total_calls_today = sum(metric.requests_count for metric in yfinance_today)
        print(f"Yahoo Finance calls today (calculated): {total_calls_today}")
        print(f"Records found: {len(yfinance_today)}")

        if yfinance_today:
            print("Today's records:")
            for metric in yfinance_today:
                print(f"  {metric.recorded_at}: {metric.requests_count} calls ({metric.metric_id})")

        await service.close_session()

    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


async def check_metrics_table_structure():
    """Check if the metrics table structure is correct."""
    print("\n=== Metrics Table Structure Check ===")

    db = SessionLocal()
    try:
        # Check if table exists and has expected columns
        result = db.execute("PRAGMA table_info(market_data_api_usage_metrics)")
        columns = result.fetchall()

        print("Table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")

        # Check if there's data in related tables
        providers = db.query(MarketDataProvider).all()
        print(f"\nProviders configured: {len(providers)}")
        for provider in providers:
            print(f"  {provider.name}: enabled={provider.is_enabled}")

    except Exception as e:
        print(f"❌ Table structure check failed: {e}")
    finally:
        db.close()


def check_admin_api_logic():
    """Check how the admin API calculates the metrics."""
    print("\n=== Admin API Logic Check ===")

    try:
        # Import and test the admin API function directly
        from src.api.admin import get_provider_status
        from src.database import get_db

        db_gen = get_db()
        db = next(db_gen)

        try:
            provider_status = get_provider_status(db)
            print("Provider status from admin API:")
            for provider in provider_status:
                print(f"  {provider['name']}: {provider['usage']['calls_today']} calls today")
                print(f"    Monthly: {provider['usage']['calls_this_month']} / {provider['usage']['monthly_limit']}")

        except Exception as e:
            print(f"❌ Admin API test failed: {e}")
            import traceback
            traceback.print_exc()

        finally:
            next(db_gen, None)  # Close generator

    except ImportError as e:
        print(f"❌ Could not import admin API: {e}")


async def main():
    """Main debug function."""
    print("Debugging API usage metrics tracking issue...\n")

    await check_metrics_table_structure()
    await debug_api_usage_metrics()
    check_admin_api_logic()

    print("\n=== Debug Complete ===")
    print("Check the output above to identify why API usage metrics aren't updating.")


if __name__ == "__main__":
    asyncio.run(main())
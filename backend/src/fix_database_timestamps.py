#!/usr/bin/env python3
"""
Fix database timestamps that were incorrectly stored as local time instead of UTC.

This script converts all existing timestamps in the database from local time
(Pacific Time, UTC-8) to proper UTC time.
"""

from datetime import datetime, timezone, timedelta
import sys
import os

# Add src to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import SessionLocal
from models.market_data_provider import ProviderActivity, MarketDataProvider
from models.portfolio_valuation import PortfolioValuation
from models.user import User
from models.portfolio import Portfolio
from models.transaction import Transaction


def main():
    """Fix all database timestamps by converting from local time to UTC."""
    print("🔧 Starting database timestamp fix...")
    print("Converting local time (Pacific Time, UTC-8) to proper UTC...")

    # Your timezone offset (Pacific Time is UTC-8, but currently UTC-7 due to daylight saving)
    # Based on the 7.9 hour difference we observed
    timezone_offset_hours = 8  # Standard Pacific Time offset

    db = SessionLocal()

    try:
        # Fix ProviderActivity timestamps
        activities = db.query(ProviderActivity).all()
        print(f"\n📊 Fixing {len(activities)} provider activities...")

        for activity in activities:
            if activity.timestamp.tzinfo is None:
                # Naive datetime - assume it's local time, convert to UTC
                utc_time = activity.timestamp - timedelta(hours=timezone_offset_hours)
                activity.timestamp = utc_time.replace(tzinfo=timezone.utc)
                print(f"  ✓ {activity.activity_type}: {activity.timestamp.replace(tzinfo=None)} → {utc_time}")

        # Fix MarketDataProvider timestamps
        providers = db.query(MarketDataProvider).all()
        print(f"\n🏪 Fixing {len(providers)} market data providers...")

        for provider in providers:
            if provider.created_at and provider.created_at.tzinfo is None:
                utc_time = provider.created_at - timedelta(hours=timezone_offset_hours)
                provider.created_at = utc_time.replace(tzinfo=timezone.utc)
                print(f"  ✓ {provider.name} created_at: {provider.created_at.replace(tzinfo=None)} → {utc_time}")

            if provider.updated_at and provider.updated_at.tzinfo is None:
                utc_time = provider.updated_at - timedelta(hours=timezone_offset_hours)
                provider.updated_at = utc_time.replace(tzinfo=timezone.utc)
                print(f"  ✓ {provider.name} updated_at: {provider.updated_at.replace(tzinfo=None)} → {utc_time}")

        # Fix PortfolioValuation timestamps if they exist
        valuations = db.query(PortfolioValuation).all()
        if valuations:
            print(f"\n💰 Fixing {len(valuations)} portfolio valuations...")

            for valuation in valuations:
                if valuation.calculated_at and valuation.calculated_at.tzinfo is None:
                    utc_time = valuation.calculated_at - timedelta(hours=timezone_offset_hours)
                    valuation.calculated_at = utc_time.replace(tzinfo=timezone.utc)
                    print(f"  ✓ Valuation calculated_at: {valuation.calculated_at.replace(tzinfo=None)} → {utc_time}")

                if valuation.expires_at and valuation.expires_at.tzinfo is None:
                    utc_time = valuation.expires_at - timedelta(hours=timezone_offset_hours)
                    valuation.expires_at = utc_time.replace(tzinfo=timezone.utc)
                    print(f"  ✓ Valuation expires_at: {valuation.expires_at.replace(tzinfo=None)} → {utc_time}")

        # Commit all changes
        db.commit()
        print("\n✅ Database timestamp fix completed successfully!")
        print("\nNext steps:")
        print("1. Restart the FastAPI server to pick up changes")
        print("2. Test the scheduler API to verify UTC times")
        print("3. Monitor future timestamps to ensure they remain in UTC")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error fixing timestamps: {e}")
        return False

    finally:
        db.close()

    return True


if __name__ == "__main__":
    main()
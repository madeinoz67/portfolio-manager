#!/usr/bin/env python3
"""
Script to populate market data for existing portfolio holdings.

This script addresses the frontend issue where portfolio overview shows
$0.00 daily change due to missing market data in realtime_symbols table
and missing previous_close data.

Usage:
    python scripts/populate_market_data.py [--dry-run]
"""

import sys
import argparse
from pathlib import Path

# Add the src directory to the path so we can import our modules
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from database import get_db
from services.market_data_population_service import MarketDataPopulationService
from services.dynamic_portfolio_service import DynamicPortfolioService


def main():
    """Main script function."""
    parser = argparse.ArgumentParser(description="Populate market data for portfolio holdings")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without making changes")
    parser.add_argument("--verify-only", action="store_true",
                       help="Only verify current status without populating data")
    args = parser.parse_args()

    print("=== Market Data Population Script ===")
    print()

    # Get database session
    db = next(get_db())
    population_service = MarketDataPopulationService(db)

    try:
        # Step 1: Check current status
        print("1. Checking current market data status...")
        status = population_service.get_market_data_status()

        print(f"   Total portfolio symbols: {status['total_portfolio_symbols']}")
        print(f"   Symbols with master data: {status['symbols_with_master_data']}")
        print(f"   Symbols with previous close: {status['symbols_with_previous_close']}")
        print(f"   Coverage percentage: {status['coverage_percentage']:.1f}%")
        print(f"   Daily change enabled: {status['daily_change_enabled']}")

        if status['missing_symbols']:
            print(f"   Missing symbols: {', '.join(status['missing_symbols'])}")
        print()

        if args.verify_only:
            print("Verification complete. Use --help for population options.")
            return

        # Step 2: Show what needs to be done
        symbols_needing_data = population_service._get_symbols_needing_market_data()
        if not symbols_needing_data:
            print("✅ All portfolio symbols already have market data!")
            return

        print(f"2. Found {len(symbols_needing_data)} symbols needing market data:")
        for symbol_data in symbols_needing_data:
            print(f"   - {symbol_data['symbol']}: ${symbol_data['current_price']} ({symbol_data['company_name']})")
        print()

        if args.dry_run:
            print("DRY RUN: Would populate market data for the above symbols")
            print("Run without --dry-run to actually populate the data")
            return

        # Step 3: Populate market data
        print("3. Populating market data...")
        result = population_service.populate_portfolio_symbols_market_data(mock_data=True)

        if result["status"] == "success":
            print(f"✅ {result['message']}")
            print()

            # Show details of populated data
            for symbol_info in result["symbols"]:
                print(f"   {symbol_info['symbol']}:")
                print(f"     Current: ${symbol_info['current_price']:.2f}")
                print(f"     Previous Close: ${symbol_info['previous_close']:.2f}")
                print(f"     Daily Change/Share: ${symbol_info['daily_change_per_share']:.2f} ({symbol_info['change_percent']:.1f}%)")
                print()
        else:
            print(f"❌ {result['message']}")
            return

        # Step 4: Verify the fix worked
        print("4. Verifying daily change calculation...")

        # Get a portfolio to test with
        from sqlalchemy import text
        portfolio_result = db.execute(text("""
            SELECT DISTINCT p.id, p.name
            FROM portfolios p
            JOIN holdings h ON p.id = h.portfolio_id
            WHERE p.is_active = true AND h.quantity > 0
            LIMIT 1
        """)).fetchone()

        if portfolio_result:
            portfolio_service = DynamicPortfolioService(db)
            portfolio_response = portfolio_service.get_dynamic_portfolio(str(portfolio_result.id))

            if portfolio_response:
                print(f"   Portfolio: {portfolio_result.name}")
                print(f"   Total Value: ${portfolio_response.total_value:.2f}")
                print(f"   Daily Change: ${portfolio_response.daily_change:.2f} ({portfolio_response.daily_change_percent:.2f}%)")

                if portfolio_response.daily_change != 0:
                    print("   ✅ Daily change calculation is now working!")
                else:
                    print("   ⚠️  Daily change is still $0.00 - may need real market data")
            else:
                print("   ❌ Could not get portfolio response")
        else:
            print("   No portfolios found to test with")

        print()
        print("=== Market Data Population Complete ===")
        print()
        print("The frontend portfolio overview should now show daily change values")
        print("instead of $0.00. Refresh your browser to see the updated values.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
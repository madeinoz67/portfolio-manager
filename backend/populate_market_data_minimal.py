#!/usr/bin/env python3
"""
Minimal script to populate market data using existing TDD-tested service.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.database import SessionLocal
from src.services.market_data_population_service import MarketDataPopulationService

def main():
    """Populate market data for portfolio symbols."""
    print("=== Market Data Population (Minimal) ===")

    db = SessionLocal()
    try:
        service = MarketDataPopulationService(db)

        # Check current status
        print("1. Current status:")
        status = service.get_market_data_status()
        print(f"   Portfolio symbols: {status['total_portfolio_symbols']}")
        print(f"   With master data: {status['symbols_with_master_data']}")
        print(f"   Coverage: {status['coverage_percentage']:.1f}%")

        if status['missing_symbols']:
            print(f"   Missing: {', '.join(status['missing_symbols'])}")

        # Populate data
        print("\n2. Populating market data...")
        result = service.populate_portfolio_symbols_market_data(mock_data=True)

        if result["status"] == "success":
            print(f"✅ {result['message']}")
            for symbol_info in result["symbols"]:
                print(f"   {symbol_info['symbol']}: ${symbol_info['current_price']:.2f} → ${symbol_info['previous_close']:.2f}")
        else:
            print(f"❌ {result['message']}")

        # Verify fix
        print("\n3. Verification:")
        final_status = service.get_market_data_status()
        print(f"   Coverage now: {final_status['coverage_percentage']:.1f}%")
        print(f"   Daily change enabled: {final_status['daily_change_enabled']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
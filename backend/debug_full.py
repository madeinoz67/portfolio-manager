#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.database import SessionLocal
from src.services.market_data_population_service import MarketDataPopulationService

db = SessionLocal()
try:
    service = MarketDataPopulationService(db)

    print("=== Full Debug ===")

    # Step 1: Check provider
    provider = service._get_enabled_provider()
    print(f"Provider: {provider.name if provider else 'None'}")

    # Step 2: Get symbols needing data
    symbols_needing_data = service._get_symbols_needing_market_data()
    print(f"Symbols needing data: {len(symbols_needing_data)}")

    # Step 3: Try to populate one symbol manually
    if symbols_needing_data and provider:
        print("\nTrying to populate first symbol manually...")
        symbol_data = symbols_needing_data[0]
        print(f"Symbol data: {symbol_data}")

        try:
            result = service._populate_symbol_market_data(symbol_data, provider, mock_data=True)
            print(f"Population result: {result}")
        except Exception as e:
            print(f"Error in _populate_symbol_market_data: {e}")
            import traceback
            traceback.print_exc()

finally:
    db.close()
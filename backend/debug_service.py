#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.database import SessionLocal
from src.services.market_data_population_service import MarketDataPopulationService

db = SessionLocal()
try:
    service = MarketDataPopulationService(db)

    print("=== Testing service method directly ===")

    # Call the actual method that's failing
    symbols_needing_data = service._get_symbols_needing_market_data()
    print(f"Service returned: {len(symbols_needing_data)} symbols")
    for s in symbols_needing_data:
        print(f"  {s}")

finally:
    db.close()
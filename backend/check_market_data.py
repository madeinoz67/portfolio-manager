#!/usr/bin/env python3

from src.database import SessionLocal
from src.models.realtime_symbol import RealtimeSymbol
from datetime import datetime, timezone

def check_market_data():
    db = SessionLocal()
    try:
        symbols = db.query(RealtimeSymbol).all()
        if symbols:
            print(f"Found {len(symbols)} symbols in realtime_symbols table:")
            for symbol in symbols:
                age_seconds = (datetime.now(timezone.utc) - symbol.last_updated.replace(tzinfo=timezone.utc)).total_seconds()
                age_minutes = age_seconds / 60
                status = "FRESH" if age_minutes < 30 else "STALE"
                print(f"  {symbol.symbol}: ${symbol.current_price} - {age_minutes:.1f} min old - {status}")
        else:
            print("❌ No symbols found in realtime_symbols table")
    finally:
        db.close()

if __name__ == "__main__":
    check_market_data()
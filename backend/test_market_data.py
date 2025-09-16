#!/usr/bin/env python3

from src.database import SessionLocal
from src.models import RealtimeSymbol, MarketDataProvider, Stock

db = SessionLocal()
try:
    # Check realtime symbols
    realtime_symbols = db.query(RealtimeSymbol).all()
    print(f"Realtime symbols count: {len(realtime_symbols)}")
    for symbol in realtime_symbols:
        print(f"- {symbol.symbol}: ${symbol.current_price} (updated: {symbol.last_updated})")

    print()

    # Check market data providers
    providers = db.query(MarketDataProvider).all()
    print(f"Market data providers count: {len(providers)}")
    for provider in providers:
        print(f"- {provider.name}: enabled={provider.is_enabled}")

    print()

    # Check stocks
    stocks = db.query(Stock).all()
    print(f"Stocks count: {len(stocks)}")
    for stock in stocks:
        print(f"- {stock.symbol}: current=${stock.current_price}, previous=${stock.previous_close}")

finally:
    db.close()
#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("=== Current Data State ===")

    # Check stocks table
    stocks = db.execute(text("SELECT symbol, current_price, previous_close FROM stocks WHERE symbol IN ('FE', 'CSL')")).fetchall()
    for s in stocks:
        print(f"{s.symbol}: current=${s.current_price}, previous_close=${s.previous_close}")

    print()

    # Check realtime_symbols
    rt_symbols = db.execute(text("SELECT symbol, current_price FROM realtime_symbols WHERE symbol IN ('FE', 'CSL')")).fetchall()
    for rs in rt_symbols:
        print(f"Master {rs.symbol}: current_price=${rs.current_price}")

    print()

    # Check holdings
    holdings = db.execute(text("SELECT h.quantity, h.average_cost, s.symbol FROM holdings h JOIN stocks s ON h.stock_id = s.id WHERE s.symbol IN ('FE', 'CSL')")).fetchall()
    for h in holdings:
        print(f"{h.symbol}: {h.quantity} shares @ ${h.average_cost} avg cost")

    print()

    # Calculate expected vs actual
    print("=== Expected vs Frontend ===")
    for h in holdings:
        stock = next((s for s in stocks if s.symbol == h.symbol), None)
        if stock and stock.previous_close:
            daily_change_per_share = stock.current_price - stock.previous_close
            total_daily_change = daily_change_per_share * h.quantity
            gain_loss_vs_cost = (stock.current_price - h.average_cost) * h.quantity
            print(f"{h.symbol}:")
            print(f"  Daily change: ${daily_change_per_share:.2f}/share * {h.quantity} = ${total_daily_change:.2f}")
            print(f"  Gain/Loss vs cost: ${gain_loss_vs_cost:.2f} (this matches frontend)")
            print()

finally:
    db.close()
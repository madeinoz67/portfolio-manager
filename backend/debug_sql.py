#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("=== SQL Debug ===")

    # Check portfolios
    portfolios = db.execute(text("SELECT id, name, is_active FROM portfolios")).fetchall()
    print(f"Portfolios: {len(portfolios)}")
    for p in portfolios:
        print(f"  {p.name}: active={p.is_active}")

    print()

    # Check holdings
    holdings = db.execute(text("SELECT h.id, h.portfolio_id, h.stock_id, h.quantity, s.symbol FROM holdings h JOIN stocks s ON h.stock_id = s.id")).fetchall()
    print(f"Holdings: {len(holdings)}")
    for h in holdings:
        print(f"  Stock {h.symbol}: {h.quantity} shares in portfolio {h.portfolio_id}")

    print()

    # Debug the exact query
    query = text("""
        SELECT DISTINCT
            s.symbol,
            s.current_price,
            s.company_name,
            s.id as stock_id,
            p.is_active,
            h.quantity
        FROM stocks s
        JOIN holdings h ON s.id = h.stock_id
        JOIN portfolios p ON h.portfolio_id = p.id
        WHERE p.is_active = true
            AND h.quantity > 0
            AND s.symbol NOT IN (SELECT symbol FROM realtime_symbols)
        ORDER BY s.symbol
    """)

    results = db.execute(query).fetchall()
    print(f"Query results: {len(results)}")
    for r in results:
        print(f"  {r.symbol}: ${r.current_price} ({r.company_name}) - {r.quantity} shares, active={r.is_active}")

finally:
    db.close()
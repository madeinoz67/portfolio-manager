#!/usr/bin/env python3

from src.database import SessionLocal
from src.models.portfolio import Portfolio
from datetime import datetime, timezone

def check_portfolio_updates():
    db = SessionLocal()
    try:
        portfolios = db.query(Portfolio).all()
        if portfolios:
            print(f"Found {len(portfolios)} portfolios:")
            for portfolio in portfolios:
                # Calculate age
                now = datetime.now(timezone.utc)

                # Check updated_at
                if portfolio.updated_at:
                    updated_age_seconds = (now - portfolio.updated_at.replace(tzinfo=timezone.utc)).total_seconds()
                    updated_age_minutes = updated_age_seconds / 60
                    updated_status = "FRESH" if updated_age_minutes < 30 else "STALE"
                    print(f"  {portfolio.name} (ID: {portfolio.id})")
                    print(f"    updated_at: {updated_age_minutes:.1f} min ago - {updated_status}")

                # Check price_last_updated if available
                if hasattr(portfolio, 'price_last_updated') and portfolio.price_last_updated:
                    price_age_seconds = (now - portfolio.price_last_updated.replace(tzinfo=timezone.utc)).total_seconds()
                    price_age_minutes = price_age_seconds / 60
                    price_status = "FRESH" if price_age_minutes < 30 else "STALE"
                    print(f"    price_last_updated: {price_age_minutes:.1f} min ago - {price_status}")
                else:
                    print(f"    price_last_updated: None")

                print()
        else:
            print("❌ No portfolios found")
    finally:
        db.close()

if __name__ == "__main__":
    check_portfolio_updates()
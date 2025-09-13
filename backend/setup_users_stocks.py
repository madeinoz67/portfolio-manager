#!/usr/bin/env python3
"""
Create basic users, stocks, and portfolios for testing.
"""

import sys
from sqlalchemy.orm import Session

from src.database import engine, Base
from src.models import User, Portfolio, Stock, StockStatus
from src.core.auth import get_password_hash


def setup_basic_data():
    """Create users, stocks, and empty portfolios."""
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        # Create test users
        print("Creating test users...")
        admin_user = User(
            email="admin@example.com",
            password_hash=get_password_hash("admin123"),
            first_name="Admin",
            last_name="User",
            role="ADMIN"
        )
        regular_user = User(
            email="user@example.com",
            password_hash=get_password_hash("user12345"),
            first_name="Regular",
            last_name="User",
            role="USER"
        )
        db.add(admin_user)
        db.add(regular_user)
        db.commit()
        db.refresh(admin_user)
        db.refresh(regular_user)
        print(f"Created admin user: {admin_user.email}")
        print(f"Created regular user: {regular_user.email}")

        # Create ASX stocks
        print("Creating ASX stocks...")
        stocks = [
            Stock(symbol="CBA", company_name="Commonwealth Bank of Australia", exchange="ASX", status=StockStatus.ACTIVE),
            Stock(symbol="BHP", company_name="BHP Group Limited", exchange="ASX", status=StockStatus.ACTIVE),
            Stock(symbol="WBC", company_name="Westpac Banking Corporation", exchange="ASX", status=StockStatus.ACTIVE),
            Stock(symbol="CSL", company_name="CSL Limited", exchange="ASX", status=StockStatus.ACTIVE),
            Stock(symbol="WOW", company_name="Woolworths Group Limited", exchange="ASX", status=StockStatus.ACTIVE),
            Stock(symbol="ANZ", company_name="Australia and New Zealand Banking Group", exchange="ASX", status=StockStatus.ACTIVE),
            Stock(symbol="NAB", company_name="National Australia Bank Limited", exchange="ASX", status=StockStatus.ACTIVE),
            Stock(symbol="TLS", company_name="Telstra Corporation Limited", exchange="ASX", status=StockStatus.ACTIVE),
        ]

        for stock in stocks:
            db.add(stock)
        db.commit()
        print(f"Created {len(stocks)} ASX stocks")

        # Create portfolios
        print("Creating portfolios...")
        admin_portfolio = Portfolio(
            name="Admin ASX Portfolio",
            description="Admin's Australian Stock Exchange investment portfolio",
            owner_id=admin_user.id
        )
        regular_portfolio = Portfolio(
            name="Growth Portfolio",
            description="Regular user's growth-focused ASX portfolio",
            owner_id=regular_user.id
        )
        db.add(admin_portfolio)
        db.add(regular_portfolio)
        db.commit()
        db.refresh(admin_portfolio)
        db.refresh(regular_portfolio)
        print(f"Created admin portfolio: {admin_portfolio.name} (ID: {admin_portfolio.id})")
        print(f"Created regular portfolio: {regular_portfolio.name} (ID: {regular_portfolio.id})")

        print("\nSetup complete!")
        print("Admin login: admin@example.com / admin123")
        print("User login: user@example.com / user123")
        print(f"Admin portfolio ID: {admin_portfolio.id}")
        print(f"Regular portfolio ID: {regular_portfolio.id}")


if __name__ == "__main__":
    try:
        setup_basic_data()
        print("\n✅ Setup completed successfully!")
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        sys.exit(1)
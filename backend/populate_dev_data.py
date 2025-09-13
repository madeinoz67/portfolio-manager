#!/usr/bin/env python3
"""
Populate development database with scaffolding data for testing the transaction list functionality.
"""

import sys
import asyncio
from decimal import Decimal
from datetime import date, datetime

from sqlalchemy.orm import Session

# Import our application models and database setup
from src.database import engine, Base
from src.models import User, Portfolio, Stock, Transaction, Holding, StockStatus
from src.models.transaction import TransactionType, SourceType
from src.core.auth import get_password_hash


def populate_dev_database():
    """Populate the development database with scaffolding data."""
    # Create all tables
    print("Creating database tables...")
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
            password_hash=get_password_hash("user123"),
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

        # Create test stocks
        print("Creating test stocks...")
        stocks = [
            Stock(
                symbol="CBA",
                company_name="Commonwealth Bank of Australia",
                exchange="ASX",
                status=StockStatus.ACTIVE
            ),
            Stock(
                symbol="BHP",
                company_name="BHP Group Limited",
                exchange="ASX",
                status=StockStatus.ACTIVE
            ),
            Stock(
                symbol="WBC",
                company_name="Westpac Banking Corporation",
                exchange="ASX",
                status=StockStatus.ACTIVE
            ),
            Stock(
                symbol="CSL",
                company_name="CSL Limited",
                exchange="ASX",
                status=StockStatus.ACTIVE
            ),
            Stock(
                symbol="WOW",
                company_name="Woolworths Group Limited",
                exchange="ASX",
                status=StockStatus.ACTIVE
            )
        ]

        for stock in stocks:
            db.add(stock)

        db.commit()
        for stock in stocks:
            db.refresh(stock)
        print(f"Created {len(stocks)} stocks")

        # Create portfolios for both users
        print("Creating test portfolios...")
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
        print(f"Created admin portfolio: {admin_portfolio.name}")
        print(f"Created regular portfolio: {regular_portfolio.name}")

        # Create comprehensive test transactions to ensure every transaction is accounted for
        print("Creating test transactions...")
        transactions = [
            # Admin Portfolio transactions
            # CBA transactions - 3 transactions
            Transaction(
                portfolio_id=admin_portfolio.id,
                stock_id=stocks[0].id,  # CBA
                transaction_type=TransactionType.BUY,
                quantity=Decimal("200"),
                price_per_share=Decimal("48.50"),
                total_amount=Decimal("9700.00"),
                source_type=SourceType.MANUAL,
                transaction_date=date(2024, 1, 15),
                notes="Initial CBA investment"
            ),
            Transaction(
                portfolio_id=admin_portfolio.id,
                stock_id=stocks[0].id,  # CBA
                transaction_type=TransactionType.BUY,
                quantity=Decimal("100"),
                price_per_share=Decimal("52.00"),
                total_amount=Decimal("5200.00"),
                source_type=SourceType.MANUAL,
                transaction_date=date(2024, 3, 10),
                notes="Additional CBA purchase"
            ),
            Transaction(
                portfolio_id=admin_portfolio.id,
                stock_id=stocks[0].id,  # CBA
                transaction_type=TransactionType.SELL,
                quantity=Decimal("50"),
                price_per_share=Decimal("55.00"),
                total_amount=Decimal("2750.00"),
                source_type=SourceType.MANUAL,
                transaction_date=date(2024, 6, 20),
                notes="Partial CBA sale for profit taking"
            ),

            # BHP transactions - 2 transactions
            Transaction(
                portfolio_id=admin_portfolio.id,
                stock_id=stocks[1].id,  # BHP
                transaction_type=TransactionType.BUY,
                quantity=Decimal("300"),
                price_per_share=Decimal("35.00"),
                total_amount=Decimal("10500.00"),
                source_type=SourceType.MANUAL,
                transaction_date=date(2024, 2, 5),
                notes="Initial BHP investment"
            ),
            Transaction(
                portfolio_id=admin_portfolio.id,
                stock_id=stocks[1].id,  # BHP
                transaction_type=TransactionType.BUY,
                quantity=Decimal("100"),
                price_per_share=Decimal("38.50"),
                total_amount=Decimal("3850.00"),
                source_type=SourceType.MANUAL,
                transaction_date=date(2024, 4, 15),
                notes="Additional BHP purchase"
            ),

            # WBC transactions - 2 transactions
            Transaction(
                portfolio_id=admin_portfolio.id,
                stock_id=stocks[2].id,  # WBC
                transaction_type=TransactionType.BUY,
                quantity=Decimal("250"),
                price_per_share=Decimal("22.50"),
                total_amount=Decimal("5625.00"),
                source_type=SourceType.MANUAL,
                transaction_date=date(2024, 1, 30),
                notes="Initial WBC investment"
            ),
            Transaction(
                portfolio_id=admin_portfolio.id,
                stock_id=stocks[2].id,  # WBC
                transaction_type=TransactionType.SELL,
                quantity=Decimal("100"),
                price_per_share=Decimal("24.00"),
                total_amount=Decimal("2400.00"),
                source_type=SourceType.MANUAL,
                transaction_date=date(2024, 5, 10),
                notes="Partial WBC sale"
            ),

            # CSL transactions - 1 transaction
            Transaction(
                portfolio_id=admin_portfolio.id,
                stock_id=stocks[3].id,  # CSL
                transaction_type=TransactionType.BUY,
                quantity=Decimal("50"),
                price_per_share=Decimal("280.00"),
                total_amount=Decimal("14000.00"),
                source_type=SourceType.MANUAL,
                transaction_date=date(2024, 3, 25),
                notes="CSL investment for diversification"
            ),

            # WOW transactions - 1 transaction
            Transaction(
                portfolio_id=admin_portfolio.id,
                stock_id=stocks[4].id,  # WOW
                transaction_type=TransactionType.BUY,
                quantity=Decimal("180"),
                price_per_share=Decimal("35.50"),
                total_amount=Decimal("6390.00"),
                source_type=SourceType.MANUAL,
                transaction_date=date(2024, 2, 18),
                notes="WOW investment for retail exposure"
            ),

            # Regular User Portfolio transactions
            # BHP transactions - focused on resources
            Transaction(
                portfolio_id=regular_portfolio.id,
                stock_id=stocks[1].id,  # BHP
                transaction_type=TransactionType.BUY,
                quantity=Decimal("500"),
                price_per_share=Decimal("36.00"),
                total_amount=Decimal("18000.00"),
                source_type=SourceType.MANUAL,
                transaction_date=date(2024, 1, 20),
                notes="Initial BHP position for resources exposure"
            ),
            Transaction(
                portfolio_id=regular_portfolio.id,
                stock_id=stocks[1].id,  # BHP
                transaction_type=TransactionType.SELL,
                quantity=Decimal("100"),
                price_per_share=Decimal("38.00"),
                total_amount=Decimal("3800.00"),
                source_type=SourceType.MANUAL,
                transaction_date=date(2024, 5, 15),
                notes="Partial BHP sale for rebalancing"
            ),

            # CSL transactions - healthcare focus
            Transaction(
                portfolio_id=regular_portfolio.id,
                stock_id=stocks[3].id,  # CSL
                transaction_type=TransactionType.BUY,
                quantity=Decimal("75"),
                price_per_share=Decimal("275.00"),
                total_amount=Decimal("20625.00"),
                source_type=SourceType.MANUAL,
                transaction_date=date(2024, 3, 5),
                notes="Healthcare diversification through CSL"
            ),

            # WOW transactions - consumer staples
            Transaction(
                portfolio_id=regular_portfolio.id,
                stock_id=stocks[4].id,  # WOW
                transaction_type=TransactionType.BUY,
                quantity=Decimal("200"),
                price_per_share=Decimal("34.50"),
                total_amount=Decimal("6900.00"),
                source_type=SourceType.MANUAL,
                transaction_date=date(2024, 2, 10),
                notes="Consumer staples exposure via WOW"
            )
        ]

        for transaction in transactions:
            db.add(transaction)

        db.commit()
        for transaction in transactions:
            db.refresh(transaction)

        print(f"Created {len(transactions)} transactions")
        print("Transaction breakdown:")
        print(f"  - CBA: 3 transactions")
        print(f"  - BHP: 2 transactions")
        print(f"  - WBC: 2 transactions")
        print(f"  - CSL: 1 transaction")
        print(f"  - WOW: 1 transaction")
        print(f"  - Total: {len(transactions)} transactions")

        # Create corresponding holdings based on net transactions
        print("Creating holdings...")
        holdings = [
            Holding(
                portfolio_id=admin_portfolio.id,
                stock_id=stocks[0].id,  # CBA: 200 + 100 - 50 = 250 shares
                quantity=Decimal("250"),
                average_cost=Decimal("49.80"),  # Weighted average
                current_value=Decimal("13750.00")  # 250 * $55
            ),
            Holding(
                portfolio_id=admin_portfolio.id,
                stock_id=stocks[1].id,  # BHP: 300 + 100 = 400 shares
                quantity=Decimal("400"),
                average_cost=Decimal("35.875"),  # Weighted average
                current_value=Decimal("15400.00")  # 400 * $38.50
            ),
            Holding(
                portfolio_id=admin_portfolio.id,
                stock_id=stocks[2].id,  # WBC: 250 - 100 = 150 shares
                quantity=Decimal("150"),
                average_cost=Decimal("22.50"),
                current_value=Decimal("3600.00")  # 150 * $24
            ),
            Holding(
                portfolio_id=admin_portfolio.id,
                stock_id=stocks[3].id,  # CSL: 50 shares
                quantity=Decimal("50"),
                average_cost=Decimal("280.00"),
                current_value=Decimal("15000.00")  # 50 * $300
            ),
            Holding(
                portfolio_id=admin_portfolio.id,
                stock_id=stocks[4].id,  # WOW: 180 shares
                quantity=Decimal("180"),
                average_cost=Decimal("35.50"),
                current_value=Decimal("6480.00")  # 180 * $36
            ),

            # Regular Portfolio Holdings
            Holding(
                portfolio_id=regular_portfolio.id,
                stock_id=stocks[1].id,  # BHP: 500 - 100 = 400 shares
                quantity=Decimal("400"),
                average_cost=Decimal("36.00"),
                current_value=Decimal("15200.00")  # 400 * $38
            ),
            Holding(
                portfolio_id=regular_portfolio.id,
                stock_id=stocks[3].id,  # CSL: 75 shares
                quantity=Decimal("75"),
                average_cost=Decimal("275.00"),
                current_value=Decimal("22125.00")  # 75 * $295
            ),
            Holding(
                portfolio_id=regular_portfolio.id,
                stock_id=stocks[4].id,  # WOW: 200 shares
                quantity=Decimal("200"),
                average_cost=Decimal("34.50"),
                current_value=Decimal("7200.00")  # 200 * $36
            )
        ]

        for holding in holdings:
            db.add(holding)

        db.commit()
        for holding in holdings:
            db.refresh(holding)

        print(f"Created {len(holdings)} holdings")

        # Update portfolio total value
        total_value = sum(holding.current_value for holding in holdings)
        portfolio.total_value = total_value
        db.commit()
        print(f"Portfolio total value: ${total_value:,.2f}")

        print("\nDatabase successfully populated with scaffolding data!")
        print(f"Login credentials: {user.email} / admin123")
        print(f"Portfolio ID: {portfolio.id}")
        print("You can now test the transaction list API that accounts for every transaction.")


if __name__ == "__main__":
    try:
        populate_dev_database()
        print("\n✅ Database population completed successfully!")
    except Exception as e:
        print(f"\n❌ Error populating database: {e}")
        sys.exit(1)
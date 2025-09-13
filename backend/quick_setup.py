#!/usr/bin/env python3
"""
Quick setup with manual transactions.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from decimal import Decimal
from datetime import date

from src.database import engine
from src.models import Transaction, Holding, Portfolio, Stock
from src.models.transaction import TransactionType, SourceType


def add_quick_test_data():
    with Session(engine) as db:
        # Get existing portfolio and stock using ORM
        portfolio = db.query(Portfolio).filter(Portfolio.name.like('%Admin%')).first()
        cba_stock = db.query(Stock).filter(Stock.symbol == 'CBA').first()

        if not portfolio or not cba_stock:
            print("No portfolio or CBA stock found")
            return

        portfolio_id = portfolio.id
        cba_stock_id = cba_stock.id

        if not portfolio_id or not cba_stock_id:
            print("No portfolio or CBA stock found")
            return

        print(f"Portfolio ID: {portfolio_id}")
        print(f"CBA Stock ID: {cba_stock_id}")

        # Add a simple transaction
        transaction = Transaction(
            portfolio_id=portfolio_id,
            stock_id=cba_stock_id,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("100"),
            price_per_share=Decimal("50.00"),
            total_amount=Decimal("5000.00"),
            source_type=SourceType.MANUAL,
            transaction_date=date(2024, 1, 15),
            notes="Test CBA purchase"
        )
        db.add(transaction)

        # Add corresponding holding
        holding = Holding(
            portfolio_id=portfolio_id,
            stock_id=cba_stock_id,
            quantity=Decimal("100"),
            average_cost=Decimal("50.00"),
            current_value=Decimal("5000.00")
        )
        db.add(holding)

        # Update portfolio total
        portfolio.total_value = Decimal("5000.00")

        db.commit()
        print("✅ Added test transaction and holding!")


if __name__ == "__main__":
    add_quick_test_data()
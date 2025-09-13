"""
Test data factories for portfolio management tests.
Provides reusable test data with real stock names and realistic values.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List
from uuid import uuid4

from faker import Faker
from sqlalchemy.orm import Session

from src.models import Portfolio, Stock, Transaction, Holding
from src.models.transaction import TransactionType, SourceType
from src.schemas.transaction import TransactionCreate

fake = Faker()

# Real stock symbols and company names for realistic test data
REAL_STOCKS = [
    ("AAPL", "Apple Inc.", "NASDAQ"),
    ("MSFT", "Microsoft Corporation", "NASDAQ"),
    ("GOOGL", "Alphabet Inc.", "NASDAQ"),
    ("AMZN", "Amazon.com Inc.", "NASDAQ"),
    ("TSLA", "Tesla Inc.", "NASDAQ"),
    ("META", "Meta Platforms Inc.", "NASDAQ"),
    ("NVDA", "NVIDIA Corporation", "NASDAQ"),
    ("BRK.B", "Berkshire Hathaway Inc.", "NYSE"),
    ("JNJ", "Johnson & Johnson", "NYSE"),
    ("V", "Visa Inc.", "NYSE"),
    ("WMT", "Walmart Inc.", "NYSE"),
    ("PG", "Procter & Gamble Co.", "NYSE"),
    ("UNH", "UnitedHealth Group Inc.", "NYSE"),
    ("HD", "Home Depot Inc.", "NYSE"),
    ("MA", "Mastercard Inc.", "NYSE"),
    ("CRM", "Salesforce Inc.", "NYSE"),
    ("NFLX", "Netflix Inc.", "NASDAQ"),
    ("ADBE", "Adobe Inc.", "NASDAQ"),
    ("PEP", "PepsiCo Inc.", "NASDAQ"),
    ("KO", "Coca-Cola Co.", "NYSE"),
]


class TestDataFactory:
    """Factory for creating test data with realistic values."""
    
    def __init__(self, db: Session):
        self.db = db
        self._stock_index = 0

    def create_portfolio(self, **kwargs) -> Portfolio:
        """Create a test portfolio with realistic data."""
        defaults = {
            "name": fake.company(),
            "description": fake.text(max_nb_chars=200),
            "owner_id": uuid4(),
        }
        defaults.update(kwargs)
        
        portfolio = Portfolio(**defaults)
        self.db.add(portfolio)
        self.db.flush()
        return portfolio

    def create_stock(self, **kwargs) -> Stock:
        """Create a test stock with real company data."""
        if "symbol" not in kwargs:
            # Cycle through real stocks
            symbol, company_name, exchange = REAL_STOCKS[self._stock_index % len(REAL_STOCKS)]
            self._stock_index += 1
            defaults = {
                "symbol": symbol,
                "company_name": company_name,
                "exchange": exchange,
            }
        else:
            defaults = {
                "company_name": f"{kwargs.get('symbol', 'TEST')} Corporation",
                "exchange": "NYSE",
            }
        
        defaults.update({
            "current_price": Decimal(str(fake.pyfloat(min_value=10, max_value=500, right_digits=2))),
            "previous_close": Decimal(str(fake.pyfloat(min_value=10, max_value=500, right_digits=2))),
        })
        defaults.update(kwargs)
        
        stock = Stock(**defaults)
        self.db.add(stock)
        self.db.flush()
        return stock

    def create_transaction(self, portfolio: Portfolio, stock: Stock, **kwargs) -> Transaction:
        """Create a test transaction with realistic data."""
        defaults = {
            "portfolio_id": portfolio.id,
            "stock_id": stock.id,
            "transaction_type": fake.random_element(elements=[TransactionType.BUY, TransactionType.SELL]),
            "quantity": Decimal(str(fake.random_int(min=1, max=1000))),
            "price_per_share": Decimal(str(fake.pyfloat(min_value=10, max_value=500, right_digits=2))),
            "fees": Decimal(str(fake.pyfloat(min_value=0, max_value=50, right_digits=2))),
            "transaction_date": fake.date_between(start_date='-2y', end_date='today'),
            "source_type": SourceType.MANUAL,
            "notes": fake.text(max_nb_chars=100) if fake.boolean(chance_of_getting_true=30) else None,
            "is_verified": True,
        }
        defaults.update(kwargs)
        
        # Calculate total amount
        if "total_amount" not in defaults:
            defaults["total_amount"] = defaults["quantity"] * defaults["price_per_share"]
        
        transaction = Transaction(**defaults)
        self.db.add(transaction)
        self.db.flush()
        return transaction

    def create_holding(self, portfolio: Portfolio, stock: Stock, **kwargs) -> Holding:
        """Create a test holding with realistic data."""
        defaults = {
            "portfolio_id": portfolio.id,
            "stock_id": stock.id,
            "quantity": Decimal(str(fake.random_int(min=1, max=1000))),
            "average_cost": Decimal(str(fake.pyfloat(min_value=10, max_value=500, right_digits=2))),
            "current_value": Decimal(str(fake.pyfloat(min_value=100, max_value=50000, right_digits=2))),
            "unrealized_gain_loss": Decimal(str(fake.pyfloat(min_value=-5000, max_value=5000, right_digits=2))),
            "unrealized_gain_loss_percent": Decimal(str(fake.pyfloat(min_value=-50, max_value=50, right_digits=2))),
        }
        defaults.update(kwargs)
        
        holding = Holding(**defaults)
        self.db.add(holding)
        self.db.flush()
        return holding

    def create_transaction_create_schema(self, stock_symbol: str = None, **kwargs) -> TransactionCreate:
        """Create a TransactionCreate schema object for API testing."""
        if not stock_symbol:
            stock_symbol = REAL_STOCKS[self._stock_index % len(REAL_STOCKS)][0]
            self._stock_index += 1
            
        defaults = {
            "stock_symbol": stock_symbol,
            "transaction_type": fake.random_element(elements=[TransactionType.BUY, TransactionType.SELL]),
            "quantity": Decimal(str(fake.random_int(min=1, max=1000))),
            "price_per_share": Decimal(str(fake.pyfloat(min_value=10, max_value=500, right_digits=2))),
            "fees": Decimal(str(fake.pyfloat(min_value=0, max_value=50, right_digits=2))),
            "transaction_date": fake.date_between(start_date='-1y', end_date='today'),
            "notes": fake.text(max_nb_chars=100) if fake.boolean(chance_of_getting_true=30) else None,
        }
        defaults.update(kwargs)
        
        return TransactionCreate(**defaults)

    def create_multiple_transactions_for_sorting(
        self, 
        portfolio: Portfolio, 
        count: int = 5
    ) -> List[Transaction]:
        """
        Create multiple transactions with specific dates for testing sorting.
        Returns transactions in creation order (not sorted).
        """
        base_date = date.today() - timedelta(days=30)
        transactions = []
        
        for i in range(count):
            # Create transactions with different dates
            transaction_date = base_date + timedelta(days=i * 2)
            
            stock = self.create_stock()
            transaction = self.create_transaction(
                portfolio=portfolio,
                stock=stock,
                transaction_date=transaction_date,
                transaction_type=TransactionType.BUY,
                quantity=Decimal("100"),
                price_per_share=Decimal(f"{100 + i * 10}.00")
            )
            transactions.append(transaction)
            
        return transactions

    def commit(self):
        """Commit all changes to the database."""
        self.db.commit()

    def rollback(self):
        """Rollback all changes."""
        self.db.rollback()
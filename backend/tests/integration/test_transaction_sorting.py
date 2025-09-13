"""
Integration tests for transaction sorting and pagination.
Tests the complete flow of transaction retrieval with proper ordering.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from tests.factories import TestDataFactory
from src.models.transaction import TransactionType


@pytest.mark.integration
class TestTransactionSorting:
    """Test transaction sorting and pagination functionality."""

    def test_transactions_sorted_by_date_descending_by_default(self, db: Session):
        """
        When retrieving transactions, they should be sorted by transaction_date
        in descending order (most recent first) by default.
        """
        # Arrange: Create portfolio and transactions with specific dates
        factory = TestDataFactory(db)
        portfolio = factory.create_portfolio(name="Test Sorting Portfolio")
        
        # Create transactions with known dates (older to newer)
        base_date = date.today() - timedelta(days=10)
        transactions_data = [
            (base_date, "AAPL", Decimal("150.00")),  # 10 days ago
            (base_date + timedelta(days=2), "MSFT", Decimal("250.00")),  # 8 days ago  
            (base_date + timedelta(days=5), "GOOGL", Decimal("2500.00")),  # 5 days ago
            (base_date + timedelta(days=8), "AMZN", Decimal("3200.00")),  # 2 days ago
            (base_date + timedelta(days=10), "TSLA", Decimal("800.00")),  # Today
        ]
        
        created_transactions = []
        for transaction_date, symbol, price in transactions_data:
            stock = factory.create_stock(symbol=symbol)
            transaction = factory.create_transaction(
                portfolio=portfolio,
                stock=stock,
                transaction_date=transaction_date,
                transaction_type=TransactionType.BUY,
                quantity=Decimal("100"),
                price_per_share=price
            )
            created_transactions.append(transaction)
        
        factory.commit()
        
        # Act: Retrieve transactions using the API
        from src.api.transactions import get_portfolio_transactions
        import asyncio
        
        # Simulate API call with default parameters
        async def get_result():
            return await get_portfolio_transactions(
                portfolio_id=portfolio.id,
                limit=50,
                offset=0,
                db=db
            )
        
        result = asyncio.run(get_result())
        
        # Assert: Transactions should be sorted by date descending (newest first)
        assert len(result.transactions) == 5
        assert result.total == 5
        
        # Verify sorting: newest first (TSLA -> AMZN -> GOOGL -> MSFT -> AAPL)
        expected_symbols = ["TSLA", "AMZN", "GOOGL", "MSFT", "AAPL"]
        actual_symbols = [t.stock.symbol for t in result.transactions]
        assert actual_symbols == expected_symbols
        
        # Verify dates are in descending order
        transaction_dates = [t.transaction_date for t in result.transactions]
        assert transaction_dates == sorted(transaction_dates, reverse=True)

    def test_transaction_pagination_preserves_date_sorting(self, db: Session):
        """
        When using pagination, the date sorting should be preserved across pages.
        Each page should show the next set of transactions in date descending order.
        """
        # Arrange: Create portfolio with many transactions
        factory = TestDataFactory(db)
        portfolio = factory.create_portfolio(name="Pagination Test Portfolio")
        
        # Create 7 transactions over 7 days
        base_date = date.today() - timedelta(days=6)
        expected_order = []
        
        for i in range(7):
            transaction_date = base_date + timedelta(days=i)
            stock_symbol = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA"][i]
            
            stock = factory.create_stock(symbol=stock_symbol)
            transaction = factory.create_transaction(
                portfolio=portfolio,
                stock=stock,
                transaction_date=transaction_date,
                transaction_type=TransactionType.BUY,
                quantity=Decimal("100"),
                price_per_share=Decimal(f"{100 + i * 50}.00")
            )
            # Build expected order (newest first)
            expected_order.insert(0, stock_symbol)
        
        factory.commit()
        
        # Act & Assert: Test pagination
        from src.api.transactions import get_portfolio_transactions
        import asyncio
        
        # Page 1: First 3 transactions (newest)
        async def get_page1():
            return await get_portfolio_transactions(
                portfolio_id=portfolio.id,
                limit=3,
                offset=0,
                db=db
            )
        page1 = asyncio.run(get_page1())
        
        assert len(page1.transactions) == 3
        assert page1.total == 7
        assert page1.limit == 3
        assert page1.offset == 0
        
        page1_symbols = [t.stock.symbol for t in page1.transactions]
        assert page1_symbols == expected_order[:3]  # First 3 newest
        
        # Page 2: Next 3 transactions
        async def get_page2():
            return await get_portfolio_transactions(
                portfolio_id=portfolio.id,
                limit=3,
                offset=3,
                db=db
            )
        page2 = asyncio.run(get_page2())
        
        assert len(page2.transactions) == 3
        assert page2.total == 7
        assert page2.offset == 3
        
        page2_symbols = [t.stock.symbol for t in page2.transactions]
        assert page2_symbols == expected_order[3:6]  # Next 3
        
        # Page 3: Last transaction
        async def get_page3():
            return await get_portfolio_transactions(
                portfolio_id=portfolio.id,
                limit=3,
                offset=6,
                db=db
            )
        page3 = asyncio.run(get_page3())
        
        assert len(page3.transactions) == 1
        assert page3.total == 7
        assert page3.offset == 6
        
        page3_symbols = [t.stock.symbol for t in page3.transactions]
        assert page3_symbols == expected_order[6:]  # Last 1

    def test_transactions_same_date_sorted_by_creation_time(self, db: Session):
        """
        When transactions have the same transaction_date, they should be sorted 
        by creation time (processed_date) in descending order.
        """
        # Arrange: Create portfolio and multiple transactions on same date
        factory = TestDataFactory(db)
        portfolio = factory.create_portfolio(name="Same Date Test Portfolio")
        
        same_date = date.today()
        
        # Create 3 transactions on the same date but at different times
        # (creation order will determine processed_date)
        transaction_symbols = ["AAPL", "MSFT", "GOOGL"]
        
        for symbol in transaction_symbols:
            stock = factory.create_stock(symbol=symbol)
            factory.create_transaction(
                portfolio=portfolio,
                stock=stock,
                transaction_date=same_date,
                transaction_type=TransactionType.BUY,
                quantity=Decimal("100"),
                price_per_share=Decimal("200.00")
            )
        
        factory.commit()
        
        # Act: Retrieve transactions
        from src.api.transactions import get_portfolio_transactions
        import asyncio
        
        async def get_result():
            return await get_portfolio_transactions(
                portfolio_id=portfolio.id,
                limit=50,
                offset=0,
                db=db
            )
        result = asyncio.run(get_result())
        
        # Assert: All transactions have same date
        assert len(result.transactions) == 3
        all_same_date = all(t.transaction_date == same_date for t in result.transactions)
        assert all_same_date
        
        # Verify they're sorted by processed_date descending (most recently created first)
        processed_dates = [t.processed_date for t in result.transactions]
        assert processed_dates == sorted(processed_dates, reverse=True)
        
        # Since we created AAPL first, MSFT second, GOOGL third,
        # they should appear as GOOGL, MSFT, AAPL (newest processed first)
        actual_symbols = [t.stock.symbol for t in result.transactions]
        assert actual_symbols == ["GOOGL", "MSFT", "AAPL"]

    def test_empty_portfolio_returns_empty_sorted_list(self, db: Session):
        """
        When a portfolio has no transactions, the API should return
        an empty list with proper pagination metadata.
        """
        # Arrange: Create empty portfolio
        factory = TestDataFactory(db)
        portfolio = factory.create_portfolio(name="Empty Portfolio")
        factory.commit()
        
        # Act: Retrieve transactions
        from src.api.transactions import get_portfolio_transactions
        import asyncio
        
        async def get_result():
            return await get_portfolio_transactions(
                portfolio_id=portfolio.id,
                limit=50,
                offset=0,
                db=db
            )
        result = asyncio.run(get_result())
        
        # Assert: Empty result with correct metadata
        assert len(result.transactions) == 0
        assert result.total == 0
        assert result.limit == 50
        assert result.offset == 0

    def test_pagination_beyond_available_transactions(self, db: Session):
        """
        When requesting a page beyond available transactions,
        should return empty list but correct total count.
        """
        # Arrange: Create portfolio with only 2 transactions
        factory = TestDataFactory(db)
        portfolio = factory.create_portfolio(name="Limited Transactions Portfolio")
        
        for i, symbol in enumerate(["AAPL", "MSFT"]):
            stock = factory.create_stock(symbol=symbol)
            factory.create_transaction(
                portfolio=portfolio,
                stock=stock,
                transaction_date=date.today() - timedelta(days=i),
                transaction_type=TransactionType.BUY,
                quantity=Decimal("100"),
                price_per_share=Decimal("200.00")
            )
        
        factory.commit()
        
        # Act: Request page beyond available data
        from src.api.transactions import get_portfolio_transactions
        import asyncio
        
        async def get_result():
            return await get_portfolio_transactions(
                portfolio_id=portfolio.id,
                limit=10,
                offset=10,  # Beyond the 2 available transactions
                db=db
            )
        result = asyncio.run(get_result())
        
        # Assert: Empty page but correct total
        assert len(result.transactions) == 0
        assert result.total == 2  # Still shows total available
        assert result.limit == 10
        assert result.offset == 10
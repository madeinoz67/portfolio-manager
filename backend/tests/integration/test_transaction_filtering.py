"""
Integration tests for transaction filtering functionality.
Tests filtering by date range, stock symbol, and combined filters.
"""

import asyncio
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from src.api.transactions import get_portfolio_transactions
from src.models.transaction import TransactionType
from tests.factories import (
    create_test_user,
    create_test_portfolio,
    create_test_stock,
    create_test_transaction,
    REAL_STOCKS
)


@pytest.mark.asyncio
async def test_filter_transactions_by_date_range(db: Session):
    """Test filtering transactions by date range."""
    # Create test data
    user = create_test_user(db)
    portfolio = create_test_portfolio(db, user.id)
    
    # Create stocks
    aapl = create_test_stock(db, "AAPL", "Apple Inc.", "NASDAQ")
    msft = create_test_stock(db, "MSFT", "Microsoft Corporation", "NASDAQ")
    
    # Create transactions across different dates
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Transactions from different periods
    old_transaction = create_test_transaction(
        db, portfolio.id, aapl.id, TransactionType.BUY,
        Decimal("10"), Decimal("150.00"), month_ago
    )
    
    recent_transaction = create_test_transaction(
        db, portfolio.id, msft.id, TransactionType.BUY,
        Decimal("5"), Decimal("300.00"), week_ago
    )
    
    today_transaction = create_test_transaction(
        db, portfolio.id, aapl.id, TransactionType.SELL,
        Decimal("2"), Decimal("160.00"), today
    )
    
    # Test filtering by date range (last 2 weeks)
    start_date = today - timedelta(days=14)
    end_date = today
    
    result = await get_portfolio_transactions(
        portfolio_id=portfolio.id,
        limit=50,
        offset=0,
        start_date=start_date,
        end_date=end_date,
        db=db
    )
    
    # Should only return recent and today transactions
    assert result.total == 2
    assert len(result.transactions) == 2
    
    transaction_ids = [t.id for t in result.transactions]
    assert recent_transaction.id in transaction_ids
    assert today_transaction.id in transaction_ids
    assert old_transaction.id not in transaction_ids
    
    # Verify transactions are still sorted by date descending
    assert result.transactions[0].transaction_date >= result.transactions[1].transaction_date


@pytest.mark.asyncio
async def test_filter_transactions_by_stock_symbol(db: Session):
    """Test filtering transactions by stock symbol."""
    # Create test data
    user = create_test_user(db)
    portfolio = create_test_portfolio(db, user.id)
    
    # Create multiple stocks
    aapl = create_test_stock(db, "AAPL", "Apple Inc.", "NASDAQ")
    msft = create_test_stock(db, "MSFT", "Microsoft Corporation", "NASDAQ")
    googl = create_test_stock(db, "GOOGL", "Alphabet Inc.", "NASDAQ")
    
    # Create transactions for different stocks
    aapl_buy = create_test_transaction(
        db, portfolio.id, aapl.id, TransactionType.BUY,
        Decimal("10"), Decimal("150.00")
    )
    
    aapl_sell = create_test_transaction(
        db, portfolio.id, aapl.id, TransactionType.SELL,
        Decimal("5"), Decimal("160.00")
    )
    
    msft_buy = create_test_transaction(
        db, portfolio.id, msft.id, TransactionType.BUY,
        Decimal("8"), Decimal("300.00")
    )
    
    googl_buy = create_test_transaction(
        db, portfolio.id, googl.id, TransactionType.BUY,
        Decimal("3"), Decimal("2500.00")
    )
    
    # Test filtering by AAPL symbol
    result = await get_portfolio_transactions(
        portfolio_id=portfolio.id,
        limit=50,
        offset=0,
        stock_symbol="AAPL",
        db=db
    )
    
    # Should only return AAPL transactions
    assert result.total == 2
    assert len(result.transactions) == 2
    
    for transaction in result.transactions:
        assert transaction.stock.symbol == "AAPL"
    
    transaction_ids = [t.id for t in result.transactions]
    assert aapl_buy.id in transaction_ids
    assert aapl_sell.id in transaction_ids
    assert msft_buy.id not in transaction_ids
    assert googl_buy.id not in transaction_ids


@pytest.mark.asyncio
async def test_filter_transactions_by_stock_symbol_partial_match(db: Session):
    """Test filtering transactions by partial stock symbol match."""
    # Create test data
    user = create_test_user(db)
    portfolio = create_test_portfolio(db, user.id)
    
    # Create stocks with similar symbols
    aapl = create_test_stock(db, "AAPL", "Apple Inc.", "NASDAQ")
    aap = create_test_stock(db, "AAP", "Advance Auto Parts", "NYSE")
    msft = create_test_stock(db, "MSFT", "Microsoft Corporation", "NASDAQ")
    
    # Create transactions
    aapl_transaction = create_test_transaction(
        db, portfolio.id, aapl.id, TransactionType.BUY,
        Decimal("10"), Decimal("150.00")
    )
    
    aap_transaction = create_test_transaction(
        db, portfolio.id, aap.id, TransactionType.BUY,
        Decimal("5"), Decimal("75.00")
    )
    
    msft_transaction = create_test_transaction(
        db, portfolio.id, msft.id, TransactionType.BUY,
        Decimal("8"), Decimal("300.00")
    )
    
    # Test partial match for "AA" - should match both AAPL and AAP
    result = await get_portfolio_transactions(
        portfolio_id=portfolio.id,
        limit=50,
        offset=0,
        stock_symbol="AA",
        db=db
    )
    
    # Should return both AAPL and AAP transactions
    assert result.total == 2
    assert len(result.transactions) == 2
    
    symbols = [t.stock.symbol for t in result.transactions]
    assert "AAPL" in symbols
    assert "AAP" in symbols
    assert "MSFT" not in symbols


@pytest.mark.asyncio
async def test_filter_transactions_by_date_and_stock_combined(db: Session):
    """Test filtering transactions by both date range and stock symbol (AND logic)."""
    # Create test data
    user = create_test_user(db)
    portfolio = create_test_portfolio(db, user.id)
    
    # Create stocks
    aapl = create_test_stock(db, "AAPL", "Apple Inc.", "NASDAQ")
    msft = create_test_stock(db, "MSFT", "Microsoft Corporation", "NASDAQ")
    
    # Create transactions across different dates and stocks
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # AAPL transactions
    old_aapl = create_test_transaction(
        db, portfolio.id, aapl.id, TransactionType.BUY,
        Decimal("10"), Decimal("150.00"), month_ago
    )
    
    recent_aapl = create_test_transaction(
        db, portfolio.id, aapl.id, TransactionType.SELL,
        Decimal("5"), Decimal("160.00"), week_ago
    )
    
    # MSFT transactions
    old_msft = create_test_transaction(
        db, portfolio.id, msft.id, TransactionType.BUY,
        Decimal("8"), Decimal("280.00"), month_ago
    )
    
    recent_msft = create_test_transaction(
        db, portfolio.id, msft.id, TransactionType.BUY,
        Decimal("3"), Decimal("320.00"), week_ago
    )
    
    # Test combined filter: AAPL transactions from last 2 weeks
    start_date = today - timedelta(days=14)
    end_date = today
    
    result = await get_portfolio_transactions(
        portfolio_id=portfolio.id,
        limit=50,
        offset=0,
        start_date=start_date,
        end_date=end_date,
        stock_symbol="AAPL",
        db=db
    )
    
    # Should only return recent AAPL transaction
    assert result.total == 1
    assert len(result.transactions) == 1
    assert result.transactions[0].id == recent_aapl.id
    assert result.transactions[0].stock.symbol == "AAPL"
    assert result.transactions[0].transaction_date == week_ago


@pytest.mark.asyncio
async def test_filter_transactions_with_pagination(db: Session):
    """Test that filtering works correctly with pagination."""
    # Create test data
    user = create_test_user(db)
    portfolio = create_test_portfolio(db, user.id)
    
    # Create stock
    aapl = create_test_stock(db, "AAPL", "Apple Inc.", "NASDAQ")
    
    # Create multiple AAPL transactions
    transactions = []
    for i in range(5):
        transaction = create_test_transaction(
            db, portfolio.id, aapl.id, TransactionType.BUY,
            Decimal("10"), Decimal(f"{150 + i}.00")
        )
        transactions.append(transaction)
    
    # Test filtering with pagination (limit=2, offset=1)
    result = await get_portfolio_transactions(
        portfolio_id=portfolio.id,
        limit=2,
        offset=1,
        stock_symbol="AAPL",
        db=db
    )
    
    # Should return 2 transactions starting from offset 1
    assert result.total == 5  # Total AAPL transactions
    assert len(result.transactions) == 2  # Limited to 2
    assert result.limit == 2
    assert result.offset == 1
    
    # All returned transactions should be AAPL
    for transaction in result.transactions:
        assert transaction.stock.symbol == "AAPL"


@pytest.mark.asyncio
async def test_filter_transactions_no_matches(db: Session):
    """Test filtering when no transactions match the criteria."""
    # Create test data
    user = create_test_user(db)
    portfolio = create_test_portfolio(db, user.id)
    
    # Create some transactions but don't match filter criteria
    aapl = create_test_stock(db, "AAPL", "Apple Inc.", "NASDAQ")
    create_test_transaction(
        db, portfolio.id, aapl.id, TransactionType.BUY,
        Decimal("10"), Decimal("150.00")
    )
    
    # Test filtering by non-existent stock symbol
    result = await get_portfolio_transactions(
        portfolio_id=portfolio.id,
        limit=50,
        offset=0,
        stock_symbol="NONEXISTENT",
        db=db
    )
    
    # Should return empty results
    assert result.total == 0
    assert len(result.transactions) == 0
    assert result.limit == 50
    assert result.offset == 0


@pytest.mark.asyncio
async def test_filter_transactions_case_insensitive_stock_search(db: Session):
    """Test that stock symbol filtering is case insensitive."""
    # Create test data
    user = create_test_user(db)
    portfolio = create_test_portfolio(db, user.id)
    
    # Create stock with uppercase symbol
    aapl = create_test_stock(db, "AAPL", "Apple Inc.", "NASDAQ")
    transaction = create_test_transaction(
        db, portfolio.id, aapl.id, TransactionType.BUY,
        Decimal("10"), Decimal("150.00")
    )
    
    # Test filtering with lowercase symbol
    result = await get_portfolio_transactions(
        portfolio_id=portfolio.id,
        limit=50,
        offset=0,
        stock_symbol="aapl",
        db=db
    )
    
    # Should still find the AAPL transaction
    assert result.total == 1
    assert len(result.transactions) == 1
    assert result.transactions[0].id == transaction.id
    assert result.transactions[0].stock.symbol == "AAPL"
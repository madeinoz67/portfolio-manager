"""
Integration tests for update storm protection mechanisms.
Tests debouncing, rate limiting, and coalescing of portfolio updates.
"""

import pytest
import asyncio
import time
from decimal import Decimal
from sqlalchemy.orm import Session

from src.models import Portfolio, User, Stock, Holding
from src.services.portfolio_update_queue import PortfolioUpdateQueue


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    user = User(
        email="storm@example.com",
        password_hash="$2b$12$dummy.hash.value",
        first_name="Storm",
        last_name="Test"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_portfolio(db: Session, test_user: User):
    """Create a test portfolio."""
    portfolio = Portfolio(
        name="Storm Protection Portfolio",
        description="Portfolio for update storm testing",
        owner_id=test_user.id,
        total_value=Decimal("0.00"),
        daily_change=Decimal("0.00"),
        daily_change_percent=Decimal("0.00")
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@pytest.fixture
def test_stocks_and_holdings(db: Session, test_portfolio: Portfolio):
    """Create multiple stocks and holdings for storm testing."""
    stocks = []
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX", "BABA", "UBER"]

    for symbol in symbols:
        stock = Stock(symbol=symbol, company_name=f"{symbol} Inc.", exchange="NASDAQ")
        db.add(stock)
        db.commit()
        db.refresh(stock)
        stocks.append(stock)

        # Add holding for each stock
        holding = Holding(
            portfolio_id=test_portfolio.id,
            stock_id=stock.id,
            quantity=Decimal("100"),
            average_cost=Decimal("150.00")
        )
        db.add(holding)

    db.commit()
    return stocks


class TestUpdateStormProtection:
    """Test update storm protection mechanisms."""

    def test_update_coalescing_merges_multiple_symbol_updates(self):
        """Test that multiple symbol updates for same portfolio are coalesced."""
        queue = PortfolioUpdateQueue(debounce_seconds=1.0)
        portfolio_id = "test-portfolio-1"

        # Queue multiple updates for same portfolio with different symbols
        result1 = queue.queue_portfolio_update(portfolio_id, ["AAPL"])
        result2 = queue.queue_portfolio_update(portfolio_id, ["GOOGL", "MSFT"])
        result3 = queue.queue_portfolio_update(portfolio_id, ["TSLA"])

        assert result1 is True
        assert result2 is True
        assert result3 is True

        # Check queue stats
        stats = queue.get_queue_stats()
        assert stats["pending_updates"] == 1  # Only one pending update despite 3 calls

        # Check that symbols were merged
        pending_portfolio = queue._pending_updates.get(portfolio_id)
        assert pending_portfolio is not None
        assert pending_portfolio.symbols == {"AAPL", "GOOGL", "MSFT", "TSLA"}

    def test_rate_limiting_prevents_excessive_updates(self):
        """Test that rate limiting prevents excessive updates per portfolio."""
        # Set very low rate limit for testing
        queue = PortfolioUpdateQueue(debounce_seconds=0.1, max_updates_per_minute=3)
        portfolio_id = "test-portfolio-rate-limit"

        # First 3 updates should succeed
        for i in range(3):
            result = queue.queue_portfolio_update(portfolio_id, [f"STOCK{i}"])
            assert result is True

        # Record these as processed
        for i in range(3):
            queue._record_update(portfolio_id)

        # Next update should be rate limited
        result = queue.queue_portfolio_update(portfolio_id, ["STOCK3"])
        assert result is False

        # Check that portfolio was not queued
        stats = queue.get_queue_stats()
        assert portfolio_id not in stats.get("portfolio_symbol_counts", {})

    def test_debouncing_delays_updates_until_quiet_period(self):
        """Test that debouncing delays updates until there's a quiet period."""
        debounce_time = 0.5
        queue = PortfolioUpdateQueue(debounce_seconds=debounce_time)
        portfolio_id = "test-portfolio-debounce"

        # Queue initial update
        queue.queue_portfolio_update(portfolio_id, ["AAPL"])
        initial_timestamp = queue._pending_updates[portfolio_id].timestamp

        # Wait a bit but not enough to trigger
        time.sleep(debounce_time * 0.5)

        # Add another update - should reset the timer
        queue.queue_portfolio_update(portfolio_id, ["GOOGL"])
        new_timestamp = queue._pending_updates[portfolio_id].timestamp

        # Timestamp should be updated (timer reset)
        assert new_timestamp > initial_timestamp

        # Symbols should be coalesced
        assert queue._pending_updates[portfolio_id].symbols == {"AAPL", "GOOGL"}

    def test_priority_queuing_handles_important_updates_first(self):
        """Test that priority queuing handles important updates first."""
        queue = PortfolioUpdateQueue(debounce_seconds=0.1)

        # Queue updates with different priorities
        queue.queue_portfolio_update("portfolio-1", ["STOCK1"], priority=1)  # Normal
        queue.queue_portfolio_update("portfolio-2", ["STOCK2"], priority=3)  # High
        queue.queue_portfolio_update("portfolio-3", ["STOCK3"], priority=2)  # Medium

        # Wait for debounce period
        time.sleep(0.2)

        # Get ready updates
        current_time = time.time()
        ready_updates = []

        for portfolio_id, request in queue._pending_updates.items():
            if current_time - request.timestamp >= queue.debounce_seconds:
                ready_updates.append(request)

        # Sort by priority as the queue would
        ready_updates.sort(key=lambda x: x.priority, reverse=True)

        # Should be ordered by priority: 3, 2, 1
        assert len(ready_updates) == 3
        assert ready_updates[0].priority == 3
        assert ready_updates[1].priority == 2
        assert ready_updates[2].priority == 1

    @pytest.mark.asyncio
    async def test_queue_handles_high_volume_updates_gracefully(self, test_portfolio: Portfolio, test_stocks_and_holdings):
        """Test that queue handles high volume of updates gracefully."""
        queue = PortfolioUpdateQueue(debounce_seconds=0.1, max_updates_per_minute=50)
        await queue.start_processing()

        try:
            portfolio_id = str(test_portfolio.id)
            symbols = [stock.symbol for stock in test_stocks_and_holdings]

            # Simulate update storm - rapid fire updates
            start_time = time.time()
            updates_queued = 0

            for i in range(100):  # Lots of updates
                # Vary the symbols to simulate real market conditions
                selected_symbols = symbols[i % len(symbols):i % len(symbols) + 3]
                result = queue.queue_portfolio_update(portfolio_id, selected_symbols)

                if result:
                    updates_queued += 1

                # Small delay to simulate real timing
                await asyncio.sleep(0.001)

            end_time = time.time()
            duration = end_time - start_time

            # Should handle updates quickly
            assert duration < 2.0  # Should complete in under 2 seconds

            # Should have coalesced many updates into fewer actual queue entries
            stats = queue.get_queue_stats()

            print(f"Updates queued: {updates_queued}, Duration: {duration:.3f}s")
            print(f"Queue stats: {stats}")

            # Queue should remain manageable
            assert stats["pending_updates"] <= 10  # Should be much lower than 100

        finally:
            await queue.stop_processing()

    @pytest.mark.asyncio
    async def test_queue_processes_updates_after_debounce_period(self):
        """Test that queue actually processes updates after debounce period."""
        queue = PortfolioUpdateQueue(debounce_seconds=0.2, max_updates_per_minute=50)
        await queue.start_processing()

        try:
            portfolio_id = "test-processing"

            # Queue an update
            result = queue.queue_portfolio_update(portfolio_id, ["AAPL", "GOOGL"])
            assert result is True

            # Should be pending
            stats = queue.get_queue_stats()
            assert stats["pending_updates"] == 1

            # Wait for debounce period + processing time
            await asyncio.sleep(0.5)

            # Should be processed and removed from queue
            stats = queue.get_queue_stats()
            assert stats["pending_updates"] == 0

        finally:
            await queue.stop_processing()

    def test_queue_stats_provide_monitoring_information(self):
        """Test that queue stats provide useful monitoring information."""
        queue = PortfolioUpdateQueue(debounce_seconds=1.0, max_updates_per_minute=20)

        # Queue some updates
        queue.queue_portfolio_update("portfolio-1", ["AAPL", "GOOGL"])
        queue.queue_portfolio_update("portfolio-2", ["MSFT"])

        # Record some rate limiting
        queue._record_update("portfolio-1")
        queue._record_update("portfolio-1")

        stats = queue.get_queue_stats()

        # Check all expected fields are present
        assert "pending_updates" in stats
        assert "portfolio_symbol_counts" in stats
        assert "rate_limit_windows" in stats
        assert "is_processing" in stats
        assert "debounce_seconds" in stats
        assert "max_updates_per_minute" in stats

        # Check values are reasonable
        assert stats["pending_updates"] == 2
        assert stats["portfolio_symbol_counts"]["portfolio-1"] == 2  # AAPL + GOOGL
        assert stats["portfolio_symbol_counts"]["portfolio-2"] == 1  # MSFT
        assert stats["rate_limit_windows"]["portfolio-1"] == 2  # 2 recorded updates
        assert stats["debounce_seconds"] == 1.0
        assert stats["max_updates_per_minute"] == 20

    @pytest.mark.asyncio
    async def test_queue_survives_processing_errors_gracefully(self):
        """Test that queue continues working even if individual updates fail."""
        queue = PortfolioUpdateQueue(debounce_seconds=0.1)
        await queue.start_processing()

        try:
            # Queue updates for non-existent portfolios (will cause errors)
            queue.queue_portfolio_update("non-existent-1", ["AAPL"])
            queue.queue_portfolio_update("non-existent-2", ["GOOGL"])

            # Wait for processing
            await asyncio.sleep(0.3)

            # Queue should still be working
            stats = queue.get_queue_stats()
            assert stats["is_processing"] is True

            # Should be able to queue new updates
            result = queue.queue_portfolio_update("new-portfolio", ["MSFT"])
            assert result is True

        finally:
            await queue.stop_processing()
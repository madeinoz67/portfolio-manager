"""
Test scheduler integration with market data service.
Verify that scheduler actually fetches market data and updates metrics.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.models.scheduler_execution import SchedulerExecution
from src.models.stock import Stock
from src.models.portfolio import Portfolio
from src.models.holding import Holding
from src.services.scheduler_service import MarketDataSchedulerService
from src.services.market_data_service import MarketDataService
from src.utils.datetime_utils import utc_now


class TestSchedulerMarketDataIntegration:
    """Test scheduler integration with actual market data fetching."""

    @pytest.mark.asyncio
    async def test_scheduler_should_fetch_market_data_when_running(self, db: Session):
        """
        Test that running scheduler actually fetches market data for portfolio holdings.

        Given: Portfolio with stock holdings exists
        When: Scheduler executes a run
        Then: Market data is fetched for the stocks
        And: Metrics show symbols processed > 0
        And: Database records the execution details
        """
        # Create test data - portfolio with holdings
        from src.models.user import User
        from src.models.user_role import UserRole

        # Create user and portfolio
        user = User(
            email="test@example.com",
            password_hash="hashed",
            first_name="Test",
            last_name="User",
            role=UserRole.USER,
            is_active=True
        )
        db.add(user)
        db.commit()

        portfolio = Portfolio(
            name="Test Portfolio",
            description="Test portfolio for scheduler",
            owner_id=user.id
        )
        db.add(portfolio)
        db.commit()

        # Create stocks
        stock_aapl = Stock(symbol="AAPL", company_name="Apple Inc")
        stock_googl = Stock(symbol="GOOGL", company_name="Alphabet Inc")
        db.add_all([stock_aapl, stock_googl])
        db.commit()

        # Create holdings
        holding1 = Holding(
            portfolio_id=portfolio.id,
            stock_id=stock_aapl.id,
            quantity=10,
            average_cost=150.00
        )
        holding2 = Holding(
            portfolio_id=portfolio.id,
            stock_id=stock_googl.id,
            quantity=5,
            average_cost=2800.00
        )
        db.add_all([holding1, holding2])
        db.commit()

        # Set up market data providers for testing
        from src.models.market_data_provider import MarketDataProvider

        # Create test provider (yfinance - free and doesn't need API key)
        provider = MarketDataProvider(
            name="yfinance",
            display_name="Yahoo Finance",
            is_enabled=True,
            priority=1,  # Highest priority
            api_key=None,  # yfinance doesn't need API key
            rate_limit_per_day=1000,
            rate_limit_per_minute=60
        )
        db.add(provider)
        db.commit()

        # Get scheduler service
        scheduler = MarketDataSchedulerService(db, auto_start=False)
        scheduler.start()

        # Currently scheduler only has simulate_run() - no real execution
        # This test will fail initially, demonstrating the missing functionality

        # Check initial state
        initial_status = scheduler.get_status()
        assert initial_status["total_symbols_processed"] == 0, "Should start with 0 symbols processed"

        # The scheduler should have a method to execute real market data fetching
        # This method doesn't exist yet - that's what we need to implement
        try:
            # This should fetch market data for AAPL and GOOGL
            execution_result = await scheduler.execute_market_data_fetch()

            # Verify execution results - at least one symbol should be processed
            assert execution_result["symbols_processed"] > 0, "Should process at least one symbol from portfolio holdings"
            assert execution_result["status"] == "completed", "Execution should complete successfully"
            assert len(execution_result.get("symbols_fetched", [])) > 0, "Should fetch data for at least one symbol"

            # Log the results for debugging
            print(f"Symbols processed: {execution_result['symbols_processed']}")
            print(f"Symbols fetched: {execution_result.get('symbols_fetched', [])}")
            print(f"Failed symbols: {execution_result.get('failed_symbols', [])}")

            # Check updated metrics
            updated_status = scheduler.get_status()
            assert updated_status["total_symbols_processed"] > 0, "Metrics should show processed symbols"
            assert updated_status["last_run"] is not None, "Should record last run time"

            # Verify database execution record
            executions = db.query(SchedulerExecution).all()
            latest_execution = max(executions, key=lambda x: x.started_at)
            assert latest_execution.symbols_processed > 0, "Database should record symbols processed"
            assert latest_execution.status == "success", "Database should record successful execution"

        except AttributeError:
            # Expected failure - method doesn't exist yet
            pytest.fail("MarketDataSchedulerService.execute_market_data_fetch() method not implemented")

    def test_scheduler_should_update_metrics_after_execution(self, db: Session):
        """
        Test that scheduler metrics are updated after each execution.

        Given: Scheduler with execution history
        When: New execution completes
        Then: Success rate and response time metrics are updated
        And: Frontend displays accurate metrics
        """
        # This will test the actual metrics calculation after we implement the execution method
        scheduler = MarketDataSchedulerService(db, auto_start=False)

        # Initial metrics should be zero
        status = scheduler.get_status()
        assert status["success_rate"] == 0.0, "Initial success rate should be 0"
        assert status["total_symbols_processed"] == 0, "Initial symbols processed should be 0"

        # After implementation, we should be able to:
        # 1. Execute market data fetch
        # 2. Record execution metrics
        # 3. Calculate success rates
        # 4. Track response times

        # This test serves as specification for the implementation
        assert False, "Market data execution not implemented - need to integrate with MarketDataService"

    def test_scheduler_should_handle_api_failures_gracefully(self, db: Session):
        """
        Test that scheduler handles market data API failures gracefully.

        Given: Market data API is unavailable
        When: Scheduler attempts to fetch data
        Then: Failed execution is recorded
        And: Error metrics are updated
        And: System remains stable
        """
        # This will test error handling after we implement the execution method
        assert False, "Error handling for market data fetching not implemented"
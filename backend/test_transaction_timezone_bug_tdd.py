#!/usr/bin/env python3
"""
TDD test to fix transaction date timezone bug.

Issue: Adding a buy transaction to portfolio returns "transaction date cant be in the future"
This indicates timezone conversion problems in transaction date handling.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal

from src.database import SessionLocal
from src.models.transaction import Transaction, TransactionType
from src.models.portfolio import Portfolio
from src.models.stock import Stock, StockStatus
from src.models.user import User
from src.models.user_role import UserRole
from src.utils.datetime_utils import now


class TestTransactionTimezoneBugTDD:
    """TDD tests to verify and fix transaction date timezone issues."""

    @pytest.fixture
    def db_session(self):
        """Create a database session for testing."""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    @pytest.fixture
    def test_user(self, db_session):
        """Create a test user."""
        user = User(
            email="transaction_test@example.com",
            password_hash="test_hash",
            role=UserRole.USER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    @pytest.fixture
    def test_portfolio(self, db_session, test_user):
        """Create a test portfolio."""
        portfolio = Portfolio(
            name="Test Portfolio",
            description="Portfolio for transaction testing",
            user_id=test_user.id,
            created_at=now(),
            updated_at=now()
        )
        db_session.add(portfolio)
        db_session.commit()
        db_session.refresh(portfolio)
        return portfolio

    @pytest.fixture
    def test_stock(self, db_session):
        """Create a test stock."""
        stock = Stock(
            symbol="TEST",
            company_name="Test Company",
            status=StockStatus.ACTIVE
        )
        db_session.add(stock)
        db_session.commit()
        db_session.refresh(stock)
        return stock

    def test_todays_transaction_date_should_be_valid(self, db_session, test_portfolio, test_stock):
        """
        Test that today's date is valid for transactions.

        This test should PASS if timezone handling is correct.
        If it fails, it reproduces the user's "cant be in future" bug.
        """
        # User enters today's date in their local timezone
        local_today = date.today()

        # Create transaction with today's date
        transaction = Transaction(
            portfolio_id=test_portfolio.id,
            stock_symbol=test_stock.symbol,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("10.0"),
            price_per_share=Decimal("100.00"),
            transaction_date=datetime.combine(local_today, datetime.min.time()),  # Local midnight
            created_at=now(),
            updated_at=now()
        )

        try:
            db_session.add(transaction)
            db_session.commit()
            print(f"✅ Transaction with today's date ({local_today}) was created successfully")
        except Exception as e:
            pytest.fail(f"❌ Transaction with today's date ({local_today}) failed: {e}")

    def test_yesterday_transaction_date_should_be_valid(self, db_session, test_portfolio, test_stock):
        """
        Test that yesterday's date is valid for transactions.

        This should always work if timezone handling is correct.
        """
        # User enters yesterday's date
        local_yesterday = date.today() - timedelta(days=1)

        # Create transaction with yesterday's date
        transaction = Transaction(
            portfolio_id=test_portfolio.id,
            stock_symbol=test_stock.symbol,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("5.0"),
            price_per_share=Decimal("99.00"),
            transaction_date=datetime.combine(local_yesterday, datetime.min.time()),
            created_at=now(),
            updated_at=now()
        )

        try:
            db_session.add(transaction)
            db_session.commit()
            print(f"✅ Transaction with yesterday's date ({local_yesterday}) was created successfully")
        except Exception as e:
            pytest.fail(f"❌ Transaction with yesterday's date ({local_yesterday}) failed: {e}")

    def test_future_transaction_date_should_be_rejected(self, db_session, test_portfolio, test_stock):
        """
        Test that future dates are properly rejected.

        This verifies our validation logic works correctly.
        """
        # User tries to enter tomorrow's date
        local_tomorrow = date.today() + timedelta(days=1)

        # Create transaction with future date
        transaction = Transaction(
            portfolio_id=test_portfolio.id,
            stock_symbol=test_stock.symbol,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("5.0"),
            price_per_share=Decimal("101.00"),
            transaction_date=datetime.combine(local_tomorrow, datetime.min.time()),
            created_at=now(),
            updated_at=now()
        )

        # This should fail with proper validation
        try:
            db_session.add(transaction)
            db_session.commit()
            pytest.fail(f"❌ Future transaction date ({local_tomorrow}) should have been rejected but was accepted")
        except Exception as e:
            print(f"✅ Future transaction date ({local_tomorrow}) was properly rejected: {e}")
            # This is expected behavior

    def test_transaction_api_with_local_date_conversion(self, db_session, test_user, test_portfolio, test_stock):
        """
        Test transaction creation through API with proper timezone conversion.

        This simulates the frontend sending a local date that needs conversion.
        """
        from src.api.transactions import create_transaction_endpoint
        from src.schemas.transaction import TransactionCreate

        # Simulate frontend sending today's date as YYYY-MM-DD string
        local_today_string = date.today().isoformat()  # "2025-09-16"

        # Convert to expected API input format
        transaction_data = TransactionCreate(
            stock_symbol=test_stock.symbol,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("15.0"),
            price_per_share=Decimal("98.50"),
            transaction_date=local_today_string  # Frontend sends this format
        )

        try:
            # This should work if timezone conversion is correct
            result = create_transaction_endpoint(
                portfolio_id=test_portfolio.id,
                transaction=transaction_data,
                current_user=test_user,
                db=db_session
            )
            print(f"✅ API transaction with local date string ({local_today_string}) was created successfully")
        except Exception as e:
            pytest.fail(f"❌ API transaction with local date string ({local_today_string}) failed: {e}")

    def test_transaction_date_validation_consistency(self, db_session):
        """
        Test that transaction date validation uses consistent timezone handling.

        Checks if validation logic and storage logic use the same timezone assumptions.
        """
        from src.utils.datetime_utils import now

        # Test the timezone consistency between validation and storage
        current_time = now()
        local_today = date.today()

        print(f"Current UTC time: {current_time}")
        print(f"Local today: {local_today}")
        print(f"Current local time: {datetime.now()}")

        # Check if today's date would be considered "future" by validation
        local_today_datetime = datetime.combine(local_today, datetime.min.time())

        # This comparison should be consistent between validation and storage
        is_future = local_today_datetime.date() > current_time.date()

        if is_future:
            pytest.fail(f"❌ Today's date ({local_today}) is considered future relative to UTC time ({current_time}). "
                       "This indicates timezone conversion issues in validation logic.")
        else:
            print(f"✅ Today's date ({local_today}) is correctly not considered future relative to UTC time ({current_time})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
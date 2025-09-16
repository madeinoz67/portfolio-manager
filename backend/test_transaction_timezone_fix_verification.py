#!/usr/bin/env python3
"""
Quick test to verify transaction timezone fix works.
"""

import pytest
from datetime import date
from decimal import Decimal

from src.schemas.transaction import TransactionCreate
from src.models.transaction import TransactionType


def test_transaction_timezone_fix_allows_today():
    """
    Test that today's date is now accepted after timezone fix.
    """
    # This should work now with the timezone fix
    today_str = date.today().isoformat()

    # Create transaction data with today's date
    transaction_data = {
        "stock_symbol": "TEST",
        "transaction_type": TransactionType.BUY,
        "quantity": Decimal("10.0"),
        "price_per_share": Decimal("100.00"),
        "transaction_date": today_str
    }

    # This should not raise "Transaction date cannot be in the future" error
    try:
        transaction = TransactionCreate(**transaction_data)
        print(f"✅ SUCCESS: Today's date ({today_str}) accepted: {transaction.transaction_date}")
        assert transaction.transaction_date == date.today()
    except ValueError as e:
        if "cannot be in the future" in str(e):
            pytest.fail(f"❌ FAILED: Today's date ({today_str}) still rejected after timezone fix: {e}")
        else:
            pytest.fail(f"❌ FAILED: Unexpected validation error: {e}")


def test_future_date_still_rejected():
    """
    Test that actual future dates are still properly rejected.
    """
    from datetime import timedelta

    # Try tomorrow's date (should still fail)
    tomorrow = date.today() + timedelta(days=1)
    tomorrow_str = tomorrow.isoformat()

    transaction_data = {
        "stock_symbol": "TEST",
        "transaction_type": TransactionType.BUY,
        "quantity": Decimal("10.0"),
        "price_per_share": Decimal("100.00"),
        "transaction_date": tomorrow_str
    }

    # This should still raise "cannot be in the future" error
    try:
        transaction = TransactionCreate(**transaction_data)
        pytest.fail(f"❌ FAILED: Future date ({tomorrow_str}) should have been rejected but was accepted")
    except ValueError as e:
        if "cannot be in the future" in str(e):
            print(f"✅ SUCCESS: Future date ({tomorrow_str}) properly rejected: {e}")
        else:
            pytest.fail(f"❌ FAILED: Wrong error for future date: {e}")


if __name__ == "__main__":
    test_transaction_timezone_fix_allows_today()
    test_future_date_still_rejected()
    print("🎉 All transaction timezone tests passed!")
#!/usr/bin/env python3
"""
Quick test to verify transaction API now accepts today's date.
"""

import requests
import json
from datetime import date

def test_transaction_api():
    """Test that transaction API now accepts today's date."""

    # Test data
    today_str = date.today().isoformat()
    transaction_data = {
        "stock_symbol": "TEST",
        "transaction_type": "BUY",
        "quantity": "10.0",
        "price_per_share": "100.00",
        "transaction_date": today_str
    }

    print(f"Testing transaction creation with today's date: {today_str}")

    # Test validation directly (this should work now)
    try:
        from src.schemas.transaction import TransactionCreate
        transaction = TransactionCreate(**transaction_data)
        print(f"✅ SUCCESS: TransactionCreate schema validation passed")
        print(f"   Parsed date: {transaction.transaction_date}")
        return True
    except Exception as e:
        print(f"❌ FAILED: TransactionCreate schema validation failed: {e}")
        return False

if __name__ == "__main__":
    success = test_transaction_api()
    if success:
        print("🎉 Transaction timezone fix is working!")
    else:
        print("💥 Transaction timezone fix still has issues")
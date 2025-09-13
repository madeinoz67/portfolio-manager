#!/usr/bin/env python3
"""
Add test transactions via API calls to properly create holdings.
"""

import requests
import json
from datetime import date
import time

BASE_URL = "http://localhost:8001/api/v1"

def login_user(email, password):
    """Login and get access token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        headers={"Content-Type": "application/json"},
        json={"email": email, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.text}")
        return None

def get_stocks(token):
    """Get list of stocks."""
    response = requests.get(
        f"{BASE_URL}/stocks/",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Get stocks failed: {response.text}")
        return []

def get_portfolios(token):
    """Get user's portfolios."""
    response = requests.get(
        f"{BASE_URL}/portfolios/",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Get portfolios failed: {response.text}")
        return []

def add_transaction(token, portfolio_id, transaction_data):
    """Add a transaction to a portfolio."""
    response = requests.post(
        f"{BASE_URL}/portfolios/{portfolio_id}/transactions",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=transaction_data
    )
    if response.status_code in [200, 201]:
        print(f"✅ Added transaction: {transaction_data['stock_symbol']} {transaction_data['transaction_type']} {transaction_data['quantity']}")
        return response.json()
    else:
        print(f"❌ Add transaction failed: {response.text}")
        return None

def main():
    # Login as admin
    print("🔐 Logging in as admin...")
    admin_token = login_user("admin@example.com", "admin123")
    if not admin_token:
        return

    # Get stocks
    print("📊 Getting stocks...")
    stocks = get_stocks(admin_token)
    stock_symbols = {stock["symbol"]: stock["id"] for stock in stocks}
    print(f"Found stocks: {list(stock_symbols.keys())}")

    # Get admin portfolios
    print("📁 Getting admin portfolios...")
    portfolios = get_portfolios(admin_token)
    admin_portfolio = portfolios[0] if portfolios else None
    if not admin_portfolio:
        print("❌ No admin portfolio found")
        return

    admin_portfolio_id = admin_portfolio["id"]
    print(f"Found admin portfolio: {admin_portfolio['name']} ({admin_portfolio_id})")

    # Add admin transactions
    print("💰 Adding admin transactions...")
    admin_transactions = [
        {
            "stock_symbol": "CBA",
            "transaction_type": "BUY",
            "quantity": "200",
            "price_per_share": "48.50",
            "transaction_date": "2024-01-15",
            "notes": "Initial CBA investment"
        },
        {
            "stock_symbol": "CBA",
            "transaction_type": "BUY",
            "quantity": "100",
            "price_per_share": "52.00",
            "transaction_date": "2024-03-10",
            "notes": "Additional CBA purchase"
        },
        {
            "stock_symbol": "BHP",
            "transaction_type": "BUY",
            "quantity": "300",
            "price_per_share": "35.00",
            "transaction_date": "2024-02-05",
            "notes": "Initial BHP investment"
        },
        {
            "stock_symbol": "WBC",
            "transaction_type": "BUY",
            "quantity": "250",
            "price_per_share": "22.50",
            "transaction_date": "2024-01-30",
            "notes": "Initial WBC investment"
        },
        {
            "stock_symbol": "CSL",
            "transaction_type": "BUY",
            "quantity": "50",
            "price_per_share": "280.00",
            "transaction_date": "2024-03-25",
            "notes": "CSL investment for diversification"
        }
    ]

    for tx in admin_transactions:
        add_transaction(admin_token, admin_portfolio_id, tx)
        time.sleep(0.1)  # Small delay between requests

    print(f"\n🎉 Added {len(admin_transactions)} transactions for admin user")

    # Now login as regular user
    print("\n🔐 Logging in as regular user...")
    user_token = login_user("user@example.com", "user12345")
    if not user_token:
        return

    # Get regular user portfolios
    print("📁 Getting regular user portfolios...")
    user_portfolios = get_portfolios(user_token)
    user_portfolio = user_portfolios[0] if user_portfolios else None
    if not user_portfolio:
        print("❌ No user portfolio found")
        return

    user_portfolio_id = user_portfolio["id"]
    print(f"Found user portfolio: {user_portfolio['name']} ({user_portfolio_id})")

    # Add regular user transactions
    print("💰 Adding regular user transactions...")
    user_transactions = [
        {
            "stock_symbol": "BHP",
            "transaction_type": "BUY",
            "quantity": "500",
            "price_per_share": "36.00",
            "transaction_date": "2024-01-20",
            "notes": "Initial BHP position for resources exposure"
        },
        {
            "stock_symbol": "CSL",
            "transaction_type": "BUY",
            "quantity": "75",
            "price_per_share": "275.00",
            "transaction_date": "2024-03-05",
            "notes": "Healthcare diversification through CSL"
        },
        {
            "stock_symbol": "WOW",
            "transaction_type": "BUY",
            "quantity": "200",
            "price_per_share": "34.50",
            "transaction_date": "2024-02-10",
            "notes": "Consumer staples exposure via WOW"
        },
        {
            "stock_symbol": "ANZ",
            "transaction_type": "BUY",
            "quantity": "150",
            "price_per_share": "28.00",
            "transaction_date": "2024-04-01",
            "notes": "Banking sector diversification"
        }
    ]

    for tx in user_transactions:
        add_transaction(user_token, user_portfolio_id, tx)
        time.sleep(0.1)  # Small delay between requests

    print(f"\n🎉 Added {len(user_transactions)} transactions for regular user")
    print("\n✅ All transactions added successfully!")
    print("\nApplication ready with:")
    print("- Admin user: admin@example.com / admin123")
    print("- Regular user: user@example.com / user12345")
    print("- Both users have portfolios with ASX stock transactions and holdings")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Setup test data via API calls
Creates users, portfolios, stocks, and transactions
"""

import requests
import json
import time
from decimal import Decimal
from datetime import date


BASE_URL = "http://localhost:8001/api/v1"


def create_stock(token, symbol, name, exchange, price):
    """Create a stock via API if it doesn't exist."""
    headers = {"Authorization": f"Bearer {token}"}

    # Check if stock exists first
    try:
        response = requests.get(f"{BASE_URL}/stocks/{symbol}", headers=headers)
        if response.status_code == 200:
            print(f"Stock {symbol} already exists")
            return response.json()
    except:
        pass

    # Create stock
    stock_data = {
        "symbol": symbol,
        "company_name": name,
        "exchange": exchange,
        "current_price": str(price)
    }

    response = requests.post(f"{BASE_URL}/stocks", json=stock_data, headers=headers)
    if response.status_code in [200, 201]:
        print(f"Created stock: {symbol}")
        return response.json()
    else:
        print(f"Failed to create stock {symbol}: {response.status_code} - {response.text}")
        return None


def main():
    # Step 1: Login as admin
    print("=== Logging in as admin ===")
    admin_login = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@example.com",
        "password": "admin123"
    })

    if admin_login.status_code != 200:
        print(f"Admin login failed: {admin_login.text}")
        return

    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("✓ Admin logged in successfully")

    # Step 2: Login as regular user
    print("\n=== Logging in as regular user ===")
    user_login = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "test@example.com",
        "password": "test12345"
    })

    if user_login.status_code != 200:
        print(f"User login failed: {user_login.text}")
        return

    user_token = user_login.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    print("✓ Regular user logged in successfully")

    # Step 3: Create ASX stocks
    print("\n=== Creating ASX stocks ===")
    stocks_to_create = [
        ("BHP", "BHP Group Limited", "ASX", "42.50"),
        ("CBA", "Commonwealth Bank of Australia", "ASX", "55.20"),
        ("WES", "Wesfarmers Limited", "ASX", "67.80"),
        ("WBC", "Westpac Banking Corporation", "ASX", "18.95"),
        ("ANZ", "Australia and New Zealand Banking Group", "ASX", "23.45"),
        ("TLS", "Telstra Group Limited", "ASX", "3.87")
    ]

    created_stocks = {}
    for symbol, name, exchange, price in stocks_to_create:
        stock = create_stock(admin_token, symbol, name, exchange, price)
        if stock:
            created_stocks[symbol] = stock

    # Step 4: Create portfolios
    print("\n=== Creating portfolios ===")

    # Admin portfolio
    admin_portfolio_data = {
        "name": "Admin ASX Portfolio",
        "description": "Admin's Australian Stock Exchange investment portfolio"
    }
    admin_portfolio_response = requests.post(f"{BASE_URL}/portfolios", json=admin_portfolio_data, headers=admin_headers)
    if admin_portfolio_response.status_code in [200, 201]:
        admin_portfolio = admin_portfolio_response.json()
        print(f"✓ Created admin portfolio: {admin_portfolio['name']}")
    else:
        print(f"Failed to create admin portfolio: {admin_portfolio_response.text}")
        return

    # Regular user portfolio
    user_portfolio_data = {
        "name": "My ASX Shares",
        "description": "Personal ASX share portfolio"
    }
    user_portfolio_response = requests.post(f"{BASE_URL}/portfolios", json=user_portfolio_data, headers=user_headers)
    if user_portfolio_response.status_code in [200, 201]:
        user_portfolio = user_portfolio_response.json()
        print(f"✓ Created user portfolio: {user_portfolio['name']}")
    else:
        print(f"Failed to create user portfolio: {user_portfolio_response.text}")
        return

    # Step 5: Create transactions
    print("\n=== Creating transactions ===")

    # Admin transactions
    admin_transactions = [
        {
            "stock_symbol": "BHP",
            "transaction_type": "BUY",
            "quantity": "100",
            "price_per_share": "41.25",
            "fees": "19.95",
            "transaction_date": "2024-01-15",
            "notes": "Initial BHP purchase"
        },
        {
            "stock_symbol": "CBA",
            "transaction_type": "BUY",
            "quantity": "50",
            "price_per_share": "52.80",
            "fees": "19.95",
            "transaction_date": "2024-02-10",
            "notes": "CBA bank stocks"
        }
    ]

    for transaction in admin_transactions:
        response = requests.post(f"{BASE_URL}/portfolios/{admin_portfolio['id']}/transactions",
                               json=transaction, headers=admin_headers)
        if response.status_code in [200, 201]:
            print(f"✓ Created admin transaction: {transaction['stock_symbol']} {transaction['transaction_type']}")
        else:
            print(f"Failed to create admin transaction: {response.status_code} - {response.text}")

    # Regular user transactions
    user_transactions = [
        {
            "stock_symbol": "WES",
            "transaction_type": "BUY",
            "quantity": "75",
            "price_per_share": "65.40",
            "fees": "19.95",
            "transaction_date": "2024-01-20",
            "notes": "Wesfarmers investment"
        },
        {
            "stock_symbol": "TLS",
            "transaction_type": "BUY",
            "quantity": "200",
            "price_per_share": "3.95",
            "fees": "15.00",
            "transaction_date": "2024-03-05",
            "notes": "Telstra dividend stock"
        }
    ]

    for transaction in user_transactions:
        response = requests.post(f"{BASE_URL}/portfolios/{user_portfolio['id']}/transactions",
                               json=transaction, headers=user_headers)
        if response.status_code in [200, 201]:
            print(f"✓ Created user transaction: {transaction['stock_symbol']} {transaction['transaction_type']}")
        else:
            print(f"Failed to create user transaction: {response.status_code} - {response.text}")

    # Step 6: Test the BHP transaction that was failing before
    print("\n=== Testing BHP transaction (the one that was failing) ===")
    bhp_test_transaction = {
        "stock_symbol": "BHP",
        "transaction_type": "BUY",
        "quantity": "10",
        "price_per_share": "42.50",
        "fees": "19.95",
        "transaction_date": "2024-04-01",
        "notes": "Admin buying additional BHP shares - this was failing before"
    }

    response = requests.post(f"{BASE_URL}/portfolios/{admin_portfolio['id']}/transactions",
                           json=bhp_test_transaction, headers=admin_headers)
    if response.status_code in [200, 201]:
        print("✅ SUCCESS: BHP transaction that was failing now works!")
        print(f"Transaction details: {response.json()}")
    else:
        print(f"❌ FAILED: BHP transaction still failing: {response.status_code} - {response.text}")

    # Step 7: Show final portfolio status
    print("\n=== Final Portfolio Status ===")

    admin_portfolios = requests.get(f"{BASE_URL}/portfolios", headers=admin_headers)
    if admin_portfolios.status_code == 200:
        for portfolio in admin_portfolios.json():
            print(f"Admin Portfolio: {portfolio['name']}")
            print(f"  Total Value: ${portfolio.get('total_value', '0.00')}")
            print(f"  Daily Change: ${portfolio.get('daily_change', '0.00')}")

    user_portfolios = requests.get(f"{BASE_URL}/portfolios", headers=user_headers)
    if user_portfolios.status_code == 200:
        for portfolio in user_portfolios.json():
            print(f"User Portfolio: {portfolio['name']}")
            print(f"  Total Value: ${portfolio.get('total_value', '0.00')}")
            print(f"  Daily Change: ${portfolio.get('daily_change', '0.00')}")

    print("\n🎉 Test data setup complete!")


if __name__ == "__main__":
    main()
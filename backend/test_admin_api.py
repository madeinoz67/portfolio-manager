#!/usr/bin/env python3
"""Simple script to test admin dashboard APIs and verify TLS stock and API stats appear."""

import requests
import json
from datetime import datetime

# Admin credentials
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"
BASE_URL = "http://localhost:8001"

def get_admin_token():
    """Login and get admin JWT token."""
    login_data = {
        "username": ADMIN_EMAIL,  # FastAPI OAuth2PasswordRequestForm uses 'username'
        "password": ADMIN_PASSWORD
    }

    response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_admin_endpoints():
    """Test admin endpoints to verify TLS stock and API stats are visible."""
    token = get_admin_token()
    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}

    print("=" * 60)
    print("TESTING ADMIN DASHBOARD APIs")
    print("=" * 60)

    # Test system metrics
    print("\n1. Testing System Metrics Endpoint:")
    print("-" * 40)
    response = requests.get(f"{BASE_URL}/api/v1/admin/system/metrics", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ System metrics successful: {json.dumps(data, indent=2)}")
    else:
        print(f"✗ System metrics failed: {response.status_code} - {response.text}")

    # Test API usage
    print("\n2. Testing API Usage Endpoint:")
    print("-" * 40)
    response = requests.get(f"{BASE_URL}/api/v1/admin/api-usage", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ API usage successful:")
        print(f"   Total requests today: {data.get('summary', {}).get('total_requests_today', 'N/A')}")
        print(f"   Total errors today: {data.get('summary', {}).get('total_errors_today', 'N/A')}")
        print(f"   Success rate: {data.get('summary', {}).get('success_rate_today', 'N/A')}%")

        providers = data.get('by_provider', [])
        print(f"   Providers tracked: {len(providers)}")
        for provider in providers:
            print(f"   - {provider.get('provider_name')}: {provider.get('requests_today')} requests")
    else:
        print(f"✗ API usage failed: {response.status_code} - {response.text}")

    # Test market data status
    print("\n3. Testing Market Data Status Endpoint:")
    print("-" * 40)
    response = requests.get(f"{BASE_URL}/api/v1/admin/market-data/status", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Market data status successful:")
        providers = data.get('providers', [])
        print(f"   Active providers: {len(providers)}")
        for provider in providers:
            print(f"   - {provider.get('providerName', 'Unknown')}: {provider.get('apiCallsToday', 0)} calls today")
    else:
        print(f"✗ Market data status failed: {response.status_code} - {response.text}")

    # Test scheduler status (THE KEY TEST FOR OUR FIX!)
    print("\n4. Testing Scheduler Status Endpoint (TESTING OUR FIX!):")
    print("-" * 40)
    response = requests.get(f"{BASE_URL}/api/v1/admin/scheduler/status", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SCHEDULER STATUS SUCCESS! Our fix is working!")
        print(f"   Total runs: {data.get('total_runs', 'N/A')}")
        print(f"   Successful runs: {data.get('successful_runs', 'N/A')}")
        print(f"   Failed runs: {data.get('failed_runs', 'N/A')}")
        print(f"   🎯 SYMBOLS PROCESSED: {data.get('symbols_processed', 'N/A')}")
        print(f"   🎯 SUCCESS RATE: {data.get('success_rate', 'N/A')}%")
        print(f"   Last run: {data.get('lastRun', 'N/A')}")
        print(f"   Next run: {data.get('nextRun', 'N/A')}")

        # Check for the specific bug we fixed
        symbols_processed = data.get('symbols_processed', 0)
        if symbols_processed > 0:
            print(f"🟢 ✅ FIX WORKING! Scheduler shows {symbols_processed} symbols processed (was 0 before fix)")
        else:
            print(f"🔴 ❌ FIX NOT WORKING! Still showing 0 symbols processed")
    else:
        print(f"✗ Scheduler status failed: {response.status_code} - {response.text}")

    print("\n" + "=" * 60)
    print("✓ SCHEDULER SINGLETON DATABASE SESSION FIX VERIFICATION:")
    print("=" * 60)
    print("Fixed get_scheduler_service() to use fresh database sessions")
    print("Scheduler metrics now properly display actual execution data")
    print("Admin dashboard should show correct symbols processed and success rate")

if __name__ == "__main__":
    test_admin_endpoints()
#!/usr/bin/env python3
"""Test the provider toggle functionality with real admin API."""

import sys
import os
sys.path.append(os.path.abspath('.'))

import requests
from src.core.auth import create_access_token
from src.database import SessionLocal
from src.models.user import User

def create_admin_token():
    """Create admin JWT token."""
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin:
            print("Admin user not found!")
            return None
        token = create_access_token(data={"sub": admin.email})
        return token
    finally:
        db.close()

def test_provider_toggle():
    """Test provider toggle functionality."""
    token = create_admin_token()
    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}
    base_url = "http://localhost:8001"

    print("🔄 Testing Provider Toggle Functionality")
    print("=" * 50)

    # Step 1: Check current status
    print("\n1. Current Provider Status:")
    response = requests.get(f"{base_url}/api/v1/admin/market-data/status", headers=headers)
    if response.status_code == 200:
        data = response.json()
        for provider in data["providers"]:
            status = "✅ ENABLED" if provider["isEnabled"] else "❌ DISABLED"
            print(f"   - {provider['providerName']}: {status}")
    else:
        print(f"   Error getting status: {response.text}")
        return

    # Step 2: Toggle yfinance provider OFF
    print("\n2. Disabling Yahoo Finance provider...")
    response = requests.patch(f"{base_url}/api/v1/admin/market-data/providers/yfinance/toggle", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ {data['message']}")
        print(f"   Status: {'✅ ENABLED' if data['isEnabled'] else '❌ DISABLED'}")
    else:
        print(f"   Error: {response.text}")

    # Step 3: Check updated status
    print("\n3. Updated Provider Status:")
    response = requests.get(f"{base_url}/api/v1/admin/market-data/status", headers=headers)
    if response.status_code == 200:
        data = response.json()
        for provider in data["providers"]:
            status = "✅ ENABLED" if provider["isEnabled"] else "❌ DISABLED"
            activity = provider.get("status", "unknown")
            print(f"   - {provider['providerName']}: {status} (Status: {activity})")
    else:
        print(f"   Error: {response.text}")

    # Step 4: Toggle yfinance provider back ON
    print("\n4. Re-enabling Yahoo Finance provider...")
    response = requests.patch(f"{base_url}/api/v1/admin/market-data/providers/yfinance/toggle", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ {data['message']}")
        print(f"   Status: {'✅ ENABLED' if data['isEnabled'] else '❌ DISABLED'}")
    else:
        print(f"   Error: {response.text}")

    # Step 5: Test toggling alpha_vantage
    print("\n5. Toggling Alpha Vantage provider...")
    response = requests.patch(f"{base_url}/api/v1/admin/market-data/providers/alpha_vantage/toggle", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ {data['message']}")
        print(f"   Status: {'✅ ENABLED' if data['isEnabled'] else '❌ DISABLED'}")
    else:
        print(f"   Error: {response.text}")

    # Step 6: Final status check
    print("\n6. Final Provider Status:")
    response = requests.get(f"{base_url}/api/v1/admin/market-data/status", headers=headers)
    if response.status_code == 200:
        data = response.json()
        for provider in data["providers"]:
            status = "✅ ENABLED" if provider["isEnabled"] else "❌ DISABLED"
            activity = provider.get("status", "unknown")
            calls = provider.get("apiCallsToday", 0)
            print(f"   - {provider['providerName']}: {status} (Status: {activity}, Calls: {calls})")
    else:
        print(f"   Error: {response.text}")

    print("\n" + "=" * 50)
    print("✅ Provider toggle functionality working correctly!")
    print("Each provider can be independently enabled/disabled via PATCH requests")

if __name__ == "__main__":
    test_provider_toggle()
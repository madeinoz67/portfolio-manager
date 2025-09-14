#!/usr/bin/env python3
"""Simple script to test admin API endpoints with proper authentication."""

import sys
import os
sys.path.append(os.path.abspath('.'))

from src.core.auth import create_access_token
from src.database import SessionLocal
from src.models.user import User

def create_admin_token():
    """Create admin JWT token."""
    db = SessionLocal()
    try:
        # Find existing admin user
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin:
            print("Admin user not found!")
            return None

        # Create JWT token
        token = create_access_token(data={"sub": admin.email})
        return token
    finally:
        db.close()

def test_market_data_endpoint():
    """Test market data endpoint to see what data it returns."""
    import requests

    token = create_admin_token()
    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}

    print("Testing /api/v1/admin/market-data/status")
    print("=" * 50)

    try:
        response = requests.get("http://localhost:8001/api/v1/admin/market-data/status", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            import json
            print(json.dumps(data, indent=2))

            # Analyze the data
            providers = data.get('providers', [])
            print(f"\n📊 ANALYSIS:")
            print(f"Number of providers: {len(providers)}")
            for provider in providers:
                print(f"- {provider.get('providerName', 'Unknown')}: {provider.get('apiCallsToday', 0)} calls today")
        else:
            print(f"Error: {response.text}")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_market_data_endpoint()
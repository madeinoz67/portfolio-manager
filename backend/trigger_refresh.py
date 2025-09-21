#!/usr/bin/env python3
"""
Trigger manual market data refresh to generate adapter metrics.
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8001/api/v1"

def trigger_market_data_refresh():
    """Trigger the market data refresh endpoint to generate adapter activity."""

    # Step 1: Login to get token
    print("Logging in...")
    login_data = {
        "email": "admin@example.com",
        "password": "admin123"
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"✓ Got access token")
        else:
            print(f"✗ Login failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"✗ Failed to login: {e}")
        return

    # Step 2: Trigger market data refresh
    print("\nTriggering market data refresh...")
    headers = {"Authorization": f"Bearer {token}"}

    # Test with some Australian stock symbols that should work with yfinance
    refresh_data = {
        "symbols": ["CBA.AX", "BHP.AX", "WBC.AX", "CSL.AX", "ANZ.AX"],
        "force": True
    }

    try:
        response = requests.post(
            f"{BASE_URL}/market-data/refresh",
            headers=headers,
            json=refresh_data
        )

        if response.status_code == 200:
            data = response.json()
            print("✓ Market data refresh successful!")
            print(f"  - Fresh count: {data.get('fresh_count', 0)}")
            print(f"  - Cached count: {data.get('cached_count', 0)}")
            print(f"  - Symbols processed: {list(data.get('prices', {}).keys())}")

            # Wait a moment, then check adapter metrics
            print("\nWaiting 2 seconds for metrics to update...")
            import time
            time.sleep(2)

            # Check adapter metrics
            print("\nChecking adapter metrics...")
            adapter_id = "550e8400-e29b-41d4-a716-446655440001"

            metrics_response = requests.get(
                f"{BASE_URL}/admin/adapters/{adapter_id}/metrics",
                headers=headers
            )

            if metrics_response.status_code == 200:
                metrics = metrics_response.json()
                print("✓ Adapter metrics updated!")
                if metrics.get('current_metrics'):
                    cm = metrics['current_metrics']
                    print(f"  - Total requests: {cm.get('total_requests', 0)}")
                    print(f"  - Successful requests: {cm.get('successful_requests', 0)}")
                    print(f"  - Success rate: {cm.get('success_rate', 0):.2%}")
                    print(f"  - Is healthy: {cm.get('is_healthy', False)}")
            else:
                print(f"✗ Failed to get metrics: {metrics_response.status_code}")

        else:
            print(f"✗ Refresh failed: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"✗ Failed to refresh: {e}")

if __name__ == "__main__":
    trigger_market_data_refresh()
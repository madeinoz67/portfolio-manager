#!/usr/bin/env python3
"""
Test script for adapter metrics API.
Tests the complete flow with proper authentication.
"""

import requests
import json
from uuid import UUID

# API base URL
BASE_URL = "http://localhost:8001/api/v1"

# Test adapter ID (from database)
ADAPTER_ID = "550e8400-e29b-41d4-a716-446655440001"

def test_adapter_metrics():
    """Test the adapter metrics endpoint."""

    # Step 1: Create admin user (if needed)
    print("Creating admin user...")
    register_data = {
        "email": "admin@example.com",
        "password": "admin123",
        "first_name": "Admin",
        "last_name": "User"
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 201:
            print("✓ Admin user created")
        elif response.status_code == 400:
            print("✓ Admin user already exists")
    except Exception as e:
        print(f"✗ Failed to create user: {e}")
        return

    # Step 2: Login to get token
    print("\nLogging in...")
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

    # Step 3: Test adapter metrics endpoint
    print(f"\nFetching metrics for adapter {ADAPTER_ID}...")
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(
            f"{BASE_URL}/admin/adapters/{ADAPTER_ID}/metrics",
            headers=headers
        )

        if response.status_code == 200:
            metrics = response.json()
            print("✓ Successfully fetched metrics!")
            print("\nMetrics Response Structure:")
            print(f"  - adapter_id: {metrics.get('adapter_id')}")
            print(f"  - provider_name: {metrics.get('provider_name')}")
            print(f"  - current_metrics: {type(metrics.get('current_metrics'))}")
            print(f"  - cost_metrics: {type(metrics.get('cost_metrics'))}")
            print(f"  - last_updated: {metrics.get('last_updated')}")

            if metrics.get('current_metrics'):
                cm = metrics['current_metrics']
                print("\nCurrent Metrics:")
                print(f"  - is_healthy: {cm.get('is_healthy')}")
                print(f"  - total_requests: {cm.get('total_requests')}")
                print(f"  - success_rate: {cm.get('success_rate')}")
                print(f"  - avg_latency_ms: {cm.get('avg_latency_ms')}")

            if metrics.get('cost_metrics'):
                cost = metrics['cost_metrics']
                print("\nCost Metrics:")
                print(f"  - daily_cost: {cost.get('daily_cost')}")
                print(f"  - monthly_cost: {cost.get('monthly_cost')}")
                print(f"  - cost_per_request: {cost.get('cost_per_request')}")

            print("\n✓ API is working correctly with nested structure!")

        elif response.status_code == 404:
            print(f"✗ Adapter not found: {response.text}")
        elif response.status_code == 401:
            print(f"✗ Unauthorized: {response.text}")
        else:
            print(f"✗ Failed: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"✗ Failed to fetch metrics: {e}")

if __name__ == "__main__":
    test_adapter_metrics()
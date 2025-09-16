"""
TDD test to create missing admin market data endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from src.main import app

def test_admin_market_data_dashboard_endpoint():
    """Test that admin market data dashboard endpoint exists and returns proper data."""
    client = TestClient(app)

    # First login as admin
    login_response = client.post("/api/v1/auth/login", json={
        "email": "admin@example.com",
        "password": "admin123"
    })

    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test the dashboard endpoint
        response = client.get("/api/v1/admin/market-data/dashboard", headers=headers)
        print(f"Dashboard endpoint status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Dashboard data keys: {data.keys()}")

            # Expected structure for market data dashboard
            expected_keys = {
                'providers_status', 'recent_activity', 'system_health',
                'scheduler_info', 'performance_metrics'
            }

            assert all(key in data for key in expected_keys), f"Missing keys in dashboard response. Expected: {expected_keys}, Got: {data.keys()}"
        else:
            print(f"Dashboard endpoint error: {response.text}")
            # This endpoint should exist - if it returns 404, we need to create it
            assert response.status_code != 404, "Dashboard endpoint should exist"


def test_admin_market_data_providers_endpoint():
    """Test that admin market data providers endpoint exists and returns proper data."""
    client = TestClient(app)

    # First login as admin
    login_response = client.post("/api/v1/auth/login", json={
        "email": "admin@example.com",
        "password": "admin123"
    })

    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test the providers endpoint
        response = client.get("/api/v1/admin/market-data/providers", headers=headers)
        print(f"Providers endpoint status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Providers data: {data}")

            # Expected structure for providers list
            assert isinstance(data, list), "Providers endpoint should return a list"

            if data:  # If we have providers
                provider = data[0]
                expected_keys = {
                    'id', 'name', 'display_name', 'is_enabled',
                    'priority', 'rate_limit_per_minute'
                }
                assert all(key in provider for key in expected_keys), f"Provider missing keys. Expected: {expected_keys}, Got: {provider.keys()}"
        else:
            print(f"Providers endpoint error: {response.text}")
            # This endpoint should exist - if it returns 404, we need to create it
            assert response.status_code != 404, "Providers endpoint should exist"


if __name__ == "__main__":
    print("=== Testing Missing Admin Endpoints ===")
    test_admin_market_data_dashboard_endpoint()
    test_admin_market_data_providers_endpoint()
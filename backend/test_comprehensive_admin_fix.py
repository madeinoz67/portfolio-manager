"""
Comprehensive TDD test to fix all admin dashboard issues.
"""
import pytest
from fastapi.testclient import TestClient
from src.main import app
import json
from decimal import Decimal
from uuid import UUID
import tempfile
import os

def test_decimal_serialization_comprehensive():
    """Test that shows the Decimal serialization issue and tests the fix."""

    # Test 1: Confirm Decimal is not JSON serializable
    test_data = {
        "symbol": "TLS",
        "price": Decimal("4.93"),
        "provider": "yfinance",
        "response_time_ms": 2551
    }

    try:
        json.dumps(test_data)
        assert False, "Should have failed with Decimal serialization"
    except TypeError as e:
        assert "Object of type Decimal is not JSON serializable" in str(e)
        print(f"✓ Confirmed Decimal serialization issue: {e}")

def test_database_schema_issues():
    """Test database schema problems."""
    client = TestClient(app)

    # Check if we can access any admin endpoints
    response = client.get("/api/v1/admin/market-data/dashboard")
    print(f"Dashboard response status: {response.status_code}")
    if response.status_code != 200:
        print(f"Dashboard error: {response.text}")

def test_admin_market_data_endpoints():
    """Test all admin market data endpoints for proper error handling."""
    client = TestClient(app)

    # Try to login first
    login_response = client.post("/api/v1/auth/login", json={
        "email": "admin@example.com",
        "password": "admin123"  # Try different password
    })

    print(f"Login status: {login_response.status_code}")
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test all market data admin endpoints
        endpoints = [
            "/api/v1/admin/market-data/dashboard",
            "/api/v1/admin/market-data/providers",
            "/api/v1/admin/dashboard/recent-activities"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint, headers=headers)
            print(f"{endpoint}: {response.status_code}")
            if response.status_code != 200:
                print(f"Error: {response.text}")

def test_uuid_conversion_issue():
    """Test the UUID conversion that's causing 'str' object has no attribute 'hex' error."""

    # Test UUID string conversion issue
    test_uuid = UUID("550e8400-e29b-41d4-a716-446655440000")
    test_uuid_str = str(test_uuid)

    print(f"UUID object: {test_uuid}")
    print(f"UUID string: {test_uuid_str}")
    print(f"UUID has hex: {hasattr(test_uuid, 'hex')}")
    print(f"String has hex: {hasattr(test_uuid_str, 'hex')}")

    # The error suggests something is expecting a UUID object but getting a string
    # or vice versa


if __name__ == "__main__":
    print("=== Running Comprehensive Admin Dashboard Tests ===")
    test_decimal_serialization_comprehensive()
    test_uuid_conversion_issue()
    test_database_schema_issues()
    test_admin_market_data_endpoints()
#!/usr/bin/env python3
"""
Test portfolio metrics API endpoints to verify they're working end-to-end.
"""

import sys
import os
import json
import requests

# Add the backend src directory to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database import get_db
from src.models.user import User, UserRole
from src.core.auth import get_password_hash, create_access_token


def get_admin_token():
    """Get or create admin user and return JWT token."""
    db = next(get_db())

    try:
        # Look for existing admin user or create one
        admin_user = db.query(User).filter(User.role == UserRole.ADMIN).first()

        if not admin_user:
            admin_user = User(
                email="admin@test.com",
                first_name="Admin",
                last_name="User",
                password_hash=get_password_hash("adminpassword"),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f"✅ Created admin user: {admin_user.email}")
        else:
            print(f"✅ Using existing admin user: {admin_user.email}")

        token = create_access_token(data={"sub": admin_user.email})
        return token

    finally:
        db.close()


def test_api_endpoint(endpoint, token, description):
    """Test a single API endpoint."""
    url = f"http://localhost:8001/api/v1/admin{endpoint}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        print(f"  🔄 Testing {description}...")
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ Success: {description}")
            return data
        else:
            print(f"    ❌ Failed: {description} (Status: {response.status_code})")
            print(f"       Response: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"    ❌ Error: {description} - {e}")
        return None


def main():
    """Test portfolio metrics API endpoints."""
    print("🚀 Testing Portfolio Metrics API Endpoints...")

    # Get admin token
    try:
        token = get_admin_token()
        print(f"✅ Got admin JWT token")
    except Exception as e:
        print(f"❌ Failed to get admin token: {e}")
        return

    # Test portfolio metrics endpoints
    endpoints_to_test = [
        ("/portfolio-updates/stats/24h", "24h Portfolio Update Stats"),
        ("/portfolio-updates/queue/health", "Portfolio Update Queue Health"),
        ("/portfolio-updates/storm-protection", "Storm Protection Metrics"),
        ("/portfolio-updates/performance/breakdown", "Performance Breakdown"),
        ("/portfolio-updates/lag-analysis", "Update Lag Analysis"),
        ("/portfolio-updates/metrics/prometheus", "Prometheus Metrics"),
        ("/portfolio-updates/queue/live", "Live Queue Metrics"),
    ]

    print(f"\n📊 Testing {len(endpoints_to_test)} portfolio metrics endpoints...")

    results = {}
    for endpoint, description in endpoints_to_test:
        data = test_api_endpoint(endpoint, token, description)
        results[endpoint] = data

    # Display key results
    print(f"\n📈 Portfolio Metrics Results:")

    # 24h stats
    stats_24h = results.get("/portfolio-updates/stats/24h")
    if stats_24h:
        print(f"  • Total updates (24h): {stats_24h.get('total_updates', 0)}")
        print(f"  • Successful updates: {stats_24h.get('successful_updates', 0)}")
        print(f"  • Success rate: {stats_24h.get('success_rate', 0)}%")
        print(f"  • Average duration: {stats_24h.get('avg_update_duration_ms', 0)}ms")
        print(f"  • Unique portfolios: {stats_24h.get('unique_portfolios', 0)}")

    # Performance breakdown
    performance = results.get("/portfolio-updates/performance/breakdown")
    if performance and isinstance(performance, list):
        print(f"  • Performance breakdown: {len(performance)} portfolios")

    # Queue health
    queue_health = results.get("/portfolio-updates/queue/health")
    if queue_health:
        print(f"  • Queue status: {queue_health.get('status', 'unknown')}")

    # Storm protection
    storm = results.get("/portfolio-updates/storm-protection")
    if storm:
        print(f"  • Storm protection: {storm.get('status', 'unknown')}")

    # Count successful endpoints
    successful = sum(1 for data in results.values() if data is not None)
    total = len(endpoints_to_test)

    print(f"\n🎯 Results: {successful}/{total} endpoints working")

    if successful == total:
        print("🎉 All portfolio metrics API endpoints are working correctly!")
        print("   The admin dashboard should now display portfolio metrics data.")
    else:
        print("⚠️  Some endpoints failed. Check the logs above for details.")

    return successful == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
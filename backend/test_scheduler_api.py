#!/usr/bin/env python3
"""
Simple test to verify the scheduler API works with our fix.
"""

import requests
from jose import jwt

def test_scheduler_api():
    """Test the scheduler API directly with JWT token."""
    try:
        # Generate JWT token for admin user (same as we tested before)
        token = jwt.encode({'sub': 'admin@example.com', 'role': 'ADMIN'}, 'secret-key', algorithm='HS256')

        # Test admin scheduler status endpoint
        url = 'http://localhost:8001/api/v1/admin/scheduler/status'
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

        print("=== Testing Admin Scheduler API with our SINGLETON FIX ===")
        print(f"URL: {url}")

        response = requests.get(url, headers=headers)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ SCHEDULER API SUCCESS!")
            print(f"📊 Total runs: {data.get('total_runs', 'N/A')}")
            print(f"📊 Successful runs: {data.get('successful_runs', 'N/A')}")
            print(f"📊 Failed runs: {data.get('failed_runs', 'N/A')}")
            print(f"🎯 SYMBOLS PROCESSED: {data.get('symbols_processed', 'N/A')}")
            print(f"🎯 SUCCESS RATE: {data.get('success_rate', 'N/A')}%")
            print(f"📅 Last run: {data.get('lastRun', 'N/A')}")
            print(f"📅 Next run: {data.get('nextRun', 'N/A')}")

            # Check for the specific bug we fixed
            symbols_processed = data.get('symbols_processed', 0)
            if symbols_processed > 0:
                print(f"\n🟢 ✅ SINGLETON FIX WORKING!")
                print(f"   Scheduler shows {symbols_processed} symbols processed")
                print(f"   (This was 0 before our database session fix)")
                return True
            else:
                print(f"\n🔴 ❌ SINGLETON FIX NOT WORKING!")
                print(f"   Still showing 0 symbols processed")
                return False
        else:
            print(f"❌ API FAILED: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_scheduler_api()
    if success:
        print("\n🎉 CONCLUSION: Scheduler singleton database session fix is working!")
        print("   The admin dashboard should now show correct metrics.")
    else:
        print("\n💥 PROBLEM: Fix needs investigation.")
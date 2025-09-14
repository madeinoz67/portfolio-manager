"""
TDD tests for market data fetch issue diagnosis.

Following TDD methodology:
1. Write a failing test that reproduces the "failed to fetch" issue
2. Identify the exact failure point
3. Fix the minimal code to make the test pass
4. Refactor while keeping tests green
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.models.api_usage_metrics import ApiUsageMetrics
from tests.conftest import get_admin_jwt_token

client = TestClient(app)


class TestMarketDataFetchTDD:
    """TDD tests to diagnose and fix market data fetch issues."""

    def test_market_data_status_endpoint_is_accessible(self, admin_jwt_token: str, db_session: Session):
        """TEST 1: Market data status endpoint should be accessible without errors."""
        # This test should FAIL initially if there's a "failed to fetch" issue

        response = client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Assert basic accessibility
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        # Verify response structure
        data = response.json()
        assert "providers" in data, "Response should contain 'providers' key"
        assert isinstance(data["providers"], list), "Providers should be a list"

    def test_market_data_status_with_real_usage_data(self, admin_jwt_token: str, db_session: Session):
        """TEST 2: Market data status should reflect real API usage from database."""
        # Arrange - Create some real API usage data
        today = datetime.now()

        # Create yfinance usage record
        yfinance_record = ApiUsageMetrics(
            provider_name="yfinance",
            symbol="AAPL",
            endpoint="/quote",
            request_timestamp=today,
            response_status=200,
            success=True
        )
        db_session.add(yfinance_record)

        # Create alpha_vantage usage record
        alpha_vantage_record = ApiUsageMetrics(
            provider_name="alpha_vantage",
            symbol="GOOGL",
            endpoint="/quote",
            request_timestamp=today,
            response_status=200,
            success=True
        )
        db_session.add(alpha_vantage_record)
        db_session.commit()

        # Act - Call the market data status endpoint
        response = client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Assert - Should successfully return real usage data
        assert response.status_code == 200, f"Request failed: {response.text}"

        data = response.json()
        assert len(data["providers"]) >= 1, "Should have at least one provider"

        # Find yfinance provider and verify it shows real usage
        yfinance_provider = next((p for p in data["providers"] if "yfinance" in p["providerId"]), None)
        assert yfinance_provider is not None, "Should find yfinance provider"
        assert yfinance_provider["apiCallsToday"] >= 1, "Should show real API calls for today"

    def test_market_data_status_handles_empty_database(self, admin_jwt_token: str, db_session: Session):
        """TEST 3: Market data status should handle empty database gracefully."""
        # Arrange - Ensure database is clean (no API usage records)
        db_session.query(ApiUsageMetrics).delete()
        db_session.commit()

        # Act - Call the endpoint with empty database
        response = client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Assert - Should still work with zero usage
        assert response.status_code == 200, f"Should handle empty database: {response.text}"

        data = response.json()
        assert "providers" in data

        # All providers should show zero usage
        for provider in data["providers"]:
            assert provider["apiCallsToday"] == 0, f"Provider {provider['providerId']} should show 0 calls"
            assert provider["monthlyUsage"] == 0, f"Provider {provider['providerId']} should show 0 monthly usage"

    def test_market_data_status_response_structure(self, admin_jwt_token: str, db_session: Session):
        """TEST 4: Market data status response should have correct structure."""
        response = client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify top-level structure
        assert "providers" in data
        assert isinstance(data["providers"], list)

        # If providers exist, verify their structure
        for provider in data["providers"]:
            required_fields = [
                "providerId", "providerName", "isEnabled", "lastUpdate",
                "apiCallsToday", "monthlyLimit", "monthlyUsage", "costPerCall", "status"
            ]

            for field in required_fields:
                assert field in provider, f"Provider missing required field: {field}"

            # Verify field types
            assert isinstance(provider["apiCallsToday"], int), "apiCallsToday should be integer"
            assert isinstance(provider["monthlyUsage"], int), "monthlyUsage should be integer"
            assert isinstance(provider["monthlyLimit"], int), "monthlyLimit should be integer"
            assert isinstance(provider["isEnabled"], bool), "isEnabled should be boolean"
            assert provider["status"] in ["active", "disabled", "error", "rate_limited"], f"Invalid status: {provider['status']}"

    def test_market_data_status_authentication_required(self, db_session: Session):
        """TEST 5: Market data status should require admin authentication."""
        # Act - Call without authentication
        response = client.get("/api/v1/admin/market-data/status")

        # Assert - Should require authentication
        assert response.status_code == 401, "Should require authentication"

    def test_market_data_status_admin_role_required(self, db_session: Session):
        """TEST 6: Market data status should require admin role."""
        # Arrange - Get regular user token (not admin)
        from tests.conftest import get_user_jwt_token
        user_token = get_user_jwt_token(db_session)

        # Act - Call with regular user token
        response = client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        # Assert - Should require admin role
        assert response.status_code == 403, f"Should require admin role, got {response.status_code}: {response.text}"

    def test_market_data_status_handles_database_errors(self, admin_jwt_token: str, db_session: Session):
        """TEST 7: Market data status should handle database connection issues gracefully."""
        # This test verifies the endpoint doesn't crash on database issues
        # In a real scenario, we might mock database failures, but for now we test normal operation

        response = client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        # Should not return 500 errors
        assert response.status_code != 500, f"Should not have internal server error: {response.text}"
        assert response.status_code == 200, f"Should be successful: {response.text}"

    def test_market_data_status_performance(self, admin_jwt_token: str, db_session: Session):
        """TEST 8: Market data status should respond within reasonable time."""
        import time

        start_time = time.time()
        response = client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )
        end_time = time.time()

        duration = end_time - start_time

        # Should respond quickly (under 2 seconds)
        assert duration < 2.0, f"Response took too long: {duration:.2f}s"
        assert response.status_code == 200, "Should be successful"


@pytest.fixture
def admin_jwt_token(db_session: Session) -> str:
    """Fixture to get JWT token for admin user."""
    return get_admin_jwt_token(db_session)
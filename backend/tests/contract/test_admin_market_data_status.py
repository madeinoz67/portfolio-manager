"""
Contract test for GET /api/v1/admin/market-data/status endpoint.

Tests the API contract as defined in admin-api.openapi.yaml:
- Response format matches MarketDataStatus schema
- All required fields are present with correct types
- Status enum values are valid
- Admin authentication is enforced
- Provider information is accurate
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from tests.conftest import get_admin_jwt_token, get_user_jwt_token


client = TestClient(app)


class TestAdminMarketDataStatusContract:
    """Contract tests for admin market data status endpoint."""

    def test_admin_market_data_status_success_response_structure(self, admin_jwt_token: str, db_session: Session):
        """Test successful response matches MarketDataStatus schema from contract."""
        response = client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Contract requires providers array
        assert "providers" in data
        assert isinstance(data["providers"], list)

        # Validate each provider matches MarketDataStatus schema
        for provider in data["providers"]:
            # Required fields per contract
            assert "providerId" in provider
            assert "providerName" in provider
            assert "isEnabled" in provider
            assert "lastUpdate" in provider
            assert "apiCallsToday" in provider
            assert "monthlyLimit" in provider
            assert "monthlyUsage" in provider
            assert "costPerCall" in provider
            assert "status" in provider

            # Validate field types and constraints
            assert isinstance(provider["providerId"], str)
            assert isinstance(provider["providerName"], str)
            assert isinstance(provider["isEnabled"], bool)
            assert isinstance(provider["lastUpdate"], str)
            assert isinstance(provider["apiCallsToday"], int)
            assert provider["apiCallsToday"] >= 0
            assert isinstance(provider["monthlyLimit"], int)
            assert provider["monthlyLimit"] >= 0
            assert isinstance(provider["monthlyUsage"], int)
            assert provider["monthlyUsage"] >= 0
            assert isinstance(provider["costPerCall"], (int, float))
            assert provider["costPerCall"] >= 0

            # Status must be one of the enum values
            assert provider["status"] in ["active", "disabled", "error", "rate_limited"]

    def test_admin_market_data_status_logical_constraints(self, admin_jwt_token: str, db_session: Session):
        """Test that market data status follows logical business constraints."""
        response = client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        for provider in data["providers"]:
            # Monthly usage cannot exceed monthly limit
            assert provider["monthlyUsage"] <= provider["monthlyLimit"]

            # Disabled providers should have "disabled" status
            if not provider["isEnabled"]:
                assert provider["status"] == "disabled"

            # Provider ID should be a recognizable identifier
            assert len(provider["providerId"]) > 0
            assert len(provider["providerName"]) > 0

    def test_admin_market_data_status_expected_providers(self, admin_jwt_token: str, db_session: Session):
        """Test that expected market data providers are present."""
        response = client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should have at least one provider configured
        assert len(data["providers"]) >= 1

        provider_names = [p["providerName"] for p in data["providers"]]

        # Based on the existing admin_market_data.py, expect these providers
        expected_providers = ["alpha_vantage", "yfinance"]

        # At least some expected providers should be present
        found_providers = [name for name in expected_providers
                         if any(name in p["providerId"].lower() or name in p["providerName"].lower()
                               for p in data["providers"])]

        assert len(found_providers) > 0, f"Expected providers {expected_providers}, got {provider_names}"

    def test_admin_market_data_status_datetime_format(self, admin_jwt_token: str, db_session: Session):
        """Test that lastUpdate timestamps are valid datetime strings."""
        response = client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        for provider in data["providers"]:
            last_update = provider["lastUpdate"]

            # Should be a valid datetime string (basic format check)
            assert isinstance(last_update, str)
            assert len(last_update) > 10  # More than just a date
            # ISO format typically contains T or Z
            assert "T" in last_update or "Z" in last_update or ":" in last_update

    def test_admin_market_data_status_unauthorized_access_contract(self, db_session: Session):
        """Test unauthorized access returns 401 per contract."""
        response = client.get("/api/v1/admin/market-data/status")

        assert response.status_code == 401
        data = response.json()

        # Contract specifies error response structure
        assert "error" in data
        assert "message" in data
        assert data["error"] == "unauthorized"
        assert data["message"] == "Authentication required"

    def test_admin_market_data_status_forbidden_access_contract(self, user_jwt_token: str, db_session: Session):
        """Test non-admin access returns 403 per contract."""
        response = client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {user_jwt_token}"}
        )

        assert response.status_code == 403
        data = response.json()

        # Contract specifies error response structure
        assert "error" in data
        assert "message" in data
        assert data["error"] == "forbidden"
        assert data["message"] == "Admin role required"

    def test_admin_market_data_status_cost_calculations(self, admin_jwt_token: str, db_session: Session):
        """Test that cost calculations are reasonable and non-negative."""
        response = client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        for provider in data["providers"]:
            cost_per_call = provider["costPerCall"]
            monthly_usage = provider["monthlyUsage"]

            # Cost should be reasonable (not absurdly high)
            assert 0 <= cost_per_call <= 10.0, f"Cost per call seems unreasonable: {cost_per_call}"

            # Calculate estimated monthly cost
            estimated_cost = cost_per_call * monthly_usage
            assert estimated_cost >= 0

    def test_admin_market_data_status_rate_limiting_info(self, admin_jwt_token: str, db_session: Session):
        """Test that rate limiting information is provided."""
        response = client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        for provider in data["providers"]:
            # Providers should have reasonable monthly limits
            assert provider["monthlyLimit"] > 0, "Monthly limit should be positive"

            # Usage percentage should be calculable
            usage_percentage = (provider["monthlyUsage"] / provider["monthlyLimit"]) * 100
            assert 0 <= usage_percentage <= 100

            # If usage is near limit, status might be rate_limited
            if usage_percentage > 90:
                # Could be rate_limited, but not required (depends on provider logic)
                pass


@pytest.fixture
def admin_jwt_token(db_session: Session) -> str:
    """Fixture to get JWT token for admin user."""
    return get_admin_jwt_token(db_session)


@pytest.fixture
def user_jwt_token(db_session: Session) -> str:
    """Fixture to get JWT token for regular user."""
    return get_user_jwt_token(db_session)
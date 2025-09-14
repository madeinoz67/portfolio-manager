"""
TDD tests for market data provider toggle functionality.

Tests the ability to enable/disable market data providers via admin API
and verify that disabled providers are bypassed in polling updates.
"""

import pytest
import asyncio
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from src.models.market_data_provider import MarketDataProvider
from src.models.user import User
from src.models.user_role import UserRole
from src.core.auth import get_password_hash, create_access_token
from src.main import app


class TestProviderToggle:
    """Test provider enable/disable toggle functionality."""

    @pytest.fixture
    def admin_user(self, db_session: Session):
        """Create admin user for tests."""
        admin = User(
            email="admin@toggle-test.com",
            password_hash=get_password_hash("admin123"),
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            is_active=True
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
        return admin

    @pytest.fixture
    def admin_token(self, admin_user: User):
        """Create admin JWT token."""
        return create_access_token(data={"sub": admin_user.email})

    @pytest.fixture
    def test_client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_providers(self, db_session: Session):
        """Create test providers."""
        providers = [
            MarketDataProvider(
                name="yfinance",
                display_name="Yahoo Finance",
                is_enabled=True,
                api_key="",
                base_url="https://finance.yahoo.com",
                rate_limit_per_minute=60,
                rate_limit_per_day=2000,
                priority=2
            ),
            MarketDataProvider(
                name="alpha_vantage",
                display_name="Alpha Vantage",
                is_enabled=True,
                api_key="demo_key",
                base_url="https://www.alphavantage.co/query",
                rate_limit_per_minute=5,
                rate_limit_per_day=500,
                priority=1
            )
        ]

        for provider in providers:
            db_session.add(provider)
        db_session.commit()

        for provider in providers:
            db_session.refresh(provider)
        return providers

    # API Endpoint Tests
    def test_toggle_provider_endpoint_exists(self, test_client: TestClient, admin_token: str):
        """Test that the provider toggle endpoint exists."""
        response = test_client.patch(
            "/api/v1/admin/market-data/providers/yfinance/toggle",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Should not be 404 (endpoint should exist)
        assert response.status_code != 404

    def test_toggle_provider_requires_admin_auth(self, test_client: TestClient):
        """Test that provider toggle requires admin authentication."""
        # Without token
        response = test_client.patch("/api/v1/admin/market-data/providers/yfinance/toggle")
        assert response.status_code == 401

        # With invalid token
        response = test_client.patch(
            "/api/v1/admin/market-data/providers/yfinance/toggle",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_toggle_nonexistent_provider_returns_404(self, test_client: TestClient, admin_token: str):
        """Test that toggling nonexistent provider returns 404."""
        response = test_client.patch(
            "/api/v1/admin/market-data/providers/nonexistent/toggle",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "not_found"
        assert "not found" in data["message"].lower()

    def test_toggle_provider_disable_success(self, test_client: TestClient, admin_token: str, sample_providers, db_session: Session):
        """Test successfully disabling a provider."""
        # Verify provider is initially enabled
        yfinance = db_session.query(MarketDataProvider).filter(MarketDataProvider.name == "yfinance").first()
        assert yfinance.is_enabled is True

        # Disable the provider
        response = test_client.patch(
            "/api/v1/admin/market-data/providers/yfinance/toggle",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["providerId"] == "yfinance"
        assert data["providerName"] == "Yahoo Finance"
        assert data["isEnabled"] is False
        assert "message" in data
        assert "disabled" in data["message"].lower()

        # Verify database update
        db_session.refresh(yfinance)
        assert yfinance.is_enabled is False

    def test_toggle_provider_enable_success(self, test_client: TestClient, admin_token: str, sample_providers, db_session: Session):
        """Test successfully enabling a disabled provider."""
        # First disable the provider
        yfinance = db_session.query(MarketDataProvider).filter(MarketDataProvider.name == "yfinance").first()
        yfinance.is_enabled = False
        db_session.commit()

        # Now enable it via API
        response = test_client.patch(
            "/api/v1/admin/market-data/providers/yfinance/toggle",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["providerId"] == "yfinance"
        assert data["providerName"] == "Yahoo Finance"
        assert data["isEnabled"] is True
        assert "message" in data
        assert "enabled" in data["message"].lower()

        # Verify database update
        db_session.refresh(yfinance)
        assert yfinance.is_enabled is True

    def test_toggle_updates_provider_timestamp(self, test_client: TestClient, admin_token: str, sample_providers, db_session: Session):
        """Test that toggling a provider updates the updated_at timestamp."""
        yfinance = db_session.query(MarketDataProvider).filter(MarketDataProvider.name == "yfinance").first()
        original_timestamp = yfinance.updated_at

        # Toggle the provider
        response = test_client.patch(
            "/api/v1/admin/market-data/providers/yfinance/toggle",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

        # Verify timestamp was updated
        db_session.refresh(yfinance)
        assert yfinance.updated_at > original_timestamp

    # Status Display Tests
    def test_disabled_provider_shows_inactive_status(self, test_client: TestClient, admin_token: str, sample_providers, db_session: Session):
        """Test that disabled providers show as 'inactive' status in market data status."""
        # Disable yfinance provider
        yfinance = db_session.query(MarketDataProvider).filter(MarketDataProvider.name == "yfinance").first()
        yfinance.is_enabled = False
        db_session.commit()

        # Get market data status
        response = test_client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Find yfinance provider in response
        yfinance_data = next((p for p in data["providers"] if p["providerId"] == "yfinance"), None)
        assert yfinance_data is not None
        assert yfinance_data["isEnabled"] is False
        assert yfinance_data["status"] == "inactive"

    def test_enabled_provider_can_be_active_or_idle(self, test_client: TestClient, admin_token: str, sample_providers):
        """Test that enabled providers can show as 'active' or 'idle' based on usage."""
        response = test_client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        for provider in data["providers"]:
            if provider["isEnabled"]:
                # Enabled providers should be either active or idle, not inactive
                assert provider["status"] in ["active", "idle"]
                assert provider["status"] != "inactive"

    # Integration Tests
    def test_multiple_provider_toggles(self, test_client: TestClient, admin_token: str, sample_providers, db_session: Session):
        """Test toggling multiple providers in sequence."""
        # Initial state: both providers enabled
        response = test_client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        enabled_count = sum(1 for p in data["providers"] if p["isEnabled"])
        assert enabled_count == 2

        # Disable yfinance
        response = test_client.patch(
            "/api/v1/admin/market-data/providers/yfinance/toggle",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json()["isEnabled"] is False

        # Disable alpha_vantage
        response = test_client.patch(
            "/api/v1/admin/market-data/providers/alpha_vantage/toggle",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json()["isEnabled"] is False

        # Verify both are disabled
        response = test_client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        enabled_count = sum(1 for p in data["providers"] if p["isEnabled"])
        assert enabled_count == 0

        # Re-enable yfinance
        response = test_client.patch(
            "/api/v1/admin/market-data/providers/yfinance/toggle",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json()["isEnabled"] is True

        # Verify only one is enabled
        response = test_client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        enabled_count = sum(1 for p in data["providers"] if p["isEnabled"])
        assert enabled_count == 1

    def test_provider_toggle_response_format(self, test_client: TestClient, admin_token: str, sample_providers):
        """Test that provider toggle response has correct format."""
        response = test_client.patch(
            "/api/v1/admin/market-data/providers/yfinance/toggle",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify required fields are present
        required_fields = ["providerId", "providerName", "isEnabled", "message"]
        for field in required_fields:
            assert field in data

        # Verify field types
        assert isinstance(data["providerId"], str)
        assert isinstance(data["providerName"], str)
        assert isinstance(data["isEnabled"], bool)
        assert isinstance(data["message"], str)

    # Polling Logic Tests (placeholder for future implementation)
    def test_disabled_provider_bypassed_in_polling(self, db_session: Session):
        """Test that disabled providers are bypassed during polling updates."""
        # This test will verify that when polling for market data updates,
        # disabled providers are skipped entirely

        # TODO: This test will be implemented when we add the actual polling logic
        # For now, we'll test the database state that polling would check

        # Create disabled provider
        disabled_provider = MarketDataProvider(
            name="test_disabled",
            display_name="Test Disabled Provider",
            is_enabled=False,
            api_key="test_key",
            base_url="https://test.com",
            rate_limit_per_minute=60,
            rate_limit_per_day=1000,
            priority=3
        )
        db_session.add(disabled_provider)
        db_session.commit()

        # Query for enabled providers (what polling logic would do)
        enabled_providers = db_session.query(MarketDataProvider).filter(
            MarketDataProvider.is_enabled == True
        ).all()

        # Verify disabled provider is not included
        provider_names = [p.name for p in enabled_providers]
        assert "test_disabled" not in provider_names

        # Clean up
        db_session.delete(disabled_provider)
        db_session.commit()

    def test_provider_toggle_idempotency(self, test_client: TestClient, admin_token: str, sample_providers, db_session: Session):
        """Test that toggling a provider multiple times works correctly."""
        # Get initial state
        yfinance = db_session.query(MarketDataProvider).filter(MarketDataProvider.name == "yfinance").first()
        initial_state = yfinance.is_enabled

        # Toggle twice (should return to original state)
        response1 = test_client.patch(
            "/api/v1/admin/market-data/providers/yfinance/toggle",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response1.status_code == 200
        first_toggle_state = response1.json()["isEnabled"]
        assert first_toggle_state != initial_state

        response2 = test_client.patch(
            "/api/v1/admin/market-data/providers/yfinance/toggle",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response2.status_code == 200
        second_toggle_state = response2.json()["isEnabled"]
        assert second_toggle_state == initial_state

        # Verify database state
        db_session.refresh(yfinance)
        assert yfinance.is_enabled == initial_state
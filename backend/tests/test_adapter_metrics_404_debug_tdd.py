"""
TDD test to debug the 404 adapter not found issue.

This test will systematically verify each step of the adapter metrics lookup
to identify exactly where the failure is occurring.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import UUID, uuid4

from src.models.provider_configuration import ProviderConfiguration
from src.models.user import User, UserRole
from src.services.adapter_metrics_service import AdapterMetricsService
from tests.conftest import TestingSessionLocal


class TestAdapterMetrics404Debug:
    """TDD tests to debug the 404 adapter not found issue."""

    def test_adapter_exists_in_database(self, client: TestClient, db: Session, admin_user: User):
        """
        TDD test to verify the adapter exists in the database with correct format.
        """
        # Step 1: Create test adapter with known UUID (use UUID object)
        test_adapter_id = UUID("550e8400-e29b-41d4-a716-446655440001")  # UUID object
        test_adapter = ProviderConfiguration(
            id=test_adapter_id,
            provider_name="yfinance",
            display_name="Test Yahoo Finance",
            config_data={"api_key": "test_key"},
            is_active=True,
            created_by_user_id=admin_user.id
        )
        db.add(test_adapter)
        db.commit()
        db.refresh(test_adapter)

        # Verify the adapter was stored correctly
        stored_adapter = db.query(ProviderConfiguration).filter(
            ProviderConfiguration.id == test_adapter_id
        ).first()

        assert stored_adapter is not None, "Adapter should exist in database"
        assert stored_adapter.id == test_adapter_id, f"Expected {test_adapter_id}, got {stored_adapter.id}"
        assert stored_adapter.provider_name == "yfinance", f"Expected yfinance, got {stored_adapter.provider_name}"

        print(f"✅ Adapter exists in DB with ID: {stored_adapter.id} (type: {type(stored_adapter.id)})")

    def test_uuid_conversion_logic(self, client: TestClient, db: Session, admin_user: User):
        """
        TDD test to verify UUID conversion logic works correctly.
        """
        # Step 1: Create test adapter
        test_uuid_32 = "550e8400e29b41d4a716446655440001"
        test_adapter = ProviderConfiguration(
            id=test_uuid_32,
            provider_name="yfinance",
            display_name="Test Yahoo Finance",
            config_data={"api_key": "test_key"},
            is_active=True,
            created_by_user_id=admin_user.id
        )
        db.add(test_adapter)
        db.commit()

        # Step 2: Test UUID conversion with hyphens (what frontend sends)
        frontend_uuid = "550e8400-e29b-41d4-a716-446655440001"  # 36 chars with hyphens

        # Test the conversion logic that the service uses
        normalized_uuid = str(frontend_uuid).replace('-', '')

        assert normalized_uuid == test_uuid_32, f"UUID normalization failed: {normalized_uuid} != {test_uuid_32}"

        # Test database query with normalized UUID
        found_adapter = db.query(ProviderConfiguration).filter(
            ProviderConfiguration.id == normalized_uuid
        ).first()

        assert found_adapter is not None, f"Adapter not found with normalized UUID: {normalized_uuid}"

        print(f"✅ UUID conversion working: {frontend_uuid} -> {normalized_uuid}")

    async def test_adapter_metrics_service_lookup(self, client: TestClient, db: Session, admin_user: User):
        """
        TDD test to verify the adapter metrics service can find the adapter.
        """
        # Step 1: Create test adapter
        test_uuid_32 = "550e8400e29b41d4a716446655440001"
        test_adapter = ProviderConfiguration(
            id=test_uuid_32,
            provider_name="yfinance",
            display_name="Test Yahoo Finance",
            config_data={"api_key": "test_key"},
            is_active=True,
            created_by_user_id=admin_user.id
        )
        db.add(test_adapter)
        db.commit()

        # Step 2: Test the adapter metrics service directly
        metrics_service = AdapterMetricsService(db)

        # Test with frontend UUID format (with hyphens)
        frontend_uuid = "550e8400-e29b-41d4-a716-446655440001"

        # This should find the adapter using the service's UUID normalization
        try:
            result = await metrics_service.get_adapter_metrics(frontend_uuid)

            # If we get here, the service found the adapter
            assert result is not None, "Service should return metrics data"
            assert result.get("adapter_id") is not None, "Result should contain adapter_id"

            print(f"✅ Service found adapter: {result.get('adapter_id')}")

        except Exception as e:
            # If we get an error, let's see what it is
            pytest.fail(f"Service failed to find adapter: {e}")

    def test_api_endpoint_with_auth(self, client: TestClient, db: Session, admin_user: User):
        """
        TDD test to verify the full API endpoint works with proper authentication.
        """
        # Step 1: Create test adapter
        test_uuid_32 = "550e8400e29b41d4a716446655440001"
        test_adapter = ProviderConfiguration(
            id=test_uuid_32,
            provider_name="yfinance",
            display_name="Test Yahoo Finance",
            config_data={"api_key": "test_key"},
            is_active=True,
            created_by_user_id=admin_user.id
        )
        db.add(test_adapter)
        db.commit()

        # Step 2: Get admin access token
        login_response = client.post("/api/v1/auth/login", json={
            "email": admin_user.email,
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json()["access_token"]

        # Step 3: Test the API endpoint with frontend UUID format
        frontend_uuid = "550e8400-e29b-41d4-a716-446655440001"

        response = client.get(
            f"/api/v1/admin/adapters/{frontend_uuid}/metrics",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Debug the response
        print(f"API Response Status: {response.status_code}")
        print(f"API Response Body: {response.text}")

        # The goal is to NOT get a 404 - any other status indicates progress
        if response.status_code == 404:
            pytest.fail(f"Still getting 404: {response.text}")
        elif response.status_code == 500:
            # A 500 error shows us what's actually failing
            print(f"Service error (shows what's broken): {response.text}")
        else:
            print(f"✅ Progress! Got status {response.status_code} instead of 404")


# Fixtures
@pytest.fixture
def db():
    """Create test database session."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def admin_user(db: Session):
    """Create admin user for testing."""
    # Use a UUID object (not string) for proper database compatibility
    admin_user_id = UUID("550e8400-e29b-41d4-a716-446655440000")  # UUID object
    user = User(
        id=admin_user_id,
        email="admin@test.com",
        password_hash="$2b$12$mHX8MCxLQ.paQr1VTYAKI.DJ0lE5u.EEVimyOVSBtstV0xuP32v5i",  # admin123
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
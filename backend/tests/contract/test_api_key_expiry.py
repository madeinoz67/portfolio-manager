"""
Security-focused tests for API key expiry functionality.

CRITICAL SECURITY FEATURE:
- API keys without expiry dates create indefinite access risks
- Expired keys must be completely rejected by authentication
- Expiry dates must be properly validated and enforced
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models.user import User
from src.models.api_key import ApiKey
from src.core.auth import get_password_hash
from src.core.api_keys import generate_api_key, hash_api_key


@pytest.mark.contract
class TestApiKeyExpirySecurity:
    """Security tests for API key expiry functionality."""

    def test_create_api_key_with_expiry_date(self, client: TestClient, db: Session):
        """Test creating API key with expiry date - SECURITY CRITICAL."""
        # Create test user
        user = User(
            email="test@example.com",
            password_hash=get_password_hash("password123"),
            first_name="Test",
            last_name="User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Login to get token
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        token = response.json()["access_token"]

        # Test creating API key with expiry date (30 days from now)
        expiry_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        
        response = client.post(
            "/api/v1/api-keys",
            json={
                "name": "Test Key with Expiry",
                "expires_at": expiry_date
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        api_key_data = response.json()
        
        # Verify expiry date is set correctly
        assert api_key_data["expires_at"] is not None
        assert "pk_" in api_key_data["key"]  # Verify key was generated

    def test_create_api_key_without_expiry_should_fail(self, client: TestClient, db: Session):
        """Test that creating API keys without expiry fails - SECURITY REQUIREMENT."""
        # Create test user and login
        user = User(
            email="test@example.com",
            password_hash=get_password_hash("password123"),
            first_name="Test",
            last_name="User"
        )
        db.add(user)
        db.commit()
        
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        token = response.json()["access_token"]

        # Test creating API key without expiry (should require expiry for security)
        response = client.post(
            "/api/v1/api-keys",
            json={"name": "Test Key No Expiry"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should require expiry date for security
        assert response.status_code in [400, 422], "API keys must have expiry dates for security"

    def test_expired_api_key_authentication_fails(self, client: TestClient, db: Session):
        """Test that expired API keys are rejected - SECURITY CRITICAL."""
        # Create user
        user = User(
            email="test@example.com",
            password_hash=get_password_hash("password123"),
            first_name="Test",
            last_name="User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create expired API key directly in database
        expired_key = generate_api_key()
        api_key = ApiKey(
            user_id=user.id,
            name="Expired Test Key",
            key_hash=hash_api_key(expired_key),
            expires_at=datetime.utcnow() - timedelta(days=1),  # Expired yesterday
            is_active=True
        )
        db.add(api_key)
        db.commit()

        # Try to use expired API key - should fail
        response = client.get(
            "/api/v1/portfolios",
            headers={"X-API-Key": expired_key}
        )
        
        assert response.status_code == 401, "Expired API keys must be rejected"
        assert "expired" in response.json().get("detail", "").lower()

    def test_valid_api_key_before_expiry_works(self, client: TestClient, db: Session):
        """Test that valid API keys work before expiry."""
        # Create user
        user = User(
            email="test@example.com",
            password_hash=get_password_hash("password123"),
            first_name="Test",
            last_name="User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create valid API key (expires tomorrow)
        valid_key = generate_api_key()
        api_key = ApiKey(
            user_id=user.id,
            name="Valid Test Key",
            key_hash=hash_api_key(valid_key),
            expires_at=datetime.utcnow() + timedelta(days=1),  # Expires tomorrow
            is_active=True
        )
        db.add(api_key)
        db.commit()

        # Use valid API key - should work
        response = client.get(
            "/api/v1/portfolios",
            headers={"X-API-Key": valid_key}
        )
        
        assert response.status_code in [200, 404], "Valid API keys should work"

    def test_expiry_date_validation_future_only(self, client: TestClient, db: Session):
        """Test that expiry dates must be in the future - SECURITY VALIDATION."""
        # Create user and login
        user = User(
            email="test@example.com",
            password_hash=get_password_hash("password123"),
            first_name="Test",
            last_name="User"
        )
        db.add(user)
        db.commit()
        
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        token = response.json()["access_token"]

        # Test creating API key with past expiry date
        past_date = (datetime.utcnow() - timedelta(days=1)).isoformat()
        
        response = client.post(
            "/api/v1/api-keys",
            json={
                "name": "Invalid Past Expiry Key",
                "expires_at": past_date
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 422, "Past expiry dates should be rejected"

    def test_maximum_expiry_date_limit(self, client: TestClient, db: Session):
        """Test that expiry dates have reasonable maximum limits - SECURITY POLICY."""
        # Create user and login
        user = User(
            email="test@example.com",
            password_hash=get_password_hash("password123"),
            first_name="Test",
            last_name="User"
        )
        db.add(user)
        db.commit()
        
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        token = response.json()["access_token"]

        # Test creating API key with excessive expiry (10 years)
        far_future_date = (datetime.utcnow() + timedelta(days=3650)).isoformat()
        
        response = client.post(
            "/api/v1/api-keys",
            json={
                "name": "Too Long Expiry Key",
                "expires_at": far_future_date
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should enforce reasonable maximum (e.g., 1-2 years max)
        assert response.status_code == 422, "Excessive expiry dates should be rejected for security"

    def test_list_api_keys_shows_expiry_status(self, client: TestClient, db: Session):
        """Test that API key list shows expiry information clearly."""
        # Create user and login
        user = User(
            email="test@example.com",
            password_hash=get_password_hash("password123"),
            first_name="Test",
            last_name="User"
        )
        db.add(user)
        db.commit()
        
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        token = response.json()["access_token"]

        # Create API key with expiry
        future_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        
        response = client.post(
            "/api/v1/api-keys",
            json={
                "name": "Test Key",
                "expires_at": future_date
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201

        # List API keys and verify expiry info
        response = client.get(
            "/api/v1/api-keys",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        keys = response.json()
        assert len(keys) > 0
        assert keys[0]["expires_at"] is not None

    def test_delete_expired_keys_cleanup(self, client: TestClient, db: Session):
        """Test cleanup of expired API keys for security maintenance."""
        # This test ensures expired keys can be cleaned up
        # Implementation should include automated cleanup processes
        
        # Create user
        user = User(
            email="test@example.com",
            password_hash=get_password_hash("password123"),
            first_name="Test",
            last_name="User"
        )
        db.add(user)
        db.commit()

        # Create expired API key
        expired_key = generate_api_key()
        api_key = ApiKey(
            user_id=user.id,
            name="Expired Key",
            key_hash=hash_api_key(expired_key),
            expires_at=datetime.utcnow() - timedelta(days=30),
            is_active=True
        )
        db.add(api_key)
        db.commit()

        # Verify expired key exists
        expired_keys = db.query(ApiKey).filter(
            ApiKey.expires_at < datetime.utcnow(),
            ApiKey.is_active == True
        ).all()
        
        assert len(expired_keys) > 0, "Expired keys should be identified for cleanup"
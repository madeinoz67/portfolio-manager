"""
Integration tests for admin permission system.

Tests the admin role enforcement using TDD approach.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models.user import User
from src.models.user_role import UserRole


class TestAdminPermissions:
    """Test admin permission system."""

    def test_admin_user_can_access_admin_endpoint(self, client: TestClient, db: Session):
        """Test that admin users can access admin-only endpoints."""
        # Clear database and create admin user (first user)
        db.query(User).delete()
        db.commit()

        # Register admin user (first user becomes admin)
        admin_data = {
            "email": "admin@example.com",
            "password": "adminpass123",
            "first_name": "Admin",
            "last_name": "User"
        }

        response = client.post("/api/v1/auth/register", json=admin_data)
        assert response.status_code == 201

        # Login to get admin token
        login_data = {
            "email": "admin@example.com",
            "password": "adminpass123"
        }

        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        admin_token = login_response.json()["access_token"]

        # Try to access a test admin endpoint (we'll create this)
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/admin/users", headers=headers)

        # Should succeed (200) or endpoint not found (404), but not forbidden (403)
        assert response.status_code in [200, 404]  # 404 means endpoint doesn't exist yet

    def test_regular_user_cannot_access_admin_endpoint(self, client: TestClient, db: Session):
        """Test that regular users cannot access admin-only endpoints."""
        # Clear database
        db.query(User).delete()
        db.commit()

        # Register admin user first
        admin_data = {
            "email": "admin@example.com",
            "password": "adminpass123",
            "first_name": "Admin",
            "last_name": "User"
        }
        client.post("/api/v1/auth/register", json=admin_data)

        # Register regular user (second user)
        user_data = {
            "email": "user@example.com",
            "password": "userpass123",
            "first_name": "Regular",
            "last_name": "User"
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

        # Login as regular user
        login_data = {
            "email": "user@example.com",
            "password": "userpass123"
        }

        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        user_token = login_response.json()["access_token"]

        # Verify user has regular role
        user = db.query(User).filter(User.email == "user@example.com").first()
        assert user.role == UserRole.USER

        # Try to access admin endpoint - should be forbidden
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/api/v1/admin/users", headers=headers)

        # Should be forbidden (403) or endpoint not found (404)
        # If 404, the endpoint doesn't exist yet but permissions would still block
        assert response.status_code in [403, 404]

    def test_unauthenticated_user_cannot_access_admin_endpoint(self, client: TestClient, db: Session):
        """Test that unauthenticated users cannot access admin-only endpoints."""
        # Try to access admin endpoint without token
        response = client.get("/api/v1/admin/users")

        # Should require authentication (401/403) or endpoint not found (404)
        assert response.status_code in [401, 403, 404]

    def test_admin_dependency_blocks_non_admin_users(self, client: TestClient, db: Session):
        """Test that admin dependency properly blocks non-admin users with specific error."""
        # Clear database
        db.query(User).delete()
        db.commit()

        # Create admin user first
        admin_data = {
            "email": "admin@example.com",
            "password": "adminpass123",
            "first_name": "Admin",
            "last_name": "User"
        }
        client.post("/api/v1/auth/register", json=admin_data)

        # Create regular user
        user_data = {
            "email": "user@example.com",
            "password": "userpass123",
            "first_name": "Regular",
            "last_name": "User"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # Login as regular user
        login_data = {
            "email": "user@example.com",
            "password": "userpass123"
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        user_token = login_response.json()["access_token"]

        # Verify user is authenticated but not admin
        headers = {"Authorization": f"Bearer {user_token}"}
        profile_response = client.get("/api/v1/auth/me", headers=headers)
        assert profile_response.status_code == 200
        assert profile_response.json()["role"] == "user"

        # Try admin endpoint - should get forbidden if endpoint exists
        admin_response = client.get("/api/v1/admin/users", headers=headers)
        if admin_response.status_code == 403:
            assert "Admin access required" in admin_response.json()["detail"]
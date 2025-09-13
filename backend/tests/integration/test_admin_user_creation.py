"""
Integration tests for admin user creation logic.

Tests the "first user becomes admin" business rule using TDD approach.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models.user import User
from src.models.user_role import UserRole
from src.core.auth import verify_password


class TestAdminUserCreation:
    """Test admin user creation logic."""

    def test_first_user_registration_gets_admin_role(self, client: TestClient, db: Session):
        """Test that the very first user to register gets admin role."""
        # Ensure database is completely empty of users
        db.query(User).delete()
        db.commit()

        # Register first user
        user_data = {
            "email": "first@example.com",
            "password": "firstpass123",
            "first_name": "First",
            "last_name": "User"
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        response_data = response.json()
        assert response_data["email"] == "first@example.com"

        # Check that user was created with admin role
        user = db.query(User).filter(User.email == "first@example.com").first()
        assert user is not None
        assert user.role == UserRole.ADMIN
        assert user.first_name == "First"
        assert user.last_name == "User"
        assert verify_password("firstpass123", user.password_hash)

    def test_second_user_registration_gets_user_role(self, client: TestClient, db: Session):
        """Test that subsequent users get standard user role."""
        # Ensure database is empty
        db.query(User).delete()
        db.commit()

        # Register first user (should be admin)
        first_user_data = {
            "email": "admin@example.com",
            "password": "adminpass123",
            "first_name": "Admin",
            "last_name": "User"
        }

        response = client.post("/api/v1/auth/register", json=first_user_data)
        assert response.status_code == 201

        # Register second user (should be regular user)
        second_user_data = {
            "email": "user@example.com",
            "password": "userpass123",
            "first_name": "Regular",
            "last_name": "User"
        }

        response = client.post("/api/v1/auth/register", json=second_user_data)
        if response.status_code != 201:
            print(f"Second user registration failed with status {response.status_code}: {response.json()}")
        assert response.status_code == 201

        # Check roles
        admin_user = db.query(User).filter(User.email == "admin@example.com").first()
        regular_user = db.query(User).filter(User.email == "user@example.com").first()

        assert admin_user.role == UserRole.ADMIN
        assert regular_user.role == UserRole.USER

    def test_multiple_users_only_first_is_admin(self, client: TestClient, db: Session):
        """Test that only the first user becomes admin, all others are regular users."""
        # Ensure database is empty
        db.query(User).delete()
        db.commit()

        users_data = [
            {
                "email": "first@example.com",
                "password": "firstpass123",
                "first_name": "First",
                "last_name": "User"
            },
            {
                "email": "second@example.com",
                "password": "secondpass123",
                "first_name": "Second",
                "last_name": "User"
            },
            {
                "email": "third@example.com",
                "password": "thirdpass123",
                "first_name": "Third",
                "last_name": "User"
            }
        ]

        # Register all users
        for user_data in users_data:
            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == 201

        # Check that only first user is admin
        first_user = db.query(User).filter(User.email == "first@example.com").first()
        second_user = db.query(User).filter(User.email == "second@example.com").first()
        third_user = db.query(User).filter(User.email == "third@example.com").first()

        assert first_user.role == UserRole.ADMIN
        assert second_user.role == UserRole.USER
        assert third_user.role == UserRole.USER

        # Verify there's exactly one admin
        admin_count = db.query(User).filter(User.role == UserRole.ADMIN).count()
        assert admin_count == 1

        # Verify we have two regular users
        user_count = db.query(User).filter(User.role == UserRole.USER).count()
        assert user_count == 2

    def test_admin_user_can_login_successfully(self, client: TestClient, db: Session):
        """Test that admin user can login and gets proper JWT token."""
        # Ensure database is empty
        db.query(User).delete()
        db.commit()

        # Register admin user (first user)
        user_data = {
            "email": "admin@example.com",
            "password": "adminpass123",
            "first_name": "Admin",
            "last_name": "User"
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

        # Login as admin
        login_data = {
            "email": "admin@example.com",
            "password": "adminpass123"
        }

        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200

        response_data = response.json()
        assert "access_token" in response_data
        assert response_data["token_type"] == "bearer"
        assert response_data["user"]["email"] == "admin@example.com"
        assert response_data["user"]["role"] == "admin"
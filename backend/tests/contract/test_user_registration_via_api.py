"""
TDD Test for User Registration via API
Tests the complete user registration flow via API endpoints.
"""

import pytest
import requests
from fastapi.testclient import TestClient

from src.main import app


class TestUserRegistrationAPI:
    """Test user registration via API calls."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_register_admin_user_via_api(self, client):
        """Test registering an admin user via API."""
        # Arrange
        user_data = {
            "email": "admin@example.com",
            "password": "admin123",
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin"
        }

        # Act
        response = client.post("/api/v1/auth/register", json=user_data)

        # Assert
        assert response.status_code == 201, f"Registration failed: {response.text}"

        response_data = response.json()
        assert "user" in response_data
        assert response_data["user"]["email"] == "admin@example.com"
        assert response_data["user"]["role"] == "admin"
        assert response_data["user"]["first_name"] == "Admin"
        assert response_data["user"]["last_name"] == "User"
        assert response_data["user"]["is_active"] == True

    def test_register_regular_user_via_api(self, client):
        """Test registering a regular user via API."""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "password": "test123",
            "first_name": "Test",
            "last_name": "User"
        }

        # Act
        response = client.post("/api/v1/auth/register", json=user_data)

        # Assert
        assert response.status_code == 201, f"Registration failed: {response.text}"

        response_data = response.json()
        assert "user" in response_data
        assert response_data["user"]["email"] == "test@example.com"
        assert response_data["user"]["role"] == "user"  # Should default to user
        assert response_data["user"]["first_name"] == "Test"
        assert response_data["user"]["last_name"] == "User"
        assert response_data["user"]["is_active"] == True

    def test_login_admin_user_via_api(self, client):
        """Test logging in as admin user."""
        # Arrange - First register admin
        user_data = {
            "email": "admin@example.com",
            "password": "admin123",
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # Act - Login
        login_data = {
            "email": "admin@example.com",
            "password": "admin123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200, f"Login failed: {response.text}"

        response_data = response.json()
        assert "access_token" in response_data
        assert "user" in response_data
        assert response_data["user"]["email"] == "admin@example.com"
        assert response_data["user"]["role"] == "admin"

    def test_login_regular_user_via_api(self, client):
        """Test logging in as regular user."""
        # Arrange - First register user
        user_data = {
            "email": "test@example.com",
            "password": "test123",
            "first_name": "Test",
            "last_name": "User"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # Act - Login
        login_data = {
            "email": "test@example.com",
            "password": "test123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200, f"Login failed: {response.text}"

        response_data = response.json()
        assert "access_token" in response_data
        assert "user" in response_data
        assert response_data["user"]["email"] == "test@example.com"
        assert response_data["user"]["role"] == "user"

    def test_duplicate_email_registration_fails(self, client):
        """Test that registering with duplicate email fails."""
        # Arrange - First registration
        user_data = {
            "email": "test@example.com",
            "password": "test123",
            "first_name": "Test",
            "last_name": "User"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # Act - Try to register with same email
        duplicate_data = {
            "email": "test@example.com",
            "password": "different123",
            "first_name": "Different",
            "last_name": "User"
        }
        response = client.post("/api/v1/auth/register", json=duplicate_data)

        # Assert
        assert response.status_code == 400, "Duplicate registration should fail"
        response_data = response.json()
        assert "email already registered" in response_data["error"]["message"].lower()

    def test_invalid_role_defaults_to_user(self, client):
        """Test that invalid role defaults to user."""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "password": "test123",
            "first_name": "Test",
            "last_name": "User",
            "role": "invalid_role"  # Invalid role
        }

        # Act
        response = client.post("/api/v1/auth/register", json=user_data)

        # Assert
        # This should either fail validation or default to user role
        if response.status_code == 201:
            response_data = response.json()
            assert response_data["user"]["role"] == "user"  # Should default
        else:
            # Or it should fail with validation error
            assert response.status_code == 422  # Validation error

    def test_missing_required_fields_fails(self, client):
        """Test that missing required fields fails registration."""
        # Arrange - Missing email
        user_data = {
            "password": "test123",
            "first_name": "Test",
            "last_name": "User"
        }

        # Act
        response = client.post("/api/v1/auth/register", json=user_data)

        # Assert
        assert response.status_code == 422  # Validation error

    def test_password_too_short_fails(self, client):
        """Test that short password fails registration."""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "password": "123",  # Too short
            "first_name": "Test",
            "last_name": "User"
        }

        # Act
        response = client.post("/api/v1/auth/register", json=user_data)

        # Assert - Should fail validation
        assert response.status_code in [400, 422]  # Either bad request or validation error
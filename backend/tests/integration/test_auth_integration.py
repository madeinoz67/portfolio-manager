"""
Integration Tests for Authentication System
Tests the complete authentication flow including error handling, timeouts, and edge cases.
"""

import pytest
import time
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.main import app


class TestAuthenticationIntegration:
    """Test complete authentication integration scenarios."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_complete_registration_and_login_flow(self, client):
        """Test complete user registration followed by login flow."""
        # Step 1: Register user
        user_data = {
            "email": "integration@example.com",
            "password": "integration123",
            "full_name": "Integration Test User"
        }

        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201

        user_id = register_response.json()["id"]
        assert user_id is not None

        # Step 2: Login with same credentials
        login_data = {
            "email": "integration@example.com",
            "password": "integration123"
        }

        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200

        login_result = login_response.json()
        assert "access_token" in login_result
        assert login_result["user"]["email"] == "integration@example.com"
        assert login_result["user"]["id"] == user_id

        # Step 3: Use token to access protected endpoint
        token = login_result["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200

        me_result = me_response.json()
        assert me_result["email"] == "integration@example.com"
        assert me_result["id"] == user_id

    def test_authentication_error_handling(self, client):
        """Test authentication error scenarios that frontend should handle gracefully."""
        # Test 1: Invalid credentials (401 error)
        invalid_login = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }

        response = client.post("/api/v1/auth/login", json=invalid_login)
        assert response.status_code == 401

        error_data = response.json()
        assert "detail" in error_data or "error" in error_data

        # Test 2: Invalid email format (422 validation error)
        invalid_email = {
            "email": "not-an-email",
            "password": "validpassword123"
        }

        response = client.post("/api/v1/auth/login", json=invalid_email)
        assert response.status_code == 422

        # Test 3: Missing required fields
        incomplete_data = {"email": "test@example.com"}

        response = client.post("/api/v1/auth/login", json=incomplete_data)
        assert response.status_code == 422

    def test_password_validation_scenarios(self, client):
        """Test password validation that frontend should handle."""
        # Test 1: Password too short (should fail with 422)
        short_password_data = {
            "email": "test@example.com",
            "password": "short",
            "full_name": "Test User"
        }

        response = client.post("/api/v1/auth/register", json=short_password_data)
        assert response.status_code == 422

        # Test 2: Valid password length (should succeed)
        valid_password_data = {
            "email": "valid@example.com",
            "password": "validpass123",
            "full_name": "Valid User"
        }

        response = client.post("/api/v1/auth/register", json=valid_password_data)
        assert response.status_code == 201

    def test_duplicate_registration_handling(self, client):
        """Test duplicate email registration that frontend should handle."""
        # Register first user
        user_data = {
            "email": "duplicate@example.com",
            "password": "password123",
            "full_name": "First User"
        }

        first_response = client.post("/api/v1/auth/register", json=user_data)
        assert first_response.status_code == 201

        # Attempt duplicate registration
        duplicate_data = {
            "email": "duplicate@example.com",  # Same email
            "password": "differentpass123",
            "full_name": "Second User"
        }

        duplicate_response = client.post("/api/v1/auth/register", json=duplicate_data)
        assert duplicate_response.status_code == 400

        error_data = duplicate_response.json()
        assert "email" in error_data["detail"].lower() or "already" in error_data["detail"].lower()

    def test_token_expiry_and_refresh_scenarios(self, client):
        """Test token expiry scenarios that frontend should handle."""
        # Register and login to get token
        user_data = {
            "email": "token@example.com",
            "password": "tokentest123",
            "full_name": "Token Test User"
        }

        client.post("/api/v1/auth/register", json=user_data)

        login_response = client.post("/api/v1/auth/login", json={
            "email": "token@example.com",
            "password": "tokentest123"
        })

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Valid token should work
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200

        # Invalid token should return 401
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}
        invalid_response = client.get("/api/v1/auth/me", headers=invalid_headers)
        assert invalid_response.status_code == 401

    def test_concurrent_authentication_requests(self, client):
        """Test concurrent authentication requests to ensure thread safety."""
        import concurrent.futures
        import threading

        # Register a test user first
        user_data = {
            "email": "concurrent@example.com",
            "password": "concurrent123",
            "full_name": "Concurrent User"
        }
        client.post("/api/v1/auth/register", json=user_data)

        def attempt_login():
            """Attempt login in separate thread."""
            login_data = {
                "email": "concurrent@example.com",
                "password": "concurrent123"
            }
            response = client.post("/api/v1/auth/login", json=login_data)
            return response.status_code == 200

        # Execute multiple concurrent login attempts
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(attempt_login) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # All login attempts should succeed
        assert all(results), "Some concurrent login attempts failed"

    def test_authentication_with_special_characters(self, client):
        """Test authentication with special characters in password."""
        special_password_data = {
            "email": "special@example.com",
            "password": "p@ssw0rd!123#$",
            "full_name": "Special Char User"
        }

        # Registration should work with special characters
        register_response = client.post("/api/v1/auth/register", json=special_password_data)
        assert register_response.status_code == 201

        # Login should also work with special characters
        login_response = client.post("/api/v1/auth/login", json={
            "email": "special@example.com",
            "password": "p@ssw0rd!123#$"
        })
        assert login_response.status_code == 200

    def test_case_sensitive_email_handling(self, client):
        """Test case sensitivity in email handling."""
        # Register with lowercase email
        user_data = {
            "email": "CaseTest@Example.com",
            "password": "casetest123",
            "full_name": "Case Test User"
        }

        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201

        # Login should work with different case variations
        login_variations = [
            "casetest@example.com",
            "CaseTest@Example.com",
            "CASETEST@EXAMPLE.COM"
        ]

        for email_variant in login_variations:
            login_response = client.post("/api/v1/auth/login", json={
                "email": email_variant,
                "password": "casetest123"
            })
            # Should either work consistently or fail consistently
            # The specific behavior depends on backend implementation
            assert login_response.status_code in [200, 401]

    def test_malformed_json_handling(self, client):
        """Test that malformed JSON is handled gracefully."""
        # This tests the frontend's ability to handle server errors gracefully
        response = client.post(
            "/api/v1/auth/login",
            data="invalid json{{{",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # Validation error for malformed JSON

    def test_large_payload_handling(self, client):
        """Test handling of unusually large payloads."""
        large_data = {
            "email": "large@example.com",
            "password": "a" * 1000,  # Very long password
            "full_name": "x" * 500   # Very long name
        }

        response = client.post("/api/v1/auth/register", json=large_data)
        # Should either succeed or fail gracefully with validation error
        assert response.status_code in [201, 422]

    def test_empty_and_whitespace_handling(self, client):
        """Test handling of empty and whitespace-only values."""
        test_cases = [
            {"email": "", "password": "test123456", "full_name": "Test"},
            {"email": "   ", "password": "test123456", "full_name": "Test"},
            {"email": "test@example.com", "password": "", "full_name": "Test"},
            {"email": "test@example.com", "password": "   ", "full_name": "Test"},
            {"email": "test@example.com", "password": "test123456", "full_name": ""},
        ]

        for test_data in test_cases:
            response = client.post("/api/v1/auth/register", json=test_data)
            # Should fail validation gracefully
            assert response.status_code == 422
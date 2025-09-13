"""
Integration tests for portfolio update functionality.
Tests the complete flow from API request to database update.
"""

import pytest
from fastapi.testclient import TestClient

from src.models import Portfolio
from src.core.auth import create_access_token
from tests.factories import create_test_user


def create_test_user_with_token(db, email="test@example.com"):
    """Helper function to create a test user and return user and auth token."""
    user = create_test_user(db, email=email)
    db.commit()
    token = create_access_token(data={"sub": user.email})
    return user, token


@pytest.mark.integration
class TestPortfolioUpdate:
    """Test portfolio update integration."""

    def test_update_portfolio_name_and_description(self, client: TestClient, db):
        """Test updating both portfolio name and description."""
        # Setup: Create user and portfolio
        user, token = create_test_user_with_token(db)
        
        # Create initial portfolio
        create_data = {
            "name": "Original Portfolio",
            "description": "Original description"
        }
        
        create_response = client.post(
            "/api/v1/portfolios",
            json=create_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert create_response.status_code == 201
        portfolio = create_response.json()
        portfolio_id = portfolio["id"]
        
        # Test: Update the portfolio
        update_data = {
            "name": "Updated Portfolio Name",
            "description": "Updated portfolio description"
        }
        
        response = client.put(
            f"/api/v1/portfolios/{portfolio_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Verify API response
        assert response.status_code == 200
        updated_portfolio = response.json()
        assert updated_portfolio["name"] == "Updated Portfolio Name"
        assert updated_portfolio["description"] == "Updated portfolio description"
        assert updated_portfolio["id"] == portfolio_id
        
        # Verify database was updated
        db_portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        assert db_portfolio is not None
        assert db_portfolio.name == "Updated Portfolio Name"
        assert db_portfolio.description == "Updated portfolio description"

    def test_update_portfolio_name_only(self, client: TestClient, db):
        """Test updating only the portfolio name."""
        # Setup: Create user and portfolio
        user, token = create_test_user_with_token(db)
        
        # Create initial portfolio
        create_data = {
            "name": "Original Portfolio",
            "description": "Original description"
        }
        
        create_response = client.post(
            "/api/v1/portfolios",
            json=create_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert create_response.status_code == 201
        portfolio = create_response.json()
        portfolio_id = portfolio["id"]
        
        # Test: Update only the name
        update_data = {
            "name": "New Name Only"
        }
        
        response = client.put(
            f"/api/v1/portfolios/{portfolio_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Verify API response
        assert response.status_code == 200
        updated_portfolio = response.json()
        assert updated_portfolio["name"] == "New Name Only"
        assert updated_portfolio["description"] == "Original description"  # Should remain unchanged
        assert updated_portfolio["id"] == portfolio_id

    def test_update_portfolio_description_only(self, client: TestClient, db):
        """Test updating only the portfolio description."""
        # Setup: Create user and portfolio
        user, token = create_test_user_with_token(db)
        
        # Create initial portfolio
        create_data = {
            "name": "Original Portfolio",
            "description": "Original description"
        }
        
        create_response = client.post(
            "/api/v1/portfolios",
            json=create_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert create_response.status_code == 201
        portfolio = create_response.json()
        portfolio_id = portfolio["id"]
        
        # Test: Update only the description
        update_data = {
            "description": "New description only"
        }
        
        response = client.put(
            f"/api/v1/portfolios/{portfolio_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Verify API response
        assert response.status_code == 200
        updated_portfolio = response.json()
        assert updated_portfolio["name"] == "Original Portfolio"  # Should remain unchanged
        assert updated_portfolio["description"] == "New description only"
        assert updated_portfolio["id"] == portfolio_id

    def test_update_portfolio_validation_error(self, client: TestClient, db):
        """Test that invalid update data returns validation error."""
        # Setup: Create user and portfolio
        user, token = create_test_user_with_token(db)
        
        # Create initial portfolio
        create_data = {
            "name": "Original Portfolio",
            "description": "Original description"
        }
        
        create_response = client.post(
            "/api/v1/portfolios",
            json=create_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert create_response.status_code == 201
        portfolio = create_response.json()
        portfolio_id = portfolio["id"]
        
        # Test: Try to update with invalid data (name too long)
        update_data = {
            "name": "x" * 101,  # Exceeds max length of 100
            "description": "Valid description"
        }
        
        response = client.put(
            f"/api/v1/portfolios/{portfolio_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Verify validation error
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data

    def test_update_portfolio_not_found(self, client: TestClient, db):
        """Test updating a non-existent portfolio returns 404."""
        # Setup: Create user and token
        user, token = create_test_user_with_token(db)
        
        # Test: Try to update non-existent portfolio
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_data = {
            "name": "New Name",
            "description": "New description"
        }
        
        response = client.put(
            f"/api/v1/portfolios/{fake_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Verify 404 error
        assert response.status_code == 404
        error_data = response.json()
        assert error_data["detail"] == "Portfolio not found"

    def test_update_portfolio_unauthorized(self, client: TestClient, db):
        """Test updating portfolio without authentication returns 401."""
        # Test: Try to update without token
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_data = {
            "name": "New Name",
            "description": "New description"
        }
        
        response = client.put(
            f"/api/v1/portfolios/{fake_id}",
            json=update_data
        )
        
        # Verify 401 error
        assert response.status_code == 401

    def test_update_portfolio_different_owner(self, client: TestClient, db):
        """Test that user cannot update another user's portfolio."""
        # Setup: Create first user and portfolio
        user1, token1 = create_test_user_with_token(db, email="user1@test.com")
        
        create_data = {
            "name": "User 1 Portfolio",
            "description": "Belongs to user 1"
        }
        
        create_response = client.post(
            "/api/v1/portfolios",
            json=create_data,
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert create_response.status_code == 201
        portfolio = create_response.json()
        portfolio_id = portfolio["id"]
        
        # Setup: Create second user
        user2, token2 = create_test_user_with_token(db, email="user2@test.com")
        
        # Test: Try to update user1's portfolio as user2
        update_data = {
            "name": "Hacked Portfolio",
            "description": "Should not work"
        }
        
        response = client.put(
            f"/api/v1/portfolios/{portfolio_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token2}"}
        )
        
        # Verify 404 error (portfolio not found for user2)
        assert response.status_code == 404
        error_data = response.json()
        assert error_data["detail"] == "Portfolio not found"
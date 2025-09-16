"""
Test for portfolio value calculation bug.
Reproduces the issue where portfolios with no holdings show incorrect values.
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import Portfolio, User
from src.services.dynamic_portfolio_service import DynamicPortfolioService


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    user = User(
        email="testuser@example.com",
        password_hash="$2b$12$dummy.hash.value",
        first_name="Test",
        last_name="User"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def empty_portfolio(db: Session, test_user: User):
    """Create an empty portfolio with incorrect stored value."""
    portfolio = Portfolio(
        name="test",
        description="Test portfolio with no holdings",
        owner_id=test_user.id,
        total_value=Decimal("496.00"),  # This should be 0.00 since no holdings
        daily_change=Decimal("0.00"),
        daily_change_percent=Decimal("0.00")
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


class TestPortfolioValueBug:
    """Test portfolio value calculation bug reproduction."""

    def test_empty_portfolio_shows_correct_value_in_service(self, db: Session, empty_portfolio: Portfolio):
        """Dynamic portfolio service should calculate 0.00 for empty portfolio."""
        service = DynamicPortfolioService(db)
        portfolio_value = service.calculate_portfolio_value(empty_portfolio.id)

        # Should calculate 0.00 for empty portfolio
        assert portfolio_value.total_value == Decimal("0.00")
        assert portfolio_value.total_cost_basis == Decimal("0.00")
        assert portfolio_value.total_unrealized_gain == Decimal("0.00")
        assert portfolio_value.total_gain_percent == Decimal("0.00")

    def test_empty_portfolio_shows_correct_value_in_dynamic_service(self, db: Session, empty_portfolio: Portfolio):
        """Dynamic portfolio service get_dynamic_portfolio should return 0.00 for empty portfolio."""
        service = DynamicPortfolioService(db)
        portfolio_response = service.get_dynamic_portfolio(empty_portfolio.id)

        # Should calculate 0.00 for empty portfolio
        assert portfolio_response.total_value == Decimal("0.00")
        assert portfolio_response.daily_change == Decimal("0.00")
        assert portfolio_response.daily_change_percent == Decimal("0.00")

    def test_empty_portfolio_api_returns_static_incorrect_value(self, db: Session, empty_portfolio: Portfolio, test_user: User, client: TestClient):
        """Current API returns static values from database instead of calculated values."""
        from src.core.auth import create_access_token

        # Create token for our test user
        token = create_access_token(data={"sub": test_user.email})
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(f"/api/v1/portfolios/{empty_portfolio.id}", headers=headers)
        assert response.status_code == 200

        data = response.json()

        # Fixed: API should now return calculated value (0.00) instead of static DB value (496.00)
        assert data["total_value"] == "0.00", "API should return calculated value for empty portfolio"

    def test_list_portfolios_api_returns_static_incorrect_values(self, db: Session, empty_portfolio: Portfolio, test_user: User, client: TestClient):
        """List portfolios API also returns static values instead of calculated values."""
        from src.core.auth import create_access_token

        # Create token for our test user
        token = create_access_token(data={"sub": test_user.email})
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/v1/portfolios", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data) >= 1

        # Find our test portfolio
        test_portfolio = next((p for p in data if p["id"] == str(empty_portfolio.id)), None)
        assert test_portfolio is not None

        # Fixed: API should now return calculated value (0.00) instead of static DB value (496.00)
        assert test_portfolio["total_value"] == "0.00", "API should return calculated value for empty portfolio"
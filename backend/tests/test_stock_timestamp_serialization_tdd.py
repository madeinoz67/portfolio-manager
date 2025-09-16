"""
TDD tests for stock timestamp serialization consistency.

This test ensures that stock timestamps are serialized consistently
with market data timestamps to prevent frontend timezone issues.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.models.stock import Stock
from src.models.portfolio import Portfolio
from src.models.holding import Holding
from src.models.user import User
from src.utils.datetime_utils import now, to_iso_string


def test_stock_timestamp_serialization_matches_market_data_format(
    db_session: Session,
    test_data
):
    """
    Test that stock.last_price_update is serialized in the same format
    as market data API's fetched_at field for frontend consistency.

    REQUIREMENT:
    Both timestamps should use to_iso_string() format with 'Z' suffix
    for proper JavaScript Date parsing and timezone handling.
    """
    client = TestClient(app)

    # Create a stock with a known timestamp
    test_timestamp = now()  # UTC timestamp from datetime_utils

    stock = Stock(
        symbol="TEST",
        company_name="Test Company",
        exchange="ASX",
        current_price=100.50,
        last_price_update=test_timestamp
    )
    db_session.add(stock)
    db_session.commit()
    db_session.refresh(stock)

    # Create portfolio and holding to test holdings API
    portfolio = Portfolio(
        name="Test Portfolio",
        owner_id=test_data.user.id
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)

    holding = Holding(
        portfolio_id=portfolio.id,
        stock_id=stock.id,
        quantity=100,
        average_cost=95.00,
        current_value=10050.00,
        unrealized_gain_loss=550.00,
        unrealized_gain_loss_percent=5.79
    )
    db_session.add(holding)
    db_session.commit()

    # Test holdings API response (this is where the issue occurs)
    response = client.get(
        f"/api/v1/portfolios/{portfolio.id}/holdings",
        headers={"Authorization": f"Bearer {test_data.access_token}"}
    )

    assert response.status_code == 200
    holdings_data = response.json()

    # Extract the timestamp from holdings response
    assert len(holdings_data) == 1
    stock_data = holdings_data[0]["stock"]
    holdings_timestamp = stock_data["last_price_update"]

    # Compare with market data API format (this should be our target format)
    expected_format = to_iso_string(test_timestamp)

    # EXPECTED TO FAIL: Currently holdings API doesn't use to_iso_string()
    # This should pass after we fix the serialization
    assert holdings_timestamp == expected_format, (
        f"Holdings timestamp '{holdings_timestamp}' should match "
        f"market data format '{expected_format}'"
    )

    # Verify the timestamp can be parsed by JavaScript Date constructor
    # (this is the real-world requirement)
    assert holdings_timestamp.endswith('Z'), (
        "Timestamp should end with 'Z' for proper JavaScript parsing"
    )

    # Additional validation: ensure no '+00:00Z' format
    assert '+00:00Z' not in holdings_timestamp, (
        "Should not have invalid '+00:00Z' format that breaks JavaScript"
    )


def test_market_data_timestamp_format_baseline(
    db_session: Session,
    test_data
):
    """
    Baseline test to verify market data API timestamp format.
    This documents the expected format that holdings should match.
    """
    client = TestClient(app)

    # Create a stock for market data testing
    stock = Stock(
        symbol="BASELINE",
        company_name="Baseline Test",
        exchange="ASX",
        current_price=50.00
    )
    test_db_session.add(stock)
    test_db_session.commit()

    # Test market data API response
    response = client.get(
        "/api/v1/market-data/prices?symbols=BASELINE",
        headers=auth_headers
    )

    if response.status_code == 200:
        market_data = response.json()

        if "prices" in market_data and "BASELINE" in market_data["prices"]:
            baseline_timestamp = market_data["prices"]["BASELINE"]["fetched_at"]

            # Document the expected format
            assert isinstance(baseline_timestamp, str), "Should be string format"
            assert baseline_timestamp.endswith('Z'), "Should end with 'Z'"
            assert '+00:00' not in baseline_timestamp, "Should not contain '+00:00'"

            # This is the format holdings should match
            print(f"Market data timestamp format: {baseline_timestamp}")


def test_timezone_consistency_between_apis():
    """
    Test that both APIs handle timezone conversion consistently.
    """
    # Create test datetime in UTC
    test_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.utc)

    # Both APIs should produce the same string format
    expected_format = to_iso_string(test_time)

    # Expected format should be: "2024-01-15T14:30:00Z"
    assert expected_format == "2024-01-15T14:30:00Z"
    assert expected_format.endswith('Z')
    assert '+00:00' not in expected_format
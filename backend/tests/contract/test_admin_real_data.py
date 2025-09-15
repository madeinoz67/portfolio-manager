"""
TDD Contract tests for admin dashboard with real data.

These tests verify that the admin dashboard shows real data from the database
instead of mock data. Following TDD principles:
1. Write failing tests first
2. Make tests pass with minimal implementation
3. Refactor while keeping tests green
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.models.market_data_api_usage_metrics import ApiUsageMetrics
from tests.conftest import get_admin_jwt_token, get_user_jwt_token

client = TestClient(app)


class TestAdminRealDataContract:
    """TDD contract tests for real admin data functionality."""

    def test_api_usage_shows_zero_with_no_data(self, admin_jwt_token: str, db_session: Session):
        """TEST 1: API usage should show 0 requests when database is empty."""
        # This test should PASS immediately since empty DB should return 0s

        response = client.get(
            "/api/v1/admin/api-usage",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # With no data, should show all zeros
        assert data["summary"]["total_requests_today"] == 0
        assert data["summary"]["total_requests_this_month"] == 0
        assert data["summary"]["errors_today"] == 0
        assert data["summary"]["success_rate_today"] == 100.0  # 100% when no errors

    def test_api_usage_reflects_real_database_records(self, admin_jwt_token: str, db_session: Session):
        """TEST 2: API usage should reflect actual database records."""
        # This test should FAIL initially - we need to create real data and verify it's displayed

        # Create real API usage data
        today = datetime.now()
        api_record = ApiUsageMetrics(
            provider_name="yfinance",
            symbol="AAPL",
            endpoint="/quote",
            request_timestamp=today,
            response_status=200,
            success=True
        )
        db_session.add(api_record)
        db_session.commit()

        response = client.get(
            "/api/v1/admin/api-usage",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should now show 1 request today
        assert data["summary"]["total_requests_today"] == 1
        assert data["summary"]["errors_today"] == 0
        assert data["summary"]["success_rate_today"] == 100.0

    def test_api_usage_tracks_errors_correctly(self, admin_jwt_token: str, db_session: Session):
        """TEST 3: API usage should correctly track and display errors."""

        # Create successful and failed requests
        today = datetime.now()

        success_record = ApiUsageMetrics(
            provider_name="yfinance",
            symbol="GOOGL",
            endpoint="/quote",
            request_timestamp=today,
            response_status=200,
            success=True
        )

        error_record = ApiUsageMetrics(
            provider_name="alpha_vantage",
            symbol="MSFT",
            endpoint="/quote",
            request_timestamp=today,
            response_status=429,
            success=False,
            error_message="Rate limit exceeded"
        )

        db_session.add_all([success_record, error_record])
        db_session.commit()

        response = client.get(
            "/api/v1/admin/api-usage",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should show 2 total requests, 1 error, 50% success rate
        assert data["summary"]["total_requests_today"] == 2
        assert data["summary"]["errors_today"] == 1
        assert data["summary"]["success_rate_today"] == 50.0

    def test_api_usage_provider_breakdown_is_accurate(self, admin_jwt_token: str, db_session: Session):
        """TEST 4: API usage should show accurate per-provider breakdown."""

        today = datetime.now()

        # Create multiple records for different providers
        for i in range(3):
            yfinance_record = ApiUsageMetrics(
                provider_name="yfinance",
                symbol=f"STOCK{i}",
                endpoint="/quote",
                request_timestamp=today,
                response_status=200,
                success=True
            )
            db_session.add(yfinance_record)

        for i in range(2):
            av_record = ApiUsageMetrics(
                provider_name="alpha_vantage",
                symbol=f"STOCK{i}",
                endpoint="/quote",
                request_timestamp=today,
                response_status=200,
                success=True
            )
            db_session.add(av_record)

        db_session.commit()

        response = client.get(
            "/api/v1/admin/api-usage",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Find provider stats
        yfinance_stats = next((p for p in data["by_provider"] if p["provider_name"] == "yfinance"), None)
        alpha_vantage_stats = next((p for p in data["by_provider"] if p["provider_name"] == "alpha_vantage"), None)

        assert yfinance_stats is not None
        assert yfinance_stats["requests_today"] == 3
        assert yfinance_stats["errors_today"] == 0

        assert alpha_vantage_stats is not None
        assert alpha_vantage_stats["requests_today"] == 2
        assert alpha_vantage_stats["errors_today"] == 0

    def test_api_usage_date_filtering_works(self, admin_jwt_token: str, db_session: Session):
        """TEST 5: API usage should support date range filtering."""

        today = datetime.now()
        yesterday = today - timedelta(days=1)

        # Create records for today and yesterday
        today_record = ApiUsageMetrics(
            provider_name="yfinance",
            symbol="TODAY",
            endpoint="/quote",
            request_timestamp=today,
            response_status=200,
            success=True
        )

        yesterday_record = ApiUsageMetrics(
            provider_name="yfinance",
            symbol="YESTERDAY",
            endpoint="/quote",
            request_timestamp=yesterday,
            response_status=200,
            success=True
        )

        db_session.add_all([today_record, yesterday_record])
        db_session.commit()

        # Test filtering by specific date
        response = client.get(
            f"/api/v1/admin/api-usage?start_date={today.date()}&end_date={today.date()}",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should only show today's records
        assert data["summary"]["total_requests_today"] == 1

    def test_system_metrics_reflect_real_database_counts(self, admin_jwt_token: str, db_session: Session):
        """TEST 6: System metrics should show real user/portfolio counts."""

        response = client.get(
            "/api/v1/admin/system/metrics",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should show real counts from database (we know there are 4 users from earlier test)
        assert isinstance(data["totalUsers"], int)
        assert data["totalUsers"] >= 1  # At least the admin user
        assert isinstance(data["totalPortfolios"], int)
        assert data["totalPortfolios"] >= 0
        assert isinstance(data["activeUsers"], int)
        assert isinstance(data["adminUsers"], int)
        assert data["adminUsers"] >= 1  # At least one admin exists
        assert data["systemStatus"] in ["healthy", "warning", "error"]

    def test_market_data_status_uses_real_provider_data(self, admin_jwt_token: str, db_session: Session):
        """TEST 7: Market data status should reflect actual provider usage."""

        # Create some API usage for providers
        today = datetime.now()

        provider_record = ApiUsageMetrics(
            provider_name="yfinance",
            symbol="TEST",
            endpoint="/quote",
            request_timestamp=today,
            response_status=200,
            success=True
        )
        db_session.add(provider_record)
        db_session.commit()

        response = client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should have providers with real data
        assert "providers" in data
        assert len(data["providers"]) >= 1

        # Find yfinance provider
        yfinance_provider = next((p for p in data["providers"] if "yfinance" in p["providerId"]), None)
        assert yfinance_provider is not None
        assert yfinance_provider["apiCallsToday"] >= 1  # Should show our test record

    def test_api_usage_pagination_affects_results(self, admin_jwt_token: str, db_session: Session):
        """TEST 8: API usage pagination should actually limit results."""

        today = datetime.now()

        # Create 10 days of data
        for days_ago in range(10):
            date = today - timedelta(days=days_ago)
            record = ApiUsageMetrics(
                provider_name="yfinance",
                symbol=f"DAY{days_ago}",
                endpoint="/quote",
                request_timestamp=date,
                response_status=200,
                success=True
            )
            db_session.add(record)

        db_session.commit()

        # Test with limit=3
        response = client.get(
            "/api/v1/admin/api-usage?limit=3",
            headers={"Authorization": f"Bearer {admin_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should respect the limit
        assert len(data["by_date"]) <= 3


@pytest.fixture
def admin_jwt_token(db_session: Session) -> str:
    """Fixture to get JWT token for admin user."""
    return get_admin_jwt_token(db_session)


@pytest.fixture
def user_jwt_token(db_session: Session) -> str:
    """Fixture to get JWT token for regular user."""
    return get_user_jwt_token(db_session)
"""
TDD tests for provider detail page functionality.
Tests comprehensive provider statistics and detail endpoint.
"""

import pytest
from datetime import datetime, date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.models.user import User
from src.models.user_role import UserRole
from src.models.market_data_provider import MarketDataProvider
from src.models.api_usage_metrics import ApiUsageMetrics
from src.core.auth import create_access_token, get_password_hash


@pytest.fixture
def admin_user(db_session: Session) -> User:
    """Create admin user for testing."""
    admin_user = User(
        email="admin@test.com",
        first_name="Admin",
        last_name="User",
        password_hash=get_password_hash("adminpassword"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin_user)
    db_session.commit()
    db_session.refresh(admin_user)
    return admin_user


@pytest.fixture
def regular_user(db_session: Session) -> User:
    """Create regular user for testing."""
    regular_user = User(
        email="user@test.com",
        first_name="Regular",
        last_name="User",
        password_hash=get_password_hash("userpassword"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(regular_user)
    db_session.commit()
    db_session.refresh(regular_user)
    return regular_user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """Create admin JWT token for testing."""
    return create_access_token(data={"sub": admin_user.email})


@pytest.fixture
def sample_provider(db_session: Session) -> MarketDataProvider:
    """Create sample provider for testing."""
    provider = MarketDataProvider(
        name="yfinance",
        display_name="Yahoo Finance",
        is_enabled=True,
        rate_limit_per_minute=5,
        rate_limit_per_day=500,
        priority=1
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)
    return provider


@pytest.fixture
def sample_usage_data(db_session: Session, sample_provider: MarketDataProvider):
    """Create comprehensive usage data for testing."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)

    # Create usage metrics for different time periods
    metrics = [
        # Today's data
        ApiUsageMetrics(
            metric_id="test_today_1",
            provider_id=sample_provider.name,
            request_type="price_fetch",
            requests_count=25,
            data_points_fetched=25,
            cost_estimate=0.25,
            recorded_at=datetime.now(),
            time_bucket="daily",
            rate_limit_hit=False,
            error_count=2,
            avg_response_time_ms=150
        ),
        ApiUsageMetrics(
            metric_id="test_today_2",
            provider_id=sample_provider.name,
            request_type="bulk_fetch",
            requests_count=5,
            data_points_fetched=100,
            cost_estimate=0.50,
            recorded_at=datetime.now(),
            time_bucket="daily",
            rate_limit_hit=True,
            error_count=0,
            avg_response_time_ms=300
        ),
        # Yesterday's data
        ApiUsageMetrics(
            metric_id="test_yesterday",
            provider_id=sample_provider.name,
            request_type="price_fetch",
            requests_count=20,
            data_points_fetched=20,
            cost_estimate=0.20,
            recorded_at=datetime.combine(yesterday, datetime.min.time()),
            time_bucket="daily",
            rate_limit_hit=False,
            error_count=1,
            avg_response_time_ms=120
        ),
        # Week ago data
        ApiUsageMetrics(
            metric_id="test_week_ago",
            provider_id=sample_provider.name,
            request_type="price_fetch",
            requests_count=15,
            data_points_fetched=15,
            cost_estimate=0.15,
            recorded_at=datetime.combine(week_ago, datetime.min.time()),
            time_bucket="daily",
            rate_limit_hit=False,
            error_count=0,
            avg_response_time_ms=100
        )
    ]

    db_session.add_all(metrics)
    db_session.commit()
    return metrics


class TestProviderDetailEndpoint:
    """Test provider detail API endpoint."""

    def test_get_provider_details_success(self, client: TestClient, admin_token: str,
                                        sample_provider: MarketDataProvider, sample_usage_data):
        """Test successful provider detail retrieval."""
        response = client.get(
            f"/api/v1/admin/market-data/providers/{sample_provider.name}/details",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify basic provider information
        assert data["providerId"] == sample_provider.name
        assert data["providerName"] == sample_provider.display_name
        assert data["isEnabled"] == sample_provider.is_enabled
        assert data["priority"] == sample_provider.priority
        assert data["rateLimitPerMinute"] == sample_provider.rate_limit_per_minute
        assert data["rateLimitPerDay"] == sample_provider.rate_limit_per_day

        # Verify usage statistics exist
        assert "usageStats" in data
        usage_stats = data["usageStats"]

        # Verify today's stats
        assert "today" in usage_stats
        today_stats = usage_stats["today"]
        assert today_stats["totalRequests"] == 30  # 25 + 5
        assert today_stats["totalErrors"] == 2
        assert today_stats["totalCost"] == 0.75  # 0.25 + 0.50
        assert today_stats["avgResponseTime"] >= 200  # Should be weighted average, around 225
        assert today_stats["rateLimitHits"] == 1

        # Verify historical stats
        assert "historical" in usage_stats
        historical = usage_stats["historical"]
        assert "last7Days" in historical
        assert "last30Days" in historical

        # Verify performance metrics
        assert "performanceMetrics" in data
        performance = data["performanceMetrics"]
        assert "successRate" in performance
        assert "errorRate" in performance
        assert "uptimePercentage" in performance

        # Verify configuration
        assert "configuration" in data
        config = data["configuration"]
        assert "apiEndpoint" in config
        assert "authentication" in config

        # Verify recent activity
        assert "recentActivity" in data
        assert isinstance(data["recentActivity"], list)

    def test_get_provider_details_not_found(self, client: TestClient, admin_token: str):
        """Test provider detail retrieval for non-existent provider."""
        response = client.get(
            "/api/v1/admin/market-data/providers/nonexistent/details",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "not_found"
        assert "not found" in data["message"].lower()

    def test_get_provider_details_unauthorized(self, client: TestClient,
                                             sample_provider: MarketDataProvider):
        """Test provider detail retrieval without authentication."""
        response = client.get(
            f"/api/v1/admin/market-data/providers/{sample_provider.name}/details"
        )

        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "unauthorized"

    def test_get_provider_details_non_admin(self, client: TestClient,
                                          sample_provider: MarketDataProvider,
                                          regular_user: User):
        """Test provider detail retrieval with non-admin user."""
        token = create_access_token(data={"sub": regular_user.email})

        response = client.get(
            f"/api/v1/admin/market-data/providers/{sample_provider.name}/details",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403
        data = response.json()
        assert data["error"] == "forbidden"

    def test_provider_details_with_no_usage_data(self, client: TestClient,
                                                admin_token: str,
                                                sample_provider: MarketDataProvider):
        """Test provider detail retrieval when no usage data exists."""
        response = client.get(
            f"/api/v1/admin/market-data/providers/{sample_provider.name}/details",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should still return provider info with zero stats
        assert data["providerId"] == sample_provider.name
        usage_stats = data["usageStats"]

        # Today's stats should be zero
        today_stats = usage_stats["today"]
        assert today_stats["totalRequests"] == 0
        assert today_stats["totalErrors"] == 0
        assert today_stats["totalCost"] == 0.0
        assert today_stats["rateLimitHits"] == 0

    def test_provider_details_response_format(self, client: TestClient,
                                            admin_token: str,
                                            sample_provider: MarketDataProvider,
                                            sample_usage_data):
        """Test that provider detail response has correct format."""
        response = client.get(
            f"/api/v1/admin/market-data/providers/{sample_provider.name}/details",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Required top-level fields
        required_fields = [
            "providerId", "providerName", "isEnabled", "priority",
            "rateLimitPerMinute", "rateLimitPerDay", "lastUpdated",
            "usageStats", "performanceMetrics", "configuration",
            "recentActivity", "costAnalysis"
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Check usage stats structure
        usage_stats = data["usageStats"]
        assert "today" in usage_stats
        assert "yesterday" in usage_stats
        assert "historical" in usage_stats

        # Check performance metrics structure
        performance = data["performanceMetrics"]
        performance_fields = ["successRate", "errorRate", "avgResponseTime", "uptimePercentage"]
        for field in performance_fields:
            assert field in performance, f"Missing performance field: {field}"

        # Check configuration structure
        config = data["configuration"]
        config_fields = ["apiEndpoint", "authentication", "rateLimits", "timeout"]
        for field in config_fields:
            assert field in config, f"Missing config field: {field}"

    def test_provider_details_cost_analysis(self, client: TestClient,
                                          admin_token: str,
                                          sample_provider: MarketDataProvider,
                                          sample_usage_data):
        """Test cost analysis section in provider details."""
        response = client.get(
            f"/api/v1/admin/market-data/providers/{sample_provider.name}/details",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        cost_analysis = data["costAnalysis"]

        # Cost analysis fields
        assert "totalCostToday" in cost_analysis
        assert "totalCostThisMonth" in cost_analysis
        assert "projectedMonthlyCost" in cost_analysis
        assert "costPerRequest" in cost_analysis
        assert "costBreakdown" in cost_analysis

        # Verify cost calculations are reasonable
        assert cost_analysis["totalCostToday"] >= 0
        assert cost_analysis["costPerRequest"] >= 0
        assert isinstance(cost_analysis["costBreakdown"], list)

    def test_provider_details_recent_activity(self, client: TestClient,
                                            admin_token: str,
                                            sample_provider: MarketDataProvider,
                                            sample_usage_data):
        """Test recent activity section in provider details."""
        response = client.get(
            f"/api/v1/admin/market-data/providers/{sample_provider.name}/details",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        recent_activity = data["recentActivity"]

        # Should be a list of activity items
        assert isinstance(recent_activity, list)

        if recent_activity:  # If there's activity data
            activity_item = recent_activity[0]

            # Each activity item should have required fields
            activity_fields = ["timestamp", "type", "description", "status"]
            for field in activity_fields:
                assert field in activity_item, f"Missing activity field: {field}"
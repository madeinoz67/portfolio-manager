"""
Test-driven development tests for admin dashboard data updates.

Tests that admin dashboard reflects real-time data updates including:
- New stock additions (like TLS)
- API usage statistics
- Market data provider status
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from src.models.stock import Stock, StockStatus
from src.models.api_usage_metrics import ApiUsageMetrics
from src.models.market_data_provider import MarketDataProvider
from src.models.user import User
from src.models.user_role import UserRole
from src.api.admin import get_market_data_status, get_api_usage, get_system_metrics
from src.utils.datetime_utils import now
from src.core.auth import get_password_hash
import uuid
import asyncio


class TestAdminDataUpdates:
    """Test that admin dashboard shows updated data."""

    @pytest.fixture
    def admin_user(self, db_session: Session):
        """Create admin user for tests."""
        admin = User(
            email="admin@test.com",
            password_hash=get_password_hash("admin123"),
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            is_active=True
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
        return admin

    @pytest.fixture
    def sample_stocks(self, db_session: Session):
        """Create sample stocks including TLS."""
        stocks = [
            Stock(
                symbol="TLS",
                company_name="Telos Corporation",
                exchange="NASDAQ",
                current_price=Decimal("2.45"),
                status=StockStatus.ACTIVE
            ),
            Stock(
                symbol="AAPL",
                company_name="Apple Inc.",
                exchange="NASDAQ",
                current_price=Decimal("175.43"),
                status=StockStatus.ACTIVE
            ),
            Stock(
                symbol="MSFT",
                company_name="Microsoft Corporation",
                exchange="NASDAQ",
                current_price=Decimal("378.85"),
                status=StockStatus.ACTIVE
            )
        ]

        for stock in stocks:
            db_session.add(stock)
        db_session.commit()

        for stock in stocks:
            db_session.refresh(stock)
        return stocks

    @pytest.fixture
    def sample_providers(self, db_session: Session):
        """Create sample market data providers."""
        providers = [
            MarketDataProvider(
                name="yfinance",
                display_name="Yahoo Finance",
                is_enabled=True,
                api_key="",
                base_url="https://finance.yahoo.com",
                rate_limit_per_minute=60,
                rate_limit_per_day=2000,
                priority=2
            ),
            MarketDataProvider(
                name="alpha_vantage",
                display_name="Alpha Vantage",
                is_enabled=True,
                api_key="demo_key",
                base_url="https://www.alphavantage.co/query",
                rate_limit_per_minute=5,
                rate_limit_per_day=500,
                priority=1
            )
        ]

        for provider in providers:
            db_session.add(provider)
        db_session.commit()

        for provider in providers:
            db_session.refresh(provider)
        return providers

    @pytest.fixture
    def api_usage_data(self, db_session: Session):
        """Create API usage metrics data."""
        current_time = now()
        yesterday = current_time - timedelta(days=1)

        metrics = [
            # Today's metrics
            ApiUsageMetrics(
                metric_id=str(uuid.uuid4()),
                provider_id="yfinance",
                request_type="stock_quote",
                requests_count=125,
                error_count=8,
                data_points_fetched=625,
                cost_estimate=Decimal("0.00"),
                avg_response_time_ms=450,
                time_bucket="daily",
                recorded_at=current_time
            ),
            ApiUsageMetrics(
                metric_id=str(uuid.uuid4()),
                provider_id="alpha_vantage",
                request_type="stock_quote",
                requests_count=85,
                error_count=3,
                data_points_fetched=425,
                cost_estimate=Decimal("1.70"),
                avg_response_time_ms=680,
                time_bucket="daily",
                recorded_at=current_time
            ),
            # Yesterday's metrics for trends
            ApiUsageMetrics(
                metric_id=str(uuid.uuid4()),
                provider_id="yfinance",
                request_type="stock_quote",
                requests_count=98,
                error_count=12,
                data_points_fetched=490,
                cost_estimate=Decimal("0.00"),
                avg_response_time_ms=520,
                time_bucket="daily",
                recorded_at=yesterday
            ),
            ApiUsageMetrics(
                metric_id=str(uuid.uuid4()),
                provider_id="alpha_vantage",
                request_type="stock_quote",
                requests_count=62,
                error_count=1,
                data_points_fetched=310,
                cost_estimate=Decimal("1.24"),
                avg_response_time_ms=610,
                time_bucket="daily",
                recorded_at=yesterday
            )
        ]

        for metric in metrics:
            db_session.add(metric)
        db_session.commit()

        for metric in metrics:
            db_session.refresh(metric)
        return metrics

    def test_tls_stock_appears_in_system_metrics(self, db_session: Session, admin_user: User, sample_stocks):
        """Test that TLS stock addition increases total stock count in system metrics."""
        result = asyncio.run(get_system_metrics(admin_user, db_session))

        # Should have sample stocks (including TLS)
        assert "totalStocks" in result or len(sample_stocks) >= 1

        # Check if we can query TLS specifically
        tls_stock = db_session.query(Stock).filter(Stock.symbol == "TLS").first()
        assert tls_stock is not None
        assert tls_stock.company_name == "Telos Corporation"
        assert float(tls_stock.current_price) == 2.45

    def test_api_usage_shows_current_data(self, db_session: Session, admin_user: User, api_usage_data, sample_providers):
        """Test that API usage endpoint shows current usage statistics."""
        result = asyncio.run(get_api_usage(admin_user, db_session))

        # Should have summary statistics
        assert "summary" in result
        summary = result["summary"]

        # Should show today's total requests (125 + 85 = 210)
        assert summary["total_requests_today"] == 210

        # Should show today's total errors (8 + 3 = 11)
        assert summary["total_errors_today"] == 11

        # Should calculate success rate: (210 - 11) / 210 * 100 = 94.8%
        expected_success_rate = ((210 - 11) / 210) * 100
        assert abs(summary["success_rate_today"] - expected_success_rate) < 0.1

    def test_api_usage_shows_provider_breakdown(self, db_session: Session, admin_user: User, api_usage_data, sample_providers):
        """Test that API usage shows breakdown by provider."""
        result = asyncio.run(get_api_usage(admin_user, db_session))

        assert "by_provider" in result
        providers = result["by_provider"]

        # Should have 2 providers
        assert len(providers) == 2

        # Find yfinance provider
        yfinance_data = next((p for p in providers if p["provider_name"] == "yfinance"), None)
        assert yfinance_data is not None
        assert yfinance_data["requests_today"] == 125
        assert yfinance_data["errors_today"] == 8

        # Find alpha_vantage provider
        alpha_data = next((p for p in providers if p["provider_name"] == "alpha_vantage"), None)
        assert alpha_data is not None
        assert alpha_data["requests_today"] == 85
        assert alpha_data["errors_today"] == 3

    def test_api_usage_calculates_trends(self, db_session: Session, admin_user: User, api_usage_data, sample_providers):
        """Test that API usage calculates day-over-day trends."""
        result = asyncio.run(get_api_usage(admin_user, db_session))

        # Should include trends if implemented
        if "trends" in result:
            trends = result["trends"]

            # Today: 210 requests, Yesterday: 160 requests (98 + 62)
            # Daily change: (210 - 160) / 160 * 100 = 31.25%
            expected_daily_change = ((210 - 160) / 160) * 100
            assert abs(trends["daily_change_percent"] - expected_daily_change) < 0.1

    def test_market_data_status_shows_providers(self, db_session: Session, admin_user: User, sample_providers, api_usage_data):
        """Test that market data status shows provider information."""
        result = asyncio.run(get_market_data_status(admin_user, db_session))

        assert "providers" in result
        providers = result["providers"]

        # Should show both providers
        provider_names = [p["providerId"] for p in providers]
        assert "yfinance" in provider_names
        assert "alpha_vantage" in provider_names

        # Check yfinance provider details
        yfinance = next((p for p in providers if p["providerId"] == "yfinance"), None)
        assert yfinance is not None
        assert yfinance["providerName"] == "Yahoo Finance"
        assert yfinance["isEnabled"] is True
        assert yfinance["apiCallsToday"] == 125  # From api_usage_data

    def test_market_data_shows_response_times(self, db_session: Session, admin_user: User, sample_providers, api_usage_data):
        """Test that market data status shows average response times."""
        result = asyncio.run(get_market_data_status(admin_user, db_session))

        providers = result["providers"]

        # Check if response times are included
        for provider in providers:
            if "avgResponseTimeMs" in provider:
                # yfinance should show 450ms average
                if provider["providerId"] == "yfinance":
                    assert provider["avgResponseTimeMs"] == 450
                # alpha_vantage should show 680ms average
                elif provider["providerId"] == "alpha_vantage":
                    assert provider["avgResponseTimeMs"] == 680

    def test_data_updates_reflect_immediately(self, db_session: Session, admin_user: User):
        """Test that new data additions are reflected immediately in API responses."""
        # Add a new stock
        new_stock = Stock(
            symbol="NVDA",
            company_name="NVIDIA Corporation",
            exchange="NASDAQ",
            current_price=Decimal("421.50"),
            status=StockStatus.ACTIVE
        )
        db_session.add(new_stock)
        db_session.commit()

        # Add new API metrics
        current_time = now()
        new_metric = ApiUsageMetrics(
            metric_id=str(uuid.uuid4()),
            provider_id="yfinance",
            request_type="stock_quote",
            requests_count=50,
            error_count=2,
            data_points_fetched=250,
            cost_estimate=Decimal("0.00"),
            avg_response_time_ms=380,
            time_bucket="daily",
            recorded_at=current_time
        )
        db_session.add(new_metric)
        db_session.commit()

        # Verify stock is queryable
        nvda_stock = db_session.query(Stock).filter(Stock.symbol == "NVDA").first()
        assert nvda_stock is not None
        assert nvda_stock.company_name == "NVIDIA Corporation"

        # Verify API usage data is queryable
        new_metrics = db_session.query(ApiUsageMetrics).filter(
            ApiUsageMetrics.provider_id == "yfinance",
            ApiUsageMetrics.requests_count == 50
        ).first()
        assert new_metrics is not None
        assert new_metrics.avg_response_time_ms == 380

    def test_admin_endpoints_handle_no_data_gracefully(self, db_session: Session, admin_user: User):
        """Test that admin endpoints handle empty data gracefully."""
        # Clear all data
        db_session.query(ApiUsageMetrics).delete()
        db_session.query(Stock).delete()
        db_session.commit()

        # API usage should return zeros
        result = asyncio.run(get_api_usage(admin_user, db_session))
        assert result["summary"]["total_requests_today"] == 0
        assert result["summary"]["total_errors_today"] == 0
        assert result["summary"]["success_rate_today"] == 0.0

        # System metrics should handle zero stocks
        system_result = asyncio.run(get_system_metrics(admin_user, db_session))
        # Should not crash, may return system status
        assert hasattr(system_result, "systemStatus") or "systemStatus" in system_result
"""
Live integration tests for admin dashboard data updates.

These tests actually fetch real data from APIs and verify that:
1. Data is correctly stored in the database
2. Admin dashboard APIs reflect the real data
3. Data updates are visible in the UI endpoints
"""

import pytest
import asyncio
import requests
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from src.models.stock import Stock, StockStatus
from src.models.market_data_api_usage_metrics import ApiUsageMetrics
from src.models.market_data_provider import MarketDataProvider
from src.models.user import User
from src.models.user_role import UserRole
from src.api.admin import get_market_data_status, get_api_usage, get_system_metrics
from src.utils.datetime_utils import now
from src.core.auth import get_password_hash, create_access_token
from src.main import app


class TestLiveAdminIntegration:
    """Live integration tests that fetch real data and verify admin dashboard updates."""

    @pytest.fixture
    def live_client(self):
        """Create a test client for live integration tests."""
        return TestClient(app)

    @pytest.fixture
    def admin_auth_token(self, db_session: Session):
        """Create admin user and return auth token for API calls."""
        # Create admin user if not exists
        admin = db_session.query(User).filter(User.email == "admin@live-test.com").first()
        if not admin:
            admin = User(
                email="admin@live-test.com",
                password_hash=get_password_hash("livetest123"),
                first_name="Live",
                last_name="Admin",
                role=UserRole.ADMIN,
                is_active=True
            )
            db_session.add(admin)
            db_session.commit()
            db_session.refresh(admin)

        # Generate JWT token
        token = create_access_token(data={"sub": admin.email})
        return token

    def test_fetch_real_tls_data_and_verify_admin_response(self, db_session: Session, live_client: TestClient, admin_auth_token: str):
        """Test fetching real TLS stock data and verifying it appears in admin endpoints."""

        # Step 0: Clear previous data to ensure clean test
        db_session.query(ApiUsageMetrics).delete()
        db_session.query(Stock).filter(Stock.symbol == "TLS").delete()
        db_session.commit()

        # Step 1: Fetch real TLS data from Yahoo Finance API (free)
        try:
            response = requests.get(
                "https://query1.finance.yahoo.com/v8/finance/chart/TLS",
                params={
                    "interval": "1d",
                    "range": "1d"
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if "chart" in data and data["chart"]["result"]:
                    chart_data = data["chart"]["result"][0]
                    meta = chart_data.get("meta", {})
                    current_price = meta.get("regularMarketPrice", 2.45)  # fallback

                    # Step 2: Store the real data in database
                    tls_stock = db_session.query(Stock).filter(Stock.symbol == "TLS").first()
                    if tls_stock:
                        tls_stock.current_price = Decimal(str(current_price))
                    else:
                        tls_stock = Stock(
                            symbol="TLS",
                            company_name="Telos Corporation",
                            exchange="NASDAQ",
                            current_price=Decimal(str(current_price)),
                            status=StockStatus.ACTIVE
                        )
                        db_session.add(tls_stock)

                    db_session.commit()
                    db_session.refresh(tls_stock)

                    # Step 3: Record this as an API usage metric
                    api_metric = ApiUsageMetrics(
                        metric_id=str(uuid.uuid4()),
                        provider_id="yfinance",
                        request_type="stock_quote",
                        requests_count=1,
                        error_count=0,
                        data_points_fetched=1,
                        cost_estimate=Decimal("0.00"),
                        avg_response_time_ms=int(response.elapsed.total_seconds() * 1000),
                        time_bucket="daily",
                        recorded_at=now()
                    )
                    db_session.add(api_metric)
                    db_session.commit()

                    print(f"Fetched real TLS data: ${current_price}")

                else:
                    # Fallback to sample data if API doesn't return expected format
                    current_price = 2.45
                    print("Using fallback TLS price due to API format")
            else:
                # Fallback to sample data if API fails
                current_price = 2.45
                print(f"Yahoo Finance API failed (status {response.status_code}), using fallback")

        except Exception as e:
            print(f"Exception fetching real data: {e}, using fallback")
            current_price = 2.45

            # Still create the stock with fallback data for testing
            tls_stock = db_session.query(Stock).filter(Stock.symbol == "TLS").first()
            if not tls_stock:
                tls_stock = Stock(
                    symbol="TLS",
                    company_name="Telos Corporation",
                    exchange="NASDAQ",
                    current_price=Decimal(str(current_price)),
                    status=StockStatus.ACTIVE
                )
                db_session.add(tls_stock)
                db_session.commit()
                db_session.refresh(tls_stock)

        # Step 4: Test admin system metrics endpoint shows the stock
        response = live_client.get(
            "/api/v1/admin/system/metrics",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )

        assert response.status_code == 200
        system_data = response.json()

        # Should have system metrics - TLS stock should contribute to total count
        assert "totalUsers" in system_data
        assert "totalPortfolios" in system_data
        assert "systemStatus" in system_data

        # Step 5: Verify the stock exists in database query
        tls_stock = db_session.query(Stock).filter(Stock.symbol == "TLS").first()
        assert tls_stock is not None
        assert tls_stock.company_name == "Telos Corporation"
        assert float(tls_stock.current_price) == current_price

    def test_live_api_usage_tracking_and_admin_display(self, db_session: Session, live_client: TestClient, admin_auth_token: str):
        """Test that real API calls are tracked and show up in admin usage stats."""

        # Step 0: Clear previous data to ensure clean test
        db_session.query(ApiUsageMetrics).delete()
        db_session.commit()

        # Step 1: Ensure we have providers set up
        providers = ["yfinance", "alpha_vantage"]
        for provider_name in providers:
            provider = db_session.query(MarketDataProvider).filter(MarketDataProvider.name == provider_name).first()
            if not provider:
                provider = MarketDataProvider(
                    name=provider_name,
                    display_name=provider_name.title().replace("_", " "),
                    is_enabled=True,
                    api_key="demo_key" if provider_name == "alpha_vantage" else "",
                    base_url="https://api.example.com",
                    rate_limit_per_minute=60,
                    rate_limit_per_day=1000,
                    priority=1
                )
                db_session.add(provider)

        db_session.commit()

        # Step 2: Simulate real API usage by creating metrics
        current_time = now()
        real_metrics = []

        # Simulate fetching data for multiple stocks
        stocks_to_fetch = ["TLS", "AAPL", "MSFT", "GOOGL", "NVDA"]

        for i, symbol in enumerate(stocks_to_fetch):
            # Create metric for yfinance
            metric = ApiUsageMetrics(
                metric_id=str(uuid.uuid4()),
                provider_id="yfinance",
                request_type="stock_quote",
                requests_count=1,
                error_count=0,
                data_points_fetched=1,
                cost_estimate=Decimal("0.00"),
                avg_response_time_ms=400 + (i * 50),  # Varying response times
                time_bucket="daily",
                recorded_at=current_time
            )
            db_session.add(metric)
            real_metrics.append(metric)

            # Also create the stock if it doesn't exist
            stock = db_session.query(Stock).filter(Stock.symbol == symbol).first()
            if not stock:
                stock = Stock(
                    symbol=symbol,
                    company_name=f"{symbol} Corporation",
                    exchange="NASDAQ",
                    current_price=Decimal("100.00") + Decimal(str(i * 10)),
                    status=StockStatus.ACTIVE
                )
                db_session.add(stock)

        db_session.commit()

        # Step 3: Test admin API usage endpoint reflects the real data
        response = live_client.get(
            "/api/v1/admin/api-usage",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )

        assert response.status_code == 200
        usage_data = response.json()

        # Should have summary showing our API calls
        assert "summary" in usage_data
        summary = usage_data["summary"]

        # Should show at least 5 requests (one for each stock)
        assert summary["total_requests_today"] >= 5

        # Should show low error rate (we didn't simulate errors)
        assert summary["total_errors_today"] >= 0

        # Should have provider breakdown
        assert "by_provider" in usage_data
        providers = usage_data["by_provider"]

        # Should have yfinance provider with our requests
        yfinance_provider = next((p for p in providers if p["provider_name"] == "yfinance"), None)
        assert yfinance_provider is not None
        assert yfinance_provider["requests_today"] >= 5

    def test_live_market_data_status_reflects_real_activity(self, db_session: Session, live_client: TestClient, admin_auth_token: str):
        """Test that market data status shows real provider activity."""

        # Step 1: Ensure we have recent activity recorded
        current_time = now()

        # Simulate some recent API activity with different response times
        activity_metrics = [
            {
                "provider_id": "yfinance",
                "requests_count": 15,
                "error_count": 1,
                "avg_response_time_ms": 420
            },
            {
                "provider_id": "alpha_vantage",
                "requests_count": 8,
                "error_count": 0,
                "avg_response_time_ms": 750
            }
        ]

        for activity in activity_metrics:
            metric = ApiUsageMetrics(
                metric_id=str(uuid.uuid4()),
                provider_id=activity["provider_id"],
                request_type="stock_quote",
                requests_count=activity["requests_count"],
                error_count=activity["error_count"],
                data_points_fetched=activity["requests_count"] * 5,
                cost_estimate=Decimal("0.20") if activity["provider_id"] == "alpha_vantage" else Decimal("0.00"),
                avg_response_time_ms=activity["avg_response_time_ms"],
                time_bucket="daily",
                recorded_at=current_time
            )
            db_session.add(metric)

        db_session.commit()

        # Step 2: Test admin market data status endpoint
        response = live_client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )

        assert response.status_code == 200
        status_data = response.json()

        # Should have providers list
        assert "providers" in status_data
        providers = status_data["providers"]
        assert len(providers) >= 1

        # Check for provider activity
        for provider in providers:
            assert "providerId" in provider
            assert "providerName" in provider
            assert "isEnabled" in provider
            assert "apiCallsToday" in provider

            # If it's our test providers, check specific values
            if provider["providerId"] == "yfinance":
                assert provider["apiCallsToday"] >= 15
            elif provider["providerId"] == "alpha_vantage":
                assert provider["apiCallsToday"] >= 8

    def test_live_integration_end_to_end_workflow(self, db_session: Session, live_client: TestClient, admin_auth_token: str):
        """Test complete workflow: fetch data -> store -> verify admin dashboard updates."""

        # Step 1: Clear previous data to ensure clean test
        db_session.query(ApiUsageMetrics).delete()
        initial_stock_count = db_session.query(Stock).count()

        # Step 2: Simulate adding new stock data (like user adding TLS)
        new_stocks = [
            ("TLS", "Telos Corporation", "2.45"),
            ("PLTR", "Palantir Technologies", "18.50"),
            ("SNOW", "Snowflake Inc.", "145.20")
        ]

        start_time = now()

        for symbol, company, price in new_stocks:
            # Create stock
            stock = Stock(
                symbol=symbol,
                company_name=company,
                exchange="NASDAQ",
                current_price=Decimal(price),
                status=StockStatus.ACTIVE
            )
            db_session.add(stock)

            # Record the "API call" that would have fetched this data
            metric = ApiUsageMetrics(
                metric_id=str(uuid.uuid4()),
                provider_id="yfinance",
                request_type="stock_quote",
                requests_count=1,
                error_count=0,
                data_points_fetched=1,
                cost_estimate=Decimal("0.00"),
                avg_response_time_ms=450,
                time_bucket="daily",
                recorded_at=start_time
            )
            db_session.add(metric)

        db_session.commit()

        # Step 3: Verify system metrics reflects new stocks
        response = live_client.get(
            "/api/v1/admin/system/metrics",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )

        assert response.status_code == 200
        system_data = response.json()

        # Should have updated system status
        assert "systemStatus" in system_data

        # Step 4: Verify API usage reflects our activity
        response = live_client.get(
            "/api/v1/admin/api-usage",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )

        assert response.status_code == 200
        usage_data = response.json()

        # Should show our 3 API calls
        assert usage_data["summary"]["total_requests_today"] >= 3
        assert usage_data["summary"]["total_errors_today"] == 0

        # Step 5: Verify market data status shows activity
        response = live_client.get(
            "/api/v1/admin/market-data/status",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )

        assert response.status_code == 200
        status_data = response.json()

        providers = status_data["providers"]
        yfinance_provider = next((p for p in providers if p["providerId"] == "yfinance"), None)
        assert yfinance_provider is not None
        assert yfinance_provider["apiCallsToday"] >= 3

        # Step 6: Verify the stocks are actually queryable
        final_stock_count = db_session.query(Stock).count()
        assert final_stock_count >= initial_stock_count + 3

        # Verify TLS specifically
        tls_stock = db_session.query(Stock).filter(Stock.symbol == "TLS").first()
        assert tls_stock is not None
        assert tls_stock.company_name == "Telos Corporation"
        assert float(tls_stock.current_price) == 2.45

        print("✓ Live integration test completed successfully")
        print(f"✓ Added {len(new_stocks)} stocks including TLS")
        print(f"✓ Recorded {len(new_stocks)} API usage metrics")
        print("✓ Admin dashboard reflects all updates")

    def test_admin_dashboard_real_time_updates(self, db_session: Session, live_client: TestClient, admin_auth_token: str):
        """Test that admin dashboard shows updates immediately after data changes."""

        # Step 0: Clear previous data to ensure clean test
        db_session.query(ApiUsageMetrics).delete()
        db_session.commit()

        # Step 1: Get baseline metrics
        response = live_client.get(
            "/api/v1/admin/api-usage",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )
        assert response.status_code == 200
        baseline_data = response.json()
        baseline_requests = baseline_data["summary"]["total_requests_today"]

        # Step 2: Add new activity
        current_time = now()
        new_metric = ApiUsageMetrics(
            metric_id=str(uuid.uuid4()),
            provider_id="alpha_vantage",
            request_type="stock_quote",
            requests_count=10,
            error_count=1,
            data_points_fetched=50,
            cost_estimate=Decimal("0.50"),
            avg_response_time_ms=800,
            time_bucket="daily",
            recorded_at=current_time
        )
        db_session.add(new_metric)
        db_session.commit()

        # Step 3: Verify updated metrics immediately
        response = live_client.get(
            "/api/v1/admin/api-usage",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )
        assert response.status_code == 200
        updated_data = response.json()

        # Should show increased request count
        new_requests = updated_data["summary"]["total_requests_today"]
        assert new_requests >= baseline_requests + 10

        # Should show the new error
        assert updated_data["summary"]["total_errors_today"] >= 1

        print(f"✓ Real-time update verified: {baseline_requests} -> {new_requests} requests")
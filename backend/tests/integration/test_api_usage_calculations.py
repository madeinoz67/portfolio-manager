"""
Test API Usage Calculations - TDD tests for total API call calculations.

This test ensures that total API calls only includes actual external provider calls,
not internal system activities like health checks or batch summaries.
"""

import pytest
from datetime import datetime, date
from sqlalchemy.orm import Session

from src.models.market_data_provider import ProviderActivity
from src.api.admin import get_api_usage


class TestApiUsageCalculations:
    """Test API usage calculation logic."""

    def test_total_api_calls_excludes_system_activities(self, db: Session):
        """
        Test that total API calls only includes actual external provider API calls,
        not internal system activities.

        Given:
        - 5 actual yfinance API calls
        - 3 actual alpha_vantage API calls
        - 10 system health checks
        - 5 system batch summaries

        When: Calculating total API calls for today
        Then: Total should be 8 (5 + 3), not 23 (5 + 3 + 10 + 5)
        """
        today = datetime.utcnow()

        # Create actual external API call activities
        external_provider_activities = [
            ProviderActivity(
                provider_id="yfinance",
                activity_type="API_CALL",
                description=f"Successfully fetched price for AAPL: $150.{i:02d}",
                status="success",
                timestamp=today,
                activity_metadata={"symbol": "AAPL", "price": f"150.{i:02d}"}
            ) for i in range(5)
        ]

        external_provider_activities.extend([
            ProviderActivity(
                provider_id="alpha_vantage",
                activity_type="API_CALL",
                description=f"Successfully fetched price for GOOGL: $2500.{i:02d}",
                status="success",
                timestamp=today,
                activity_metadata={"symbol": "GOOGL", "price": f"2500.{i:02d}"}
            ) for i in range(3)
        ])

        # Create internal system activities (should NOT count as API calls)
        system_activities = [
            ProviderActivity(
                provider_id="system",
                activity_type="HEALTH_CHECK",
                description="System health check completed",
                status="success",
                timestamp=today,
                activity_metadata={"uptime_minutes": i * 15}
            ) for i in range(10)
        ]

        system_activities.extend([
            ProviderActivity(
                provider_id="system",
                activity_type="BATCH_SUMMARY",
                description=f"Batch update completed: {i}/8 symbols updated",
                status="success",
                timestamp=today,
                activity_metadata={"symbols_processed": i}
            ) for i in range(5)
        ])

        # Add all activities to database
        all_activities = external_provider_activities + system_activities
        for activity in all_activities:
            db.add(activity)
        db.commit()

        # Create mock admin user and call the API function
        from src.models.user import User, UserRole
        admin_user = User(
            email="admin@test.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            first_name="Test",
            last_name="Admin"
        )

        # Get API usage statistics
        from unittest.mock import AsyncMock
        mock_get_current_admin_user = AsyncMock(return_value=admin_user)

        # Test the calculation logic directly by calling the endpoint logic
        from src.api.admin import get_api_usage
        import asyncio

        result = asyncio.run(get_api_usage(admin_user, db))

        # Assertions
        assert result["summary"]["total_requests_today"] == 8, (
            f"Expected 8 total API calls (5 yfinance + 3 alpha_vantage), "
            f"but got {result['summary']['total_requests_today']}. "
            f"System activities should not be counted as API calls."
        )

        # Verify by-provider breakdown
        by_provider = {p["provider_name"]: p["requests_today"] for p in result["by_provider"]}

        assert by_provider.get("yfinance", 0) == 5, f"Expected 5 yfinance calls, got {by_provider.get('yfinance', 0)}"
        assert by_provider.get("alpha_vantage", 0) == 3, f"Expected 3 alpha_vantage calls, got {by_provider.get('alpha_vantage', 0)}"

        # System should not appear in provider breakdown for API calls
        assert "system" not in by_provider, "System activities should not appear in API provider breakdown"

    def test_total_api_calls_with_only_external_providers(self, db: Session):
        """
        Test total API calls calculation when there are only external provider calls.
        """
        today = datetime.utcnow()

        # Create only external API calls
        activities = [
            ProviderActivity(
                provider_id="yfinance",
                activity_type="API_CALL",
                description="Successfully fetched price for MSFT: $300.00",
                status="success",
                timestamp=today,
                activity_metadata={"symbol": "MSFT"}
            ),
            ProviderActivity(
                provider_id="alpha_vantage",
                activity_type="API_CALL",
                description="Successfully fetched price for TSLA: $800.00",
                status="success",
                timestamp=today,
                activity_metadata={"symbol": "TSLA"}
            )
        ]

        for activity in activities:
            db.add(activity)
        db.commit()

        from src.models.user import User, UserRole
        admin_user = User(
            email="admin2@test.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            first_name="Test",
            last_name="Admin"
        )

        import asyncio
        result = asyncio.run(get_api_usage(admin_user, db))

        assert result["summary"]["total_requests_today"] == 2
        assert len(result["by_provider"]) == 2

    def test_empty_api_calls_calculation(self, db: Session):
        """
        Test that when there are no activities, total API calls is 0.
        """
        from src.models.user import User, UserRole
        admin_user = User(
            email="admin3@test.com",
            password_hash="hashed",
            role=UserRole.ADMIN,
            first_name="Test",
            last_name="Admin"
        )

        import asyncio
        result = asyncio.run(get_api_usage(admin_user, db))

        assert result["summary"]["total_requests_today"] == 0
        assert len(result["by_provider"]) == 0
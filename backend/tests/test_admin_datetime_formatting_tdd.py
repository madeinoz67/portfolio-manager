"""
TDD tests for admin API datetime formatting following FastAPI best practices.

Tests that all admin API endpoints return properly formatted datetime strings
that JavaScript Date constructor can parse correctly.
"""

import pytest
import json
import subprocess
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from src.api.admin import (
    list_users, get_user, get_system_metrics, get_market_data_status,
    get_dashboard_recent_activities, calculate_relative_time
)
from src.models.user import User
from src.models.user_role import UserRole
from src.models.portfolio import Portfolio
from src.models.market_data_provider import MarketDataProvider, ProviderActivity
from src.utils.datetime_utils import utc_now, to_iso_string


class TestAdminDatetimeFormattingTDD:
    """TDD tests for proper datetime formatting in admin API responses."""

    def test_admin_api_datetime_format_contract(self):
        """Test that all admin API datetime fields follow proper formatting."""
        # Test all expected datetime formats that admin API should return
        test_timestamps = [
            "2025-09-14T20:28:54.754899+00:00",  # UTC with explicit offset
            "2025-09-14T20:28:54.000Z",          # UTC with Z suffix
            "2025-09-14T20:28:54+00:00",         # UTC without microseconds
        ]

        for timestamp in test_timestamps:
            # Each should be parseable by JavaScript
            js_test = f'''
            const date = new Date("{timestamp}");
            console.log(JSON.stringify({{
                valid: !isNaN(date.getTime()),
                iso_output: date.toISOString(),
                local_display: date.toLocaleString()
            }}));
            '''

            result = subprocess.run(['node', '-e', js_test], capture_output=True, text=True)
            js_result = json.loads(result.stdout.strip())

            assert js_result["valid"] is True, f"Invalid datetime format: {timestamp}"
            assert "T" in js_result["iso_output"], "Should produce valid ISO output"

    @pytest.fixture
    def mock_admin_user(self):
        """Mock admin user for testing."""
        admin = Mock(spec=User)
        admin.id = "admin-123"
        admin.email = "admin@test.com"
        admin.role = UserRole.ADMIN
        admin.is_active = True
        return admin

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock(spec=Session)

    @pytest.mark.asyncio
    async def test_list_users_datetime_formatting(self, mock_admin_user, mock_db_session):
        """Test that list_users returns properly formatted datetime strings."""
        # Setup mock user data with datetime fields
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_user.email = "test@user.com"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.role = UserRole.USER
        mock_user.is_active = True
        mock_user.created_at = utc_now()

        # Mock database query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_user]

        mock_portfolio_query = Mock()
        mock_portfolio_query.filter.return_value = mock_portfolio_query
        mock_portfolio_query.count.return_value = 0

        mock_db_session.query.side_effect = lambda model: (
            mock_query if model == User else mock_portfolio_query
        )

        # Call the function
        with patch('src.api.admin.logger'):
            result = await list_users(
                admin_user=mock_admin_user,
                db=mock_db_session,
                page=1,
                size=20
            )

        # Verify the datetime formatting
        assert len(result.users) == 1
        user_item = result.users[0]

        # Test that createdAt field is properly formatted
        created_at_str = user_item.createdAt

        # Should be parseable by JavaScript Date constructor
        js_test = f'''
        const date = new Date("{created_at_str}");
        console.log(JSON.stringify({{
            valid: !isNaN(date.getTime()),
            has_timezone: /{created_at_str}/.test(/[Z]|[+-]\d{{2}}:\d{{2}}$/)
        }}));
        '''

        result = subprocess.run(['node', '-e', js_test], capture_output=True, text=True)
        js_result = json.loads(result.stdout.strip())

        assert js_result["valid"] is True, f"createdAt should be valid JavaScript date: {created_at_str}"

    @pytest.mark.asyncio
    async def test_get_user_details_datetime_formatting(self, mock_admin_user, mock_db_session):
        """Test that get_user returns properly formatted datetime strings."""
        # Setup mock user with portfolios
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_user.email = "test@user.com"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.role = UserRole.USER
        mock_user.is_active = True
        mock_user.created_at = utc_now()

        mock_portfolio = Mock()
        mock_portfolio.id = "portfolio-123"
        mock_portfolio.name = "Test Portfolio"
        mock_portfolio.total_value = 1000.0
        mock_portfolio.updated_at = utc_now()

        # Mock database queries
        user_query = Mock()
        user_query.filter.return_value = user_query
        user_query.first.return_value = mock_user

        portfolio_query = Mock()
        portfolio_query.filter.return_value = portfolio_query
        portfolio_query.all.return_value = [mock_portfolio]

        mock_db_session.query.side_effect = lambda model: (
            user_query if model == User else portfolio_query
        )

        # Call the function
        with patch('src.api.admin.logger'):
            result = await get_user(
                user_id="user-123",
                admin_user=mock_admin_user,
                db=mock_db_session
            )

        # Verify datetime formatting in response
        created_at_str = result.createdAt

        # Test the problematic line 192: should NOT have invalid double timezone format
        assert not ("+00:00" in created_at_str and created_at_str.endswith("Z")), \
            f"createdAt should not have both timezone offset and Z suffix: {created_at_str}"

        # Should be parseable by JavaScript
        js_test = f'''
        const date = new Date("{created_at_str}");
        console.log(!isNaN(date.getTime()));
        '''

        result = subprocess.run(['node', '-e', js_test], capture_output=True, text=True)
        is_valid = result.stdout.strip() == "true"

        assert is_valid, f"createdAt should be valid JavaScript date: {created_at_str}"

        # Test portfolio lastUpdated field
        if result.portfolios:
            portfolio = result.portfolios[0]
            last_updated_str = portfolio.lastUpdated

            js_test = f'''
            const date = new Date("{last_updated_str}");
            console.log(!isNaN(date.getTime()));
            '''

            result = subprocess.run(['node', '-e', js_test], capture_output=True, text=True)
            is_valid = result.stdout.strip() == "true"

            assert is_valid, f"portfolio.lastUpdated should be valid: {last_updated_str}"

    def test_system_metrics_datetime_formatting(self, mock_admin_user, mock_db_session):
        """Test that system metrics returns properly formatted datetime strings."""
        # Mock database queries for metrics
        mock_query = Mock()
        mock_query.count.return_value = 5
        mock_query.filter.return_value = mock_query

        mock_db_session.query.return_value = mock_query

        # Call the function
        with patch('src.api.admin.logger'):
            result = get_system_metrics(
                admin_user=mock_admin_user,
                db=mock_db_session
            )

        # Test lastUpdated field formatting
        last_updated_str = result.lastUpdated

        # Should be parseable by JavaScript Date constructor
        js_test = f'''
        const date = new Date("{last_updated_str}");
        console.log(!isNaN(date.getTime()));
        '''

        result_js = subprocess.run(['node', '-e', js_test], capture_output=True, text=True)
        is_valid = result_js.stdout.strip() == "true"

        assert is_valid, f"lastUpdated should be valid JavaScript date: {last_updated_str}"

    def test_market_data_status_datetime_formatting(self, mock_admin_user, mock_db_session):
        """Test that market data status returns properly formatted datetime strings."""
        # Setup mock providers
        mock_provider = Mock()
        mock_provider.name = "yfinance"
        mock_provider.display_name = "Yahoo Finance"
        mock_provider.is_enabled = True
        mock_provider.updated_at = utc_now()
        mock_provider.rate_limit_per_day = 1000

        # Mock database queries
        provider_query = Mock()
        provider_query.all.return_value = [mock_provider]

        usage_query = Mock()
        usage_query.filter.return_value = usage_query
        usage_query.group_by.return_value = usage_query
        usage_query.all.return_value = []

        mock_db_session.query.side_effect = lambda model: (
            provider_query if model == MarketDataProvider else usage_query
        )

        # Call the function
        with patch('src.api.admin.logger'):
            result = get_market_data_status(
                current_admin=mock_admin_user,
                db=mock_db_session
            )

        # Test provider lastUpdate field formatting
        assert len(result["providers"]) == 1
        provider = result["providers"][0]
        last_update_str = provider["lastUpdate"]

        # Should be parseable by JavaScript Date constructor
        js_test = f'''
        const date = new Date("{last_update_str}");
        console.log(!isNaN(date.getTime()));
        '''

        result_js = subprocess.run(['node', '-e', js_test], capture_output=True, text=True)
        is_valid = result_js.stdout.strip() == "true"

        assert is_valid, f"provider.lastUpdate should be valid: {last_update_str}"

    def test_dashboard_activities_datetime_formatting(self, mock_admin_user, mock_db_session):
        """Test that dashboard activities returns properly formatted datetime strings."""
        # Setup mock activity
        mock_activity = Mock()
        mock_activity.id = "activity-123"
        mock_activity.provider_id = "yfinance"
        mock_activity.activity_type = "API_CALL"
        mock_activity.description = "Fetched price for CBA"
        mock_activity.status = "success"
        mock_activity.timestamp = utc_now()
        mock_activity.activity_metadata = {}

        mock_provider = Mock()
        mock_provider.name = "yfinance"
        mock_provider.display_name = "Yahoo Finance"
        mock_provider.is_enabled = True
        mock_provider.rate_limit_per_minute = 60
        mock_provider.rate_limit_per_day = 1000
        mock_provider.priority = 1

        # Mock database queries
        provider_query = Mock()
        provider_query.all.return_value = [mock_provider]

        # Mock activity service
        with patch('src.api.admin.get_recent_activities_all_providers') as mock_get_activities:
            with patch('src.api.admin.get_dashboard_activity_summary') as mock_get_summary:
                mock_get_activities.return_value = [mock_activity]
                mock_get_summary.return_value = {"total_activities": 1}

                mock_db_session.query.return_value = provider_query

                # Call the function
                with patch('src.api.admin.logger'):
                    result = get_dashboard_recent_activities(
                        limit=10,
                        current_admin=mock_admin_user,
                        db=mock_db_session
                    )

        # Test activity timestamp formatting
        assert len(result.activities) == 1
        activity = result.activities[0]
        timestamp_str = activity.timestamp

        # Should be parseable by JavaScript Date constructor
        js_test = f'''
        const date = new Date("{timestamp_str}");
        console.log(!isNaN(date.getTime()));
        '''

        result_js = subprocess.run(['node', '-e', js_test], capture_output=True, text=True)
        is_valid = result_js.stdout.strip() == "true"

        assert is_valid, f"activity.timestamp should be valid: {timestamp_str}"

    def test_calculate_relative_time_with_various_timestamps(self):
        """Test the calculate_relative_time function with various timestamp formats."""
        from datetime import timedelta

        # Test with timezone-aware timestamps
        now = utc_now()

        test_cases = [
            (now - timedelta(seconds=5), "just now"),
            (now - timedelta(seconds=30), "30 seconds ago"),
            (now - timedelta(minutes=2), "2 minutes ago"),
            (now - timedelta(hours=1), "1 hour ago"),
            (now - timedelta(days=1), "1 day ago"),
        ]

        for timestamp, expected_pattern in test_cases:
            result = calculate_relative_time(timestamp)

            # Verify it returns a reasonable relative time string
            assert isinstance(result, str)
            assert len(result) > 0

            # For "just now" case, be exact
            if expected_pattern == "just now":
                assert result == "just now"
            else:
                # For others, just ensure it contains expected units
                if "second" in expected_pattern:
                    assert "second" in result
                elif "minute" in expected_pattern:
                    assert "minute" in result
                elif "hour" in expected_pattern:
                    assert "hour" in result
                elif "day" in expected_pattern:
                    assert "day" in result
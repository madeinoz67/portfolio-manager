"""
Test Driven Development tests for real recent activity data functionality.
These tests define the expected behavior for capturing and retrieving
actual market data provider activity logs.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from src.core.database import get_db
from src.models.user import User, UserRole
from src.models.market_data import MarketDataProvider
from src.api.admin import get_provider_details


@pytest.fixture
def test_provider(db_session):
    """Create a test market data provider."""
    provider = MarketDataProvider(
        provider_id="alpha_vantage",
        provider_name="Alpha Vantage",
        is_enabled=True,
        api_endpoint="https://www.alphavantage.co/query",
        api_key_hash="test_hash",
        rate_limit_per_minute=5,
        rate_limit_per_day=500,
        cost_per_call=Decimal("0.0001"),
        priority=1
    )
    db_session.add(provider)
    db_session.commit()
    return provider


@pytest.fixture
def admin_user(db_session):
    """Create an admin user for testing."""
    user = User(
        email="admin@test.com",
        hashed_password="hashed",
        role=UserRole.ADMIN,
        first_name="Admin",
        last_name="User"
    )
    db_session.add(user)
    db_session.commit()
    return user


class TestRecentActivityDataModel:
    """Test the ProviderActivity data model and database operations."""

    def test_provider_activity_model_creation(self, db_session, test_provider):
        """Test that ProviderActivity records can be created and stored."""
        from src.models.market_data import ProviderActivity

        activity = ProviderActivity(
            provider_id=test_provider.provider_id,
            activity_type="API_CALL",
            description="Fetched price for AAPL",
            status="success",
            timestamp=datetime.utcnow(),
            metadata={"symbol": "AAPL", "response_time_ms": 245}
        )

        db_session.add(activity)
        db_session.commit()

        # Verify the activity was stored
        stored_activity = db_session.query(ProviderActivity).first()
        assert stored_activity is not None
        assert stored_activity.provider_id == test_provider.provider_id
        assert stored_activity.activity_type == "API_CALL"
        assert stored_activity.description == "Fetched price for AAPL"
        assert stored_activity.status == "success"
        assert stored_activity.metadata["symbol"] == "AAPL"

    def test_provider_activity_relationship(self, db_session, test_provider):
        """Test the relationship between Provider and ProviderActivity."""
        from src.models.market_data import ProviderActivity

        # Create multiple activities for the provider
        activities = []
        for i in range(3):
            activity = ProviderActivity(
                provider_id=test_provider.provider_id,
                activity_type="API_CALL",
                description=f"Test activity {i}",
                status="success" if i < 2 else "error",
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            )
            activities.append(activity)
            db_session.add(activity)

        db_session.commit()

        # Test the relationship works
        provider_with_activities = db_session.query(MarketDataProvider).filter(
            MarketDataProvider.provider_id == test_provider.provider_id
        ).first()

        assert len(provider_with_activities.recent_activities) == 3

    def test_activity_ordering_by_timestamp(self, db_session, test_provider):
        """Test that activities are ordered by timestamp (newest first)."""
        from src.models.market_data import ProviderActivity

        # Create activities with different timestamps
        base_time = datetime.utcnow()
        timestamps = [
            base_time - timedelta(hours=2),  # oldest
            base_time - timedelta(minutes=30),  # middle
            base_time,  # newest
        ]

        for i, timestamp in enumerate(timestamps):
            activity = ProviderActivity(
                provider_id=test_provider.provider_id,
                activity_type="API_CALL",
                description=f"Activity {i}",
                status="success",
                timestamp=timestamp
            )
            db_session.add(activity)

        db_session.commit()

        # Query activities ordered by timestamp (newest first)
        activities = db_session.query(ProviderActivity).filter(
            ProviderActivity.provider_id == test_provider.provider_id
        ).order_by(ProviderActivity.timestamp.desc()).all()

        assert len(activities) == 3
        assert activities[0].description == "Activity 2"  # newest
        assert activities[1].description == "Activity 1"  # middle
        assert activities[2].description == "Activity 0"  # oldest


class TestRecentActivityQueries:
    """Test database queries for retrieving recent activity data."""

    def test_get_recent_activities_for_provider(self, db_session, test_provider):
        """Test querying recent activities for a specific provider."""
        from src.models.market_data import ProviderActivity
        from src.services.activity_service import get_recent_activities

        # Create test activities
        for i in range(5):
            activity = ProviderActivity(
                provider_id=test_provider.provider_id,
                activity_type="API_CALL",
                description=f"Activity {i}",
                status="success",
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            )
            db_session.add(activity)

        db_session.commit()

        # Test the service function
        recent_activities = get_recent_activities(
            db_session, test_provider.provider_id, limit=3
        )

        assert len(recent_activities) == 3
        assert recent_activities[0].description == "Activity 0"  # newest first
        assert recent_activities[2].description == "Activity 2"  # third newest

    def test_get_recent_activities_with_status_filter(self, db_session, test_provider):
        """Test filtering activities by status."""
        from src.models.market_data import ProviderActivity
        from src.services.activity_service import get_recent_activities

        # Create activities with different statuses
        statuses = ["success", "error", "success", "warning", "error"]
        for i, status in enumerate(statuses):
            activity = ProviderActivity(
                provider_id=test_provider.provider_id,
                activity_type="API_CALL",
                description=f"Activity {i}",
                status=status,
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            )
            db_session.add(activity)

        db_session.commit()

        # Test filtering by error status
        error_activities = get_recent_activities(
            db_session, test_provider.provider_id, status_filter="error"
        )

        assert len(error_activities) == 2
        assert all(activity.status == "error" for activity in error_activities)

    def test_get_recent_activities_empty_result(self, db_session, test_provider):
        """Test handling when no activities exist."""
        from src.services.activity_service import get_recent_activities

        activities = get_recent_activities(
            db_session, test_provider.provider_id
        )

        assert activities == []

    def test_get_activities_across_multiple_providers(self, db_session):
        """Test querying activities with provider filtering."""
        from src.models.market_data import ProviderActivity
        from src.services.activity_service import get_recent_activities_all_providers

        # Create multiple providers
        providers = []
        for i in range(3):
            provider = MarketDataProvider(
                provider_id=f"provider_{i}",
                provider_name=f"Provider {i}",
                is_enabled=True,
                api_endpoint=f"https://api{i}.example.com",
                api_key_hash=f"hash_{i}",
                rate_limit_per_minute=5,
                rate_limit_per_day=500,
                cost_per_call=Decimal("0.001"),
                priority=i + 1
            )
            providers.append(provider)
            db_session.add(provider)

        db_session.commit()

        # Create activities for different providers
        for i, provider in enumerate(providers):
            for j in range(3):
                activity = ProviderActivity(
                    provider_id=provider.provider_id,
                    activity_type="API_CALL",
                    description=f"Provider {i} Activity {j}",
                    status="success",
                    timestamp=datetime.utcnow() - timedelta(minutes=i * 3 + j)
                )
                db_session.add(activity)

        db_session.commit()

        # Test getting activities for all providers
        all_activities = get_recent_activities_all_providers(db_session, limit=5)
        assert len(all_activities) == 5

        # Test filtering by specific provider
        provider_0_activities = get_recent_activities_all_providers(
            db_session, provider_filter="provider_0"
        )
        assert len(provider_0_activities) == 3
        assert all(act.provider_id == "provider_0" for act in provider_0_activities)

        # Test filtering by multiple providers
        filtered_activities = get_recent_activities_all_providers(
            db_session, provider_filter=["provider_0", "provider_2"]
        )
        assert len(filtered_activities) == 6
        provider_ids = {act.provider_id for act in filtered_activities}
        assert provider_ids == {"provider_0", "provider_2"}

    def test_get_activities_with_provider_and_status_filters(self, db_session):
        """Test combining provider and status filters."""
        from src.models.market_data import ProviderActivity
        from src.services.activity_service import get_recent_activities_all_providers

        # Create providers
        provider_a = MarketDataProvider(
            provider_id="provider_a",
            provider_name="Provider A",
            is_enabled=True,
            api_endpoint="https://api-a.example.com",
            api_key_hash="hash_a",
            rate_limit_per_minute=5,
            rate_limit_per_day=500,
            cost_per_call=Decimal("0.001"),
            priority=1
        )
        provider_b = MarketDataProvider(
            provider_id="provider_b",
            provider_name="Provider B",
            is_enabled=True,
            api_endpoint="https://api-b.example.com",
            api_key_hash="hash_b",
            rate_limit_per_minute=5,
            rate_limit_per_day=500,
            cost_per_call=Decimal("0.001"),
            priority=2
        )
        db_session.add(provider_a)
        db_session.add(provider_b)
        db_session.commit()

        # Create activities with different statuses
        activities_data = [
            ("provider_a", "success"),
            ("provider_a", "error"),
            ("provider_b", "success"),
            ("provider_b", "error"),
            ("provider_a", "warning"),
        ]

        for i, (provider_id, status) in enumerate(activities_data):
            activity = ProviderActivity(
                provider_id=provider_id,
                activity_type="API_CALL",
                description=f"Activity {i}",
                status=status,
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            )
            db_session.add(activity)

        db_session.commit()

        # Test combined filtering
        error_activities_provider_a = get_recent_activities_all_providers(
            db_session,
            provider_filter="provider_a",
            status_filter="error"
        )

        assert len(error_activities_provider_a) == 1
        assert error_activities_provider_a[0].provider_id == "provider_a"
        assert error_activities_provider_a[0].status == "error"


class TestRecentActivityService:
    """Test the activity service layer functions."""

    def test_log_provider_activity_success(self, db_session, test_provider):
        """Test logging a successful provider activity."""
        from src.services.activity_service import log_provider_activity

        log_provider_activity(
            db_session=db_session,
            provider_id=test_provider.provider_id,
            activity_type="API_CALL",
            description="Successfully fetched AAPL price",
            status="success",
            metadata={"symbol": "AAPL", "price": "150.25", "response_time": 234}
        )

        # Verify the activity was logged
        from src.models.market_data import ProviderActivity
        activity = db_session.query(ProviderActivity).first()

        assert activity is not None
        assert activity.provider_id == test_provider.provider_id
        assert activity.activity_type == "API_CALL"
        assert activity.description == "Successfully fetched AAPL price"
        assert activity.status == "success"
        assert activity.metadata["symbol"] == "AAPL"
        assert activity.metadata["price"] == "150.25"

    def test_log_provider_activity_error(self, db_session, test_provider):
        """Test logging a failed provider activity."""
        from src.services.activity_service import log_provider_activity

        log_provider_activity(
            db_session=db_session,
            provider_id=test_provider.provider_id,
            activity_type="API_CALL",
            description="Failed to fetch AAPL price - rate limited",
            status="error",
            metadata={"error_code": 429, "retry_after": 60}
        )

        # Verify the error activity was logged
        from src.models.market_data import ProviderActivity
        activity = db_session.query(ProviderActivity).first()

        assert activity is not None
        assert activity.status == "error"
        assert activity.metadata["error_code"] == 429

    def test_cleanup_old_activities(self, db_session, test_provider):
        """Test cleaning up old activity records."""
        from src.models.market_data import ProviderActivity
        from src.services.activity_service import cleanup_old_activities

        # Create activities spanning different time periods
        now = datetime.utcnow()
        timestamps = [
            now - timedelta(days=45),  # should be cleaned up
            now - timedelta(days=15),  # should remain
            now - timedelta(hours=1),  # should remain
        ]

        for i, timestamp in enumerate(timestamps):
            activity = ProviderActivity(
                provider_id=test_provider.provider_id,
                activity_type="API_CALL",
                description=f"Activity {i}",
                status="success",
                timestamp=timestamp
            )
            db_session.add(activity)

        db_session.commit()

        # Clean up activities older than 30 days
        cleanup_old_activities(db_session, days_to_keep=30)

        # Verify only recent activities remain
        remaining_activities = db_session.query(ProviderActivity).all()
        assert len(remaining_activities) == 2
        assert all(
            activity.timestamp > now - timedelta(days=30)
            for activity in remaining_activities
        )


class TestProviderDetailsWithRealActivity:
    """Test the provider details endpoint with real activity data."""

    def test_provider_details_includes_real_recent_activity(self, client, admin_user, test_provider, db_session):
        """Test that provider details endpoint returns real recent activity data."""
        from src.models.market_data import ProviderActivity

        # Create real activity data
        activities_data = [
            {
                "type": "API_CALL",
                "description": "Successfully fetched AAPL price",
                "status": "success",
                "timestamp": datetime.utcnow() - timedelta(minutes=5),
                "metadata": {"symbol": "AAPL", "response_time": 245}
            },
            {
                "type": "RATE_LIMIT",
                "description": "Rate limit reached, waiting 60 seconds",
                "status": "warning",
                "timestamp": datetime.utcnow() - timedelta(minutes=10),
                "metadata": {"wait_time": 60}
            },
            {
                "type": "API_ERROR",
                "description": "Failed to connect to API endpoint",
                "status": "error",
                "timestamp": datetime.utcnow() - timedelta(minutes=15),
                "metadata": {"error": "Connection timeout", "retry_count": 3}
            }
        ]

        for activity_data in activities_data:
            activity = ProviderActivity(
                provider_id=test_provider.provider_id,
                activity_type=activity_data["type"],
                description=activity_data["description"],
                status=activity_data["status"],
                timestamp=activity_data["timestamp"],
                metadata=activity_data["metadata"]
            )
            db_session.add(activity)

        db_session.commit()

        # Mock authentication
        with patch('src.api.admin.get_current_admin_user', return_value=admin_user):
            response = client.get(
                f"/api/v1/admin/market-data/providers/{test_provider.provider_id}/details"
            )

        assert response.status_code == 200
        data = response.json()

        # Verify recent activity is included and has real data
        assert "recentActivity" in data
        assert len(data["recentActivity"]) == 3

        # Verify activity data structure and content
        first_activity = data["recentActivity"][0]
        assert first_activity["type"] == "API_CALL"
        assert first_activity["description"] == "Successfully fetched AAPL price"
        assert first_activity["status"] == "success"
        assert "timestamp" in first_activity

        # Verify activities are ordered by timestamp (newest first)
        timestamps = [activity["timestamp"] for activity in data["recentActivity"]]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_provider_details_empty_activity_list(self, client, admin_user, test_provider):
        """Test provider details when no activities exist."""
        with patch('src.api.admin.get_current_admin_user', return_value=admin_user):
            response = client.get(
                f"/api/v1/admin/market-data/providers/{test_provider.provider_id}/details"
            )

        assert response.status_code == 200
        data = response.json()

        # Verify empty activity list is handled gracefully
        assert "recentActivity" in data
        assert data["recentActivity"] == []

    def test_provider_details_activity_limit(self, client, admin_user, test_provider, db_session):
        """Test that provider details limits the number of recent activities returned."""
        from src.models.market_data import ProviderActivity

        # Create more activities than the limit (assume limit is 10)
        for i in range(15):
            activity = ProviderActivity(
                provider_id=test_provider.provider_id,
                activity_type="API_CALL",
                description=f"Activity {i}",
                status="success",
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            )
            db_session.add(activity)

        db_session.commit()

        with patch('src.api.admin.get_current_admin_user', return_value=admin_user):
            response = client.get(
                f"/api/v1/admin/market-data/providers/{test_provider.provider_id}/details"
            )

        assert response.status_code == 200
        data = response.json()

        # Verify the limit is enforced
        assert len(data["recentActivity"]) == 10

        # Verify we get the most recent activities
        first_activity = data["recentActivity"][0]
        assert first_activity["description"] == "Activity 0"  # newest


class TestActivityIntegration:
    """Test integration between activity logging and market data operations."""

    def test_api_call_logs_activity(self, db_session, test_provider):
        """Test that making an API call automatically logs activity."""
        from src.services.market_data_service import fetch_price_with_logging
        from src.models.market_data import ProviderActivity

        # Mock the actual API call
        with patch('src.services.market_data_service.make_api_call') as mock_api:
            mock_api.return_value = {"price": 150.25, "timestamp": "2023-12-01T10:00:00Z"}

            # This should log the activity
            result = fetch_price_with_logging(
                db_session, test_provider.provider_id, "AAPL"
            )

            assert result is not None

            # Verify activity was logged
            activity = db_session.query(ProviderActivity).first()
            assert activity is not None
            assert activity.activity_type == "API_CALL"
            assert "AAPL" in activity.description
            assert activity.status == "success"

    def test_api_error_logs_activity(self, db_session, test_provider):
        """Test that API errors are logged as activities."""
        from src.services.market_data_service import fetch_price_with_logging
        from src.models.market_data import ProviderActivity

        # Mock the API call to raise an exception
        with patch('src.services.market_data_service.make_api_call') as mock_api:
            mock_api.side_effect = Exception("API rate limit exceeded")

            # This should log the error activity
            try:
                fetch_price_with_logging(
                    db_session, test_provider.provider_id, "AAPL"
                )
            except Exception:
                pass  # Expected to fail

            # Verify error activity was logged
            activity = db_session.query(ProviderActivity).first()
            assert activity is not None
            assert activity.activity_type == "API_ERROR"
            assert activity.status == "error"
            assert "rate limit" in activity.description.lower()


class TestRecentActivityApiEndpoints:
    """Test API endpoints for recent activity with provider filtering."""

    def test_get_all_activities_endpoint(self, client, admin_user, db_session):
        """Test endpoint for getting activities across all providers."""
        # Create multiple providers with activities
        providers = []
        for i in range(2):
            provider = MarketDataProvider(
                provider_id=f"test_provider_{i}",
                provider_name=f"Test Provider {i}",
                is_enabled=True,
                api_endpoint=f"https://api{i}.test.com",
                api_key_hash=f"hash_{i}",
                rate_limit_per_minute=5,
                rate_limit_per_day=500,
                cost_per_call=Decimal("0.001"),
                priority=i + 1
            )
            providers.append(provider)
            db_session.add(provider)

        db_session.commit()

        # Create activities for each provider
        from src.models.market_data import ProviderActivity
        for i, provider in enumerate(providers):
            for j in range(2):
                activity = ProviderActivity(
                    provider_id=provider.provider_id,
                    activity_type="API_CALL",
                    description=f"Provider {i} Activity {j}",
                    status="success" if j == 0 else "error",
                    timestamp=datetime.utcnow() - timedelta(minutes=i * 2 + j)
                )
                db_session.add(activity)

        db_session.commit()

        # Test the endpoint
        with patch('src.api.admin.get_current_admin_user', return_value=admin_user):
            response = client.get("/api/v1/admin/market-data/activities")

        assert response.status_code == 200
        data = response.json()

        assert "activities" in data
        assert len(data["activities"]) == 4  # 2 providers × 2 activities each

        # Verify activity structure
        first_activity = data["activities"][0]
        assert "providerId" in first_activity
        assert "providerName" in first_activity
        assert "type" in first_activity
        assert "description" in first_activity
        assert "status" in first_activity
        assert "timestamp" in first_activity

    def test_get_activities_with_provider_filter(self, client, admin_user, db_session):
        """Test filtering activities by provider via API."""
        # Create multiple providers
        provider_a = MarketDataProvider(
            provider_id="provider_a",
            provider_name="Provider A",
            is_enabled=True,
            api_endpoint="https://api-a.test.com",
            api_key_hash="hash_a",
            rate_limit_per_minute=5,
            rate_limit_per_day=500,
            cost_per_call=Decimal("0.001"),
            priority=1
        )
        provider_b = MarketDataProvider(
            provider_id="provider_b",
            provider_name="Provider B",
            is_enabled=True,
            api_endpoint="https://api-b.test.com",
            api_key_hash="hash_b",
            rate_limit_per_minute=5,
            rate_limit_per_day=500,
            cost_per_call=Decimal("0.001"),
            priority=2
        )
        db_session.add(provider_a)
        db_session.add(provider_b)
        db_session.commit()

        # Create activities
        from src.models.market_data import ProviderActivity
        for provider in [provider_a, provider_b]:
            for i in range(2):
                activity = ProviderActivity(
                    provider_id=provider.provider_id,
                    activity_type="API_CALL",
                    description=f"{provider.provider_name} Activity {i}",
                    status="success",
                    timestamp=datetime.utcnow() - timedelta(minutes=i)
                )
                db_session.add(activity)

        db_session.commit()

        # Test filtering by single provider
        with patch('src.api.admin.get_current_admin_user', return_value=admin_user):
            response = client.get("/api/v1/admin/market-data/activities?provider=provider_a")

        assert response.status_code == 200
        data = response.json()

        assert len(data["activities"]) == 2
        assert all(act["providerId"] == "provider_a" for act in data["activities"])

        # Test filtering by multiple providers
        with patch('src.api.admin.get_current_admin_user', return_value=admin_user):
            response = client.get("/api/v1/admin/market-data/activities?provider=provider_a&provider=provider_b")

        assert response.status_code == 200
        data = response.json()

        assert len(data["activities"]) == 4
        provider_ids = {act["providerId"] for act in data["activities"]}
        assert provider_ids == {"provider_a", "provider_b"}

    def test_get_activities_with_combined_filters(self, client, admin_user, db_session):
        """Test combining provider and status filters via API."""
        # Setup provider
        provider = MarketDataProvider(
            provider_id="test_provider",
            provider_name="Test Provider",
            is_enabled=True,
            api_endpoint="https://api.test.com",
            api_key_hash="hash",
            rate_limit_per_minute=5,
            rate_limit_per_day=500,
            cost_per_call=Decimal("0.001"),
            priority=1
        )
        db_session.add(provider)
        db_session.commit()

        # Create activities with different statuses
        from src.models.market_data import ProviderActivity
        statuses = ["success", "error", "success", "warning"]
        for i, status in enumerate(statuses):
            activity = ProviderActivity(
                provider_id=provider.provider_id,
                activity_type="API_CALL",
                description=f"Activity {i}",
                status=status,
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            )
            db_session.add(activity)

        db_session.commit()

        # Test combined filtering
        with patch('src.api.admin.get_current_admin_user', return_value=admin_user):
            response = client.get(
                f"/api/v1/admin/market-data/activities?provider={provider.provider_id}&status=error"
            )

        assert response.status_code == 200
        data = response.json()

        assert len(data["activities"]) == 1
        assert data["activities"][0]["status"] == "error"
        assert data["activities"][0]["providerId"] == provider.provider_id

    def test_get_activities_pagination(self, client, admin_user, db_session):
        """Test pagination for activities endpoint."""
        # Setup provider
        provider = MarketDataProvider(
            provider_id="test_provider",
            provider_name="Test Provider",
            is_enabled=True,
            api_endpoint="https://api.test.com",
            api_key_hash="hash",
            rate_limit_per_minute=5,
            rate_limit_per_day=500,
            cost_per_call=Decimal("0.001"),
            priority=1
        )
        db_session.add(provider)
        db_session.commit()

        # Create many activities
        from src.models.market_data import ProviderActivity
        for i in range(25):
            activity = ProviderActivity(
                provider_id=provider.provider_id,
                activity_type="API_CALL",
                description=f"Activity {i}",
                status="success",
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            )
            db_session.add(activity)

        db_session.commit()

        # Test pagination
        with patch('src.api.admin.get_current_admin_user', return_value=admin_user):
            response = client.get("/api/v1/admin/market-data/activities?page=1&size=10")

        assert response.status_code == 200
        data = response.json()

        assert len(data["activities"]) == 10
        assert "pagination" in data
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["size"] == 10
        assert data["pagination"]["total"] == 25
        assert data["pagination"]["pages"] == 3

        # Test second page
        with patch('src.api.admin.get_current_admin_user', return_value=admin_user):
            response = client.get("/api/v1/admin/market-data/activities?page=2&size=10")

        assert response.status_code == 200
        data = response.json()

        assert len(data["activities"]) == 10
        assert data["pagination"]["page"] == 2
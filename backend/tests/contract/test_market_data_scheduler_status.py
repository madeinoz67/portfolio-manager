"""
Contract tests for market data scheduler status endpoint.

Tests the API contract for getting background scheduler status and metrics.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.models.user import User, UserRole
from src.core.auth import create_access_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_token(db_session: Session):
    admin_user = User(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        password_hash="hashed_password",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin_user)
    db_session.commit()

    return create_access_token(data={"sub": admin_user.email})


class TestSchedulerStatusEndpoint:
    """Test scheduler status API endpoint contract."""

    def test_get_scheduler_status_success(self, client: TestClient, admin_token: str):
        """Test getting scheduler status returns proper structure."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/market-data/scheduler/status", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Verify contract structure
        assert "scheduler" in data
        assert "status" in data["scheduler"]  # 'running', 'stopped', 'error'
        assert "uptime_seconds" in data["scheduler"]
        assert "next_run_at" in data["scheduler"]
        assert "last_run_at" in data["scheduler"]
        assert "total_runs" in data["scheduler"]
        assert "successful_runs" in data["scheduler"]
        assert "failed_runs" in data["scheduler"]

        assert "recent_activity" in data
        assert "total_symbols_processed" in data["recent_activity"]
        assert "success_rate" in data["recent_activity"]
        assert "avg_response_time_ms" in data["recent_activity"]

        assert "provider_stats" in data
        assert isinstance(data["provider_stats"], dict)

        # Verify data types
        assert isinstance(data["scheduler"]["status"], str)
        assert isinstance(data["scheduler"]["uptime_seconds"], int)
        assert data["scheduler"]["next_run_at"] is None or isinstance(data["scheduler"]["next_run_at"], str)
        assert data["scheduler"]["last_run_at"] is None or isinstance(data["scheduler"]["last_run_at"], str)
        assert isinstance(data["scheduler"]["total_runs"], int)
        assert isinstance(data["scheduler"]["successful_runs"], int)
        assert isinstance(data["scheduler"]["failed_runs"], int)

        assert isinstance(data["recent_activity"]["total_symbols_processed"], int)
        assert isinstance(data["recent_activity"]["success_rate"], (int, float))
        assert isinstance(data["recent_activity"]["avg_response_time_ms"], (int, float, type(None)))

    def test_get_scheduler_status_unauthorized(self, client: TestClient):
        """Test scheduler status endpoint requires authentication."""
        response = client.get("/api/v1/market-data/scheduler/status")

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["error"] == "unauthorized"

    def test_get_scheduler_status_forbidden_non_admin(self, client: TestClient, db_session: Session):
        """Test scheduler status endpoint requires admin role."""
        # Create regular user token
        user = User(
            email="user@example.com",
            first_name="Regular",
            last_name="User",
            password_hash="hashed_password",
            role=UserRole.USER,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        user_token = create_access_token(data={"sub": user.email})
        headers = {"Authorization": f"Bearer {user_token}"}

        response = client.get("/api/v1/market-data/scheduler/status", headers=headers)

        assert response.status_code == 403
        data = response.json()
        assert "error" in data
        assert data["error"] == "forbidden"
        assert "Admin role required" in data["message"]

    def test_scheduler_status_response_structure_when_running(self, client: TestClient, admin_token: str):
        """Test scheduler status response when scheduler is running."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/market-data/scheduler/status", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # When scheduler is running
        if data["scheduler"]["status"] == "running":
            assert data["scheduler"]["uptime_seconds"] > 0
            assert data["scheduler"]["next_run_at"] is not None

        # Verify provider stats structure
        for provider_name, stats in data["provider_stats"].items():
            assert "calls_last_hour" in stats
            assert "success_rate" in stats
            assert "avg_response_time_ms" in stats
            assert "last_successful_call" in stats
            assert isinstance(stats["calls_last_hour"], int)
            assert isinstance(stats["success_rate"], (int, float))

    def test_scheduler_status_content_validation(self, client: TestClient, admin_token: str):
        """Test scheduler status content validation."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/market-data/scheduler/status", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Status should be one of expected values
        assert data["scheduler"]["status"] in ["running", "stopped", "error"]

        # Success rate should be between 0 and 1
        success_rate = data["recent_activity"]["success_rate"]
        assert 0.0 <= success_rate <= 1.0

        # Total runs should be >= successful + failed
        total = data["scheduler"]["total_runs"]
        successful = data["scheduler"]["successful_runs"]
        failed = data["scheduler"]["failed_runs"]
        assert total >= successful + failed  # Could be >= due to in-progress runs

        # Uptime should be non-negative
        assert data["scheduler"]["uptime_seconds"] >= 0
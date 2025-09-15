"""
Test scheduler pause functionality to verify the admin dashboard pause/resume works correctly.

This test follows TDD approach - first the tests, then fix the implementation.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.core.dependencies import get_db
from src.services.scheduler_service import get_scheduler_service, reset_scheduler_service, SchedulerState
from tests.conftest import get_admin_jwt_token


class TestSchedulerPauseFunctionality:
    """Test scheduler pause/resume functionality for admin dashboard."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, db_session: Session):
        """Reset scheduler service before each test."""
        reset_scheduler_service()
        yield
        reset_scheduler_service()

    def test_scheduler_can_be_paused_when_running(self, db_session: Session):
        """Test that a running scheduler can be paused via API."""
        client = TestClient(app)

        # Override db dependency
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            # Get admin token for auth
            admin_token = get_admin_jwt_token(db_session)

            # First, start the scheduler
            scheduler = get_scheduler_service(db_session)
            start_success = scheduler.start()
            assert start_success, "Failed to start scheduler for test"
            assert scheduler.state == SchedulerState.RUNNING

            # Test pausing via admin API endpoint
            response = client.post(
                "/api/v1/admin/scheduler/control",
                json={"action": "pause"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()

            # Verify response structure
            assert data["success"] is True
            assert "paused" in data["message"].lower()
            assert data["newState"] == "paused"

            # Verify scheduler state changed
            updated_scheduler = get_scheduler_service(db_session)
            assert updated_scheduler.state == SchedulerState.PAUSED

        finally:
            app.dependency_overrides.clear()

    def test_scheduler_can_be_resumed_when_paused(self, db_session: Session):
        """Test that a paused scheduler can be resumed via API."""
        client = TestClient(app)

        # Override db dependency
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            # Setup: start then pause scheduler
            scheduler = get_scheduler_service(db_session)
            scheduler.start()
            pause_success = scheduler.pause()
            assert pause_success, "Failed to pause scheduler for test setup"
            assert scheduler.state == SchedulerState.PAUSED

            # Test resuming via admin API endpoint
            response = client.post(
                "/api/v1/admin/scheduler/control",
                json={"action": "resume"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()

            # Verify response structure
            assert data["success"] is True
            assert "resumed" in data["message"].lower()
            assert data["newState"] == "running"

            # Verify scheduler state changed
            updated_scheduler = get_scheduler_service(db_session)
            assert updated_scheduler.state == SchedulerState.RUNNING

        finally:
            app.dependency_overrides.clear()

    def test_scheduler_pause_with_duration(self, db_session: Session):
        """Test that scheduler can be paused for a specific duration."""
        client = TestClient(app)

        # Override db dependency
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            # Setup: start scheduler
            scheduler = get_scheduler_service(db_session)
            scheduler.start()
            assert scheduler.state == SchedulerState.RUNNING

            # Test pausing with duration
            response = client.post(
                "/api/v1/admin/scheduler/control",
                json={"action": "pause", "durationMinutes": 30},
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()

            # Verify response
            assert data["success"] is True
            assert "30 minutes" in data["message"]
            assert data["newState"] == "paused"

            # Verify scheduler state and pause_until is set
            updated_scheduler = get_scheduler_service(db_session)
            assert updated_scheduler.state == SchedulerState.PAUSED
            status_info = updated_scheduler.status_info
            assert status_info["pause_until"] is not None

        finally:
            app.dependency_overrides.clear()

    def test_cannot_pause_already_paused_scheduler(self, db_session: Session):
        """Test that pausing an already paused scheduler returns appropriate error."""
        client = TestClient(app)

        # Override db dependency
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            # Setup: start then pause scheduler
            scheduler = get_scheduler_service(db_session)
            scheduler.start()
            scheduler.pause()
            assert scheduler.state == SchedulerState.PAUSED

            # Try to pause again
            response = client.post(
                "/api/v1/admin/scheduler/control",
                json={"action": "pause"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            # Should still return 200 but with success=False
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "cannot pause" in data["message"].lower() or "already" in data["message"].lower()

        finally:
            app.dependency_overrides.clear()

    def test_cannot_resume_running_scheduler(self, db_session: Session):
        """Test that resuming a running scheduler returns appropriate error."""
        client = TestClient(app)

        # Override db dependency
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            # Setup: start scheduler
            scheduler = get_scheduler_service(db_session)
            scheduler.start()
            assert scheduler.state == SchedulerState.RUNNING

            # Try to resume running scheduler
            response = client.post(
                "/api/v1/admin/scheduler/control",
                json={"action": "resume"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            # Should return 200 but with success=False
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "cannot resume" in data["message"].lower() or "not paused" in data["message"].lower()

        finally:
            app.dependency_overrides.clear()

    def test_scheduler_status_endpoint_returns_correct_state(self, db_session: Session):
        """Test that the scheduler status endpoint returns correct state information."""
        client = TestClient(app)

        # Override db dependency
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            # Test status when stopped
            response = client.get(
                "/api/v1/admin/scheduler/status",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["state"] == "stopped"
            assert data["schedulerName"] == "market_data_scheduler"

            # Start scheduler and test status
            scheduler = get_scheduler_service(db_session)
            scheduler.start()

            response = client.get(
                "/api/v1/admin/scheduler/status",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["state"] == "running"
            assert data["nextRun"] is not None

            # Pause scheduler and test status
            scheduler.pause()

            response = client.get(
                "/api/v1/admin/scheduler/status",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["state"] == "paused"

        finally:
            app.dependency_overrides.clear()

    def test_frontend_api_compatibility(self, db_session: Session):
        """Test that the API responses match what the frontend expects."""
        client = TestClient(app)

        # Override db dependency
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            # Start scheduler first
            scheduler = get_scheduler_service(db_session)
            scheduler.start()

            # Test the pause action
            response = client.post(
                "/api/v1/admin/scheduler/control",
                json={"action": "pause"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
            data = response.json()

            # Verify all required fields are present for frontend
            required_fields = ["schedulerName", "action", "success", "message", "newState", "status"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

            # Verify status object has all required nested fields
            status = data["status"]
            status_required_fields = ["schedulerName", "state", "lastRun", "nextRun", "pauseUntil", "errorMessage", "configuration", "uptimeSeconds"]
            for field in status_required_fields:
                assert field in status, f"Missing required status field: {field}"

        finally:
            app.dependency_overrides.clear()

    def test_scheduler_can_be_started_when_stopped(self, db_session: Session):
        """Test that a stopped scheduler can be started via API (as requested by user)."""
        client = TestClient(app)
        admin_token = get_admin_jwt_token(db_session)

        # Override db dependency
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            # Ensure scheduler is stopped
            scheduler = get_scheduler_service(db_session)
            assert scheduler.state == SchedulerState.STOPPED

            # Test starting via admin API endpoint
            response = client.post(
                "/api/v1/admin/scheduler/control",
                json={"action": "start"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()

            # Verify response structure
            assert data["success"] is True
            assert "started" in data["message"].lower()
            assert data["newState"] == "running"

            # Verify scheduler state changed
            updated_scheduler = get_scheduler_service(db_session)
            assert updated_scheduler.state == SchedulerState.RUNNING

        finally:
            app.dependency_overrides.clear()

    def test_scheduler_can_be_stopped_when_running(self, db_session: Session):
        """Test that a running scheduler can be stopped via API."""
        client = TestClient(app)
        admin_token = get_admin_jwt_token(db_session)

        # Override db dependency
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            # Setup: start scheduler
            scheduler = get_scheduler_service(db_session)
            scheduler.start()
            assert scheduler.state == SchedulerState.RUNNING

            # Test stopping via admin API endpoint
            response = client.post(
                "/api/v1/admin/scheduler/control",
                json={"action": "stop", "reason": "admin_request"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()

            # Verify response structure
            assert data["success"] is True
            assert "stopped" in data["message"].lower()
            assert data["newState"] == "stopped"

            # Verify scheduler state changed
            updated_scheduler = get_scheduler_service(db_session)
            assert updated_scheduler.state == SchedulerState.STOPPED

        finally:
            app.dependency_overrides.clear()

    def test_frontend_scheduler_status_structure_compatibility(self, db_session: Session):
        """Test that scheduler status API returns structure expected by frontend admin dashboard."""
        client = TestClient(app)
        admin_token = get_admin_jwt_token(db_session)

        # Override db dependency
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            # Get status for stopped scheduler
            response = client.get(
                "/api/v1/admin/scheduler/status",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
            data = response.json()

            # Frontend checks for schedulerStatus.scheduler?.status
            # But we should return the correct structure
            expected_fields = ["schedulerName", "state", "lastRun", "nextRun", "pauseUntil", "errorMessage", "configuration", "uptimeSeconds"]
            for field in expected_fields:
                assert field in data, f"Missing field {field} in scheduler status response"

            # The frontend expects 'state' field to match one of: running, paused, stopped, error
            assert data["state"] in ["running", "paused", "stopped", "error"]

        finally:
            app.dependency_overrides.clear()
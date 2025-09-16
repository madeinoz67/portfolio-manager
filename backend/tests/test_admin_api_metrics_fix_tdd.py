"""
TDD test to verify admin API now properly exposes scheduler metrics.

Tests that the /api/v1/admin/scheduler/status endpoint returns execution metrics.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.services.scheduler_service import get_scheduler_service


class TestAdminAPIMetricsFix:
    """Test that admin API properly exposes scheduler metrics after fix."""

    @pytest.mark.asyncio
    async def test_admin_scheduler_status_includes_execution_metrics(self, db_session: Session):
        """
        PASSING TEST: Admin scheduler status endpoint should now include execution metrics.

        This test verifies the fix for exposing metrics through the API.
        """

        # Ensure scheduler has some metrics
        scheduler = get_scheduler_service(db_session)
        scheduler.record_execution_success(symbols_processed=8)
        scheduler.record_execution_failure("Test error")
        scheduler.record_execution_success(symbols_processed=12)

        # Verify scheduler service has the metrics
        status_info = scheduler.status_info
        assert status_info["total_executions"] == 3
        assert status_info["successful_executions"] == 2
        assert status_info["failed_executions"] == 1
        assert status_info["total_symbols_processed"] == 20

        # Test by directly calling the endpoint function instead of through HTTP
        from src.api.admin import get_scheduler_status
        from src.models.user import User

        # Create mock admin user
        mock_admin = MagicMock(spec=User)
        mock_admin.email = "admin@test.com"

        # Call the endpoint function directly
        result = await get_scheduler_status(current_admin=mock_admin, db=db_session)

        # Convert result to dict for testing
        data = result.model_dump()
        print(f"Admin scheduler status response: {data}")

        # Should now include execution metrics (using frontend field names)
        assert "total_runs" in data, "API response should include total_runs"
        assert "successful_runs" in data, "API response should include successful_runs"
        assert "failed_runs" in data, "API response should include failed_runs"
        assert "symbols_processed" in data, "API response should include symbols_processed"
        assert "success_rate" in data, "API response should include success_rate"

        # Values should match scheduler service
        assert data["total_runs"] == 3, f"Expected total_runs=3, got {data['total_runs']}"
        assert data["successful_runs"] == 2, f"Expected successful_runs=2, got {data['successful_runs']}"
        assert data["failed_runs"] == 1, f"Expected failed_runs=1, got {data['failed_runs']}"
        assert data["symbols_processed"] == 20, f"Expected symbols_processed=20, got {data['symbols_processed']}"

        # Success rate should be calculated (2 successful out of 3 total = 66.67%)
        expected_rate = (2 / 3) * 100
        assert abs(data["success_rate"] - expected_rate) < 0.01, \
            f"Expected success_rate={expected_rate:.2f}%, got {data['success_rate']}"

    @patch('src.core.dependencies.get_current_admin_user')
    def test_admin_scheduler_status_with_no_executions(self, mock_admin_user, db_session: Session):
        """
        TEST: Admin scheduler status should handle case with no executions gracefully.

        Should return zeros for metrics when no executions have occurred.
        """
        # Mock admin user
        mock_admin_user.return_value = MagicMock(email="admin@test.com")

        # Reset scheduler to fresh state
        from src.services.scheduler_service import reset_scheduler_service
        reset_scheduler_service()

        # Get fresh scheduler with no executions
        scheduler = get_scheduler_service(db_session)
        status_info = scheduler.status_info

        # Should have zero metrics
        assert status_info["total_executions"] == 0
        assert status_info["successful_executions"] == 0
        assert status_info["failed_executions"] == 0
        assert status_info["total_symbols_processed"] == 0

        client = TestClient(app)

        response = client.get("/api/v1/admin/scheduler/status")
        assert response.status_code == 200

        data = response.json()

        # Should return zeros for all metrics
        assert data["totalRuns"] == 0
        assert data["successful"] == 0
        assert data["failed"] == 0
        assert data["symbolsProcessed"] == 0
        assert data["successRate"] == 0.0

    @patch('src.core.dependencies.get_current_admin_user')
    def test_scheduler_control_response_includes_metrics(self, mock_admin_user, db_session: Session):
        """
        TEST: Scheduler control responses should also include updated metrics.

        Control actions like pause/resume should return status with metrics.
        """
        # Mock admin user
        mock_admin_user.return_value = MagicMock(email="admin@test.com")

        # Add some execution history
        scheduler = get_scheduler_service(db_session)
        scheduler.record_execution_success(symbols_processed=5)

        client = TestClient(app)

        # Test control action (pause)
        control_data = {
            "action": "pause",
            "durationMinutes": 10,
            "reason": "test pause"
        }

        response = client.post("/api/v1/admin/scheduler/control", json=control_data)
        assert response.status_code == 200

        data = response.json()
        print(f"Scheduler control response: {data}")

        # Should include status with metrics
        assert "status" in data
        status = data["status"]

        assert "totalRuns" in status
        assert "successful" in status
        assert "failed" in status
        assert "symbolsProcessed" in status
        assert "successRate" in status

        # Should reflect execution history
        assert status["totalRuns"] >= 1
        assert status["successful"] >= 1
        assert status["symbolsProcessed"] >= 5

    def test_api_response_format_matches_ui_expectations(self):
        """
        TEST: API response format should match what UI expects.

        Field names should match the screenshot expectations.
        """
        # Based on the screenshot, UI expects:
        # Total Runs, Successful, Failed, Symbols Processed, Success Rate

        expected_fields = {
            "totalRuns": int,
            "successful": int,
            "failed": int,
            "symbolsProcessed": int,
            "successRate": float
        }

        # Import the model to check field definitions
        from src.api.admin import SchedulerStatus

        # Check that model has all expected fields with correct types
        model_fields = SchedulerStatus.model_fields

        for field_name, expected_type in expected_fields.items():
            assert field_name in model_fields, f"SchedulerStatus missing field: {field_name}"

            field_info = model_fields[field_name]
            field_type = field_info.annotation

            # Handle Optional types and default values
            if hasattr(field_type, '__origin__'):
                # For Optional[type] or Union types
                field_type = field_type.__args__[0] if field_type.__args__ else field_type

            assert field_type == expected_type, \
                f"Field {field_name} has type {field_type}, expected {expected_type}"
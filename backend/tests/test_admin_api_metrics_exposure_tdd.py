"""
TDD tests to diagnose where scheduler metrics are lost between service and UI.

The Last Run field shows real timestamps (proving integration works) but
Total Runs/Successful/Failed still show 0, indicating an API exposure issue.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.services.scheduler_service import get_scheduler_service


class TestAdminAPIMetricsExposure:
    """Test that admin API properly exposes scheduler metrics to UI."""

    def test_scheduler_service_has_metrics_after_execution(self, db_session: Session):
        """
        PASSING TEST: Verify scheduler service has metrics after execution.

        This confirms the service-level metrics are working.
        """
        scheduler = get_scheduler_service(db_session)

        # Simulate execution
        scheduler.record_execution_success(symbols_processed=5)

        status = scheduler.status_info

        # These should work (proven by previous tests)
        assert status["total_executions"] > 0, "Service should track total executions"
        assert status["successful_executions"] > 0, "Service should track successful executions"
        assert status["total_symbols_processed"] >= 5, "Service should track symbols processed"

    def test_admin_api_scheduler_endpoint_exists(self):
        """
        FAILING TEST: Find the admin API endpoint that feeds scheduler status.

        Need to identify which endpoint the UI calls to get scheduler data.
        """
        client = TestClient(app)

        # Possible admin API endpoints for scheduler status
        possible_endpoints = [
            "/api/v1/admin/scheduler/status",
            "/api/v1/admin/scheduler",
            "/api/v1/admin/dashboard/scheduler",
            "/api/v1/admin/system/scheduler",
            "/api/v1/market-data/scheduler/status"
        ]

        for endpoint in possible_endpoints:
            try:
                response = client.get(endpoint, headers={"Authorization": "Bearer fake_token"})
                if response.status_code != 404:
                    print(f"Found scheduler endpoint: {endpoint} -> {response.status_code}")

                    if response.status_code == 200:
                        data = response.json()
                        print(f"Response structure: {data}")

                        # This endpoint should expose scheduler metrics
                        assert "total_runs" in data or "total_executions" in data, \
                            f"Endpoint {endpoint} should expose total_runs/total_executions"

                        return  # Found working endpoint

            except Exception as e:
                print(f"Error testing {endpoint}: {e}")

        assert False, "No admin API endpoint found that exposes scheduler metrics"

    def test_market_data_scheduler_status_endpoint_response(self, db_session: Session):
        """
        FAILING TEST: Market data scheduler endpoint should expose execution metrics.

        Test the /api/v1/market-data/scheduler/status endpoint specifically.
        """
        # First ensure scheduler has metrics
        scheduler = get_scheduler_service(db_session)
        scheduler.record_execution_success(symbols_processed=3)

        client = TestClient(app)

        # This endpoint likely exists based on the codebase structure
        response = client.get("/api/v1/market-data/scheduler/status")

        assert response.status_code == 200, f"Scheduler status endpoint should exist, got {response.status_code}"

        data = response.json()
        print(f"Market data scheduler status response: {data}")

        # Should expose the metrics we added
        assert "total_executions" in data or "total_runs" in data, \
            "API should expose total execution count"
        assert "successful_executions" in data or "successful" in data, \
            "API should expose successful execution count"
        assert "failed_executions" in data or "failed" in data, \
            "API should expose failed execution count"

    def test_admin_scheduler_control_endpoint_response(self, db_session: Session):
        """
        FAILING TEST: Admin scheduler control endpoint should expose metrics.

        Test admin-specific scheduler endpoints.
        """
        # Ensure scheduler has metrics
        scheduler = get_scheduler_service(db_session)
        scheduler.record_execution_success(symbols_processed=7)

        client = TestClient(app)

        # Test admin scheduler endpoint
        response = client.get(
            "/api/v1/admin/scheduler/status",
            headers={"Authorization": "Bearer fake_admin_token"}
        )

        if response.status_code == 404:
            # Try alternative endpoints
            alternative_endpoints = [
                "/api/v1/admin/scheduler",
                "/api/v1/admin/dashboard/scheduler"
            ]

            for endpoint in alternative_endpoints:
                alt_response = client.get(
                    endpoint,
                    headers={"Authorization": "Bearer fake_admin_token"}
                )
                if alt_response.status_code != 404:
                    response = alt_response
                    break

        print(f"Admin scheduler endpoint response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Admin scheduler response data: {data}")

            # Should include execution metrics for admin UI
            assert "total_executions" in data, "Admin API should expose total_executions"
            assert "successful_executions" in data, "Admin API should expose successful_executions"

    def test_api_response_format_matches_ui_expectations(self, db_session: Session):
        """
        FAILING TEST: API response should match what the UI expects.

        Based on the screenshot, UI expects:
        - Total Runs
        - Successful
        - Failed
        - Symbols Processed
        - Success Rate
        """
        scheduler = get_scheduler_service(db_session)
        scheduler.record_execution_success(symbols_processed=4)
        scheduler.record_execution_failure("Test error")

        # The UI likely calls a specific endpoint - need to find which one
        client = TestClient(app)

        # Try to find the endpoint that should return data in UI format
        test_endpoints = [
            "/api/v1/market-data/scheduler/status",
            "/api/v1/admin/scheduler/status"
        ]

        for endpoint in test_endpoints:
            try:
                response = client.get(endpoint)
                if response.status_code == 200:
                    data = response.json()

                    # Check if response format matches UI expectations
                    ui_expected_fields = [
                        "total_runs", "successful", "failed",
                        "symbols_processed", "success_rate"
                    ]

                    # Alternative field names that might be used
                    alt_field_mappings = {
                        "total_runs": ["total_executions"],
                        "successful": ["successful_executions"],
                        "failed": ["failed_executions"],
                        "symbols_processed": ["total_symbols_processed"],
                        "success_rate": ["success_rate_percent"]
                    }

                    missing_fields = []
                    for field in ui_expected_fields:
                        if field not in data:
                            alt_fields = alt_field_mappings.get(field, [])
                            if not any(alt in data for alt in alt_fields):
                                missing_fields.append(field)

                    if missing_fields:
                        print(f"Endpoint {endpoint} missing UI fields: {missing_fields}")
                        print(f"Available fields: {list(data.keys())}")
                    else:
                        print(f"Endpoint {endpoint} has all expected UI fields")
                        return  # Found working endpoint

            except Exception as e:
                print(f"Error testing {endpoint}: {e}")

        assert False, "No API endpoint found with correct format for UI scheduler metrics"

    def test_scheduler_status_info_contains_all_metrics(self, db_session: Session):
        """
        PASSING TEST: Verify scheduler.status_info contains all needed metrics.

        This should pass - confirms the metrics exist at service level.
        """
        scheduler = get_scheduler_service(db_session)

        # Add some execution data
        scheduler.record_execution_success(symbols_processed=6)
        scheduler.record_execution_failure("Test failure")

        status = scheduler.status_info

        # All these should exist based on our implementation
        required_fields = [
            "total_executions", "successful_executions", "failed_executions",
            "total_symbols_processed", "success_rate_percent", "last_run"
        ]

        for field in required_fields:
            assert field in status, f"scheduler.status_info missing {field}"

        # Values should be reasonable
        assert status["total_executions"] >= 2, "Should have at least 2 executions"
        assert status["successful_executions"] >= 1, "Should have at least 1 success"
        assert status["failed_executions"] >= 1, "Should have at least 1 failure"
        assert status["total_symbols_processed"] >= 6, "Should have processed symbols"
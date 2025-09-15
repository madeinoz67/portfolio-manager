"""
Integration test suite for complete admin service audit system.

Tests the end-to-end audit functionality for provider and scheduler control
through actual API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from src.main import app
from src.models.audit_log import AuditLog, AuditEventType
from src.models.user import User
from src.models.user_role import UserRole
from src.models.market_data_provider import MarketDataProvider
from src.services.scheduler_service import reset_scheduler_service


class TestAdminAuditIntegration:
    """Test complete admin audit system integration."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def admin_user(self, db_session: Session) -> User:
        """Create test admin user."""
        admin = User(
            id=uuid4(),
            email="admin@integration.com",
            first_name="Integration",
            last_name="Admin",
            role=UserRole.ADMIN,
            password_hash="test_hash"
        )
        db_session.add(admin)
        db_session.commit()
        return admin

    @pytest.fixture
    def test_provider(self, db_session: Session) -> MarketDataProvider:
        """Create test market data provider."""
        provider = MarketDataProvider(
            name="test_provider",
            display_name="Test Provider",
            is_enabled=False,
            rate_limit_per_minute=60,
            rate_limit_per_day=1000,
            priority=1
        )
        db_session.add(provider)
        db_session.commit()
        return provider

    @pytest.fixture
    def admin_headers(self, admin_user: User):
        """Create admin authentication headers."""
        # This would normally use JWT tokens, but for testing we'll mock
        return {"Authorization": f"Bearer test_admin_token_{admin_user.id}"}

    @pytest.fixture(autouse=True)
    def reset_scheduler(self):
        """Reset scheduler service before each test."""
        reset_scheduler_service()
        yield
        reset_scheduler_service()

    def test_provider_toggle_creates_audit_entry(
        self, client: TestClient, admin_user: User, test_provider: MarketDataProvider,
        admin_headers: dict, db_session: Session
    ):
        """Test that provider toggle API creates audit entries."""
        # Mock admin authentication for this test
        from unittest.mock import patch

        with patch('src.core.dependencies.get_current_admin_user', return_value=admin_user):
            # Act - Toggle provider (enable it)
            response = client.patch(
                f"/api/v1/admin/market-data/providers/{test_provider.name}/toggle",
                headers=admin_headers
            )

            # Assert - API response is successful
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["isEnabled"] is True
            assert response_data["providerId"] == test_provider.name

        # Assert - Audit entry was created
        audit_entry = db_session.query(AuditLog).filter(
            AuditLog.event_type == AuditEventType.PROVIDER_ENABLED,
            AuditLog.entity_id == test_provider.name
        ).first()

        assert audit_entry is not None
        assert audit_entry.user_id == admin_user.id
        assert audit_entry.entity_type == "market_data_provider"
        assert audit_entry.event_description == f"Market data provider '{test_provider.display_name}' enabled"

    def test_scheduler_control_creates_audit_entries(
        self, client: TestClient, admin_user: User, admin_headers: dict, db_session: Session
    ):
        """Test that scheduler control API creates audit entries."""
        from unittest.mock import patch

        with patch('src.core.dependencies.get_current_admin_user', return_value=admin_user):
            # Test 1: Start scheduler
            start_response = client.post(
                "/api/v1/admin/scheduler/control",
                headers=admin_headers,
                json={
                    "action": "start",
                    "configuration": {
                        "interval_minutes": 15,
                        "enabled_providers": ["yfinance"]
                    }
                }
            )

            assert start_response.status_code == 200
            start_data = start_response.json()
            assert start_data["success"] is True
            assert start_data["action"] == "start"
            assert start_data["newState"] == "running"

            # Test 2: Pause scheduler
            pause_response = client.post(
                "/api/v1/admin/scheduler/control",
                headers=admin_headers,
                json={
                    "action": "pause",
                    "durationMinutes": 30
                }
            )

            assert pause_response.status_code == 200
            pause_data = pause_response.json()
            assert pause_data["success"] is True
            assert pause_data["newState"] == "paused"

            # Test 3: Resume scheduler
            resume_response = client.post(
                "/api/v1/admin/scheduler/control",
                headers=admin_headers,
                json={"action": "resume"}
            )

            assert resume_response.status_code == 200
            resume_data = resume_response.json()
            assert resume_data["success"] is True
            assert resume_data["newState"] == "running"

            # Test 4: Stop scheduler
            stop_response = client.post(
                "/api/v1/admin/scheduler/control",
                headers=admin_headers,
                json={
                    "action": "stop",
                    "reason": "maintenance"
                }
            )

            assert stop_response.status_code == 200
            stop_data = stop_response.json()
            assert stop_data["success"] is True
            assert stop_data["newState"] == "stopped"

        # Assert - All audit entries were created
        audit_entries = db_session.query(AuditLog).filter(
            AuditLog.entity_type == "scheduler",
            AuditLog.entity_id == "market_data_scheduler"
        ).order_by(AuditLog.timestamp).all()

        assert len(audit_entries) == 4

        # Verify sequence
        assert audit_entries[0].event_type == AuditEventType.SCHEDULER_STARTED
        assert audit_entries[1].event_type == AuditEventType.SCHEDULER_PAUSED
        assert audit_entries[2].event_type == AuditEventType.SCHEDULER_RESUMED
        assert audit_entries[3].event_type == AuditEventType.SCHEDULER_STOPPED

        # Verify all entries have correct user
        for entry in audit_entries:
            assert entry.user_id == admin_user.id

    def test_scheduler_configuration_creates_audit_entry(
        self, client: TestClient, admin_user: User, admin_headers: dict, db_session: Session
    ):
        """Test that scheduler configuration updates create audit entries."""
        from unittest.mock import patch

        with patch('src.core.dependencies.get_current_admin_user', return_value=admin_user):
            # Act - Update scheduler configuration
            response = client.patch(
                "/api/v1/admin/scheduler/configuration",
                headers=admin_headers,
                json={
                    "intervalMinutes": 10,
                    "maxConcurrentJobs": 8,
                    "bulkMode": False
                }
            )

            # Assert - API response is successful
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert "intervalMinutes" in response_data["changes"]
            assert "maxConcurrentJobs" in response_data["changes"]
            assert "bulkMode" in response_data["changes"]

        # Assert - Audit entry was created
        audit_entry = db_session.query(AuditLog).filter(
            AuditLog.event_type == AuditEventType.SCHEDULER_CONFIGURED,
            AuditLog.entity_id == "market_data_scheduler"
        ).first()

        assert audit_entry is not None
        assert audit_entry.user_id == admin_user.id
        assert audit_entry.entity_type == "scheduler"
        assert "configuration updated" in audit_entry.event_description

        # Verify metadata contains changes
        metadata = audit_entry.event_metadata
        assert "changes" in metadata
        changes = metadata["changes"]
        assert "intervalMinutes" in changes
        assert changes["intervalMinutes"]["old"] == 15
        assert changes["intervalMinutes"]["new"] == 10

    def test_audit_logs_are_retrievable_via_admin_api(
        self, client: TestClient, admin_user: User, test_provider: MarketDataProvider,
        admin_headers: dict, db_session: Session
    ):
        """Test that audit logs can be retrieved through admin API."""
        from unittest.mock import patch

        with patch('src.core.dependencies.get_current_admin_user', return_value=admin_user):
            # Generate some audit data first
            client.patch(
                f"/api/v1/admin/market-data/providers/{test_provider.name}/toggle",
                headers=admin_headers
            )

            client.post(
                "/api/v1/admin/scheduler/control",
                headers=admin_headers,
                json={"action": "start"}
            )

            # Act - Retrieve audit logs
            audit_response = client.get(
                "/api/v1/admin/audit-logs",
                headers=admin_headers,
                params={
                    "limit": 10,
                    "sort_order": "desc"
                }
            )

            # Assert - Audit logs are returned
            assert audit_response.status_code == 200
            audit_data = audit_response.json()

            assert "data" in audit_data
            assert len(audit_data["data"]) >= 2  # At least provider toggle and scheduler start

            # Verify audit entries include our new event types
            event_types = [entry["event_type"] for entry in audit_data["data"]]
            assert "provider_enabled" in event_types
            assert "scheduler_started" in event_types

    def test_audit_system_handles_errors_gracefully(
        self, client: TestClient, admin_user: User, admin_headers: dict, db_session: Session
    ):
        """Test that main operations succeed even if audit logging fails."""
        from unittest.mock import patch, Mock

        # Mock audit service to simulate failure
        mock_audit_service = Mock()
        mock_audit_service.log_scheduler_started.side_effect = Exception("Audit failure")

        with patch('src.core.dependencies.get_current_admin_user', return_value=admin_user):
            with patch('src.api.admin.AuditService', return_value=mock_audit_service):
                # Act - Try to start scheduler (should succeed despite audit failure)
                response = client.post(
                    "/api/v1/admin/scheduler/control",
                    headers=admin_headers,
                    json={"action": "start"}
                )

                # Assert - Operation succeeds despite audit failure
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["success"] is True
                assert response_data["newState"] == "running"

                # Verify scheduler actually started
                status_response = client.get(
                    "/api/v1/admin/scheduler/status",
                    headers=admin_headers
                )

                assert status_response.status_code == 200
                status_data = status_response.json()
                assert status_data["state"] == "running"

    def test_complete_admin_workflow_audit_trail(
        self, client: TestClient, admin_user: User, test_provider: MarketDataProvider,
        admin_headers: dict, db_session: Session
    ):
        """Test complete admin workflow creates comprehensive audit trail."""
        from unittest.mock import patch

        with patch('src.core.dependencies.get_current_admin_user', return_value=admin_user):
            # Workflow: Configure provider → Start scheduler → Configure scheduler → Stop scheduler

            # 1. Enable provider
            client.patch(
                f"/api/v1/admin/market-data/providers/{test_provider.name}/toggle",
                headers=admin_headers
            )

            # 2. Start scheduler
            client.post(
                "/api/v1/admin/scheduler/control",
                headers=admin_headers,
                json={"action": "start", "configuration": {"interval_minutes": 15}}
            )

            # 3. Configure scheduler
            client.patch(
                "/api/v1/admin/scheduler/configuration",
                headers=admin_headers,
                json={"intervalMinutes": 10}
            )

            # 4. Stop scheduler
            client.post(
                "/api/v1/admin/scheduler/control",
                headers=admin_headers,
                json={"action": "stop", "reason": "workflow_test"}
            )

        # Assert - Complete audit trail exists
        audit_entries = db_session.query(AuditLog).filter(
            AuditLog.user_id == admin_user.id
        ).order_by(AuditLog.timestamp).all()

        assert len(audit_entries) == 4

        # Verify workflow sequence
        expected_types = [
            AuditEventType.PROVIDER_ENABLED,
            AuditEventType.SCHEDULER_STARTED,
            AuditEventType.SCHEDULER_CONFIGURED,
            AuditEventType.SCHEDULER_STOPPED
        ]

        for i, expected_type in enumerate(expected_types):
            assert audit_entries[i].event_type == expected_type
            assert audit_entries[i].user_id == admin_user.id

        # Verify metadata integrity
        scheduler_entries = [e for e in audit_entries if e.entity_type == "scheduler"]
        for entry in scheduler_entries:
            assert entry.entity_id == "market_data_scheduler"
            assert "scheduler_name" in entry.event_metadata
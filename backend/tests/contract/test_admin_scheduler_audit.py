"""
Test suite for admin scheduler control audit logging.

Tests the audit trail for admin actions on market data schedulers including
starting, stopping, pausing, and configuration changes.
"""

import pytest
from uuid import uuid4

from sqlalchemy.orm import Session

from src.models.audit_log import AuditLog, AuditEventType
from src.models.user import User
from src.models.user_role import UserRole
from src.services.audit_service import AuditService


class TestAdminSchedulerAudit:
    """Test audit logging for admin scheduler control actions."""

    @pytest.fixture
    def admin_user(self, db_session: Session) -> User:
        """Create test admin user."""
        admin = User(
            id=uuid4(),
            email="admin@test.com",
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            password_hash="test_hash"
        )
        db_session.add(admin)
        db_session.commit()
        return admin

    @pytest.fixture
    def audit_service(self, db_session: Session) -> AuditService:
        """Create audit service instance."""
        return AuditService(db_session)

    def test_scheduler_started_audit_entry(self, audit_service: AuditService, admin_user: User, db_session: Session):
        """Test that starting a scheduler creates proper audit entry."""
        # Arrange
        scheduler_name = "market_data_scheduler"
        scheduler_config = {
            "interval_minutes": 15,
            "enabled_providers": ["yfinance", "alpha_vantage"],
            "bulk_mode": True
        }
        ip_address = "192.168.1.100"
        user_agent = "Mozilla/5.0 Admin Browser"

        # Act - Log scheduler started event
        audit_entry = audit_service.log_scheduler_started(
            scheduler_name=scheduler_name,
            admin_user_id=str(admin_user.id),
            scheduler_config=scheduler_config,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Assert
        assert audit_entry is not None
        assert audit_entry.event_type == AuditEventType.SCHEDULER_STARTED
        assert audit_entry.event_description == "Market data scheduler 'market_data_scheduler' started"
        assert audit_entry.user_id == admin_user.id
        assert audit_entry.entity_type == "scheduler"
        assert audit_entry.entity_id == scheduler_name
        assert audit_entry.ip_address == ip_address
        assert audit_entry.user_agent == user_agent

        # Check metadata
        metadata = audit_entry.event_metadata
        assert metadata["scheduler_name"] == scheduler_name
        assert metadata["action"] == "started"
        assert metadata["previous_state"] == "stopped"
        assert metadata["configuration"] == scheduler_config

        # Verify entry was saved to database
        saved_entry = db_session.query(AuditLog).filter(
            AuditLog.event_type == AuditEventType.SCHEDULER_STARTED,
            AuditLog.entity_id == scheduler_name
        ).first()

        assert saved_entry is not None
        assert saved_entry.user_id == admin_user.id

    def test_scheduler_stopped_audit_entry(self, audit_service: AuditService, admin_user: User, db_session: Session):
        """Test that stopping a scheduler creates proper audit entry."""
        # Arrange
        scheduler_name = "market_data_scheduler"
        reason = "manual_maintenance"

        # Act - Log scheduler stopped event
        audit_entry = audit_service.log_scheduler_stopped(
            scheduler_name=scheduler_name,
            admin_user_id=str(admin_user.id),
            reason=reason
        )

        # Assert
        assert audit_entry is not None
        assert audit_entry.event_type == AuditEventType.SCHEDULER_STOPPED
        assert audit_entry.event_description == "Market data scheduler 'market_data_scheduler' stopped"
        assert audit_entry.user_id == admin_user.id
        assert audit_entry.entity_type == "scheduler"
        assert audit_entry.entity_id == scheduler_name

        # Check metadata
        metadata = audit_entry.event_metadata
        assert metadata["scheduler_name"] == scheduler_name
        assert metadata["action"] == "stopped"
        assert metadata["previous_state"] == "running"
        assert metadata["reason"] == reason

    def test_scheduler_paused_audit_entry(self, audit_service: AuditService, admin_user: User, db_session: Session):
        """Test that pausing a scheduler creates proper audit entry."""
        # Arrange
        scheduler_name = "market_data_scheduler"
        duration_minutes = 30

        # Act - Log scheduler paused event
        audit_entry = audit_service.log_scheduler_paused(
            scheduler_name=scheduler_name,
            admin_user_id=str(admin_user.id),
            duration_minutes=duration_minutes
        )

        # Assert
        assert audit_entry is not None
        assert audit_entry.event_type == AuditEventType.SCHEDULER_PAUSED
        assert audit_entry.event_description == "Market data scheduler 'market_data_scheduler' paused"
        assert audit_entry.user_id == admin_user.id
        assert audit_entry.entity_type == "scheduler"
        assert audit_entry.entity_id == scheduler_name

        # Check metadata
        metadata = audit_entry.event_metadata
        assert metadata["scheduler_name"] == scheduler_name
        assert metadata["action"] == "paused"
        assert metadata["previous_state"] == "running"
        assert metadata["duration_minutes"] == duration_minutes
        assert metadata["pause_type"] == "manual"

    def test_scheduler_resumed_audit_entry(self, audit_service: AuditService, admin_user: User, db_session: Session):
        """Test that resuming a scheduler creates proper audit entry."""
        # Arrange
        scheduler_name = "market_data_scheduler"

        # Act - Log scheduler resumed event
        audit_entry = audit_service.log_scheduler_resumed(
            scheduler_name=scheduler_name,
            admin_user_id=str(admin_user.id)
        )

        # Assert
        assert audit_entry is not None
        assert audit_entry.event_type == AuditEventType.SCHEDULER_RESUMED
        assert audit_entry.event_description == "Market data scheduler 'market_data_scheduler' resumed"
        assert audit_entry.user_id == admin_user.id
        assert audit_entry.entity_type == "scheduler"
        assert audit_entry.entity_id == scheduler_name

        # Check metadata
        metadata = audit_entry.event_metadata
        assert metadata["scheduler_name"] == scheduler_name
        assert metadata["action"] == "resumed"
        assert metadata["previous_state"] == "paused"

    def test_scheduler_configured_audit_entry(self, audit_service: AuditService, admin_user: User, db_session: Session):
        """Test that scheduler configuration changes create proper audit entry."""
        # Arrange
        scheduler_name = "market_data_scheduler"
        configuration_changes = {
            "interval_minutes": {"old": 15, "new": 10},
            "max_concurrent_jobs": {"old": 5, "new": 10},
            "retry_attempts": {"old": 3, "new": 5}
        }

        # Act - Log scheduler configuration change
        audit_entry = audit_service.log_scheduler_configured(
            scheduler_name=scheduler_name,
            admin_user_id=str(admin_user.id),
            configuration_changes=configuration_changes
        )

        # Assert
        assert audit_entry is not None
        assert audit_entry.event_type == AuditEventType.SCHEDULER_CONFIGURED
        assert audit_entry.event_description == "Market data scheduler 'market_data_scheduler' configuration updated"
        assert audit_entry.user_id == admin_user.id
        assert audit_entry.entity_type == "scheduler"
        assert audit_entry.entity_id == scheduler_name

        # Check metadata includes configuration changes
        metadata = audit_entry.event_metadata
        assert metadata["scheduler_name"] == scheduler_name
        assert metadata["action"] == "configured"
        assert metadata["changes"] == configuration_changes

    def test_scheduler_lifecycle_audit_trail(self, audit_service: AuditService, admin_user: User, db_session: Session):
        """Test that complete scheduler lifecycle creates comprehensive audit trail."""
        # Arrange
        scheduler_name = "lifecycle_test_scheduler"

        # Act - Perform complete lifecycle
        # 1. Start scheduler
        audit_service.log_scheduler_started(
            scheduler_name=scheduler_name,
            admin_user_id=str(admin_user.id),
            scheduler_config={"interval": 15}
        )

        # 2. Configure scheduler
        audit_service.log_scheduler_configured(
            scheduler_name=scheduler_name,
            admin_user_id=str(admin_user.id),
            configuration_changes={"interval": {"old": 15, "new": 10}}
        )

        # 3. Pause scheduler
        audit_service.log_scheduler_paused(
            scheduler_name=scheduler_name,
            admin_user_id=str(admin_user.id),
            duration_minutes=60
        )

        # 4. Resume scheduler
        audit_service.log_scheduler_resumed(
            scheduler_name=scheduler_name,
            admin_user_id=str(admin_user.id)
        )

        # 5. Stop scheduler
        audit_service.log_scheduler_stopped(
            scheduler_name=scheduler_name,
            admin_user_id=str(admin_user.id),
            reason="maintenance_complete"
        )

        # Assert - Check complete audit trail
        audit_entries = db_session.query(AuditLog).filter(
            AuditLog.entity_id == scheduler_name,
            AuditLog.entity_type == "scheduler"
        ).order_by(AuditLog.timestamp).all()

        assert len(audit_entries) == 5

        # Verify sequence of events
        assert audit_entries[0].event_type == AuditEventType.SCHEDULER_STARTED
        assert audit_entries[1].event_type == AuditEventType.SCHEDULER_CONFIGURED
        assert audit_entries[2].event_type == AuditEventType.SCHEDULER_PAUSED
        assert audit_entries[3].event_type == AuditEventType.SCHEDULER_RESUMED
        assert audit_entries[4].event_type == AuditEventType.SCHEDULER_STOPPED

        # All entries should be by the same admin user
        for entry in audit_entries:
            assert entry.user_id == admin_user.id
            assert entry.entity_type == "scheduler"
            assert entry.entity_id == scheduler_name

    def test_system_maintenance_audit_entries(self, audit_service: AuditService, admin_user: User, db_session: Session):
        """Test that system maintenance events create proper audit entries."""
        # Arrange
        maintenance_type = "scheduled_database_maintenance"
        expected_duration = 120

        # Act - Log maintenance start
        start_entry = audit_service.log_system_maintenance_start(
            admin_user_id=str(admin_user.id),
            maintenance_type=maintenance_type,
            expected_duration_minutes=expected_duration
        )

        # Log maintenance end
        actual_duration = 115
        end_entry = audit_service.log_system_maintenance_end(
            admin_user_id=str(admin_user.id),
            maintenance_type=maintenance_type,
            actual_duration_minutes=actual_duration
        )

        # Assert start entry
        assert start_entry is not None
        assert start_entry.event_type == AuditEventType.SYSTEM_MAINTENANCE_START
        assert start_entry.event_description == f"System maintenance started: {maintenance_type}"
        assert start_entry.user_id == admin_user.id
        assert start_entry.entity_type == "system"
        assert start_entry.entity_id == "maintenance"

        start_metadata = start_entry.event_metadata
        assert start_metadata["maintenance_type"] == maintenance_type
        assert start_metadata["action"] == "start"
        assert start_metadata["expected_duration_minutes"] == expected_duration

        # Assert end entry
        assert end_entry is not None
        assert end_entry.event_type == AuditEventType.SYSTEM_MAINTENANCE_END
        assert end_entry.event_description == f"System maintenance completed: {maintenance_type}"
        assert end_entry.user_id == admin_user.id
        assert end_entry.entity_type == "system"
        assert end_entry.entity_id == "maintenance"

        end_metadata = end_entry.event_metadata
        assert end_metadata["maintenance_type"] == maintenance_type
        assert end_metadata["action"] == "end"
        assert end_metadata["actual_duration_minutes"] == actual_duration

    def test_audit_entries_support_multiple_schedulers(self, audit_service: AuditService, admin_user: User, db_session: Session):
        """Test that audit system correctly handles multiple schedulers."""
        # Arrange
        scheduler_names = ["price_fetcher", "portfolio_updater", "notification_sender"]

        # Act - Start all schedulers
        for scheduler_name in scheduler_names:
            audit_service.log_scheduler_started(
                scheduler_name=scheduler_name,
                admin_user_id=str(admin_user.id),
                scheduler_config={"type": scheduler_name}
            )

        # Assert - Each scheduler has its own audit entry
        for scheduler_name in scheduler_names:
            entries = db_session.query(AuditLog).filter(
                AuditLog.entity_id == scheduler_name,
                AuditLog.entity_type == "scheduler",
                AuditLog.event_type == AuditEventType.SCHEDULER_STARTED
            ).all()

            assert len(entries) == 1
            assert entries[0].user_id == admin_user.id
            assert entries[0].entity_id == scheduler_name

        # Assert total entries
        all_scheduler_entries = db_session.query(AuditLog).filter(
            AuditLog.entity_type == "scheduler",
            AuditLog.event_type == AuditEventType.SCHEDULER_STARTED
        ).all()

        assert len(all_scheduler_entries) == len(scheduler_names)
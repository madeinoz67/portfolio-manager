#!/usr/bin/env python3
"""
TDD test to fix missing scheduler_executions table.

Root cause identified:
- The scheduler_executions table doesn't exist in the database
- This causes scheduler metrics to show 0 symbols processed
- SchedulerExecution model exists but table was never created

Fix: Create Alembic migration to add the missing table.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.database import SessionLocal
from src.models.scheduler_execution import SchedulerExecution
from src.services.scheduler_service import MarketDataSchedulerService, SchedulerConfiguration


class TestSchedulerExecutionTableMissingTDD:
    """TDD tests to verify and fix missing scheduler_executions table."""

    @pytest.fixture
    def db_session(self):
        """Create a database session for testing."""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def test_scheduler_executions_table_exists(self, db_session):
        """
        Test that scheduler_executions table exists.

        This test should FAIL initially, demonstrating the missing table.
        """
        try:
            result = db_session.execute(text("SELECT 1 FROM scheduler_executions LIMIT 1"))
            result.fetchone()
            print("✅ scheduler_executions table exists")
        except Exception as e:
            pytest.fail(f"❌ scheduler_executions table missing: {e}")

    def test_scheduler_execution_model_can_create_records(self, db_session):
        """
        Test that SchedulerExecution model can create and save records.

        This test should PASS after we create the missing table.
        """
        # Create a test execution record
        execution = SchedulerExecution(
            started_at=datetime.utcnow(),
            status="success",
            symbols_processed=5,
            successful_fetches=5,
            failed_fetches=0,
            execution_time_ms=1500,
            provider_used="yfinance"
        )
        execution.completed_at = datetime.utcnow()

        try:
            db_session.add(execution)
            db_session.commit()
            db_session.refresh(execution)

            print(f"✅ Successfully created SchedulerExecution record: {execution}")

            # Verify the record was saved
            assert execution.id is not None, "Record should have an ID after commit"
            assert execution.symbols_processed == 5, "Symbols processed should be saved correctly"
            assert execution.status == "success", "Status should be saved correctly"

        except Exception as e:
            pytest.fail(f"❌ Failed to create SchedulerExecution record: {e}")

    def test_scheduler_service_can_query_execution_history(self, db_session):
        """
        Test that MarketDataSchedulerService can query execution history.

        This test should PASS after we create the missing table and add some records.
        """
        # First, add some test execution records
        executions = [
            SchedulerExecution(
                started_at=datetime.utcnow() - timedelta(hours=1),
                completed_at=datetime.utcnow() - timedelta(minutes=59),
                status="success",
                symbols_processed=3,
                successful_fetches=3,
                failed_fetches=0,
                provider_used="yfinance"
            ),
            SchedulerExecution(
                started_at=datetime.utcnow() - timedelta(hours=2),
                completed_at=datetime.utcnow() - timedelta(minutes=119),
                status="success",
                symbols_processed=4,
                successful_fetches=4,
                failed_fetches=0,
                provider_used="yfinance"
            )
        ]

        for execution in executions:
            db_session.add(execution)
        db_session.commit()

        # Test scheduler service
        config = SchedulerConfiguration(
            interval_minutes=15,
            max_concurrent_jobs=5,
            retry_attempts=3,
            timeout_seconds=300
        )

        try:
            scheduler_service = MarketDataSchedulerService(db_session, config)
            status = scheduler_service.get_status()

            print(f"✅ Scheduler service status: {status}")

            # After fix, these should show > 0
            assert status.get('total_runs', 0) > 0, "Should have execution records"
            assert status.get('total_symbols_processed', 0) > 0, "Should have processed symbols"
            assert status.get('successful_runs', 0) > 0, "Should have successful runs"

        except Exception as e:
            pytest.fail(f"❌ Scheduler service failed to query execution history: {e}")

    def test_scheduler_execution_model_field_validation(self, db_session):
        """
        Test that the SchedulerExecution model has correct field structure.

        Validates that all expected fields exist and work correctly.
        """
        # Test creating record with all fields
        execution = SchedulerExecution(
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            status="failed",
            symbols_processed=2,
            successful_fetches=1,
            failed_fetches=1,
            execution_time_ms=2500,
            provider_used="alpha_vantage",
            error_message="Test error message"
        )

        # Test metadata functionality
        test_metadata = {"symbols": ["AAPL", "GOOGL"], "retry_count": 1}
        execution.set_metadata(test_metadata)

        try:
            db_session.add(execution)
            db_session.commit()
            db_session.refresh(execution)

            # Verify all fields are saved correctly
            assert execution.status == "failed"
            assert execution.symbols_processed == 2
            assert execution.successful_fetches == 1
            assert execution.failed_fetches == 1
            assert execution.execution_time_ms == 2500
            assert execution.provider_used == "alpha_vantage"
            assert execution.error_message == "Test error message"

            # Test metadata
            retrieved_metadata = execution.get_metadata()
            assert retrieved_metadata == test_metadata, "Metadata should be preserved"

            # Test computed properties
            assert execution.success_rate == 50.0, "Success rate should be calculated correctly"
            assert execution.execution_duration_seconds is not None, "Duration should be calculated"

            print("✅ All SchedulerExecution model fields work correctly")

        except Exception as e:
            pytest.fail(f"❌ SchedulerExecution model field validation failed: {e}")

    def test_raw_database_schema_validation(self, db_session):
        """
        Test that the database schema matches the SchedulerExecution model.

        This validates that the Alembic migration created the correct table structure.
        """
        try:
            # Test table structure with raw SQL
            result = db_session.execute(text("""
                SELECT
                    id,
                    started_at,
                    completed_at,
                    status,
                    symbols_processed,
                    successful_fetches,
                    failed_fetches,
                    execution_time_ms,
                    provider_used,
                    error_message,
                    execution_metadata
                FROM scheduler_executions
                LIMIT 1
            """))

            # This query should work without errors if schema is correct
            rows = result.fetchall()
            print(f"✅ Database schema validation passed. Rows: {len(rows)}")

        except Exception as e:
            pytest.fail(f"❌ Database schema validation failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
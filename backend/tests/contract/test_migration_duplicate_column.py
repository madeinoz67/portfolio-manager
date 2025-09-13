"""
TDD Test for Migration Duplicate Column Issue
Tests that the migration can handle existing columns without failing.
"""

import pytest
import sqlite3
from sqlalchemy import create_engine, text
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext

class TestMigrationDuplicateColumn:
    """Test migration duplicate column handling."""

    def test_migration_handles_existing_current_price_column(self):
        """Test that the migration can handle an existing current_price column."""
        # Create a test database with the current_price column already present
        engine = create_engine("sqlite:///./test_migration.db")

        with engine.connect() as conn:
            # Create stocks table with current_price column (simulating older migration state)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS stocks (
                    id TEXT PRIMARY KEY,
                    symbol VARCHAR(10) UNIQUE NOT NULL,
                    company_name VARCHAR(100),
                    exchange VARCHAR(10),
                    current_price NUMERIC(10, 4),
                    status VARCHAR(20) DEFAULT 'ACTIVE',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()

            # Verify the column exists
            result = conn.execute(text("PRAGMA table_info(stocks)"))
            columns = [row[1] for row in result]
            assert "current_price" in columns, "current_price column should exist"

        # Now attempt to run the problematic migration
        # The migration should either skip the existing column or handle it gracefully
        try:
            # This should not fail even though current_price already exists
            with engine.connect() as conn:
                # Simulate adding the column with IF NOT EXISTS logic
                conn.execute(text("""
                    ALTER TABLE stocks ADD COLUMN IF NOT EXISTS current_price NUMERIC(10, 4)
                """))
                conn.commit()
            success = True
        except Exception as e:
            # If SQLite doesn't support IF NOT EXISTS, we need a different approach
            if "duplicate column" in str(e).lower():
                # This is expected for the current broken migration
                success = False
            else:
                raise e

        # Clean up
        engine.dispose()
        import os
        if os.path.exists("test_migration.db"):
            os.remove("test_migration.db")

        # For now, we expect this to fail until we fix the migration
        assert success == False, "Migration should fail with current implementation (this test documents the issue)"

    def test_migration_adds_missing_columns_only(self):
        """Test that migration only adds columns that don't exist."""
        # Create a test database without the real-time price columns
        engine = create_engine("sqlite:///./test_migration_clean.db")

        with engine.connect() as conn:
            # Create stocks table WITHOUT the real-time price columns
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS stocks (
                    id TEXT PRIMARY KEY,
                    symbol VARCHAR(10) UNIQUE NOT NULL,
                    company_name VARCHAR(100),
                    exchange VARCHAR(10),
                    status VARCHAR(20) DEFAULT 'ACTIVE',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()

            # Verify current_price column does NOT exist
            result = conn.execute(text("PRAGMA table_info(stocks)"))
            columns = [row[1] for row in result]
            assert "current_price" not in columns, "current_price column should not exist initially"

            # Add the column (this should work)
            conn.execute(text("ALTER TABLE stocks ADD COLUMN current_price NUMERIC(10, 4)"))
            conn.commit()

            # Verify the column was added
            result = conn.execute(text("PRAGMA table_info(stocks)"))
            columns = [row[1] for row in result]
            assert "current_price" in columns, "current_price column should exist after adding"

        # Clean up
        engine.dispose()
        import os
        if os.path.exists("test_migration_clean.db"):
            os.remove("test_migration_clean.db")

    def test_check_column_exists_utility(self):
        """Test a utility function to check if a column exists."""
        engine = create_engine("sqlite:///./test_column_check.db")

        with engine.connect() as conn:
            # Create a test table
            conn.execute(text("""
                CREATE TABLE test_table (
                    id INTEGER PRIMARY KEY,
                    existing_column TEXT
                )
            """))
            conn.commit()

            # Function to check if column exists
            def column_exists(connection, table_name, column_name):
                result = connection.execute(text(f"PRAGMA table_info({table_name})"))
                columns = [row[1] for row in result]
                return column_name in columns

            # Test the utility
            assert column_exists(conn, "test_table", "existing_column") == True
            assert column_exists(conn, "test_table", "non_existing_column") == False

        # Clean up
        engine.dispose()
        import os
        if os.path.exists("test_column_check.db"):
            os.remove("test_column_check.db")

    def test_safe_add_column_approach(self):
        """Test a safe approach to adding columns that may already exist."""
        engine = create_engine("sqlite:///./test_safe_add.db")

        with engine.connect() as conn:
            # Create stocks table with current_price already present
            conn.execute(text("""
                CREATE TABLE stocks (
                    id TEXT PRIMARY KEY,
                    symbol VARCHAR(10) UNIQUE NOT NULL,
                    current_price NUMERIC(10, 4)
                )
            """))
            conn.commit()

            # Safe approach: check before adding
            def safe_add_column(connection, table_name, column_name, column_definition):
                result = connection.execute(text(f"PRAGMA table_info({table_name})"))
                existing_columns = [row[1] for row in result]

                if column_name not in existing_columns:
                    connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"))
                    return True  # Column was added
                return False  # Column already existed

            # Test adding existing column (should not fail)
            added = safe_add_column(conn, "stocks", "current_price", "NUMERIC(10, 4)")
            assert added == False, "Should not add existing column"

            # Test adding new column (should work)
            added = safe_add_column(conn, "stocks", "new_column", "TEXT")
            assert added == True, "Should add new column"

            # Verify both columns exist
            result = conn.execute(text("PRAGMA table_info(stocks)"))
            columns = [row[1] for row in result]
            assert "current_price" in columns
            assert "new_column" in columns

        # Clean up
        engine.dispose()
        import os
        if os.path.exists("test_safe_add.db"):
            os.remove("test_safe_add.db")
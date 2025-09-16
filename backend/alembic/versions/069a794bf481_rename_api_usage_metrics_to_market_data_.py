"""Rename api_usage_metrics to market_data_api_usage_metrics for system clarity

Revision ID: 069a794bf481
Revises: 4e2cac80bf09
Create Date: 2025-09-16 01:22:57.126130

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '069a794bf481'
down_revision = '4e2cac80bf09'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if both tables exist and handle the migration safely
    from sqlalchemy import inspect
    from alembic import context

    conn = context.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    # If both tables exist, copy data from old to new (if new is empty) then drop old
    if 'api_usage_metrics' in existing_tables and 'market_data_api_usage_metrics' in existing_tables:
        # Copy data from old table to new table if new table is empty
        result = conn.execute(sa.text("SELECT COUNT(*) FROM market_data_api_usage_metrics"))
        new_table_count = result.scalar()

        if new_table_count == 0:
            # Copy data from old to new table
            conn.execute(sa.text('''
                INSERT INTO market_data_api_usage_metrics
                SELECT * FROM api_usage_metrics
            '''))

        # Drop the old table
        op.drop_table('api_usage_metrics')

    # If only old table exists, rename it
    elif 'api_usage_metrics' in existing_tables:
        op.rename_table('api_usage_metrics', 'market_data_api_usage_metrics')


def downgrade() -> None:
    # Create the old table structure and copy data back
    from sqlalchemy import inspect
    from alembic import context

    conn = context.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'market_data_api_usage_metrics' in existing_tables:
        # Rename back to old name
        op.rename_table('market_data_api_usage_metrics', 'api_usage_metrics')
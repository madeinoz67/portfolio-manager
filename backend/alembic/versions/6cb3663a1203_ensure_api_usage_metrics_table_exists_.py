"""Ensure api_usage_metrics table exists with proper schema

Revision ID: 6cb3663a1203
Revises: 26dce3bcb832
Create Date: 2025-09-15 23:24:15.310788

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6cb3663a1203'
down_revision = '26dce3bcb832'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if table already exists, if not create it with proper schema
    # This ensures the api_usage_metrics table is never missing again

    # Get connection to check if table exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()

    # Only create the table if it doesn't already exist
    if 'api_usage_metrics' not in existing_tables:
        # Create api_usage_metrics table
        op.create_table(
            'api_usage_metrics',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('metric_id', sa.VARCHAR(length=100), nullable=False),
            sa.Column('provider_id', sa.VARCHAR(length=50), nullable=False),
            sa.Column('user_id', sa.UUID(), nullable=True),
            sa.Column('portfolio_id', sa.UUID(), nullable=True),
            sa.Column('request_type', sa.VARCHAR(length=50), nullable=False),
            sa.Column('requests_count', sa.INTEGER(), nullable=True),
            sa.Column('data_points_fetched', sa.INTEGER(), nullable=True),
            sa.Column('cost_estimate', sa.DECIMAL(precision=8, scale=4), nullable=True),
            sa.Column('recorded_at', sa.DATETIME(), nullable=False),
            sa.Column('time_bucket', sa.VARCHAR(length=20), nullable=False),
            sa.Column('rate_limit_hit', sa.BOOLEAN(), nullable=True),
            sa.Column('error_count', sa.INTEGER(), nullable=True),
            sa.Column('avg_response_time_ms', sa.INTEGER(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

        # Add indexes for common queries
        op.create_index('ix_api_usage_metrics_provider_id', 'api_usage_metrics', ['provider_id'])
        op.create_index('ix_api_usage_metrics_recorded_at', 'api_usage_metrics', ['recorded_at'])
        op.create_index('ix_api_usage_metrics_time_bucket', 'api_usage_metrics', ['time_bucket'])
    else:
        # Table exists, ensure indexes are present
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('api_usage_metrics')]

        if 'ix_api_usage_metrics_provider_id' not in existing_indexes:
            op.create_index('ix_api_usage_metrics_provider_id', 'api_usage_metrics', ['provider_id'])

        if 'ix_api_usage_metrics_recorded_at' not in existing_indexes:
            op.create_index('ix_api_usage_metrics_recorded_at', 'api_usage_metrics', ['recorded_at'])

        if 'ix_api_usage_metrics_time_bucket' not in existing_indexes:
            op.create_index('ix_api_usage_metrics_time_bucket', 'api_usage_metrics', ['time_bucket'])


def downgrade() -> None:
    # Check if table exists before trying to drop it
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()

    if 'api_usage_metrics' in existing_tables:
        # Get existing indexes to avoid errors when dropping
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('api_usage_metrics')]

        # Drop indexes first (only if they exist)
        if 'ix_api_usage_metrics_time_bucket' in existing_indexes:
            op.drop_index('ix_api_usage_metrics_time_bucket', 'api_usage_metrics')

        if 'ix_api_usage_metrics_recorded_at' in existing_indexes:
            op.drop_index('ix_api_usage_metrics_recorded_at', 'api_usage_metrics')

        if 'ix_api_usage_metrics_provider_id' in existing_indexes:
            op.drop_index('ix_api_usage_metrics_provider_id', 'api_usage_metrics')

        # Drop the table
        op.drop_table('api_usage_metrics')
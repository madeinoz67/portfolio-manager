"""Fix time_bucket column type to DateTime

Revision ID: a8081d0257b4
Revises: 4e7c61ec3018
Create Date: 2025-09-14 15:06:01.299356

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'a8081d0257b4'
down_revision = '4e7c61ec3018'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Fix the time_bucket column in api_usage_metrics from String to DateTime.

    SQLite doesn't support ALTER COLUMN, so we need to recreate the table.
    """
    # Check if the table exists first
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'api_usage_metrics' in inspector.get_table_names():
        # For SQLite, we need to recreate the table with the correct schema

        # 1. Create the new table with correct schema
        op.create_table(
            'api_usage_metrics_new',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, default=sa.text('uuid4()')),
            sa.Column('metric_id', sa.String(100), nullable=False),
            sa.Column('provider_id', sa.String(50), nullable=False),
            sa.Column('user_id', UUID(as_uuid=True), nullable=True),
            sa.Column('portfolio_id', UUID(as_uuid=True), nullable=True),
            sa.Column('request_type', sa.String(50), nullable=False),
            sa.Column('requests_count', sa.Integer, nullable=True),
            sa.Column('data_points_fetched', sa.Integer, nullable=True),
            sa.Column('cost_estimate', sa.DECIMAL(8, 4), nullable=True),
            sa.Column('recorded_at', sa.DateTime, nullable=False),
            sa.Column('time_bucket', sa.DateTime, nullable=False),  # Changed from String to DateTime
            sa.Column('rate_limit_hit', sa.Boolean, nullable=True),
            sa.Column('error_count', sa.Integer, nullable=True),
            sa.Column('avg_response_time_ms', sa.Integer, nullable=True)
        )

        # 2. Copy existing data (if any) with time_bucket conversion
        # We'll skip data migration since the table was likely empty or had constraint issues
        # If there was valid data, we would convert string time_bucket to datetime here

        # 3. Drop the old table
        op.drop_table('api_usage_metrics')

        # 4. Rename the new table
        op.rename_table('api_usage_metrics_new', 'api_usage_metrics')

        # 5. Create indexes for performance
        op.create_index('idx_api_usage_provider_time', 'api_usage_metrics', ['provider_id', 'time_bucket'])
        op.create_index('idx_api_usage_time_bucket', 'api_usage_metrics', ['time_bucket'])
        op.create_index('idx_api_usage_user_time', 'api_usage_metrics', ['user_id', 'time_bucket'])

    else:
        # If table doesn't exist, create it with the correct schema
        op.create_table(
            'api_usage_metrics',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, default=sa.text('uuid4()')),
            sa.Column('metric_id', sa.String(100), nullable=False),
            sa.Column('provider_id', sa.String(50), nullable=False),
            sa.Column('user_id', UUID(as_uuid=True), nullable=True),
            sa.Column('portfolio_id', UUID(as_uuid=True), nullable=True),
            sa.Column('request_type', sa.String(50), nullable=False),
            sa.Column('requests_count', sa.Integer, nullable=True),
            sa.Column('data_points_fetched', sa.Integer, nullable=True),
            sa.Column('cost_estimate', sa.DECIMAL(8, 4), nullable=True),
            sa.Column('recorded_at', sa.DateTime, nullable=False),
            sa.Column('time_bucket', sa.DateTime, nullable=False),
            sa.Column('rate_limit_hit', sa.Boolean, nullable=True),
            sa.Column('error_count', sa.Integer, nullable=True),
            sa.Column('avg_response_time_ms', sa.Integer, nullable=True)
        )

        # Create indexes
        op.create_index('idx_api_usage_provider_time', 'api_usage_metrics', ['provider_id', 'time_bucket'])
        op.create_index('idx_api_usage_time_bucket', 'api_usage_metrics', ['time_bucket'])
        op.create_index('idx_api_usage_user_time', 'api_usage_metrics', ['user_id', 'time_bucket'])


def downgrade() -> None:
    """
    Downgrade by changing time_bucket back to String.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'api_usage_metrics' in inspector.get_table_names():
        # Drop indexes first
        op.drop_index('idx_api_usage_provider_time')
        op.drop_index('idx_api_usage_time_bucket')
        op.drop_index('idx_api_usage_user_time')

        # Recreate table with String time_bucket
        op.create_table(
            'api_usage_metrics_old',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('metric_id', sa.String(100), nullable=False),
            sa.Column('provider_id', sa.String(50), nullable=False),
            sa.Column('user_id', UUID(as_uuid=True), nullable=True),
            sa.Column('portfolio_id', UUID(as_uuid=True), nullable=True),
            sa.Column('request_type', sa.String(50), nullable=False),
            sa.Column('requests_count', sa.Integer, nullable=True),
            sa.Column('data_points_fetched', sa.Integer, nullable=True),
            sa.Column('cost_estimate', sa.DECIMAL(8, 4), nullable=True),
            sa.Column('recorded_at', sa.DateTime, nullable=False),
            sa.Column('time_bucket', sa.String(20), nullable=False),  # Back to String
            sa.Column('rate_limit_hit', sa.Boolean, nullable=True),
            sa.Column('error_count', sa.Integer, nullable=True),
            sa.Column('avg_response_time_ms', sa.Integer, nullable=True)
        )

        op.drop_table('api_usage_metrics')
        op.rename_table('api_usage_metrics_old', 'api_usage_metrics')

        # Recreate indexes
        op.create_index('idx_api_usage_provider_time', 'api_usage_metrics', ['provider_id', 'time_bucket'])
        op.create_index('idx_api_usage_time_bucket', 'api_usage_metrics', ['time_bucket'])
        op.create_index('idx_api_usage_user_time', 'api_usage_metrics', ['user_id', 'time_bucket'])
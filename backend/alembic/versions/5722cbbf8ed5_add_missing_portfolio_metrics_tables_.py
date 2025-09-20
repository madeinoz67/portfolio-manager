"""Add missing portfolio metrics tables from branch merge

Revision ID: 5722cbbf8ed5
Revises: e28852b00c56
Create Date: 2025-09-20 08:01:41.766489

"""
from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision = '5722cbbf8ed5'
down_revision = 'e28852b00c56'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create portfolio_update_metrics table
    op.create_table('portfolio_update_metrics',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('portfolio_id', sa.String(36), nullable=False, index=True),
        sa.Column('symbols_updated', sa.JSON(), nullable=False),
        sa.Column('symbols_count', sa.Integer(), nullable=False, default=1),
        sa.Column('update_duration_ms', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, index=True),
        sa.Column('trigger_type', sa.String(50), nullable=False, index=True),
        sa.Column('update_source', sa.String(30), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_type', sa.String(50), nullable=True, index=True),
        sa.Column('queue_wait_time_ms', sa.Integer(), nullable=True),
        sa.Column('db_query_time_ms', sa.Integer(), nullable=True),
        sa.Column('calculation_time_ms', sa.Integer(), nullable=True),
        sa.Column('coalesced_count', sa.Integer(), nullable=True),
        sa.Column('debounce_delay_ms', sa.Integer(), nullable=True),
        sa.Column('price_change_timestamp', sa.DateTime(), nullable=True),
        sa.Column('queue_entry_timestamp', sa.DateTime(), nullable=True),
        sa.Column('processing_start_timestamp', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('extra_data', sa.JSON(), nullable=True)
    )

    # Create indexes for portfolio_update_metrics
    op.create_index('idx_portfolio_update_metrics_portfolio_status', 'portfolio_update_metrics', ['portfolio_id', 'status'])
    op.create_index('idx_portfolio_update_metrics_created_status', 'portfolio_update_metrics', ['created_at', 'status'])
    op.create_index('idx_portfolio_update_metrics_trigger_type', 'portfolio_update_metrics', ['trigger_type', 'created_at'])
    op.create_index('idx_portfolio_update_metrics_performance', 'portfolio_update_metrics', ['update_duration_ms', 'status'])

    # Create portfolio_queue_metrics table
    op.create_table('portfolio_queue_metrics',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('pending_updates', sa.Integer(), nullable=False, default=0),
        sa.Column('processing_rate', sa.Numeric(8, 2), nullable=False, default=0.0),
        sa.Column('active_portfolios', sa.Integer(), nullable=False, default=0),
        sa.Column('avg_processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('max_processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('queue_throughput', sa.Numeric(8, 2), nullable=True),
        sa.Column('rate_limit_hits', sa.Integer(), nullable=False, default=0),
        sa.Column('coalesced_updates', sa.Integer(), nullable=False, default=0),
        sa.Column('debounce_savings', sa.Integer(), nullable=False, default=0),
        sa.Column('memory_usage_mb', sa.Numeric(8, 2), nullable=True),
        sa.Column('cpu_usage_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('database_connections', sa.Integer(), nullable=True),
        sa.Column('is_processing', sa.Boolean(), nullable=False, default=True),
        sa.Column('last_successful_update', sa.DateTime(), nullable=True),
        sa.Column('error_count_last_hour', sa.Integer(), nullable=False, default=0),
        sa.Column('debounce_seconds', sa.Numeric(4, 1), nullable=True),
        sa.Column('max_updates_per_minute', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('extra_data', sa.JSON(), nullable=True)
    )

    # Create indexes for portfolio_queue_metrics
    op.create_index('idx_portfolio_queue_metrics_created', 'portfolio_queue_metrics', ['created_at'])
    op.create_index('idx_portfolio_queue_metrics_processing', 'portfolio_queue_metrics', ['is_processing', 'created_at'])
    op.create_index('idx_portfolio_queue_metrics_performance', 'portfolio_queue_metrics', ['processing_rate', 'pending_updates'])


def downgrade() -> None:
    op.drop_table('portfolio_queue_metrics')
    op.drop_table('portfolio_update_metrics')
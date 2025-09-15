"""Add portfolio update metrics tables for monitoring

Revision ID: 26dce3bcb832
Revises: defe323440f5
Create Date: 2025-09-15 22:58:43.814393

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '26dce3bcb832'
down_revision = 'defe323440f5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create portfolio_update_metrics table
    op.create_table('portfolio_update_metrics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
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
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
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

    # Create portfolio_update_summaries table
    op.create_table('portfolio_update_summaries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('period_start', sa.DateTime(), nullable=False, index=True),
        sa.Column('period_end', sa.DateTime(), nullable=False, index=True),
        sa.Column('period_type', sa.String(10), nullable=False, index=True),
        sa.Column('total_updates', sa.Integer(), nullable=False, default=0),
        sa.Column('successful_updates', sa.Integer(), nullable=False, default=0),
        sa.Column('failed_updates', sa.Integer(), nullable=False, default=0),
        sa.Column('rate_limited_updates', sa.Integer(), nullable=False, default=0),
        sa.Column('avg_update_duration_ms', sa.Integer(), nullable=True),
        sa.Column('median_update_duration_ms', sa.Integer(), nullable=True),
        sa.Column('p95_update_duration_ms', sa.Integer(), nullable=True),
        sa.Column('max_update_duration_ms', sa.Integer(), nullable=True),
        sa.Column('total_symbols_processed', sa.Integer(), nullable=False, default=0),
        sa.Column('coalesced_updates_count', sa.Integer(), nullable=False, default=0),
        sa.Column('coalescing_efficiency', sa.Numeric(5, 2), nullable=True),
        sa.Column('unique_portfolios', sa.Integer(), nullable=False, default=0),
        sa.Column('unique_symbols', sa.Integer(), nullable=False, default=0),
        sa.Column('avg_portfolios_per_symbol', sa.Numeric(8, 2), nullable=True),
        sa.Column('avg_update_lag_ms', sa.Integer(), nullable=True),
        sa.Column('median_update_lag_ms', sa.Integer(), nullable=True),
        sa.Column('p95_update_lag_ms', sa.Integer(), nullable=True),
        sa.Column('max_update_lag_ms', sa.Integer(), nullable=True),
        sa.Column('avg_queue_size', sa.Numeric(8, 2), nullable=True),
        sa.Column('max_queue_size', sa.Integer(), nullable=True),
        sa.Column('avg_processing_rate', sa.Numeric(8, 2), nullable=True),
        sa.Column('avg_memory_usage_mb', sa.Numeric(8, 2), nullable=True),
        sa.Column('max_memory_usage_mb', sa.Numeric(8, 2), nullable=True),
        sa.Column('avg_cpu_usage_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('top_error_types', sa.JSON(), nullable=True),
        sa.Column('error_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('uptime_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('service_interruptions', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )

    # Create indexes for portfolio_update_summaries
    op.create_index('idx_portfolio_update_summaries_period', 'portfolio_update_summaries', ['period_type', 'period_start'])
    op.create_index('idx_portfolio_update_summaries_performance', 'portfolio_update_summaries', ['period_start', 'avg_update_duration_ms'])
    op.create_index('idx_portfolio_update_summaries_created', 'portfolio_update_summaries', ['created_at'])

    # Create portfolio_update_alerts table
    op.create_table('portfolio_update_alerts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('alert_type', sa.String(50), nullable=False, index=True),
        sa.Column('severity', sa.String(20), nullable=False, index=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('threshold_value', sa.Numeric(12, 4), nullable=True),
        sa.Column('actual_value', sa.Numeric(12, 4), nullable=True),
        sa.Column('metric_name', sa.String(100), nullable=True),
        sa.Column('affected_portfolios', sa.JSON(), nullable=True),
        sa.Column('time_period', sa.String(50), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, default=False, index=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_note', sa.Text(), nullable=True),
        sa.Column('auto_resolved', sa.Boolean(), nullable=False, default=False),
        sa.Column('notification_sent', sa.Boolean(), nullable=False, default=False),
        sa.Column('notification_channels', sa.JSON(), nullable=True),
        sa.Column('first_occurred_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('last_occurred_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('extra_data', sa.JSON(), nullable=True)
    )

    # Create indexes for portfolio_update_alerts
    op.create_index('idx_portfolio_update_alerts_type_severity', 'portfolio_update_alerts', ['alert_type', 'severity'])
    op.create_index('idx_portfolio_update_alerts_active', 'portfolio_update_alerts', ['is_resolved', 'first_occurred_at'])
    op.create_index('idx_portfolio_update_alerts_recent', 'portfolio_update_alerts', ['created_at', 'severity'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('portfolio_update_alerts')
    op.drop_table('portfolio_update_summaries')
    op.drop_table('portfolio_queue_metrics')
    op.drop_table('portfolio_update_metrics')
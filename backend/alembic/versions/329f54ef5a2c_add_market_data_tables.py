"""add_market_data_tables

Revision ID: 329f54ef5a2c
Revises: 0c1dbab347e4
Create Date: 2025-09-13 15:16:05.997150

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '329f54ef5a2c'
down_revision = '0c1dbab347e4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Market data providers configuration
    op.create_table(
        'market_data_providers',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('provider_id', sa.String(50), nullable=False, unique=True),
        sa.Column('provider_name', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('api_key', sa.String(255), nullable=True),
        sa.Column('rate_limit_per_day', sa.Integer(), default=500),
        sa.Column('rate_limit_per_minute', sa.Integer(), default=5),
        sa.Column('requests_used_today', sa.Integer(), default=0),
        sa.Column('last_request_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('priority', sa.Integer(), default=1),
        sa.Column('supports_symbols', sa.ARRAY(sa.Text()), default=[]),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now()),
    )

    # Price update scheduling
    op.create_table(
        'price_update_schedules',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('schedule_id', sa.String(50), nullable=False, unique=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('market_hours_interval', sa.Integer(), default=15),
        sa.Column('after_hours_interval', sa.Integer(), default=60),
        sa.Column('weekend_interval', sa.Integer(), default=1440),
        sa.Column('market_open_time', sa.Time(), default=sa.text("'09:30:00'")),
        sa.Column('market_close_time', sa.Time(), default=sa.text("'16:00:00'")),
        sa.Column('timezone', sa.String(50), default='Australia/Sydney'),
        sa.Column('last_run_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('next_run_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now()),
    )

    # Real-time price history (extends existing pattern)
    op.create_table(
        'realtime_price_history',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('stock_id', sa.UUID(), nullable=False),
        sa.Column('price_datetime', sa.TIMESTAMP(), nullable=False),
        sa.Column('price', sa.NUMERIC(10, 4), nullable=False),
        sa.Column('volume', sa.BigInteger(), default=0),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('is_market_hours', sa.Boolean(), default=True),
        sa.Column('fetch_latency_ms', sa.Integer(), default=0),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ondelete='CASCADE'),
    )

    # SSE connection tracking
    op.create_table(
        'sse_connections',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('connection_id', sa.String(100), nullable=False, unique=True),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('connected_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('last_heartbeat', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('subscribed_portfolios', sa.ARRAY(sa.UUID()), default=[]),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('disconnected_at', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Cached portfolio valuations
    op.create_table(
        'portfolio_valuations',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('portfolio_id', sa.UUID(), nullable=False),
        sa.Column('total_value', sa.NUMERIC(15, 2), nullable=False),
        sa.Column('total_cost_basis', sa.NUMERIC(15, 2), nullable=False),
        sa.Column('unrealized_gain_loss', sa.NUMERIC(15, 2), nullable=False),
        sa.Column('daily_change', sa.NUMERIC(15, 2), default=0),
        sa.Column('daily_change_percent', sa.NUMERIC(5, 2), default=0),
        sa.Column('calculated_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('stale_price_count', sa.Integer(), default=0),
        sa.Column('last_price_update', sa.TIMESTAMP(), nullable=True),
        sa.Column('cache_expires_at', sa.TIMESTAMP(), nullable=False),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('portfolio_id', 'calculated_at'),
    )

    # Administrative poll interval configurations
    op.create_table(
        'poll_interval_configs',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('config_id', sa.String(100), nullable=False, unique=True),
        sa.Column('config_type', sa.String(20), nullable=False),
        sa.Column('target_id', sa.UUID(), nullable=True),
        sa.Column('interval_minutes', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('priority', sa.Integer(), default=5),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('effective_from', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('effective_until', sa.TIMESTAMP(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.CheckConstraint("config_type IN ('global', 'user', 'portfolio')", name='valid_config_type'),
        sa.CheckConstraint('interval_minutes > 0', name='positive_interval'),
        sa.CheckConstraint('priority BETWEEN 1 AND 10', name='valid_priority'),
        sa.CheckConstraint(
            "(config_type = 'global' AND target_id IS NULL) OR (config_type IN ('user', 'portfolio') AND target_id IS NOT NULL)",
            name='valid_target_for_type'
        ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
    )

    # API usage metrics for cost tracking and reporting
    op.create_table(
        'api_usage_metrics',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('metric_id', sa.String(100), nullable=False, unique=True),
        sa.Column('provider_id', sa.String(50), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('portfolio_id', sa.UUID(), nullable=True),
        sa.Column('request_type', sa.String(50), nullable=False),
        sa.Column('requests_count', sa.Integer(), default=1),
        sa.Column('data_points_fetched', sa.Integer(), default=0),
        sa.Column('cost_estimate', sa.NUMERIC(8, 4), default=0),
        sa.Column('recorded_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('time_bucket', sa.String(20), nullable=False),
        sa.Column('rate_limit_hit', sa.Boolean(), default=False),
        sa.Column('error_count', sa.Integer(), default=0),
        sa.CheckConstraint("time_bucket IN ('hourly', 'daily', 'monthly')", name='valid_time_bucket'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id']),
    )

    # Administrative overrides for system control
    op.create_table(
        'administrative_overrides',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('override_id', sa.String(100), nullable=False, unique=True),
        sa.Column('override_type', sa.String(50), nullable=False),
        sa.Column('scope', sa.String(20), nullable=False),
        sa.Column('target_id', sa.UUID(), nullable=True),
        sa.Column('provider_id', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('override_value', sa.Text(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('expires_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('auto_remove', sa.Boolean(), default=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.CheckConstraint("override_type IN ('disable_updates', 'force_interval', 'emergency_stop')", name='valid_override_type'),
        sa.CheckConstraint("scope IN ('global', 'user', 'portfolio', 'provider')", name='valid_scope'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
    )

    # Extend stocks table with real-time price fields
    op.add_column('stocks', sa.Column('current_price', sa.NUMERIC(10, 4), nullable=True))
    op.add_column('stocks', sa.Column('previous_close', sa.NUMERIC(10, 4), nullable=True))
    op.add_column('stocks', sa.Column('daily_change', sa.NUMERIC(8, 4), default=0))
    op.add_column('stocks', sa.Column('daily_change_percent', sa.NUMERIC(5, 2), default=0))
    op.add_column('stocks', sa.Column('last_price_update', sa.TIMESTAMP(), nullable=True))
    op.add_column('stocks', sa.Column('price_source', sa.String(50), nullable=True))
    op.add_column('stocks', sa.Column('market_status', sa.String(20), default='CLOSED'))

    # Performance indexes for real-time queries
    op.create_index('idx_stocks_symbol_hash', 'stocks', ['symbol'], postgresql_using='hash')
    op.create_index('idx_stocks_last_price_update', 'stocks', [sa.desc('last_price_update')])
    op.create_index('idx_realtime_price_history_stock_datetime', 'realtime_price_history', ['stock_id', sa.desc('price_datetime')])
    op.create_index('idx_portfolio_valuations_portfolio_calculated', 'portfolio_valuations', ['portfolio_id', sa.desc('calculated_at')])
    op.create_index('idx_sse_connections_user_active', 'sse_connections', ['user_id', 'is_active'], postgresql_where='is_active = true')

    # Performance indexes for administrative tables
    op.create_index('idx_poll_configs_active_priority', 'poll_interval_configs', ['is_active', 'priority', 'config_type'], postgresql_where='is_active = true')
    op.create_index('idx_poll_configs_target', 'poll_interval_configs', ['config_type', 'target_id'], postgresql_where='target_id IS NOT NULL')
    op.create_index('idx_api_usage_provider_time', 'api_usage_metrics', ['provider_id', sa.desc('recorded_at')])
    op.create_index('idx_api_usage_user_time', 'api_usage_metrics', ['user_id', sa.desc('recorded_at')], postgresql_where='user_id IS NOT NULL')
    op.create_index('idx_api_usage_time_bucket', 'api_usage_metrics', ['time_bucket', sa.desc('recorded_at')])
    op.create_index('idx_admin_overrides_active_scope', 'administrative_overrides', ['is_active', 'scope', 'override_type'], postgresql_where='is_active = true')


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_admin_overrides_active_scope')
    op.drop_index('idx_api_usage_time_bucket')
    op.drop_index('idx_api_usage_user_time')
    op.drop_index('idx_api_usage_provider_time')
    op.drop_index('idx_poll_configs_target')
    op.drop_index('idx_poll_configs_active_priority')
    op.drop_index('idx_sse_connections_user_active')
    op.drop_index('idx_portfolio_valuations_portfolio_calculated')
    op.drop_index('idx_realtime_price_history_stock_datetime')
    op.drop_index('idx_stocks_last_price_update')
    op.drop_index('idx_stocks_symbol_hash')

    # Remove columns from stocks table
    op.drop_column('stocks', 'market_status')
    op.drop_column('stocks', 'price_source')
    op.drop_column('stocks', 'last_price_update')
    op.drop_column('stocks', 'daily_change_percent')
    op.drop_column('stocks', 'daily_change')
    op.drop_column('stocks', 'previous_close')
    op.drop_column('stocks', 'current_price')

    # Drop tables in reverse order
    op.drop_table('administrative_overrides')
    op.drop_table('api_usage_metrics')
    op.drop_table('poll_interval_configs')
    op.drop_table('portfolio_valuations')
    op.drop_table('sse_connections')
    op.drop_table('realtime_price_history')
    op.drop_table('price_update_schedules')
    op.drop_table('market_data_providers')
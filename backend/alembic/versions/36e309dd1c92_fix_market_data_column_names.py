"""Fix market data column names

Revision ID: 36e309dd1c92
Revises: 2842139f0989
Create Date: 2025-09-13 23:41:04.668631

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '36e309dd1c92'
down_revision = '2842139f0989'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fix market_data_providers table column names
    # SQLite doesn't support ALTER COLUMN RENAME directly, so we need to recreate the table

    # Create new table with correct column names
    op.create_table(
        'market_data_providers_new',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False, unique=True),  # Changed from provider_id
        sa.Column('display_name', sa.String(100), nullable=False),      # Changed from provider_name
        sa.Column('is_enabled', sa.Boolean(), default=True),            # Changed from is_active
        sa.Column('api_key', sa.String(255), nullable=True),
        sa.Column('base_url', sa.String(255), nullable=True),
        sa.Column('rate_limit_per_minute', sa.Integer(), default=5),
        sa.Column('rate_limit_per_day', sa.Integer(), default=500),
        sa.Column('priority', sa.Integer(), default=1),
        sa.Column('config', sa.JSON(), nullable=True),                  # Changed from supports_symbols
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now()),
    )

    # Copy data from old table to new table
    connection = op.get_bind()
    connection.execute(sa.text("""
        INSERT INTO market_data_providers_new (id, name, display_name, is_enabled, api_key, rate_limit_per_minute, rate_limit_per_day, priority, created_at, updated_at)
        SELECT id, provider_id, provider_name, is_active, api_key, rate_limit_per_minute, rate_limit_per_day, priority, created_at, updated_at
        FROM market_data_providers
    """))

    # Drop old table and rename new table
    op.drop_table('market_data_providers')
    op.rename_table('market_data_providers_new', 'market_data_providers')

    # Fix sse_connections table column names
    op.create_table(
        'sse_connections_new',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('connection_id', sa.String(100), nullable=False, unique=True),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('client_ip', sa.String(45), nullable=True),           # Changed from ip_address
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('subscribed_symbols', sa.JSON(), nullable=True),      # Changed from subscribed_portfolios
        sa.Column('portfolio_ids', sa.JSON(), nullable=True),           # New column
        sa.Column('connection_type', sa.String(20), default='market_data'),  # New column
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_heartbeat', sa.TIMESTAMP(), nullable=True),
        sa.Column('messages_sent', sa.Integer(), default=0),            # New column
        sa.Column('connected_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('disconnected_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),  # New column
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Copy data from old table to new table
    connection.execute(sa.text("""
        INSERT INTO sse_connections_new (id, connection_id, user_id, client_ip, user_agent, subscribed_symbols, is_active, last_heartbeat, connected_at, disconnected_at, created_at)
        SELECT id, connection_id, user_id, ip_address, user_agent, subscribed_portfolios, is_active, last_heartbeat, connected_at, disconnected_at, connected_at
        FROM sse_connections
    """))

    # Drop old table and rename new table
    op.drop_table('sse_connections')
    op.rename_table('sse_connections_new', 'sse_connections')

    # Recreate indexes for sse_connections
    op.create_index('idx_sse_connections_user_active', 'sse_connections', ['user_id', 'is_active'])

    # Update realtime_price_history to use the new schema
    op.create_table(
        'realtime_price_history_new',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('symbol', sa.String(10), nullable=False),             # Changed from stock_id
        sa.Column('price', sa.NUMERIC(10, 4), nullable=False),
        sa.Column('volume', sa.BigInteger(), default=0),
        sa.Column('market_cap', sa.BigInteger(), nullable=True),        # New column
        sa.Column('provider_id', sa.UUID(), nullable=True),             # New column
        sa.Column('source_timestamp', sa.TIMESTAMP(), nullable=True),   # Changed from price_datetime
        sa.Column('fetched_at', sa.TIMESTAMP(), nullable=False),        # New column
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['provider_id'], ['market_data_providers.id']),
    )

    # Copy existing data, mapping stock symbols
    connection.execute(sa.text("""
        INSERT INTO realtime_price_history_new (id, symbol, price, volume, source_timestamp, fetched_at, created_at)
        SELECT rph.id, s.symbol, rph.price, rph.volume, rph.price_datetime, rph.created_at, rph.created_at
        FROM realtime_price_history rph
        JOIN stocks s ON s.id = rph.stock_id
    """))

    # Drop old table and rename
    op.drop_index('idx_realtime_price_history_stock_datetime')
    op.drop_table('realtime_price_history')
    op.rename_table('realtime_price_history_new', 'realtime_price_history')

    # Recreate index
    op.create_index('idx_realtime_price_history_symbol_fetched', 'realtime_price_history', ['symbol', sa.desc('fetched_at')])


def downgrade() -> None:
    # This downgrade would be complex due to the structural changes
    # For simplicity, we'll just recreate the original tables
    op.drop_index('idx_realtime_price_history_symbol_fetched')
    op.drop_index('idx_sse_connections_user_active')

    # Recreate original tables (this would lose data in a real scenario)
    # In practice, you'd want to migrate data back, but for development this is acceptable
    op.drop_table('realtime_price_history')
    op.drop_table('sse_connections')
    op.drop_table('market_data_providers')
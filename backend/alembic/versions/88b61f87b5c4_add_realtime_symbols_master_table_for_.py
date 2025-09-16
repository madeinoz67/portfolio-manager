"""Add realtime_symbols master table for single source of truth pricing

Revision ID: 88b61f87b5c4
Revises: 551c4dbedf91
Create Date: 2025-09-16 13:38:06.883249

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '88b61f87b5c4'
down_revision = '551c4dbedf91'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create realtime_symbols master table as single source of truth for current prices
    # Include foreign key constraints in table creation for SQLite compatibility
    op.create_table(
        'realtime_symbols',
        sa.Column('symbol', sa.VARCHAR(20), primary_key=True, nullable=False),
        sa.Column('current_price', sa.DECIMAL(10, 4), nullable=False),
        sa.Column('company_name', sa.VARCHAR(255), nullable=True),
        sa.Column('last_updated', sa.DateTime, nullable=False),
        sa.Column('provider_id', sa.UUID, nullable=False),
        sa.Column('volume', sa.Integer, nullable=True),
        sa.Column('market_cap', sa.DECIMAL(20, 2), nullable=True),
        sa.Column('latest_history_id', sa.UUID, nullable=True),  # References realtime_price_history
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        # SQLite-compatible foreign key constraints
        sa.ForeignKeyConstraint(['provider_id'], ['market_data_providers.id'], name='fk_realtime_symbols_provider'),
        sa.ForeignKeyConstraint(['latest_history_id'], ['realtime_price_history.id'], name='fk_realtime_symbols_latest_history'),
    )

    # Create indexes for performance optimization
    op.create_index('idx_realtime_symbols_symbol', 'realtime_symbols', ['symbol'])
    op.create_index('idx_realtime_symbols_last_updated', 'realtime_symbols', ['last_updated'])
    op.create_index('idx_realtime_symbols_provider', 'realtime_symbols', ['provider_id'])

    # SQLite doesn't support stored procedures/triggers like PostgreSQL
    # We'll handle updated_at in the application layer


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_realtime_symbols_provider')
    op.drop_index('idx_realtime_symbols_last_updated')
    op.drop_index('idx_realtime_symbols_symbol')

    # Drop table (foreign keys are dropped automatically)
    op.drop_table('realtime_symbols')
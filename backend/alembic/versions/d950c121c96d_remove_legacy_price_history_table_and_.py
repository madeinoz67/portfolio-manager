"""remove_legacy_price_history_table_and_references

Revision ID: d950c121c96d
Revises: d2c6a07b5f00
Create Date: 2025-09-16 20:00:49.869643

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd950c121c96d'
down_revision = 'd2c6a07b5f00'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Remove legacy price_history table that is no longer used.

    The system now uses realtime_price_history + realtime_symbols
    master table architecture. The old price_history table with
    its daily aggregated data is obsolete and unused by frontend.

    Safe to remove as confirmed:
    - Not in production (dev environment only)
    - Frontend doesn't reference price_history endpoints
    - API endpoint exists but not used by frontend
    """

    # Drop the legacy price_history table
    op.drop_table('price_history')

    print("✅ Removed legacy price_history table")
    print("ℹ️  System now uses realtime_price_history + realtime_symbols architecture")


def downgrade() -> None:
    """
    Recreate the price_history table if needed.

    Note: This will recreate the table structure but not restore
    the old data, which is acceptable for this cleanup migration.
    """
    op.create_table(
        'price_history',
        sa.Column('id', sa.UUID, primary_key=True, nullable=False),
        sa.Column('stock_id', sa.UUID, nullable=False),
        sa.Column('price_date', sa.Date, nullable=False),
        sa.Column('open_price', sa.DECIMAL(10, 4), nullable=True),
        sa.Column('close_price', sa.DECIMAL(10, 4), nullable=False),
        sa.Column('high_price', sa.DECIMAL(10, 4), nullable=True),
        sa.Column('low_price', sa.DECIMAL(10, 4), nullable=True),
        sa.Column('volume', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        # Foreign key constraint
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], name='fk_price_history_stock'),

        # Unique constraint on stock_id + price_date
        sa.UniqueConstraint('stock_id', 'price_date', name='uq_price_history_stock_date')
    )

    # Create indexes for performance
    op.create_index('idx_price_history_stock_date', 'price_history', ['stock_id', 'price_date'])
    op.create_index('idx_price_history_date', 'price_history', ['price_date'])

    print("⚠️  Recreated price_history table structure (data not restored)")
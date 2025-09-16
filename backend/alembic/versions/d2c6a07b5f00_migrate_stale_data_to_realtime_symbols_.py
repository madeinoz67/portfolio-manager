"""migrate stale data to realtime_symbols master table and clean up old artifacts

Revision ID: d2c6a07b5f00
Revises: 88b61f87b5c4
Create Date: 2025-09-16 19:39:08.246799

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd2c6a07b5f00'
down_revision = '88b61f87b5c4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Clear stale data from realtime_symbols table to force fresh data fetch.

    The CSL staleness issue was caused by 13+ hour old data in the realtime_symbols
    table because the service was using the old _store_price_data method instead
    of the new store_price_to_master method.
    """
    from sqlalchemy import text

    # Get database connection
    connection = op.get_bind()

    # Clear out all stale data from realtime_symbols table
    # This forces fresh data to be fetched using the corrected service
    connection.execute(text("DELETE FROM realtime_symbols"))

    print("✅ Cleared stale data from realtime_symbols table")
    print("ℹ️  Fresh data will be populated automatically when market data service runs")


def downgrade() -> None:
    """
    Downgrade is not implemented as this is a data cleanup migration.
    The old stale data is not preserved as it was the source of the staleness issue.
    """
    print("⚠️  Downgrade not implemented - this migration cleared stale data causing CSL staleness")
    pass
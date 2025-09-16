"""Rename market_data_api_usage_metrics table to market_data_usage_metrics

Revision ID: 89662fc34fab
Revises: 069a794bf481
Create Date: 2025-09-16 07:23:18.492352

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '89662fc34fab'
down_revision = '069a794bf481'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename the table to be more descriptive
    op.rename_table('market_data_api_usage_metrics', 'market_data_usage_metrics')


def downgrade() -> None:
    # Revert the table name back
    op.rename_table('market_data_usage_metrics', 'market_data_api_usage_metrics')
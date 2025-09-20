"""Add price_last_updated field to Portfolio model

Revision ID: 551c4dbedf91
Revises: 88ff55aea2fa
Create Date: 2025-09-16 11:01:15.018006

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '551c4dbedf91'
down_revision = '88ff55aea2fa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add price_last_updated column to portfolios table
    op.add_column('portfolios', sa.Column('price_last_updated', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove price_last_updated column from portfolios table
    op.drop_column('portfolios', 'price_last_updated')
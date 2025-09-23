"""Fix stock status enum values from lowercase to uppercase

Revision ID: 4410f4b3a5ef
Revises: 2cd1b7a1aab4
Create Date: 2025-09-23 19:36:37.771753

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4410f4b3a5ef'
down_revision = '2cd1b7a1aab4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update stock status values from lowercase to uppercase to match enum
    op.execute("UPDATE stocks SET status = 'ACTIVE' WHERE status = 'active'")
    op.execute("UPDATE stocks SET status = 'HALTED' WHERE status = 'halted'")
    op.execute("UPDATE stocks SET status = 'SUSPENDED' WHERE status = 'suspended'")
    op.execute("UPDATE stocks SET status = 'DELISTED' WHERE status = 'delisted'")


def downgrade() -> None:
    # Revert back to lowercase values
    op.execute("UPDATE stocks SET status = 'active' WHERE status = 'ACTIVE'")
    op.execute("UPDATE stocks SET status = 'halted' WHERE status = 'HALTED'")
    op.execute("UPDATE stocks SET status = 'suspended' WHERE status = 'SUSPENDED'")
    op.execute("UPDATE stocks SET status = 'delisted' WHERE status = 'DELISTED'")
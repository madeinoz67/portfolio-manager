"""Add role field to users table

Revision ID: 2842139f0989
Revises: 329f54ef5a2c
Create Date: 2025-09-13 21:07:51.173448

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '2842139f0989'
down_revision = '329f54ef5a2c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add role column to users table with default value
    op.add_column('users', sa.Column('role', sa.Enum('ADMIN', 'USER', name='userrole'), nullable=False, server_default='USER'))


def downgrade() -> None:
    # Drop role column from users table
    op.drop_column('users', 'role')
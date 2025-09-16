"""Add scheduler_executions table for persistent scheduler state

Revision ID: 4e2cac80bf09
Revises: 6cb3663a1203
Create Date: 2025-09-16 00:28:30.800169

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4e2cac80bf09'
down_revision = '6cb3663a1203'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create scheduler_executions table for persistent scheduler state
    op.create_table('scheduler_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('symbols_processed', sa.Integer(), nullable=True),
        sa.Column('successful_fetches', sa.Integer(), nullable=True),
        sa.Column('failed_fetches', sa.Integer(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('provider_used', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_metadata', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for performance
    op.create_index(op.f('ix_scheduler_executions_started_at'), 'scheduler_executions', ['started_at'], unique=False)
    op.create_index(op.f('ix_scheduler_executions_status'), 'scheduler_executions', ['status'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_scheduler_executions_status'), table_name='scheduler_executions')
    op.drop_index(op.f('ix_scheduler_executions_started_at'), table_name='scheduler_executions')

    # Drop table
    op.drop_table('scheduler_executions')
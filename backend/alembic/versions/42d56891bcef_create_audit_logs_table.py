"""Create audit_logs table

Revision ID: 42d56891bcef
Revises: 41c34498acdf
Create Date: 2025-09-15 14:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '42d56891bcef'
down_revision = '41c34498acdf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.Enum('PORTFOLIO_CREATED', 'PORTFOLIO_UPDATED', 'PORTFOLIO_DELETED', 'PORTFOLIO_SOFT_DELETED', 'PORTFOLIO_HARD_DELETED', 'TRANSACTION_CREATED', 'TRANSACTION_UPDATED', 'TRANSACTION_DELETED', 'HOLDING_CREATED', 'HOLDING_UPDATED', 'HOLDING_DELETED', 'USER_LOGIN', 'USER_LOGOUT', 'USER_CREATED', 'USER_UPDATED', 'ADMIN_ACTION_PERFORMED', name='auditeventtype'), nullable=False),
        sa.Column('event_description', sa.Text(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=100), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('event_metadata', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for efficient querying
    op.create_index('idx_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_logs_timestamp_desc', 'audit_logs', [sa.text('timestamp DESC')])
    op.create_index('idx_audit_logs_user_event_time', 'audit_logs', ['user_id', 'event_type', 'timestamp'])
    op.create_index(op.f('ix_audit_logs_entity_id'), 'audit_logs', ['entity_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_type'), 'audit_logs', ['entity_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_event_type'), 'audit_logs', ['event_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_timestamp'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_event_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_entity_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_entity_id'), table_name='audit_logs')
    op.drop_index('idx_audit_logs_user_event_time', table_name='audit_logs')
    op.drop_index('idx_audit_logs_timestamp_desc', table_name='audit_logs')
    op.drop_index('idx_audit_logs_entity', table_name='audit_logs')

    # Drop table
    op.drop_table('audit_logs')
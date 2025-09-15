"""Create api_usage_metrics table with proper UUID support

Revision ID: defe323440f5
Revises: 88ff55aea2fa
Create Date: 2025-09-15 21:47:12.133755

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'defe323440f5'
down_revision = '88ff55aea2fa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create api_usage_metrics table with proper UUID support
    op.create_table('api_usage_metrics',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('metric_id', sa.VARCHAR(length=100), nullable=False),
        sa.Column('provider_id', sa.VARCHAR(length=50), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('portfolio_id', sa.UUID(), nullable=True),
        sa.Column('request_type', sa.VARCHAR(length=50), nullable=False),
        sa.Column('requests_count', sa.INTEGER(), nullable=True),
        sa.Column('data_points_fetched', sa.INTEGER(), nullable=True),
        sa.Column('cost_estimate', sa.DECIMAL(precision=8, scale=4), nullable=True),
        sa.Column('recorded_at', sa.DATETIME(), nullable=False),
        sa.Column('time_bucket', sa.VARCHAR(length=20), nullable=False),
        sa.Column('rate_limit_hit', sa.BOOLEAN(), nullable=True),
        sa.Column('error_count', sa.INTEGER(), nullable=True),
        sa.Column('avg_response_time_ms', sa.INTEGER(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop api_usage_metrics table
    op.drop_table('api_usage_metrics')
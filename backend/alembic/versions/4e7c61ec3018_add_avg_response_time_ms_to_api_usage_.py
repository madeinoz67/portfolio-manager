"""add_avg_response_time_ms_to_api_usage_metrics

Revision ID: 4e7c61ec3018
Revises: 36e309dd1c92
Create Date: 2025-09-14 09:35:56.554998

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4e7c61ec3018'
down_revision = '36e309dd1c92'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add avg_response_time_ms column to api_usage_metrics table
    op.add_column('api_usage_metrics', sa.Column('avg_response_time_ms', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove avg_response_time_ms column from api_usage_metrics table
    op.drop_column('api_usage_metrics', 'avg_response_time_ms')
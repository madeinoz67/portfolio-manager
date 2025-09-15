"""Convert transaction_date from Date to DateTime

This migration converts transaction_date column from Date to DateTime (timestamp)
to simplify timezone handling and use standard JavaScript Date operations.

The migration preserves existing data by converting Date values to UTC timestamps
at midnight (00:00:00.000Z).

Revision ID: 9b3bfca83bef
Revises: 76b99972e95e
Create Date: 2025-09-15 08:07:29.187706

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '9b3bfca83bef'
down_revision = '76b99972e95e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Add new DateTime column temporarily
    op.add_column('transactions', sa.Column('transaction_timestamp', sa.DateTime(timezone=True), nullable=True))

    # Step 2: Update new column with converted values
    # Convert existing Date values to DateTime (midnight UTC)
    # SQLite compatible version
    connection = op.get_bind()
    connection.execute(sa.text(
        """
        UPDATE transactions
        SET transaction_timestamp = datetime(transaction_date || ' 00:00:00')
        WHERE transaction_date IS NOT NULL
        """
    ))

    # Step 3: Drop old Date column
    op.drop_column('transactions', 'transaction_date')

    # Step 4: Rename new column to original name
    op.alter_column('transactions', 'transaction_timestamp', new_column_name='transaction_date')

    # Step 5: Set NOT NULL constraint
    op.alter_column('transactions', 'transaction_date', nullable=False)


def downgrade() -> None:
    # Step 1: Add temporary Date column
    op.add_column('transactions', sa.Column('transaction_date_old', sa.Date(), nullable=True))

    # Step 2: Convert DateTime back to Date (extracting date part)
    # SQLite compatible version
    connection = op.get_bind()
    connection.execute(sa.text(
        """
        UPDATE transactions
        SET transaction_date_old = date(transaction_date)
        WHERE transaction_date IS NOT NULL
        """
    ))

    # Step 3: Drop DateTime column
    op.drop_column('transactions', 'transaction_date')

    # Step 4: Rename back to original name
    op.alter_column('transactions', 'transaction_date_old', new_column_name='transaction_date')

    # Step 5: Set NOT NULL constraint
    op.alter_column('transactions', 'transaction_date', nullable=False)
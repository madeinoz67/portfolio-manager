"""Add performance indexes for common queries

Revision ID: 0c1dbab347e4
Revises: 5209bda65d3e
Create Date: 2025-09-12 23:10:01.188732

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0c1dbab347e4'
down_revision = '5209bda65d3e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add indexes for common query patterns (using IF NOT EXISTS approach)
    
    # Portfolio queries - frequently filter by owner_id and is_active
    op.execute("CREATE INDEX IF NOT EXISTS ix_portfolios_owner_active ON portfolios (owner_id, is_active)")
    
    # Transaction queries - frequently filter by portfolio_id and transaction_date
    op.execute("CREATE INDEX IF NOT EXISTS ix_transactions_portfolio_date ON transactions (portfolio_id, transaction_date)")
    
    # Transaction queries - filter by portfolio_id for listing
    op.execute("CREATE INDEX IF NOT EXISTS ix_transactions_portfolio_id ON transactions (portfolio_id)")
    
    # Stock queries - lookup by symbol (most common) - likely already exists
    op.execute("CREATE INDEX IF NOT EXISTS ix_stocks_symbol ON stocks (symbol)")
    
    # Holdings queries - filter by portfolio_id
    op.execute("CREATE INDEX IF NOT EXISTS ix_holdings_portfolio_id ON holdings (portfolio_id)")
    
    # Holdings queries - filter by stock_id for aggregations  
    op.execute("CREATE INDEX IF NOT EXISTS ix_holdings_stock_id ON holdings (stock_id)")


def downgrade() -> None:
    # Remove indexes in reverse order (ignore if not exists)
    op.execute("DROP INDEX IF EXISTS ix_holdings_stock_id")
    op.execute("DROP INDEX IF EXISTS ix_holdings_portfolio_id") 
    op.execute("DROP INDEX IF EXISTS ix_stocks_symbol")
    op.execute("DROP INDEX IF EXISTS ix_transactions_portfolio_id")
    op.execute("DROP INDEX IF EXISTS ix_transactions_portfolio_date")
    op.execute("DROP INDEX IF EXISTS ix_portfolios_owner_active")
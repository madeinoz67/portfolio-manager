"""fix_provider_configurations_uuid_format

Fix provider_configurations table UUID columns to use 32-character format
without hyphens to match project standard (like users table).

Uses rename-add-migrate-remove approach for SQLite compatibility.

Revision ID: 2cd1b7a1aab4
Revises: 4e33f7897757
Create Date: 2025-09-20 20:24:18.209557

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2cd1b7a1aab4'
down_revision = '4e33f7897757'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite doesn't support many ALTER COLUMN operations, so we'll recreate the table

    # Clean up any leftover temporary table from previous failed migration
    connection = op.get_bind()
    connection.execute(sa.text("DROP TABLE IF EXISTS provider_configurations_new"))

    # Step 1: Create backup table with corrected schema
    op.create_table('provider_configurations_new',
        sa.Column('id', sa.String(32), nullable=False, primary_key=True),
        sa.Column('provider_name', sa.String(50), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('config_data', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_user_id', sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'])
    )

    # Step 2: Migrate data - convert 36-char UUIDs to 32-char format (skip rows with NULL UUIDs)
    connection = op.get_bind()
    connection.execute(sa.text("""
        INSERT INTO provider_configurations_new (
            id, provider_name, display_name, config_data,
            is_active, created_at, updated_at, created_by_user_id
        )
        SELECT
            REPLACE(id, '-', '') as id,
            provider_name, display_name, config_data,
            is_active, created_at, updated_at,
            REPLACE(created_by_user_id, '-', '') as created_by_user_id
        FROM provider_configurations
        WHERE id IS NOT NULL AND created_by_user_id IS NOT NULL
    """))

    # Step 3: Drop old table and rename new table
    op.drop_table('provider_configurations')
    op.rename_table('provider_configurations_new', 'provider_configurations')


def downgrade() -> None:
    # Reverse the process - convert 32-char UUIDs back to 36-char format

    # Step 1: Create backup table with old schema (36-char UUIDs with hyphens)
    op.create_table('provider_configurations_old',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('provider_name', sa.String(50), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('config_data', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_user_id', sa.String(36), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'])
    )

    # Step 2: Migrate data back - convert 32-char to 36-char format with hyphens
    connection = op.get_bind()
    connection.execute(sa.text("""
        INSERT INTO provider_configurations_old (
            id, provider_name, display_name, config_data,
            is_active, created_at, updated_at, created_by_user_id
        )
        SELECT
            SUBSTR(id, 1, 8) || '-' ||
            SUBSTR(id, 9, 4) || '-' ||
            SUBSTR(id, 13, 4) || '-' ||
            SUBSTR(id, 17, 4) || '-' ||
            SUBSTR(id, 21, 12) as id,
            provider_name, display_name, config_data,
            is_active, created_at, updated_at,
            SUBSTR(created_by_user_id, 1, 8) || '-' ||
            SUBSTR(created_by_user_id, 9, 4) || '-' ||
            SUBSTR(created_by_user_id, 13, 4) || '-' ||
            SUBSTR(created_by_user_id, 17, 4) || '-' ||
            SUBSTR(created_by_user_id, 21, 12) as created_by_user_id
        FROM provider_configurations
    """))

    # Step 3: Drop current table and rename old table
    op.drop_table('provider_configurations')
    op.rename_table('provider_configurations_old', 'provider_configurations')
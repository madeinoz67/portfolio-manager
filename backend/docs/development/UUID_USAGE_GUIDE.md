# UUID Usage Guide for SQLite Compatibility

## Problem Overview

When using UUIDs with SQLAlchemy and SQLite, there are compatibility issues between PostgreSQL-specific UUID types and SQLite's generic UUID handling.

## The Issue

### ❌ Problematic Pattern (Causes `'str' object has no attribute 'hex'` error)
```python
from sqlalchemy.dialects.postgresql import UUID

class MyModel(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

**Why this fails:**
- `UUID(as_uuid=True)` from PostgreSQL dialect expects UUID objects
- SQLite stores UUIDs as strings
- SQLAlchemy tries to call `.hex` on string values when binding parameters
- Results in `AttributeError: 'str' object has no attribute 'hex'`

### ✅ Correct Pattern (Works with SQLite)
```python
from sqlalchemy import Uuid

class MyModel(Base):
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
```

**Why this works:**
- Generic `Uuid` type handles both string and UUID object representations
- Compatible with SQLite's string-based UUID storage
- Works correctly with FastAPI's automatic UUID parameter conversion

## Migration Strategy

### 1. Model Updates
For each model with UUID columns, change the import and column definition:

```python
# Before
from sqlalchemy.dialects.postgresql import UUID
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

# After
from sqlalchemy import Uuid
id = Column(Uuid, primary_key=True, default=uuid.uuid4)
```

### 2. Database Schema Updates
Since SQLite doesn't support `ALTER COLUMN`, use table recreation:

```python
# Example: Fix provider_configurations table
conn = sqlite3.connect(database_path)
cursor = conn.cursor()

# 1. Backup data
cursor.execute('SELECT * FROM table_name')
backup_data = cursor.fetchall()

# 2. Rename old table
cursor.execute('ALTER TABLE table_name RENAME TO table_name_old')

# 3. Create new table with TEXT columns for UUIDs
cursor.execute('''
    CREATE TABLE table_name (
        id TEXT PRIMARY KEY,
        other_uuid_field TEXT,
        -- other columns...
    )
''')

# 4. Copy data
cursor.execute('INSERT INTO table_name SELECT * FROM table_name_old')

# 5. Drop old table
cursor.execute('DROP TABLE table_name_old')
conn.commit()
```

### 3. Service Layer Considerations
With the correct UUID model setup, services can handle both string and UUID parameters naturally:

```python
# Both of these work correctly:
config = db.query(Model).filter(Model.id == "550e8400-e29b-41d4-a716-446655440001").first()
config = db.query(Model).filter(Model.id == UUID("550e8400-e29b-41d4-a716-446655440001")).first()
```

## Models That Need Fixing

Based on grep results, these models use PostgreSQL UUID types and need updates:

- ✅ `provider_configuration.py` - Fixed
- ❌ `provider_metrics.py`
- ❌ `adapter_health_check.py`
- ❌ `adapter_registry.py`
- ❌ `cost_tracking_record.py`
- ❌ `sse_connection.py`
- ❌ `realtime_symbol.py`
- ❌ `realtime_price_history.py`
- ❌ `portfolio_valuation.py`
- ❌ `portfolio_update_metrics.py`
- ❌ `poll_interval_config.py`
- ❌ `market_data_usage_metrics.py`
- ❌ `market_data_provider.py`

## Testing UUID Compatibility

Use this test to verify UUID handling works correctly:

```python
from src.database import SessionLocal
from src.models.your_model import YourModel
from uuid import UUID

db = SessionLocal()
test_id = "550e8400-e29b-41d4-a716-446655440001"

# Both should work without errors
result1 = db.query(YourModel).filter(YourModel.id == test_id).first()
result2 = db.query(YourModel).filter(YourModel.id == UUID(test_id)).first()

assert result1 == result2  # Should find same record
db.close()
```

## FastAPI Integration

With correct UUID setup, FastAPI path parameters work seamlessly:

```python
@router.get("/adapters/{adapter_id}/metrics")
async def get_adapter_metrics(adapter_id: UUID):
    # adapter_id is automatically converted to UUID object
    # Works correctly with fixed models
    config = db.query(ProviderConfiguration).filter(
        ProviderConfiguration.id == adapter_id
    ).first()
```

## Key Lessons Learned from provider_configurations Fix

### Database Format Consistency is Critical

**Discovery:** The `provider_configurations` table was storing 36-character UUIDs with hyphens (`550e8400-e29b-41d4-a716-446655440001`) while the rest of the project uses 32-character UUIDs without hyphens (`550e8400e29b41d4a716446655440001`).

**Impact:** This format inconsistency caused binding errors even after fixing the model column types.

**Solution:** Used Alembic migration with table recreation approach:
```python
# Migration converts UUID format during data copy
SELECT REPLACE(id, '-', '') as id FROM old_table
```

### SQLite ALTER COLUMN Limitations

**Challenge:** SQLite doesn't support `ALTER COLUMN SET NOT NULL` or complex column type changes.

**Workaround:** Use rename-add-migrate-remove pattern:
1. Create new table with correct schema
2. Copy data with UUID format conversion
3. Drop old table and rename new table

**Example Migration:**
```python
def upgrade():
    # Create new table with VARCHAR(32) for UUIDs
    op.create_table('provider_configurations_new', ...)

    # Convert UUID format during data migration
    connection.execute(sa.text("""
        INSERT INTO provider_configurations_new (...)
        SELECT REPLACE(id, '-', '') as id, ...
        FROM provider_configurations
        WHERE id IS NOT NULL AND created_by_user_id IS NOT NULL
    """))

    # Replace old table
    op.drop_table('provider_configurations')
    op.rename_table('provider_configurations_new', 'provider_configurations')
```

### Data Quality During Migration

**Issue:** Found records with NULL UUIDs that would cause constraint violations.

**Solution:** Filter out invalid data during migration:
```sql
WHERE id IS NOT NULL AND created_by_user_id IS NOT NULL
```

**Best Practice:** Always validate data quality before schema changes.

### Testing Strategy for UUID Fixes

Use TDD to verify UUID binding works correctly:
```python
def test_uuid_handling_in_adapter_service(self, client, db, admin_user):
    # Create test adapter with known UUID
    test_uuid = uuid4()
    test_adapter = ProviderConfiguration(
        id=test_uuid,
        # ... other fields
    )
    db.add(test_adapter)
    db.commit()

    # Verify UUID was stored correctly
    assert test_adapter.id == test_uuid
    assert isinstance(test_adapter.id, UUID)
```

## Project UUID Standards

**Established Standard:** 32-character UUIDs without hyphens
- Users table: ✅ Uses `VARCHAR(32)` format
- Provider configurations: ✅ Fixed to match standard
- All other tables: Should follow this format

**Database Schema Verification:**
```bash
# Check UUID format consistency
sqlite3 portfolio.db "SELECT length(id), provider_name FROM provider_configurations LIMIT 5;"
# Should return 32 for length
```

## Summary

**Root Cause:** PostgreSQL-specific `UUID(as_uuid=True)` incompatible with SQLite + UUID format inconsistency
**Solution:** Use generic `sqlalchemy.Uuid` type + standardize to 32-character format
**Migration Pattern:** Table recreation with data format conversion for SQLite
**Impact:** Enables seamless UUID handling in SQLite with FastAPI UUID parameters
**Status:** ✅ ProviderConfiguration fixed with complete data migration, ❌ 12 other models need updates
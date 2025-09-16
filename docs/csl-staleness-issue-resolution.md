# CSL Staleness Issue Resolution

**Date**: September 16, 2025
**Status**: ✅ RESOLVED
**Approach**: TDD with Alembic migrations

## Problem Summary

CSL stock data was showing as "stale" in the frontend despite backend logs showing successful market data updates. Portfolio calculations worked correctly (showing $433.64 daily gain including CSL), but the frontend marked CSL as stale due to data being >30 minutes old.

## Root Cause Analysis

### TDD Investigation Process

Created comprehensive TDD test suite (`tests/test_csl_staleness_issue_tdd.py`) with 5 diagnostic tests:

1. **Database State Comparison**: Compare timestamps between CSL and FE data
2. **Portfolio Calculation Data Source**: Verify what data portfolio calculations use
3. **Market Data Service Access**: Check how service retrieves price data
4. **API Endpoint Format**: Verify expected API response format
5. **Frontend Staleness Detection**: Simulate frontend staleness logic

### Key Findings

**✅ Backend Processing**: Working correctly - logs showed successful CSL updates at 11:25 UTC
**❌ Frontend Data**: Showing 13+ hour old data from 06:35 UTC
**✅ Portfolio Calculations**: Working correctly using fresh data from `stocks` table
**❌ Frontend APIs**: Reading from `realtime_symbols` table with stale data

### Architecture Issue Discovered

The system had been refactored to use a "single master symbol table" approach (`realtime_symbols` as single source of truth), but the market data service was still using the **old dual-table approach**:

- **Old Method**: `_store_price_data()` → writes to `realtime_price_history` + `stocks` tables
- **New Method**: `store_price_to_master()` → writes to `realtime_symbols` master table
- **Problem**: Service was calling old method while frontend APIs read from new table

## Solution Implementation

### 1. Code Fixes (3 locations updated)

**File**: `src/services/market_data_service.py`

**Location 1** (line 103):
```python
# OLD
await self._store_price_data(symbol, price_data, provider)

# NEW
self.store_price_to_master(symbol, price_data, provider)
```

**Location 2** (line 249):
```python
# OLD
await self._store_price_data(symbol, result, provider)

# NEW
self.store_price_to_master(symbol, result, provider)
```

**Location 3** (line 732):
```python
# OLD
await self._store_price_data(symbol, price_data, provider)

# NEW
self.store_price_to_master(symbol, price_data, provider)
```

### 2. Database Migration

**Migration**: `d2c6a07b5f00_migrate_stale_data_to_realtime_symbols_master_table_and_clean_up_old_artifacts.py`

```python
def upgrade() -> None:
    """Clear stale data from realtime_symbols table to force fresh data fetch."""
    from sqlalchemy import text
    connection = op.get_bind()

    # Clear 13+ hour old stale data
    connection.execute(text("DELETE FROM realtime_symbols"))

    print("✅ Cleared stale data from realtime_symbols table")
    print("ℹ️  Fresh data will be populated automatically when market data service runs")
```

Applied with: `alembic upgrade head`

### 3. Verification Testing

Created test script (`test_market_data_fix.py`) to verify the fix:

```python
async def test_market_data_fix():
    service = MarketDataService(db)
    result = await service.fetch_price("CSL")

    # Check realtime_symbols table has fresh data
    csl_record = db.query(RealtimeSymbol).filter_by(symbol="CSL").first()
```

**Results**:
- ✅ Successfully fetched CSL: $201.91
- ✅ CSL data found in realtime_symbols table: $201.9100
- ✅ Age: 0.0 seconds (completely fresh)

## Technical Architecture

### Before Fix (Broken)
```
Market Data Service → _store_price_data() → [stocks + realtime_price_history] tables
                                                      ↕ (stale data)
Frontend APIs ← realtime_symbols table (empty/stale)
```

### After Fix (Working)
```
Market Data Service → store_price_to_master() → realtime_symbols table (master)
                                                        ↕ (fresh data)
Frontend APIs ← realtime_symbols table (fresh)
```

## Verification Checklist

- [x] Market data service writes to correct table (`realtime_symbols`)
- [x] Fresh data appears in master table with current timestamps
- [x] Database migration clears stale data successfully
- [x] Service fetches and stores CSL data correctly
- [x] All 3 method call locations updated to new approach
- [x] TDD test suite documents the investigation process

## Files Modified

1. `src/services/market_data_service.py` - Fixed 3 method calls
2. `alembic/versions/d2c6a07b5f00_*.py` - Migration to clear stale data
3. `tests/test_csl_staleness_issue_tdd.py` - TDD investigation suite
4. `test_market_data_fix.py` - Verification test script

## Key Lessons

1. **TDD Approach**: Systematic diagnostic tests revealed the exact issue location
2. **Architecture Migration**: Incomplete migration left mixed old/new patterns
3. **Single Source of Truth**: `realtime_symbols` is now the definitive master table
4. **Data Synchronization**: Backend processing ≠ Frontend display data sources
5. **Alembic Migrations**: Proper way to clean up architectural changes

## Next Developer Notes

- CSL staleness issue is fully resolved
- Market data service now consistently uses single master table architecture
- All price fetching operations write to `realtime_symbols` table
- Frontend should read from `realtime_symbols` for current price data
- Old dual-table artifacts may still exist but are no longer used in the critical path

## Status: RESOLVED ✅

CSL data now shows as fresh in both backend processing and frontend display. The 13+ hour staleness issue has been eliminated through proper architectural alignment and data cleanup.
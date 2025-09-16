# Scheduler Metrics Singleton Database Session Fix

## Issue Summary

The admin dashboard was displaying **0 symbols processed** and **0.00% success rate** for the scheduler metrics, despite the scheduler running successfully and processing symbols regularly.

## Root Cause Analysis

### Investigation Process

1. **Initial Symptoms**:
   - Admin dashboard showed 0 symbols processed
   - Scheduler was actually running and processing symbols (8 symbols every 15 minutes)
   - Storm Protection metrics worked correctly (66.7%, 100%)

2. **Database Investigation**:
   - Found 37 `SchedulerExecution` records in database with successful runs
   - Raw SQL queries showed 93 total symbols processed
   - Data was present and correct in the database

3. **Critical Discovery**:
   - The `get_scheduler_service()` function used a **singleton pattern** with flawed database session handling
   - The singleton captured the database session from the **first call only**
   - Subsequent calls ignored the fresh database session parameter

### Root Cause: Singleton Database Session Bug

**File**: `src/services/scheduler_service.py:624-635`

**Original Problematic Code**:
```python
def get_scheduler_service(db: Session) -> MarketDataSchedulerService:
    """Get or create scheduler service instance."""
    global _scheduler_service_instance

    if _scheduler_service_instance is None:
        _scheduler_service_instance = MarketDataSchedulerService(db)

    return _scheduler_service_instance  # BUG: Always returns same instance with old DB session
```

**Problem**:
- **First call**: Creates singleton with database session A
- **Subsequent calls**: Returns same singleton instance but **ignores the new database session parameter**
- **FastAPI**: Each request gets a fresh database session via `Depends(get_db)`
- **Result**: Scheduler service uses stale/expired database session, sees 0 records

## Fix Implementation

### TDD Approach

Created comprehensive test suite to reproduce and verify the fix:

1. **`tests/test_scheduler_live_data_investigation.py`**: Investigated live data and confirmed existence of execution records
2. **`tests/test_scheduler_execution_table_missing_tdd.py`**: Verified table structure and model functionality
3. **`tests/test_scheduler_database_session_debug_tdd.py`**: Comprehensive database session testing
4. **`tests/test_scheduler_singleton_bug_tdd.py`**: Reproduced and verified the singleton bug fix

### Solution

**File**: `src/services/scheduler_service.py:624-640`

**Fixed Code**:
```python
def get_scheduler_service(db: Session) -> MarketDataSchedulerService:
    """Get or create scheduler service instance with fresh database session."""
    global _scheduler_service_instance

    if _scheduler_service_instance is None:
        _scheduler_service_instance = MarketDataSchedulerService(db)
    else:
        # CRITICAL FIX: Update the database session to the current one
        # This ensures the scheduler always uses the fresh session provided by FastAPI
        _scheduler_service_instance.db = db

    return _scheduler_service_instance
```

**Key Changes**:
- **Maintains singleton pattern** for scheduler state continuity
- **Updates database session** on every call to use the fresh session
- **Ensures compatibility** with FastAPI's dependency injection system
- **No breaking changes** to existing functionality

## Verification

### Test Results

**Before Fix**:
```
Total runs: 0
Successful runs: 0
Total symbols processed: 0
Success rate: 0.0%
```

**After Fix**:
```
Total runs: 44
Successful runs: 44
Total symbols processed: 115
Success rate: 100.0%
```

### Database Consistency

- **Raw SQL Query**: 44 records, 115 symbols processed
- **ORM Query**: 44 records, 115 symbols processed
- **Scheduler Service**: 44 records, 115 symbols processed ✅
- **Admin API**: 44 records, 115 symbols processed ✅

## Impact Analysis

### Before Fix
- ❌ **Admin Dashboard**: Showed misleading 0 metrics despite successful scheduler operation
- ❌ **Monitoring**: False impression that scheduler wasn't working
- ❌ **Database Sessions**: Potential stale session issues throughout the application

### After Fix
- ✅ **Admin Dashboard**: Correctly displays real scheduler metrics (115 symbols processed, 100% success rate)
- ✅ **Real-time Accuracy**: Metrics update properly with each fresh database session
- ✅ **Monitoring Reliability**: Accurate system health monitoring
- ✅ **Database Integrity**: Fresh database sessions prevent stale data issues

## Technical Details

### Database Schema
- **Table**: `scheduler_executions`
- **Key Fields**: `symbols_processed`, `successful_fetches`, `failed_fetches`, `status`
- **Existing Data**: 37+ execution records with successful symbol processing

### API Endpoints Affected
- **`GET /api/v1/admin/scheduler/status`**: Now returns correct metrics
- **Admin Dashboard**: Scheduler section shows accurate data

### Testing Strategy
- **TDD Methodology**: Created failing tests first, then implemented fix
- **Database Testing**: Direct SQL queries, ORM queries, and API integration tests
- **Session Management**: Verified singleton pattern with fresh session updates
- **Integration Testing**: End-to-end admin dashboard simulation

## Lessons Learned

1. **Singleton + Database Sessions**: Requires careful session management to avoid stale data
2. **FastAPI Dependency Injection**: Fresh sessions per request need to be properly propagated
3. **Debugging Strategy**: Systematic investigation from symptoms → database → service layer → fix
4. **Testing Importance**: TDD approach crucial for reproducing complex session management bugs

## Future Recommendations

1. **Session Management Review**: Audit other singleton services for similar issues
2. **Monitoring Enhancement**: Add database session health checks to admin dashboard
3. **Documentation**: Document singleton patterns and their database session requirements
4. **Testing Standards**: Establish patterns for testing singleton services with database dependencies

---

**Fix Implemented**: 2025-09-16
**Testing**: Comprehensive TDD test suite
**Impact**: Critical admin dashboard functionality restored
**Status**: ✅ RESOLVED
# Scheduler API Architecture Decision

## Overview

The portfolio manager backend maintains two distinct scheduler status endpoints that serve different purposes and user contexts. This document explains the architectural decision to keep both endpoints and their specific roles.

## Endpoints

### 1. Admin Scheduler Endpoint
**Endpoint:** `/api/v1/admin/scheduler/status`
**Location:** `src/api/admin.py`
**Model:** `SchedulerStatus`

**Purpose:** Administrative oversight and system health monitoring
- High-level system metrics (total runs, success rate, uptime)
- Admin control functions (start/stop/pause scheduler)
- System health perspective for operations teams
- Overall scheduler performance monitoring

**Response Fields:**
```json
{
  "schedulerName": "market_data_scheduler",
  "state": "running|stopped|paused|error",
  "lastRun": "2025-09-16T01:56:23.202Z",
  "nextRun": "2025-09-16T02:11:23.202Z",
  "total_runs": 60,
  "successful_runs": 59,
  "failed_runs": 1,
  "symbols_processed": 187,
  "success_rate": 98.33,
  "uptimeSeconds": 3600
}
```

**Used By:** Admin dashboard, system monitoring tools

### 2. Market Data Scheduler Endpoint
**Endpoint:** `/api/v1/market-data/scheduler/status`
**Location:** `src/api/market_data.py`
**Model:** `SchedulerStatusResponse`

**Purpose:** Market data operational view and data quality monitoring
- Provider-specific metrics and performance
- Data freshness and polling intervals
- Market data quality perspective for traders/analysts
- Real-time data availability status

**Response Fields:**
```json
{
  "scheduler": {
    "state": "running",
    "next_run": "2025-09-16T02:11:23.202Z",
    "interval_minutes": 15
  },
  "recent_activity": {
    "total_symbols_processed": 8,
    "success_rate": 100.0,
    "avg_response_time_ms": 150
  },
  "provider_stats": {
    "yahoo_finance": {"enabled": true, "success_rate": 100.0},
    "alpha_vantage": {"enabled": false, "api_key_configured": false}
  }
}
```

**Used By:** Market data dashboard, trading systems, data quality monitoring

## Architectural Reasoning

### Why Keep Both Endpoints?

1. **Different User Contexts**
   - **Admins** care about system health, resource usage, and operational control
   - **Market Data Users** care about data freshness, provider performance, and trading-relevant metrics

2. **Current Usage Pattern**
   - Scheduler is currently only used for market data polling
   - Market data users expect scheduler metrics on the market-data admin page
   - Admin users need system-level scheduler control and monitoring

3. **Separation of Concerns**
   - Admin endpoint focuses on system operations and control
   - Market data endpoint focuses on business/trading operations
   - Each serves distinct use cases without overlap

4. **Future Extensibility**
   - If scheduler expands beyond market data (e.g., portfolio recalculation, reporting)
   - Admin endpoint remains system-focused
   - Domain-specific endpoints can be added (portfolio scheduler, etc.)

### UI Organization

- **Admin Dashboard (`/admin`)**: High-level scheduler health summary
- **Market Data Page (`/admin/market-data`)**: Detailed market data scheduler metrics
- **System Page (`/admin/system`)**: Technical scheduler details and controls

## Implementation Notes

### Frontend Field Mapping Fix
The frontend was initially looking for nested `recent_activity` fields but the admin endpoint returns data at the root level:

**Before (Incorrect):**
```typescript
schedulerStatus.recent_activity?.total_symbols_processed
schedulerStatus.recent_activity?.success_rate
```

**After (Correct):**
```typescript
schedulerStatus.symbols_processed
schedulerStatus.success_rate
```

### Database Session Singleton Fix
Fixed scheduler service singleton pattern to use fresh database sessions:
```python
def get_scheduler_service(db: Session) -> MarketDataSchedulerService:
    global _scheduler_service_instance
    if _scheduler_service_instance is None:
        _scheduler_service_instance = MarketDataSchedulerService(db)
    else:
        # CRITICAL: Update database session to current one
        _scheduler_service_instance.db = db
    return _scheduler_service_instance
```

## Future Considerations

1. **API Versioning**: Both endpoints should follow consistent versioning strategy
2. **Response Caching**: Consider caching scheduler status to reduce database load
3. **Real-time Updates**: WebSocket or SSE for live scheduler status updates
4. **Metrics Standardization**: Ensure consistent metric definitions across endpoints

## Related Files

- `src/api/admin.py` - Admin scheduler endpoint and models
- `src/api/market_data.py` - Market data scheduler endpoint
- `src/services/scheduler_service.py` - Core scheduler service with singleton fix
- `frontend/src/app/admin/market-data/page.tsx` - Frontend implementation
- `docs/scheduler-metrics-singleton-fix.md` - Technical details of database session fix

---

**Decision Date:** September 16, 2025
**Status:** Implemented
**Review Date:** When scheduler functionality expands beyond market data
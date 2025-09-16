# Debugging Notes & Lessons Learned

## ⚠️ CRITICAL: Always Check for Multiple Backend Instances

**Date:** 2025-09-16
**Issue:** Market data page showing stale data, admin dashboard crashes with "no such table: api_usage_metrics"
**Root Cause:** Multiple uvicorn backend instances running simultaneously

### The Problem
- Multiple background bash sessions were running `uv run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload`
- Each instance was using different database states/schemas
- One instance had old table names (`api_usage_metrics`) while another had new names (`market_data_usage_metrics`)
- This caused inconsistent behavior and database errors

### The Solution
1. **ALWAYS check for multiple instances BEFORE debugging:**
   ```bash
   ps aux | grep uvicorn | grep -v grep
   ```

2. **Kill all instances and start fresh:**
   ```bash
   killall -9 uvicorn
   cd /path/to/backend && uv run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
   ```

3. **Verify only ONE instance is running:**
   ```bash
   ps aux | grep uvicorn | grep -v grep  # Should show only one process
   curl -s "http://localhost:8001/health"  # Should return {"status":"healthy"}
   ```

### Symptoms of Multiple Instances
- ✅ **Inconsistent API responses** (some endpoints work, others fail)
- ✅ **Database table errors** ("no such table" errors)
- ✅ **High CPU usage** from multiple uvicorn processes
- ✅ **Stale data** that doesn't update despite code changes
- ✅ **Migration issues** where some tables exist and others don't

### Prevention
- **ALWAYS run this check FIRST when debugging any backend issue:**
  ```bash
  echo "=== Checking for multiple backend instances ==="
  ps aux | grep uvicorn | grep -v grep
  echo "=== Should show only ONE uvicorn process ==="
  ```

- **Before making any changes to backend code or database**
- **When encountering unexplained database errors**
- **When API responses seem inconsistent or stale**

### Golden Rule
**🚨 NEVER DEBUG BACKEND ISSUES WITHOUT FIRST VERIFYING ONLY ONE INSTANCE IS RUNNING 🚨**

---

## Market Data Freshness Investigation - 2025-09-16

**Issue:** User reported market data page showing stale prices ("15 minutes ago" for WBC vs "4 minutes ago" for others)

**Root Cause Discovery via TDD:**
1. ✅ **Created comprehensive TDD test** (`tests/test_market_data_freshness_tdd.py`)
2. ✅ **Multiple backend instances issue fixed** - Applied golden rule first
3. ✅ **Background scheduler IS working correctly:**
   - Successfully fetching 8/8 symbols every 15 minutes
   - Using yfinance provider with bulk optimization
   - All target symbols updated: BHP, CBA, CSL, FE, NAB, NEM, TLS, WBC
   - Scheduler execution logs show 100% success rate

**Key Insight:** TDD test showed "no data" because test database (SQLite test.db) is separate from main database. The background scheduler has been populating the main database correctly all along.

**Verified Working Components:**
- ✅ Background scheduler: `periodic_price_updates()` running every 15 minutes
- ✅ Market data service: yfinance provider working with bulk fetching
- ✅ Database: `realtime_price_history` table being populated
- ✅ Portfolio updates: Triggered after price changes
- ✅ Activity logging: All operations logged to `provider_activities`

**Lesson:** Always distinguish between test vs production databases when debugging data issues.

---

## Other Debugging Notes

### Database Migration Issues
- Always use `alembic upgrade head` after pulling changes
- Check `alembic current` to verify migration state
- Ensure database file paths match between `alembic.ini` and `src/core/config.py`

### Frontend-Backend Connection Issues
- Verify backend is accessible: `curl http://localhost:8001/health`
- Check CORS settings in backend config
- Verify frontend is pointing to correct backend URL

---

*This document should be updated with new debugging insights as they arise.*
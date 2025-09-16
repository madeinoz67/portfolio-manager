# Troubleshooting Pricing Issues

This guide provides step-by-step solutions for common pricing and market data issues in the Portfolio Manager system.

## Quick Diagnostic Commands

### 1. Check System Health

```bash
# Backend server status
curl -s http://localhost:8001/health | jq

# Database connectivity
cd backend && uv run python -c "from src.database import engine; print('✓ Database connected' if engine else '✗ Database failed')"

# Market data providers status
curl -s http://localhost:8001/api/v1/market-data/status | jq
```

### 2. Database Quick Checks

```sql
-- Recent price updates
SELECT symbol, current_price, last_price_update,
       NOW() - last_price_update as age
FROM stocks
WHERE last_price_update > NOW() - INTERVAL '2 hours'
ORDER BY last_price_update DESC LIMIT 10;

-- Provider activity in last hour
SELECT p.display_name, pa.activity_type, pa.status, COUNT(*)
FROM provider_activities pa
JOIN market_data_providers p ON pa.provider_id = p.id
WHERE pa.created_at > NOW() - INTERVAL '1 hour'
GROUP BY p.display_name, pa.activity_type, pa.status;

-- Data consistency check
SELECT s.symbol, s.current_price as stock_price, h.price as history_price,
       s.last_price_update, h.fetched_at,
       ABS(s.current_price - h.price) as price_diff
FROM stocks s
JOIN (
    SELECT DISTINCT ON (symbol) symbol, price, fetched_at
    FROM realtime_price_history
    ORDER BY symbol, fetched_at DESC
) h ON s.symbol = h.symbol
WHERE ABS(s.current_price - h.price) > 0.01
ORDER BY price_diff DESC;
```

## Common Issues and Solutions

### Issue 1: Holdings Show Stale "Last Updated" Times

**Symptoms:**
- Holdings page shows timestamps from hours/days ago
- Market-data page shows recent timestamps
- Price values may differ between pages

**Root Cause Analysis:**
```sql
-- Check if stocks table is being updated
SELECT symbol, current_price, last_price_update,
       EXTRACT(EPOCH FROM (NOW() - last_price_update))/60 as minutes_old
FROM stocks
WHERE symbol IN ('CBA', 'BHP', 'CSL')  -- Replace with your symbols
ORDER BY last_price_update DESC;

-- Check if price history is being updated
SELECT symbol, price, fetched_at,
       EXTRACT(EPOCH FROM (NOW() - fetched_at))/60 as minutes_old
FROM realtime_price_history
WHERE symbol IN ('CBA', 'BHP', 'CSL')
AND fetched_at > NOW() - INTERVAL '2 hours'
ORDER BY fetched_at DESC;
```

**Solution:**
```python
# Verify market data service is updating both tables
# Check src/services/market_data_service.py:_store_price_data()

# Manual fix for immediate resolution:
UPDATE stocks s
SET current_price = h.price,
    last_price_update = h.fetched_at
FROM (
    SELECT DISTINCT ON (symbol) symbol, price, fetched_at
    FROM realtime_price_history
    ORDER BY symbol, fetched_at DESC
) h
WHERE s.symbol = h.symbol;
```

**Prevention:**
- Run TDD tests: `uv run pytest tests/test_market_data_stock_update_tdd.py`
- Monitor with alerts on timestamp staleness

### Issue 2: Price Inconsistencies Between Holdings and Market Data

**Symptoms:**
- CSL shows $201.25 on market-data page
- CSL shows $199.50 on holdings page
- Different "last updated" times

**Diagnostic Steps:**
```sql
-- Find price discrepancies
WITH stock_prices AS (
    SELECT symbol, current_price as stock_price, last_price_update
    FROM stocks
),
history_prices AS (
    SELECT DISTINCT ON (symbol)
           symbol, price as history_price, fetched_at
    FROM realtime_price_history
    ORDER BY symbol, fetched_at DESC
)
SELECT sp.symbol, sp.stock_price, hp.history_price,
       ABS(sp.stock_price - hp.history_price) as difference,
       sp.last_price_update, hp.fetched_at
FROM stock_prices sp
JOIN history_prices hp ON sp.symbol = hp.symbol
WHERE ABS(sp.stock_price - hp.history_price) > 0.01;
```

**Solution:**
```bash
# Run the comprehensive TDD test
cd backend
uv run pytest tests/test_price_consistency_tdd.py::TestPriceConsistencyBug::test_both_apis_return_same_csl_price -v

# If test fails, check market data service dual-table update logic
# Manually synchronize data:
cd backend && uv run python -c "
from src.database import SessionLocal
from src.services.market_data_service import MarketDataService
from src.models.market_data_provider import MarketDataProvider

db = SessionLocal()
try:
    service = MarketDataService(db)
    provider = db.query(MarketDataProvider).filter_by(name='yahoo_finance').first()
    if provider:
        # Trigger fresh price fetch for problematic symbols
        asyncio.run(service.fetch_and_store_prices(['CSL', 'CBA', 'BHP'], provider))
finally:
    db.close()
"
```

### Issue 3: Timestamp Serialization Errors

**Symptoms:**
- API returns 500 errors
- Logs show: `AttributeError: 'str' object has no attribute 'tzinfo'`
- Holdings API calls fail

**Diagnostic:**
```bash
# Check API response
curl -s http://localhost:8001/api/v1/portfolios/1/holdings \
  -H "Authorization: Bearer YOUR_TOKEN" | jq

# Check backend logs for stack trace
docker logs portfolio-backend 2>&1 | grep -A 10 "AttributeError.*tzinfo"
```

**Solution:**
The fix is already implemented in `src/schemas/stock.py`. Verify it's applied:

```python
# Check the convert_timestamp method in StockResponse class
# Should include type checking:
if not isinstance(data.last_price_update, str):
    data.last_price_update = to_iso_string(data.last_price_update)
```

**Test the fix:**
```bash
cd backend
uv run pytest tests/test_holdings_timestamp_bug_tdd.py -v
```

### Issue 4: Market Data Scheduler Not Running

**Symptoms:**
- No recent price updates in any table
- Provider activities table shows no recent entries
- All timestamps are stale

**Diagnostic:**
```sql
-- Check scheduler execution history
SELECT execution_type, started_at, completed_at, status,
       symbols_processed, symbols_succeeded, symbols_failed
FROM scheduler_executions
WHERE started_at > NOW() - INTERVAL '24 hours'
ORDER BY started_at DESC;

-- Check provider availability
SELECT name, display_name, is_enabled,
       rate_limit_per_minute, timeout_seconds
FROM market_data_providers
WHERE is_enabled = true;
```

**Solution:**
```bash
# Check if background tasks are running
curl -s http://localhost:8001/api/v1/admin/market-data/scheduler/status \
  -H "Authorization: Bearer ADMIN_TOKEN" | jq

# Restart scheduler if needed
curl -X POST http://localhost:8001/api/v1/admin/market-data/scheduler/control \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "start"}'

# Manual price refresh
curl -X POST http://localhost:8001/api/v1/market-data/refresh \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["CBA", "BHP", "CSL"]}'
```

### Issue 5: Provider API Failures

**Symptoms:**
- All providers showing errors in admin dashboard
- No new price data being fetched
- High error counts in provider_activities

**Diagnostic:**
```sql
-- Check recent provider errors
SELECT p.display_name, pa.activity_type, pa.status,
       pa.error_message, pa.response_time_ms, pa.created_at
FROM provider_activities pa
JOIN market_data_providers p ON pa.provider_id = p.id
WHERE pa.status = 'ERROR'
AND pa.created_at > NOW() - INTERVAL '1 hour'
ORDER BY pa.created_at DESC;

-- Check rate limiting
SELECT p.display_name, COUNT(*) as request_count,
       AVG(pa.response_time_ms) as avg_response_time
FROM provider_activities pa
JOIN market_data_providers p ON pa.provider_id = p.id
WHERE pa.created_at > NOW() - INTERVAL '1 hour'
GROUP BY p.display_name;
```

**Solution:**
```bash
# Test provider connectivity manually
cd backend && uv run python -c "
import asyncio
from src.services.market_data_service import MarketDataService
from src.database import SessionLocal

async def test_provider():
    db = SessionLocal()
    try:
        service = MarketDataService(db)
        # Test Yahoo Finance directly
        data = await service._fetch_yahoo_finance_data(['AAPL'])
        print(f'✓ Yahoo Finance: {data}')
    except Exception as e:
        print(f'✗ Yahoo Finance failed: {e}')
    finally:
        db.close()

asyncio.run(test_provider())
"

# Check API key configuration for Alpha Vantage
# Update provider settings if needed
```

## Performance Issues

### Issue 6: Slow Portfolio Loading

**Symptoms:**
- Holdings page takes >5 seconds to load
- Database queries timing out
- High CPU usage on database

**Diagnostic:**
```sql
-- Check slow queries
SELECT query, mean_exec_time, calls, total_exec_time
FROM pg_stat_statements
WHERE query LIKE '%stocks%' OR query LIKE '%holdings%'
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE tablename IN ('stocks', 'holdings', 'realtime_price_history')
AND (n_distinct > 100 OR correlation < 0.1);
```

**Solution:**
```sql
-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_holdings_portfolio_calc
ON holdings(portfolio_id, stock_id, quantity, average_cost);

CREATE INDEX CONCURRENTLY idx_stocks_symbol_price_update
ON stocks(symbol, last_price_update);

CREATE INDEX CONCURRENTLY idx_price_history_symbol_recent
ON realtime_price_history(symbol, fetched_at DESC);

-- Update table statistics
ANALYZE stocks;
ANALYZE holdings;
ANALYZE realtime_price_history;
```

### Issue 7: Memory Leaks in Price Processing

**Symptoms:**
- Backend memory usage continuously increasing
- Server becoming unresponsive after hours
- Out of memory errors

**Diagnostic:**
```python
# Add memory monitoring to market data service
import psutil
import gc

# In MarketDataService methods:
def _monitor_memory(self, operation: str):
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    if memory_mb > 500:  # Alert if over 500MB
        logger.warning(f"High memory usage in {operation}: {memory_mb:.1f}MB")
        gc.collect()  # Force garbage collection
```

**Solution:**
```python
# Implement proper connection management
# In market_data_service.py:

async def _store_price_data(self, symbol: str, price_data: Dict, provider: MarketDataProvider):
    """Store price data with proper resource cleanup."""
    try:
        # Process data
        price_record = RealtimePriceHistory(...)
        self.db.add(price_record)

        # Update stocks table
        stock = self.db.query(Stock).filter_by(symbol=symbol).first()
        # ... update logic

        # Commit and cleanup
        self.db.commit()

    except Exception as e:
        self.db.rollback()
        raise
    finally:
        # Explicit cleanup
        self.db.expunge_all()
        gc.collect()
```

## Monitoring and Alerting

### Set Up Health Checks

```bash
# Create health check script
cat > /opt/portfolio-manager/health-check.sh << 'EOF'
#!/bin/bash

# Check API health
if ! curl -sf http://localhost:8001/health >/dev/null; then
    echo "❌ API health check failed"
    exit 1
fi

# Check recent price updates
STALE_COUNT=$(psql -d portfolio -t -c "
    SELECT COUNT(*) FROM stocks
    WHERE last_price_update < NOW() - INTERVAL '1 hour';
")

if [ "$STALE_COUNT" -gt 10 ]; then
    echo "❌ Too many stale prices: $STALE_COUNT"
    exit 1
fi

echo "✅ Health check passed"
EOF

chmod +x /opt/portfolio-manager/health-check.sh

# Set up cron job
echo "*/5 * * * * /opt/portfolio-manager/health-check.sh" | crontab -
```

### Database Monitoring Queries

```sql
-- Create monitoring views
CREATE VIEW pricing_health_summary AS
SELECT
    COUNT(*) as total_stocks,
    COUNT(CASE WHEN last_price_update > NOW() - INTERVAL '1 hour' THEN 1 END) as fresh_prices,
    COUNT(CASE WHEN last_price_update < NOW() - INTERVAL '24 hours' THEN 1 END) as stale_prices,
    AVG(EXTRACT(EPOCH FROM (NOW() - last_price_update))/60) as avg_age_minutes,
    MAX(last_price_update) as most_recent_update,
    MIN(last_price_update) as oldest_update
FROM stocks
WHERE last_price_update IS NOT NULL;

-- Provider performance view
CREATE VIEW provider_performance_summary AS
SELECT
    p.display_name,
    COUNT(pa.id) as total_requests,
    COUNT(CASE WHEN pa.status = 'SUCCESS' THEN 1 END) as successful_requests,
    COUNT(CASE WHEN pa.status = 'ERROR' THEN 1 END) as failed_requests,
    ROUND(AVG(pa.response_time_ms), 2) as avg_response_time_ms,
    MAX(pa.created_at) as last_activity
FROM market_data_providers p
LEFT JOIN provider_activities pa ON p.id = pa.provider_id
    AND pa.created_at > NOW() - INTERVAL '24 hours'
GROUP BY p.id, p.display_name;
```

## Emergency Procedures

### Complete System Reset

If all else fails, perform a complete pricing system reset:

```bash
# 1. Stop all services
docker-compose down

# 2. Backup current data
pg_dump portfolio > portfolio_backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Reset pricing tables
psql -d portfolio << 'EOF'
TRUNCATE realtime_price_history CASCADE;
UPDATE stocks SET last_price_update = NULL, current_price = NULL;
TRUNCATE provider_activities CASCADE;
TRUNCATE scheduler_executions CASCADE;
EOF

# 4. Restart services
docker-compose up -d

# 5. Trigger initial price fetch
curl -X POST http://localhost:8001/api/v1/market-data/refresh \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["CBA", "BHP", "CSL", "WES", "TLS"]}'

# 6. Monitor recovery
watch "psql -d portfolio -c \"SELECT * FROM pricing_health_summary;\""
```

### Data Recovery from Backup

```bash
# Restore from backup if needed
pg_restore --clean --if-exists -d portfolio portfolio_backup_YYYYMMDD_HHMMSS.sql

# Verify data integrity
psql -d portfolio -c "
    SELECT COUNT(*) as total_stocks,
           MAX(last_price_update) as most_recent,
           COUNT(CASE WHEN last_price_update > NOW() - INTERVAL '2 hours' THEN 1 END) as recent_count
    FROM stocks;
"
```

## Support Contacts

For issues not covered in this guide:

1. **Check GitHub Issues**: Look for similar problems in the project repository
2. **Enable Debug Logging**: Set `LOG_LEVEL=DEBUG` in environment variables
3. **Collect System Information**: Database version, Python version, deployed commit hash
4. **Generate Support Bundle**: Include logs, configuration, and diagnostic output

This troubleshooting guide should resolve most common pricing-related issues in the Portfolio Manager system.
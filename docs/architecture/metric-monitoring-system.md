# Metric Monitoring System

## Overview

The Portfolio Manager includes a comprehensive metric monitoring system that tracks API usage, system performance, and operational health across different system components. The system follows a **system-specific table naming convention** to eliminate confusion and enable clear monitoring of each system component.

## Architecture

### System-Specific Table Design

Each system component has its own dedicated metrics table following the pattern: `<system>_api_usage_metrics`

Currently implemented:
- **`market_data_usage_metrics`**: Tracks market data provider API calls (Yahoo Finance, Alpha Vantage, etc.)
- **`portfolio_api_usage_metrics`**: (Future) Will track portfolio-related API usage

### Database Schema

#### Market Data API Usage Metrics Table

```sql
CREATE TABLE market_data_usage_metrics (
    id INTEGER PRIMARY KEY,
    provider_id VARCHAR(50) NOT NULL,        -- 'yfinance', 'alpha_vantage', etc.
    metric_id VARCHAR(100) NOT NULL,
    user_id UUID,
    portfolio_id UUID,
    request_type VARCHAR(50),                -- 'price_fetch', 'bulk_fetch', etc.
    requests_count INTEGER DEFAULT 0,
    data_points_fetched INTEGER DEFAULT 0,
    cost_estimate DECIMAL(10, 4),
    recorded_at TIMESTAMP DEFAULT NOW(),
    time_bucket VARCHAR(20),                 -- '15min', 'hourly', 'daily'
    rate_limit_hit BOOLEAN DEFAULT FALSE,
    error_count INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER
);
```

#### Key Columns Explained

- **`provider_id`**: Identifies the market data provider (yfinance, alpha_vantage)
- **`request_type`**: Categorizes the type of data request
- **`time_bucket`**: Enables time-based aggregation for reporting
- **`rate_limit_hit`**: Tracks when provider rate limits are encountered
- **`cost_estimate`**: Estimates API usage costs for paid providers

## Integration Points

### Market Data Service Integration

The `MarketDataService` automatically logs metrics for every API call:

```python
# Automatic logging in src/services/market_data_service.py
async def fetch_stock_price(self, symbol: str) -> Optional[Decimal]:
    start_time = time.time()

    try:
        # Fetch price from provider
        price = await provider.get_price(symbol)

        # Log successful API call
        await self._log_api_usage(
            provider_id=provider.name,
            request_type="price_fetch",
            symbols_processed=1,
            success=True,
            response_time_ms=int((time.time() - start_time) * 1000)
        )

        return price

    except Exception as e:
        # Log failed API call
        await self._log_api_usage(
            provider_id=provider.name,
            request_type="price_fetch",
            symbols_processed=0,
            success=False,
            error_details=str(e)
        )
        raise
```

### Admin Dashboard Integration

The admin dashboard provides real-time visibility into API usage metrics:

#### Recent Activities API
```
GET /api/v1/admin/dashboard/recent-activities
```

Returns live system activities including:
- API call successes/failures
- Response times
- Provider performance
- Error tracking

#### API Usage Analytics
```
GET /api/v1/admin/api-usage
```

Provides aggregated metrics:
- Usage by provider
- Rate limit tracking
- Cost estimates
- Performance trends

## TDD Implementation

### Test Coverage

The metric monitoring system is fully covered by TDD tests:

1. **`tests/test_system_specific_metrics_tables_tdd.py`**
   - Validates system-specific table naming
   - Ensures old generic tables are removed
   - Verifies table structure and columns

2. **Contract Tests**
   - Admin API endpoint validation
   - Response structure verification
   - Authentication requirements

3. **Integration Tests**
   - Scheduler integration with metrics
   - End-to-end API usage logging
   - Admin dashboard data flow

### Migration Strategy

The system includes smart Alembic migrations that:
- Handle existing data gracefully
- Rename tables without data loss
- Support rollback scenarios

```python
# Migration: 069a794bf481_rename_api_usage_metrics_to_market_data_.py
def upgrade() -> None:
    # Smart migration handling existing tables
    if 'api_usage_metrics' in existing_tables and 'market_data_usage_metrics' in existing_tables:
        # Copy data from old to new if new is empty
        result = conn.execute(sa.text("SELECT COUNT(*) FROM market_data_usage_metrics"))
        if result.scalar() == 0:
            conn.execute(sa.text('''
                INSERT INTO market_data_usage_metrics
                SELECT * FROM api_usage_metrics
            '''))
        op.drop_table('api_usage_metrics')
    elif 'api_usage_metrics' in existing_tables:
        op.rename_table('api_usage_metrics', 'market_data_usage_metrics')
```

## Usage Examples

### Monitoring Market Data Provider Performance

```python
from src.models.market_data_usage_metrics import MarketDataUsageMetrics

# Query provider performance over last 24 hours
recent_metrics = db.query(MarketDataUsageMetrics)\
    .filter(MarketDataUsageMetrics.recorded_at >= datetime.now() - timedelta(hours=24))\
    .group_by(MarketDataUsageMetrics.provider_id)\
    .all()

for metric in recent_metrics:
    print(f"Provider: {metric.provider_id}")
    print(f"Success Rate: {metric.success_rate}%")
    print(f"Avg Response Time: {metric.avg_response_time_ms}ms")
```

### Admin Dashboard Queries

```python
# Get rate limit events by provider
rate_limit_events = db.query(MarketDataUsageMetrics)\
    .filter(MarketDataUsageMetrics.rate_limit_hit == True)\
    .filter(MarketDataUsageMetrics.recorded_at >= start_date)\
    .group_by(MarketDataUsageMetrics.provider_id)\
    .all()

# Calculate cost estimates
total_cost = db.query(func.sum(MarketDataUsageMetrics.cost_estimate))\
    .filter(MarketDataUsageMetrics.recorded_at >= billing_period_start)\
    .scalar()
```

## Benefits of System-Specific Tables

### Before Refactor (Problems)
- **Single `api_usage_metrics` table**: Confusion about which system was being monitored
- **Circular debugging**: Difficulty identifying whether issues were in portfolio or market data systems
- **Mixed metrics**: Portfolio and market data metrics in same table

### After Refactor (Solutions)
- **Clear system identification**: `market_data_usage_metrics` clearly indicates market data monitoring
- **Focused debugging**: Issues can be quickly traced to specific system components
- **Scalable architecture**: Easy to add new system-specific metrics tables
- **Better performance**: System-specific indexes and queries

## Future Enhancements

### Planned System Tables

1. **`portfolio_api_usage_metrics`**: Track portfolio-related API usage
   - Portfolio CRUD operations
   - Holdings calculations
   - Performance analytics

2. **`auth_api_usage_metrics`**: Monitor authentication system
   - Login attempts
   - Token generation/validation
   - Rate limiting on auth endpoints

3. **`notification_api_usage_metrics`**: Track notification delivery
   - Email notifications
   - Push notifications
   - Delivery success rates

### Advanced Features

- **Real-time alerts**: Automated notifications when rate limits approached
- **Predictive scaling**: Auto-scale based on usage patterns
- **Cost optimization**: Recommend provider switches based on cost/performance
- **Custom dashboards**: User-configurable monitoring views

## Troubleshooting

### Common Issues

1. **Missing Metrics Data**
   - Verify table exists: `SELECT * FROM market_data_usage_metrics LIMIT 1;`
   - Check model imports in `src/main.py`
   - Ensure migrations are applied: `alembic upgrade head`

2. **Import Errors**
   - Update imports: `from src.models.market_data_usage_metrics import MarketDataUsageMetrics`
   - Check `__init__.py` exports

3. **Admin Dashboard Empty**
   - Verify provider activities are being logged
   - Check admin authentication and permissions
   - Review recent API calls in logs

### Performance Considerations

- **Indexing**: Ensure proper indexes on `provider_id`, `recorded_at`, and `time_bucket`
- **Partitioning**: Consider partitioning by date for large datasets
- **Archival**: Implement data retention policies for historical metrics

## Related Documentation

- [Admin Dashboard Guide](./admin-dashboard.md)
- [API Reference](./api-reference.md)
- [Audit System](./audit-system.md)
- [Portfolio Monitoring](./portfolio-monitoring.md)
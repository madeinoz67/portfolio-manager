# Portfolio Update Monitoring System

## Overview

The Portfolio Update Monitoring System provides comprehensive real-time metrics and analytics for portfolio updates triggered by market data changes. This system tracks performance, identifies bottlenecks, and provides insights into the health of the portfolio update pipeline.

## Features

### 📊 Real-time Metrics Collection
- Automatic metrics collection on every portfolio update
- Success/failure tracking with detailed error categorization
- Response time and performance monitoring
- Update frequency and coalescing detection

### 🎯 Performance Analytics
- 24-hour statistics with success rates
- Average response times and throughput metrics
- Queue health monitoring and processing rates
- Storm protection and bulk update tracking

### 🔍 Monitoring Dashboard
- Live admin dashboard with auto-refresh (10-second intervals)
- Visual indicators for system health
- Historical trend analysis
- Error breakdown and troubleshooting insights

## Architecture

### Database Schema

#### `portfolio_update_metrics`
Core metrics table tracking individual portfolio update operations:
```sql
- id (UUID, Primary Key)
- portfolio_id (String, Indexed)
- symbols_updated (JSON Array)
- update_duration_ms (Integer)
- status (String: success/error/timeout)
- trigger_type (String: market_data_change/bulk_market_data/manual)
- update_source (String: automated/manual)
- error_message (String, Optional)
- error_type (String, Optional)
- coalesced_count (Integer, Optional)
- price_change_timestamp (DateTime, Optional)
- processing_start_timestamp (DateTime)
- created_at (DateTime)
```

#### `portfolio_queue_metrics`
Queue health and performance tracking:
```sql
- id (UUID, Primary Key)
- queue_size (Integer)
- processing_rate (Decimal)
- memory_usage_mb (Decimal)
- rate_limit_hits (Integer)
- queue_health_status (String)
- recorded_at (DateTime)
```

#### `portfolio_update_summary`
Daily/hourly aggregated statistics:
```sql
- id (UUID, Primary Key)
- date (Date)
- hour (Integer, Optional)
- total_updates (Integer)
- successful_updates (Integer)
- failed_updates (Integer)
- avg_duration_ms (Decimal)
- unique_portfolios (Integer)
- total_symbols_updated (Integer)
```

#### `portfolio_update_alert`
Alert and notification tracking:
```sql
- id (UUID, Primary Key)
- alert_type (String)
- severity (String: info/warning/error/critical)
- message (String)
- alert_data (JSON)
- is_resolved (Boolean)
- resolved_at (DateTime, Optional)
- created_at (DateTime)
```

### Backend Services

#### `PortfolioUpdateMetricsService`
Core service handling metrics collection and analysis:

**Key Methods:**
- `record_portfolio_update()` - Record individual update metrics
- `record_queue_metrics()` - Track queue health status
- `get_portfolio_update_stats_24h()` - 24-hour performance statistics
- `get_queue_health_metrics()` - Current queue health status
- `get_storm_protection_metrics()` - Coalescing and bulk update metrics
- `export_metrics_for_monitoring()` - Prometheus-compatible export

#### `RealTimePortfolioService` Integration
Automatic metrics collection integrated into portfolio update workflow:
- Metrics recorded on every `update_portfolios_for_symbol()` call
- Bulk update metrics for `bulk_update_portfolios_for_symbols()`
- Success/failure tracking with detailed timing information
- Error categorization and troubleshooting data

## API Endpoints

### Portfolio Update Metrics
```
GET /api/v1/admin/portfolio-updates/stats/24h
```
Returns 24-hour portfolio update statistics including success rates, average duration, and error breakdown.

**Response:**
```json
{
  "totalUpdates": 150,
  "successfulUpdates": 147,
  "failedUpdates": 3,
  "successRate": 98.0,
  "avgUpdateDurationMs": 245,
  "uniquePortfolios": 42,
  "updateFrequencyPerHour": 6.25,
  "commonErrorTypes": {
    "portfolio_update_error": 2,
    "database_timeout": 1
  }
}
```

### Queue Health Monitoring
```
GET /api/v1/admin/portfolio-updates/queue/health
```
Returns current queue health metrics and processing status.

**Response:**
```json
{
  "currentQueueSize": 15,
  "avgProcessingRate": 12.5,
  "maxQueueSize1h": 45,
  "rateLimitHits1h": 0,
  "memoryUsageTrend": "stable",
  "queueHealthStatus": "healthy"
}
```

### Storm Protection Metrics
```
GET /api/v1/admin/portfolio-updates/storm-protection
```
Returns metrics about update coalescing and bulk operation performance.

### Performance Breakdown
```
GET /api/v1/admin/portfolio-updates/performance
```
Detailed performance analysis with timing breakdowns by portfolio and symbol.

### Update Lag Analysis
```
GET /api/v1/admin/portfolio-updates/lag-analysis
```
Analysis of delays between price changes and portfolio updates.

### Prometheus Metrics Export
```
GET /api/v1/admin/portfolio-updates/metrics/export
```
Prometheus-compatible metrics export for external monitoring systems.

## Frontend Integration

### Portfolio Metrics Dashboard
**Location:** `/admin/portfolio-metrics`
**Component:** `PortfolioUpdateMetrics`

**Features:**
- Real-time dashboard with 10-second auto-refresh
- Comprehensive metrics display including:
  - 24-hour update statistics
  - Queue health indicators
  - Storm protection status
  - Performance trends
  - Error analysis
- Visual loading indicators and status updates
- Responsive design for different screen sizes

### Admin Dashboard Integration
**Location:** `/admin`
**Component:** Main admin dashboard includes portfolio metrics section

## Monitoring and Alerting

### Performance Thresholds
- **Success Rate**: Alert if < 95% over 1 hour
- **Response Time**: Alert if avg > 2 seconds
- **Queue Size**: Alert if > 100 pending updates
- **Error Rate**: Alert if > 5% failed updates

### Alert Types
- `PERFORMANCE_DEGRADATION`: Slow response times
- `HIGH_ERROR_RATE`: Increased failure rate
- `QUEUE_BACKUP`: Processing queue backing up
- `STORM_DETECTED`: Unusually high update volume

### Integration Points
- Prometheus metrics export for external monitoring
- Database alerts for critical failures
- Admin dashboard notifications
- Optional email/Slack integration (configurable)

## Usage Examples

### Monitoring Portfolio Update Performance
```python
# In admin dashboard or monitoring script
from src.services.portfolio_update_metrics import PortfolioUpdateMetricsService

service = PortfolioUpdateMetricsService(db)
stats = service.get_portfolio_update_stats_24h()

if stats.success_rate < 95.0:
    # Alert: Low success rate
    send_alert(f"Portfolio update success rate: {stats.success_rate}%")

if stats.avg_update_duration_ms > 2000:
    # Alert: Slow response times
    send_alert(f"Slow portfolio updates: {stats.avg_update_duration_ms}ms avg")
```

### Checking Queue Health
```python
queue_health = service.get_queue_health_metrics()

if queue_health.current_queue_size > 100:
    # Alert: Queue backing up
    send_alert(f"Portfolio update queue size: {queue_health.current_queue_size}")

if queue_health.queue_health_status == "unhealthy":
    # Critical alert
    send_critical_alert("Portfolio update queue is unhealthy")
```

## Development and Testing

### Running Tests
```bash
# Run portfolio metrics integration tests
uv run pytest tests/integration/test_portfolio_update_metrics.py -v

# Run real-time portfolio service tests
uv run pytest tests/integration/test_real_time_portfolio_updates.py -v
```

### Database Migration
```bash
# Apply portfolio metrics database schema
alembic upgrade head
```

### Local Development
```bash
# Start backend with monitoring
uv run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload

# Start frontend
npm run dev

# Access monitoring dashboard
open http://localhost:3000/admin/portfolio-metrics
```

## Configuration

### Environment Variables
- `PORTFOLIO_METRICS_ENABLED`: Enable/disable metrics collection (default: true)
- `PORTFOLIO_METRICS_RETENTION_DAYS`: Data retention period (default: 30)
- `PORTFOLIO_QUEUE_ALERT_THRESHOLD`: Queue size alert threshold (default: 100)
- `PORTFOLIO_UPDATE_TIMEOUT_MS`: Update timeout in milliseconds (default: 5000)

### Feature Flags
- `ENABLE_STORM_PROTECTION`: Enable update coalescing (default: true)
- `ENABLE_PERFORMANCE_TRACKING`: Enable detailed timing metrics (default: true)
- `ENABLE_ERROR_CATEGORIZATION`: Enable detailed error tracking (default: true)

## Troubleshooting

### Common Issues

#### High Error Rate
1. Check database connectivity and performance
2. Verify market data provider status
3. Review error logs for specific failure patterns
4. Check system resource usage (CPU, memory)

#### Slow Update Performance
1. Analyze update lag metrics to identify bottlenecks
2. Check database query performance
3. Review market data provider response times
4. Consider increasing timeout thresholds

#### Queue Backup
1. Check processing rate vs. incoming update rate
2. Verify adequate system resources
3. Consider implementing back-pressure mechanisms
4. Review bulk update coalescing effectiveness

### Monitoring Queries
```sql
-- Recent failed updates
SELECT * FROM portfolio_update_metrics
WHERE status = 'error'
AND created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;

-- Average response times by portfolio
SELECT portfolio_id, AVG(update_duration_ms) as avg_duration
FROM portfolio_update_metrics
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY portfolio_id
ORDER BY avg_duration DESC;

-- Queue health over time
SELECT recorded_at, queue_size, processing_rate, queue_health_status
FROM portfolio_queue_metrics
WHERE recorded_at > NOW() - INTERVAL '4 hours'
ORDER BY recorded_at DESC;
```

## Future Enhancements

### Planned Features
- **Predictive Analytics**: ML-based performance prediction
- **Advanced Alerting**: Custom alert rules and notifications
- **Historical Analysis**: Long-term trend analysis and reporting
- **Performance Optimization**: Automated performance tuning recommendations
- **Multi-tenant Support**: Portfolio-specific monitoring configurations

### Integration Opportunities
- **Grafana Dashboards**: Rich visualization and alerting
- **DataDog Integration**: APM and infrastructure monitoring
- **PagerDuty**: Incident management and escalation
- **Slack/Teams**: Real-time notifications and updates
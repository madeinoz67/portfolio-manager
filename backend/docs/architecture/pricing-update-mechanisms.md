# Portfolio Manager - Pricing Update Mechanisms

**Last Updated**: 2025-09-20
**Status**: Active - Legacy System Running, Adapter System Ready

## Overview

The Portfolio Manager uses a multi-layered approach to keep portfolio valuations current through automated price fetching, intelligent caching, and real-time update propagation. This document details the complete update pipeline from data acquisition to UI refresh.

## Update Pipeline Architecture

```
Data Sources → Price Fetching → Data Storage → Portfolio Updates → UI Refresh
     ↓              ↓               ↓              ↓              ↓
Yahoo Finance  → MarketDataService → realtime_*   → UpdateQueue  → WebSocket
Alpha Vantage    AdapterService     tables         Portfolio      SSE Events
                                                   Valuations     Frontend
```

## 1. Data Acquisition Layer

### External Data Sources

**Yahoo Finance (Primary)**
- **Endpoint**: `https://query1.finance.yahoo.com/v7/finance/quote`
- **Coverage**: Global markets, real-time and delayed quotes
- **Rate Limits**: 60 requests/minute, 2000 requests/day
- **Cost**: Free tier with attribution requirements
- **Reliability**: 94%+ uptime based on historical data

**Alpha Vantage (Secondary)**
- **Endpoint**: `https://www.alphavantage.co/query`
- **Coverage**: US markets, fundamentals, technical indicators
- **Rate Limits**: 5 requests/minute, 500 requests/day (free tier)
- **Cost**: $49.99/month for premium tier
- **Reliability**: 99%+ uptime with API key

### Market Coverage
```
Australian Securities Exchange (ASX): *.AX symbols
US Markets: NASDAQ, NYSE direct symbols
Global: Via Yahoo Finance international endpoints
```

## 2. Price Fetching Mechanisms

### Current Implementation (Legacy System)

**Background Scheduler** (`src/main.py`):
```python
@asynccontextmanager
async def periodic_price_updates():
    # Every 60 seconds, process up to 50 symbols
    # Dynamic symbol discovery from realtime_price_history
    # Bulk fetching for efficiency
```

**Key Characteristics**:
- **Frequency**: 60-second cycles
- **Batch Size**: Up to 50 symbols per cycle
- **Symbol Discovery**: Dynamic from recent portfolio activity
- **Provider Fallback**: Yahoo Finance primary, Alpha Vantage fallback
- **Bulk Operations**: Single API call for multiple symbols

### Future Implementation (Adapter System)

**Enhanced Scheduler** (`src/services/scheduler_service.py`):
```python
class MarketDataSchedulerService:
    async def execute_market_data_fetch():
        # 15-minute intervals with configurable timing
        # Provider-aware bulk operations
        # Circuit breaker pattern for reliability
```

**Improvements**:
- **Configurable Intervals**: 1h, 24h, 7d, 30d options
- **Provider Intelligence**: Adapter-specific optimizations
- **Circuit Breaker**: Automatic failover on provider issues
- **Cost Management**: Budget tracking and optimization

## 3. Data Storage & Caching

### Master Data Tables

**`realtime_symbols` (Current Price Cache)**:
```sql
CREATE TABLE realtime_symbols (
    symbol VARCHAR(20) PRIMARY KEY,
    current_price DECIMAL(15,4),
    last_updated DATETIME,
    volume BIGINT,
    market_cap BIGINT,
    company_name VARCHAR(255),
    currency VARCHAR(3),
    provider VARCHAR(50)
);
```

**`realtime_price_history` (Time Series)**:
```sql
CREATE TABLE realtime_price_history (
    id UUID PRIMARY KEY,
    symbol VARCHAR(20),
    price DECIMAL(15,4),
    fetched_at DATETIME,
    open_price DECIMAL(15,4),
    high_price DECIMAL(15,4),
    low_price DECIMAL(15,4),
    volume BIGINT,
    provider VARCHAR(50),
    -- Extended OHLCV data
    INDEX(symbol, fetched_at)
);
```

### Caching Strategy

**Data Freshness Levels**:
- **FRESH**: < 5 minutes old
- **ACCEPTABLE**: 5-30 minutes old
- **STALE**: > 30 minutes old
- **EXPIRED**: > 4 hours old

**Cache Invalidation**:
```python
def is_price_stale(last_updated: datetime) -> bool:
    return (utc_now() - last_updated) > timedelta(minutes=30)
```

## 4. Portfolio Update Propagation

### Update Queue System

**Portfolio Update Queue** (`src/services/portfolio_update_queue.py`):
- **Debouncing**: 2-second delay to coalesce rapid updates
- **Rate Limiting**: Maximum 20 updates per minute per portfolio
- **Background Processing**: Asynchronous queue with dedicated worker
- **Metrics Collection**: Throughput, latency, and error tracking

**Update Trigger Events**:
1. New price data received
2. Portfolio holdings modified
3. Manual refresh requested
4. Scheduled recalculation

### Valuation Calculation

**Real-time Portfolio Service** (`src/services/real_time_portfolio_service.py`):
```python
async def update_portfolio_valuations(portfolio_ids: List[str]):
    # Calculate current value = holdings × current_prices
    # Update unrealized gains/losses
    # Recalculate allocation percentages
    # Propagate to frontend via WebSocket
```

**Calculation Components**:
- **Total Value**: Σ(quantity × current_price)
- **Cost Basis**: Σ(quantity × average_cost)
- **Unrealized P&L**: total_value - cost_basis
- **Day Change**: current_value - previous_close_value
- **Allocation %**: position_value / total_portfolio_value

## 5. Frontend Update Mechanisms

### Real-time Update Channels

**WebSocket Integration** (Planned):
```javascript
// Real-time portfolio updates
const usePortfolioWebSocket = (portfolioId) => {
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8001/ws/portfolio/${portfolioId}`);
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      updatePortfolioState(update);
    };
  }, [portfolioId]);
};
```

**Server-Sent Events** (Current):
```javascript
// Polling-based updates with SSE fallback
const useMarketDataStream = () => {
  const [prices, setPrices] = useState({});

  useEffect(() => {
    const eventSource = new EventSource('/api/v1/market-data/stream');
    eventSource.onmessage = (event) => {
      setPrices(JSON.parse(event.data));
    };
  }, []);
};
```

### Update Frequency Management

**Frontend Polling Strategy**:
- **Active Tab**: 30-second intervals
- **Background Tab**: 5-minute intervals
- **Mobile/Low Power**: 10-minute intervals
- **Manual Refresh**: Immediate with 5-second cooldown

## 6. Performance Characteristics

### Current System Metrics

**Data Acquisition**:
- **Symbols Monitored**: 9 active symbols
- **Fetch Frequency**: 60-second cycles
- **Success Rate**: 94% (17/18 recent executions)
- **Avg Response Time**: 2-3 seconds for bulk operations
- **Provider Usage**: 180+ successful Yahoo Finance requests

**Portfolio Updates**:
- **Update Latency**: < 500ms from price change to portfolio update
- **Queue Throughput**: 20 updates/minute sustained
- **Debounce Efficiency**: ~15% reduction in redundant calculations
- **Memory Usage**: 50MB average queue overhead

### Scalability Projections

**Target Capacity**:
- **Symbols**: 1000+ simultaneous tracking
- **Portfolios**: 100+ active portfolios
- **Users**: 50+ concurrent real-time connections
- **Update Rate**: < 1 second end-to-end latency

## 7. Reliability & Error Handling

### Failure Scenarios & Recovery

**Provider API Failures**:
```python
# Circuit breaker pattern
@circuit_breaker(failure_threshold=5, timeout=60)
async def fetch_with_fallback(symbols):
    try:
        return await primary_provider.fetch(symbols)
    except ProviderError:
        return await fallback_provider.fetch(symbols)
```

**Network Connectivity Issues**:
- **Retry Strategy**: Exponential backoff (1s, 2s, 4s, 8s)
- **Timeout Handling**: 30-second request timeout
- **Offline Mode**: Serve last known prices with staleness indicators

**Database Connectivity**:
- **Connection Pooling**: 10 connections max, 2 connections min
- **Transaction Rollback**: Atomic price update operations
- **Backup Storage**: Redis cache for critical price data

### Data Quality Assurance

**Price Validation**:
```python
def validate_price_data(price_data: Dict) -> bool:
    # Range checking: 0 < price < 10000 (for most stocks)
    # Sanity checking: |new_price - old_price| / old_price < 50%
    # Timestamp validation: source_timestamp within last 24 hours
    # Required fields: symbol, price, timestamp
```

**Anomaly Detection**:
- **Spike Detection**: Prices > 3 standard deviations flagged
- **Missing Data**: Interpolation for brief gaps < 5 minutes
- **Provider Comparison**: Cross-validation between sources
- **Manual Review**: Admin alerts for significant anomalies

## 8. Monitoring & Observability

### Key Performance Indicators

**System Health**:
- **Price Fetch Success Rate**: Target > 95%
- **Update Queue Latency**: Target < 2 seconds P95
- **Portfolio Calculation Time**: Target < 500ms P95
- **Frontend Update Latency**: Target < 1 second end-to-end

**Business Metrics**:
- **Price Data Coverage**: % of portfolio holdings with fresh prices
- **User Engagement**: Real-time session duration
- **Data Accuracy**: % of prices within market tolerances
- **Cost Efficiency**: Provider API costs per price point

### Monitoring Infrastructure

**Metrics Collection**:
```python
# Prometheus-compatible metrics
price_fetch_duration = Histogram('price_fetch_duration_seconds')
portfolio_update_counter = Counter('portfolio_updates_total')
queue_size_gauge = Gauge('update_queue_size')
```

**Alerting Rules**:
- **Critical**: Price fetching failure > 5 minutes
- **Warning**: Success rate < 90% over 15 minutes
- **Info**: New symbol discovery or provider fallback

## 9. Configuration & Tuning

### Runtime Configuration

**Scheduler Settings**:
```yaml
scheduler:
  interval_minutes: 15
  max_concurrent_jobs: 5
  retry_attempts: 3
  enabled_providers: ["yfinance", "alpha_vantage"]
  bulk_mode: true
  timeout_seconds: 300
```

**Provider Configuration**:
```yaml
providers:
  yfinance:
    base_url: "https://query1.finance.yahoo.com"
    timeout: 30
    calls_per_minute: 60
    bulk_symbols_limit: 100

  alpha_vantage:
    base_url: "https://www.alphavantage.co"
    api_key: "${ALPHA_VANTAGE_API_KEY}"
    calls_per_minute: 5
    premium_tier: false
```

### Performance Tuning

**Database Optimization**:
```sql
-- Indexes for efficient price lookups
CREATE INDEX idx_realtime_symbols_updated ON realtime_symbols(last_updated);
CREATE INDEX idx_price_history_symbol_time ON realtime_price_history(symbol, fetched_at);
CREATE INDEX idx_holdings_portfolio_symbol ON holdings(portfolio_id, stock_id);
```

**Caching Strategy**:
```python
# Redis configuration for price caching
PRICE_CACHE_TTL = 300  # 5 minutes
PORTFOLIO_CACHE_TTL = 60  # 1 minute
CALCULATION_CACHE_TTL = 30  # 30 seconds
```

## 10. Future Enhancements

### Planned Improvements

**Real-time Streaming**:
- WebSocket connections for sub-second updates
- Market data websocket provider integration
- Event-driven architecture for instant propagation

**Advanced Analytics**:
- Predictive price modeling
- Market correlation analysis
- Volatility-based update frequency adjustment
- Machine learning for anomaly detection

**Performance Optimizations**:
- CDN integration for static market data
- GraphQL subscriptions for selective updates
- Database partitioning by symbol/date
- Materialized views for common calculations

### Integration Roadmap

**External Services**:
- Bloomberg Terminal API integration
- Real-time news correlation
- Fundamental data enrichment
- Social sentiment indicators

**User Experience**:
- Offline-first progressive web app
- Push notifications for significant changes
- Customizable alert thresholds
- Historical performance visualization

## Conclusion

The pricing update mechanism forms the backbone of the Portfolio Manager's real-time capabilities. The current system provides reliable, efficient price updates with room for growth. The planned migration to the adapter system will enhance reliability, observability, and extensibility while maintaining the proven performance characteristics of the existing implementation.

The multi-layered approach ensures data consistency, user experience quality, and system reliability across varying network conditions and user loads.
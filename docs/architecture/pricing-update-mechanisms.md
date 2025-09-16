# Pricing Update Mechanisms

This document describes the comprehensive pricing update architecture for the Portfolio Manager system, including market data integration, database synchronization, and real-time updates.

## Overview

The pricing system maintains **dual-table synchronization** to ensure consistent data across both portfolio holdings and market data views. All price updates are propagated to both the `stocks` table (for portfolio calculations) and `realtime_price_history` table (for historical tracking).

## Architecture Components

### 1. Market Data Service (`src/services/market_data_service.py`)

The central component responsible for fetching, processing, and storing price data from external providers.

#### Key Methods

**`_store_price_data(symbol, price_data, provider)`**
- Primary method used by the scheduler for bulk price updates
- Updates **both** `stocks` and `realtime_price_history` tables
- Creates new stock records for previously unknown symbols
- Triggers portfolio value recalculation via update queue

**`_store_comprehensive_price_data(symbol, price_data, provider, db_session)`**
- Enhanced method for detailed price data with extended market information
- Includes OHLC prices, volume, market cap, financial ratios
- Also maintains dual-table synchronization
- Used for API-driven price updates

#### Data Flow

```
External API → MarketDataService → Database Tables → Portfolio Updates
    ↓                    ↓               ↓              ↓
Yahoo Finance      Store prices     stocks +       Portfolio
Alpha Vantage        Process        realtime_       valuations
                   timestamps      price_history    refreshed
```

### 2. Database Schema

#### Primary Tables

**`stocks` Table**
- **Purpose**: Master stock data for portfolio calculations
- **Key Fields**: `symbol`, `current_price`, `last_price_update`, `company_name`
- **Usage**: Holdings calculations, portfolio valuations, user-facing displays
- **Update Frequency**: Every market data refresh (15-minute intervals)

**`realtime_price_history` Table**
- **Purpose**: Time-series price tracking with provider attribution
- **Key Fields**: `symbol`, `price`, `fetched_at`, `source_timestamp`, `provider_id`
- **Usage**: Historical analysis, trend calculations, audit trails
- **Extended Data**: OHLC, volume, market cap, financial ratios

**Critical Synchronization Rule**
> Both tables MUST be updated simultaneously to prevent data inconsistency between portfolio holdings and market data views.

### 3. Provider Management

#### Supported Providers
- **Yahoo Finance**: Primary provider for development and production
- **Alpha Vantage**: Secondary provider with API key support
- **Mock Provider**: Testing and development environment

#### Provider Configuration
```python
# Market data providers are configured in database
providers = [
    MarketDataProvider(
        name="yahoo_finance",
        display_name="Yahoo Finance",
        is_enabled=True
    ),
    MarketDataProvider(
        name="alpha_vantage",
        display_name="Alpha Vantage",
        api_key="your_key_here",
        is_enabled=False  # Enable when API key available
    )
]
```

### 4. Scheduling and Automation

#### Price Update Schedule
- **Interval**: 15 minutes during market hours
- **Implementation**: Background task with configurable intervals
- **Symbols**: Automatically determined from active portfolios
- **Error Handling**: Circuit breaker pattern with retry logic

#### Scheduler Configuration
```python
# Configurable via poll_interval_configs table
DEFAULT_POLL_INTERVAL = 15 * 60  # 15 minutes in seconds
MARKET_HOURS_ONLY = True         # Only update during trading hours
MAX_RETRIES = 3                  # Retry failed requests
CIRCUIT_BREAKER_THRESHOLD = 5    # Failures before circuit opens
```

## API Endpoints

### Market Data APIs

**`GET /api/v1/market-data/prices?symbols=AAPL,GOOGL`**
- Bulk price fetching for multiple symbols
- Returns current prices from `realtime_price_history` table
- Used by market-data frontend page

**`GET /api/v1/market-data/prices/{symbol}`**
- Single symbol price lookup
- Includes extended market data and trends
- Real-time price with historical context

**`POST /api/v1/market-data/refresh`**
- Manual price refresh trigger
- Rate-limited to prevent API abuse
- Admin-only endpoint for troubleshooting

### Portfolio APIs

**`GET /api/v1/portfolios/{portfolio_id}/holdings`**
- Returns holdings with current prices from `stocks` table
- Includes calculated gains/losses and portfolio metrics
- Auto-refreshes every 30 seconds on frontend

## Real-Time Updates

### Frontend Integration

#### Market Data Page
```typescript
// Uses bulk prices API for multiple symbols
const response = await fetch(`/api/v1/market-data/prices?symbols=${symbols.join(',')}`)
const priceData = await response.json()
```

#### Holdings Page
```typescript
// Uses portfolio API with stock prices
const response = await fetch(`/api/v1/portfolios/${portfolioId}/holdings`)
const holdings = await response.json()

// Auto-refresh mechanism
useEffect(() => {
  const interval = setInterval(fetchHoldings, 30 * 1000) // 30 seconds
  return () => clearInterval(interval)
}, [])
```

### WebSocket Streaming (Future Enhancement)
- Server-Sent Events (SSE) for real-time price streaming
- WebSocket connections for low-latency updates
- Subscription management for active symbols only

## Data Consistency Mechanisms

### Dual-Table Update Pattern

Every price update follows this pattern:

```python
# 1. Update realtime_price_history (time-series data)
price_record = RealtimePriceHistory(
    symbol=symbol,
    price=price_data["price"],
    fetched_at=utc_now(),
    source_timestamp=price_data["source_timestamp"],
    provider_id=provider.id
)
db.add(price_record)

# 2. Update stocks table (current prices)
stock = db.query(Stock).filter_by(symbol=symbol).first()
if stock:
    stock.current_price = price_data["price"]
    stock.last_price_update = price_data["source_timestamp"]
else:
    # Create new stock record for unknown symbols
    stock = Stock(
        symbol=symbol,
        company_name=price_data.get("company_name", f"{symbol} Company"),
        current_price=price_data["price"],
        last_price_update=price_data["source_timestamp"]
    )
    db.add(stock)

# 3. Trigger portfolio updates
portfolio_update_queue.trigger_update(symbol)
```

### Timestamp Synchronization

All timestamps follow consistent UTC handling:

```python
# Storage: Always UTC in database
source_timestamp = utc_now()
fetched_at = utc_now()

# API Response: ISO 8601 format
{
    "last_updated": "2025-09-16T04:55:42.123Z",
    "fetched_at": "2025-09-16T04:55:42.456Z"
}

# Frontend Display: Local timezone conversion
const displayTime = new Intl.DateTimeFormat('en-US', {
    timeZone: 'local',
    dateStyle: 'short',
    timeStyle: 'medium'
}).format(new Date(timestamp))
```

## Error Handling and Resilience

### Provider Failover
```python
# Automatic provider switching on failure
for provider in enabled_providers:
    try:
        price_data = await provider.fetch_prices(symbols)
        break
    except ProviderError as e:
        logger.warning(f"Provider {provider.name} failed: {e}")
        continue
else:
    # All providers failed - use cached data
    price_data = get_cached_prices(symbols)
```

### Circuit Breaker Pattern
- Opens circuit after 5 consecutive failures
- Half-open state allows test requests
- Automatic recovery when provider stabilizes

### Data Validation
```python
def validate_price_data(price_data: Dict) -> bool:
    """Validate price data before storage."""
    required_fields = ['symbol', 'price', 'source_timestamp']

    # Check required fields
    if not all(field in price_data for field in required_fields):
        return False

    # Validate price is positive number
    if not isinstance(price_data['price'], (int, float, Decimal)) or price_data['price'] <= 0:
        return False

    # Validate timestamp format
    try:
        datetime.fromisoformat(price_data['source_timestamp'])
    except ValueError:
        return False

    return True
```

## Monitoring and Observability

### Metrics Collection
- Price update success/failure rates per provider
- API response times and availability
- Database update performance
- Portfolio calculation latency

### Logging
```python
# Structured logging for price updates
logger.info(
    "Price updated successfully",
    extra={
        "symbol": symbol,
        "price": float(price_data["price"]),
        "provider": provider.name,
        "response_time_ms": response_time,
        "stocks_updated": stocks_count,
        "history_records": history_count
    }
)
```

### Admin Dashboard Integration
- Real-time provider status monitoring
- Failed update alerts and notifications
- Performance metrics and trends
- Manual intervention capabilities

## Testing Strategy

### Unit Tests
- Individual price update methods
- Data validation and transformation
- Error handling scenarios
- Provider integration mocking

### Integration Tests
```python
def test_price_update_synchronizes_both_tables():
    """Test that price updates maintain data consistency."""
    # Arrange: Create test stock and provider
    # Act: Update price via market data service
    # Assert: Both tables have consistent data

    stock_record = db.query(Stock).filter_by(symbol="TEST").first()
    history_record = db.query(RealtimePriceHistory).filter_by(symbol="TEST").first()

    assert stock_record.current_price == history_record.price
    assert stock_record.last_price_update == history_record.source_timestamp
```

### End-to-End Tests
- Full price update flow from API to frontend
- Portfolio valuation accuracy
- Real-time update propagation
- Error recovery and failover

## Performance Considerations

### Database Optimization
- Indexed queries on symbol and timestamp fields
- Batch updates for multiple symbols
- Connection pooling for concurrent requests
- Proper transaction management

### Caching Strategy
```python
# Redis caching for frequently accessed data
@cached(expire=300)  # 5-minute cache
def get_current_prices(symbols: List[str]) -> Dict[str, Decimal]:
    """Get current prices with caching."""
    return db.query(Stock).filter(Stock.symbol.in_(symbols)).all()
```

### Rate Limiting
- API provider rate limits respected
- Client-side throttling for manual refreshes
- Exponential backoff for failed requests

## Future Enhancements

### Real-Time Streaming
- WebSocket connections for live price feeds
- Server-Sent Events for portfolio updates
- Subscription management for active symbols

### Advanced Analytics
- Technical indicators and trend analysis
- Historical price charting
- Portfolio performance benchmarking

### Multi-Currency Support
- Currency conversion API integration
- Multi-currency portfolio valuations
- Exchange rate tracking and updates

### High Availability
- Multi-region deployment support
- Database replication and failover
- Load balancing for API endpoints

## Troubleshooting

### Common Issues

**Stale Holdings Timestamps**
- **Cause**: Market data service not updating stocks table
- **Solution**: Verify dual-table update logic in `_store_price_data()`
- **Prevention**: TDD tests ensuring both tables updated

**Price Inconsistencies**
- **Cause**: Different data sources for holdings vs market-data
- **Solution**: Ensure both APIs read from synchronized tables
- **Prevention**: Integration tests validating API consistency

**Timestamp Serialization Errors**
- **Cause**: Inconsistent datetime/string handling in APIs
- **Solution**: Type checking in StockResponse.convert_timestamp()
- **Prevention**: Unit tests for all timestamp formats

### Debugging Commands

```bash
# Check recent price updates
SELECT symbol, current_price, last_price_update
FROM stocks
WHERE last_price_update > NOW() - INTERVAL '1 hour'
ORDER BY last_price_update DESC;

# Verify dual-table consistency
SELECT s.symbol, s.current_price, h.price, s.last_price_update, h.fetched_at
FROM stocks s
JOIN realtime_price_history h ON s.symbol = h.symbol
WHERE s.current_price != h.price
ORDER BY s.last_price_update DESC;

# Monitor provider performance
SELECT provider_id, COUNT(*) as updates, AVG(response_time_ms)
FROM provider_activities
WHERE created_at > NOW() - INTERVAL '1 day'
GROUP BY provider_id;
```

This documentation provides a comprehensive overview of the pricing update mechanisms and should be updated as the system evolves.
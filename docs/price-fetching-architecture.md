# Price Fetching Architecture

## Overview

The Portfolio Manager implements a sophisticated price fetching mechanism that abstracts data provider interactions while optimizing for bulk operations and real-time updates. The system is designed to be provider-agnostic, supporting multiple market data sources with different capabilities and rate limits.

## Architecture Components

### 1. Market Data Service (`MarketDataService`)

The central orchestrator that coordinates price fetching across multiple providers.

**Key Features:**
- Provider abstraction and failover
- Bulk operation optimization
- Rate limiting and API usage tracking
- Real-time price storage and caching
- Portfolio update triggering

**Location:** `src/services/market_data_service.py`

### 2. Provider Adapter Pattern

Each market data provider implements a consistent interface while handling provider-specific optimizations internally.

#### Supported Providers

##### Yahoo Finance (yfinance)
- **Bulk Capability:** Up to 50 symbols per request
- **Rate Limits:** Conservative limits to avoid throttling
- **Implementation:** Uses `yfinance` library with bulk symbol fetching
- **Optimization:** Automatically batches individual requests into bulk operations

##### Alpha Vantage
- **Bulk Capability:** Up to 100 symbols per request (premium plans)
- **Rate Limits:** API key dependent (5 calls/min free, higher for paid)
- **Implementation:** REST API with JSON responses
- **Optimization:** Respects API key limits and automatically switches to bulk endpoints

### 3. Provider Configuration Model

```python
class MarketDataProvider(Base):
    name: str                    # 'yfinance', 'alpha_vantage'
    display_name: str           # Human-readable name
    is_enabled: bool            # Toggle provider on/off
    api_key: Optional[str]      # Encrypted API credentials
    rate_limit_per_minute: int  # Request throttling
    rate_limit_per_day: int     # Daily quota management
    priority: int               # Provider selection order
    config: JSON                # Provider-specific settings
```

**Location:** `src/models/market_data_provider.py`

## Fetching Mechanisms

### 1. Individual Price Fetching

For single symbol requests or when bulk optimization isn't beneficial:

```python
# Service layer abstraction
price_data = await market_data_service.fetch_price(symbol="AAPL")

# Provider adapter handles implementation details
# - Rate limiting
# - Error handling
# - Data normalization
# - Activity logging
```

### 2. Bulk Price Fetching

Optimized for multiple symbols with automatic provider selection:

```python
# Service coordinates bulk optimization
symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
results = await market_data_service.fetch_multiple_prices(symbols)

# Provider adapters implement bulk strategies:
# - yfinance: Single API call for all symbols
# - Alpha Vantage: Batch requests respecting rate limits
# - Automatic fallback to individual requests if bulk fails
```

### 3. Automated Scheduler Fetching

FastAPI background task runs every 15 minutes:

```python
# Dynamic symbol discovery
symbols = market_data_service.get_actively_monitored_symbols(
    provider_bulk_limit=50,
    minutes_lookback=60
)

# Bulk optimization with provider failover
results = await market_data_service.fetch_multiple_prices(symbols)

# Automatic portfolio updates and activity logging
```

**Location:** `src/main.py` - `periodic_price_updates()`

## Provider Adapter Implementation

### Interface Contract

All providers must implement:

```python
async def fetch_price(self, symbol: str) -> Optional[Dict]
async def fetch_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[Dict]]
```

### Bulk Optimization Strategy

1. **Provider Capability Detection**
   - Check provider bulk limits from configuration
   - Determine optimal batch sizes

2. **Intelligent Batching**
   - Split large symbol lists into optimal batches
   - Respect rate limits and API quotas
   - Log performance metrics

3. **Graceful Degradation**
   - Fall back to individual requests if bulk fails
   - Provider failover for critical operations
   - Maintain partial success handling

### Implementation Example (yfinance)

```python
async def fetch_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[Dict]]:
    if len(symbols) <= self.bulk_limit:
        # Use bulk optimization
        return await self._fetch_bulk_yfinance(symbols)
    else:
        # Split into batches and process sequentially
        return await self._fetch_batched_yfinance(symbols)

async def _fetch_bulk_yfinance(self, symbols: List[str]) -> Dict[str, Optional[Dict]]:
    # Single API call for all symbols
    tickers = yf.Tickers(' '.join(symbols))
    results = {}

    for symbol in symbols:
        try:
            info = tickers.tickers[symbol].info
            results[symbol] = self._normalize_price_data(info)
        except Exception as e:
            logger.warning(f"Failed to fetch {symbol}: {e}")
            results[symbol] = None

    return results
```

## Data Flow

### 1. Price Request Flow

```
API Request → MarketDataService → Provider Selection → Provider Adapter
     ↓                                                        ↓
Portfolio Update ← Price Storage ← Data Normalization ← Raw API Response
```

### 2. Bulk Optimization Flow

```
Multiple Symbols → Bulk Capability Check → Provider Batch Strategy
       ↓                                            ↓
Activity Logging ← Results Aggregation ← Parallel/Sequential Execution
```

### 3. Scheduler Flow

```
15-min Timer → Symbol Discovery → Bulk Fetch → Storage → Portfolio Updates
     ↓                                              ↓
Admin Dashboard ← Activity Logging ← Provider Metrics ← Success/Failure Tracking
```

## Optimization Features

### 1. Bulk Request Optimization

- **Automatic Detection:** Service detects when bulk operations are beneficial
- **Provider Limits:** Respects each provider's bulk capabilities
- **Performance Improvement:** Up to 10x faster for large symbol lists
- **API Efficiency:** Reduces API calls by batching operations

### 2. Provider Failover

- **Priority-based Selection:** Providers ordered by priority and reliability
- **Automatic Fallback:** Switch providers on rate limit or API failures
- **Health Monitoring:** Track provider success rates and response times

### 3. Rate Limiting

- **Per-Provider Limits:** Configurable rate limits for each data source
- **Intelligent Throttling:** Automatic delays between requests
- **Quota Management:** Daily and hourly usage tracking
- **Circuit Breaker:** Temporary provider disabling on repeated failures

### 4. Caching and Performance

- **Price Storage:** All fetched prices stored in `realtime_price_history`
- **TTL Management:** Automatic cache invalidation based on market hours
- **Portfolio Triggers:** Real-time portfolio value updates on price changes
- **Activity Logging:** Comprehensive audit trail for all operations

## Configuration and Monitoring

### Provider Configuration

Providers are configured via database records:

```sql
INSERT INTO market_data_providers (
    name, display_name, is_enabled, priority,
    rate_limit_per_minute, rate_limit_per_day
) VALUES (
    'yfinance', 'Yahoo Finance', true, 1, 60, 2000
);
```

### Activity Monitoring

All provider operations are logged with rich metadata:

```json
{
    "symbol": "AAPL",
    "price": "150.25",
    "provider": "yfinance",
    "response_time_ms": 1250,
    "bulk_optimization": "enabled",
    "success_rate": 0.95
}
```

### Performance Metrics

- **Response Times:** Track API latency per provider
- **Success Rates:** Monitor reliability and error rates
- **Usage Tracking:** API quota consumption and optimization gains
- **Bulk Efficiency:** Performance improvements from bulk operations

## Admin Dashboard Integration

The price fetching system integrates with the admin dashboard to provide:

- **Real-time Activity Feed:** Live updates of all price fetching operations
- **Provider Status:** Health and performance metrics for each data source
- **Scheduler Control:** Start/stop/pause automated price updates
- **Performance Analytics:** Bulk optimization gains and API efficiency metrics

## Error Handling and Resilience

### Graceful Degradation

1. **Provider Failures:** Automatic failover to backup providers
2. **Partial Success:** Handle mixed success/failure in bulk operations
3. **Rate Limiting:** Intelligent backoff and retry strategies
4. **Network Issues:** Exponential backoff with circuit breaker patterns

### Data Integrity

- **Decimal Precision:** Proper handling of financial data precision
- **Timezone Management:** UTC storage with local time display conversion
- **Transaction Safety:** Database transactions ensure consistency
- **Audit Trails:** Complete activity logging for debugging and compliance

## Future Enhancements

### Planned Improvements

1. **WebSocket Support:** Real-time streaming for select providers
2. **Machine Learning:** Intelligent provider selection based on historical performance
3. **Caching Layers:** Redis integration for high-frequency trading scenarios
4. **Multi-Region:** Geographic provider distribution for global markets

### Provider Expansion

- **Bloomberg API:** Enterprise-grade data with extended market coverage
- **IEX Cloud:** Developer-friendly with competitive pricing
- **Quandl/Nasdaq:** Alternative data sources and historical coverage
- **Custom Providers:** Framework for proprietary data source integration

This architecture provides a robust, scalable foundation for market data operations while maintaining flexibility for future enhancements and provider integrations.
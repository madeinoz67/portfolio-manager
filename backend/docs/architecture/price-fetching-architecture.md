# Portfolio Manager - Price-Fetching Architecture

**Last Updated**: 2025-09-20
**Status**: Migration In Progress (Legacy → Adapter System)

## Overview

The Portfolio Manager implements a dual-architecture price-fetching system currently in transition from a legacy hardcoded approach to a modern adapter-based pattern. This document outlines both systems and the migration strategy.

## Current State: Dual Architecture

### 1. Legacy System (ACTIVE)

**Components**:
- **Service**: `MarketDataService` (`src/services/market_data_service.py`)
- **Configuration**: `market_data_providers` table
- **Metrics**: `market_data_usage_metrics` table
- **Providers**: Hardcoded yfinance and alpha_vantage implementations

**Active Usage**:
- Background scheduler (`src/main.py` periodic tasks)
- Market data API endpoints (`/api/v1/market-data/refresh`)
- Successfully processing 180+ requests with yfinance provider

**Characteristics**:
- Hardcoded provider implementations within service
- Simple configuration via database table
- Direct Yahoo Finance and Alpha Vantage API calls
- Established metrics collection with 180+ historical records

### 2. New Adapter System (DORMANT)

**Components**:
- **Service**: `AdapterMarketDataService` (`src/services/adapter_market_data_service.py`)
- **Configuration**: `provider_configurations` table
- **Registry**: `ProviderRegistry` with dynamic adapter loading
- **Adapters**: Abstract base classes with implementations

**Provider Architecture**:
```
MarketDataAdapter (Abstract Base)
├── YahooFinanceAdapter
└── AlphaVantageAdapter
```

**Features**:
- Plugin-based architecture with registry pattern
- Comprehensive capabilities metadata
- Built-in circuit breaker and retry patterns
- Cost tracking and rate limiting
- Health check monitoring
- Metrics collection integration

**Current Status**: Configured but not actively used by price fetching

## Data Storage Architecture

Both systems share the same data storage layer:

### Master Data Tables
- **`realtime_symbols`**: Single source of truth for current prices
- **`realtime_price_history`**: Time-series price data with full OHLCV
- **`market_data_usage_metrics`**: Provider usage statistics

### Schema Design
```sql
-- Current price (master table)
realtime_symbols: {
  symbol, current_price, last_updated, volume,
  market_cap, company_name, currency, provider
}

-- Historical data (time-series)
realtime_price_history: {
  symbol, price, fetched_at, open_price, high_price,
  low_price, volume, provider, [extended fields]
}
```

## Provider Configuration

### Legacy Configuration (`market_data_providers`)
```sql
{
  name: "yfinance",
  display_name: "Yahoo Finance",
  is_enabled: true,
  priority: 1,
  rate_limit_per_minute: 60,
  api_key: null
}
```

### Adapter Configuration (`provider_configurations`)
```sql
{
  provider_name: "yfinance",
  display_name: "Yahoo Finance",
  config_data: {
    "base_url": "https://query1.finance.yahoo.com",
    "timeout": 30,
    "calls_per_minute": 60
  },
  is_active: true
}
```

## Current Data Flow

### Legacy System Flow
```
Scheduler (main.py)
  → MarketDataService
  → Hard-coded yfinance API calls
  → realtime_symbols + realtime_price_history
  → market_data_usage_metrics
```

### Adapter System Flow (Intended)
```
Scheduler (scheduler_service.py)
  → AdapterMarketDataService
  → ProviderRegistry.get_provider_instance()
  → YahooFinanceAdapter.fetch_quotes()
  → realtime_symbols + realtime_price_history
  → Adapter metrics collection
```

## Migration Strategy

### Phase 1: Parallel Systems ✅ COMPLETE
- Implement new adapter architecture
- Configure adapter providers
- Initialize adapter registry
- Create adapter-aware scheduler service

### Phase 2: Integration 🚧 IN PROGRESS
- **Issue**: Scheduler service updated but main periodic task still uses legacy
- **Solution**: Update `src/main.py` to use `AdapterMarketDataService`
- **Risk**: Price fetching interruption during transition

### Phase 3: API Migration ⏳ PENDING
- Update market data API endpoints to use adapter system
- Ensure backward compatibility for existing clients
- Migrate admin interfaces to adapter metrics

### Phase 4: Legacy Retirement ⏳ PENDING
- Remove `MarketDataService` dependencies
- Drop `market_data_providers` table
- Migrate historical metrics data if needed

## Technical Benefits of Adapter System

### Extensibility
- Plugin architecture for easy provider addition
- Standardized adapter interface
- Hot-swappable provider configurations

### Reliability
- Circuit breaker pattern for provider failures
- Automatic retry with exponential backoff
- Health check monitoring with status caching

### Observability
- Comprehensive metrics collection
- Cost tracking with budget management
- Real-time performance monitoring
- Admin dashboard integration

### Maintainability
- Separation of concerns between providers
- Consistent error handling patterns
- Testable adapter interfaces
- Configuration-driven behavior

## Current Issues & Solutions

### 1. Scheduler Integration Gap
**Issue**: `scheduler_service.py` updated but `main.py` still uses legacy
**Impact**: No price fetching via new adapter system
**Solution**: Update main periodic task to use `AdapterMarketDataService`

### 2. Timezone Handling in Metrics
**Issue**: "can't compare offset-naive and offset-aware datetimes"
**Impact**: Adapter metrics service fails
**Solution**: Standardize UTC handling across adapter system

### 3. Provider Configuration Mismatch
**Issue**: Legacy providers active, adapter providers dormant
**Impact**: Dual system confusion
**Solution**: Migrate active configuration to adapter system

## Performance Characteristics

### Legacy System
- **Throughput**: 9 symbols per cycle, 15-minute intervals
- **Success Rate**: ~94% (17/18 recent executions successful)
- **Latency**: ~2-5 seconds for bulk operations
- **Reliability**: Proven with 180+ successful requests

### Adapter System (Expected)
- **Throughput**: Configurable bulk operations (up to 100 symbols)
- **Success Rate**: Enhanced with circuit breaker pattern
- **Latency**: Optimized with provider-specific bulk operations
- **Reliability**: Improved with retry patterns and health checks

## Monitoring & Metrics

### Legacy Metrics (`market_data_usage_metrics`)
- Request counts and success rates
- Provider response times
- Cost estimates
- Simple usage tracking

### Adapter Metrics (Enhanced)
- Real-time latency percentiles (P95, P99)
- Circuit breaker state monitoring
- Rate limit tracking
- Cost tracking with budget alerts
- Health check status
- Error categorization

## Security Considerations

### API Key Management
- Legacy: Plain text storage in database
- Adapter: Encrypted credential storage with rotation support

### Rate Limiting
- Legacy: Simple per-minute limits
- Adapter: Sophisticated rate limiting with burst handling

### Error Handling
- Legacy: Basic try-catch patterns
- Adapter: Structured error responses with categorization

## Future Enhancements

### Provider Ecosystem
- Market-specific adapters (ASX, NYSE, NASDAQ)
- Real-time streaming providers
- Alternative data sources (fundamentals, news)

### Advanced Features
- Multi-provider aggregation and conflict resolution
- Intelligent provider fallback chains
- Cost optimization algorithms
- Predictive caching

### Integration Points
- WebSocket streaming for real-time updates
- Event-driven architecture for portfolio updates
- Machine learning for data quality assessment

## Conclusion

The price-fetching architecture is transitioning from a proven legacy system to a modern, extensible adapter-based approach. The migration preserves existing functionality while providing enhanced reliability, observability, and maintainability. The dual system approach ensures continuous operation during the transition period.

The new adapter system represents a significant architectural improvement that will support the platform's growth and enable sophisticated market data management capabilities.
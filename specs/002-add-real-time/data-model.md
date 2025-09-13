# Data Model: Real-Time Market Data Integration

**Branch**: `002-add-real-time` | **Date**: 2025-09-13 | **Spec**: [spec.md](./spec.md)

## Entity Definitions

Based on the feature specification and research findings, these entities support scheduled market data updates with Server-Sent Events for real-time UI updates.

### Core Entities

#### MarketDataUpdate
Represents a scheduled price update event from external data sources.

```python
@dataclass
class MarketDataUpdate:
    symbol: str                    # Stock symbol (e.g., "CBA.AX")
    price: Decimal                 # Current market price
    previous_close: Decimal        # Previous trading day close
    change: Decimal               # Price change from previous close
    change_percent: Decimal       # Percentage change
    volume: int                   # Trading volume
    timestamp: datetime           # When price was fetched
    source: str                   # "alpha_vantage" or "yfinance"
    market_status: str            # "OPEN", "CLOSED", "PRE_MARKET", "AFTER_HOURS"
```

#### DataProvider
Abstraction for multiple market data sources with extensible provider support.

```python
@dataclass
class DataProvider:
    provider_id: str              # "alpha_vantage", "yfinance", "iex"
    provider_name: str            # "Alpha Vantage", "Yahoo Finance", "IEX Cloud"
    is_active: bool              # Currently enabled
    api_key: str                 # Optional API key
    rate_limit_per_day: int      # Daily request limit
    rate_limit_per_minute: int   # Per-minute request limit
    requests_used_today: int     # Current usage counter
    last_request_at: datetime    # Last API call timestamp
    priority: int                # 1=primary, 2=fallback, etc.
    supports_symbols: List[str]  # Supported exchange suffixes [".AX", ".US"]
```

#### PriceUpdateSchedule
Manages when and how often to fetch price updates.

```python
@dataclass
class PriceUpdateSchedule:
    schedule_id: str             # Unique identifier
    is_active: bool             # Schedule enabled
    market_hours_interval: int   # Minutes between updates (15)
    after_hours_interval: int    # Minutes between updates (60)
    weekend_interval: int        # Minutes between updates (1440 = daily)
    market_open_time: time       # Market open (9:30 AM)
    market_close_time: time      # Market close (4:00 PM)
    timezone: str               # "Australia/Sydney"
    last_run_at: datetime       # Last successful execution
    next_run_at: datetime       # Scheduled next execution
```

#### RealtimePriceHistory
Extension of existing price_history table to support real-time price tracking.

```python
@dataclass
class RealtimePriceHistory:
    # Extends existing PriceHistory model
    stock_id: UUID                  # Foreign key to stocks table
    price_datetime: datetime        # Exact timestamp of price
    price: Decimal                 # Price at this timestamp
    volume: int                    # Volume traded
    source: str                    # Data provider used
    is_market_hours: bool          # Was market open when fetched
    fetch_latency_ms: int          # API response time
    created_at: datetime           # When record was inserted
```

#### ConnectionStatus
Tracks active SSE connections for portfolio updates.

```python
@dataclass
class ConnectionStatus:
    connection_id: str            # Unique connection identifier
    user_id: UUID                # Connected user
    connected_at: datetime        # Connection start time
    last_heartbeat: datetime      # Last activity
    subscribed_portfolios: List[UUID]  # Portfolio IDs to watch
    is_active: bool              # Connection status
    user_agent: str              # Browser/client info
    ip_address: str              # Client IP for monitoring
```

#### PortfolioValuation
Cached portfolio values calculated from current market prices.

```python
@dataclass
class PortfolioValuation:
    portfolio_id: UUID           # Portfolio being valued
    total_value: Decimal         # Current market value
    total_cost_basis: Decimal    # Total amount invested
    unrealized_gain_loss: Decimal # Current profit/loss
    daily_change: Decimal        # Change from previous close
    daily_change_percent: Decimal # Percentage change today
    calculated_at: datetime      # When valuation was computed
    stale_price_count: int       # Number of holdings with stale prices
    last_price_update: datetime  # Most recent price in calculation
    cache_expires_at: datetime   # When to recalculate
```

#### PollIntervalConfiguration
Administrative settings for controlling market data update frequencies.

```python
@dataclass
class PollIntervalConfiguration:
    config_id: str               # Unique identifier
    config_type: str            # "global", "user", "portfolio"
    target_id: Optional[UUID]   # User ID or Portfolio ID (None for global)
    interval_minutes: int       # Update frequency in minutes
    is_active: bool            # Configuration enabled
    priority: int              # Higher priority overrides lower (1=highest)
    created_by: UUID           # Administrator who created config
    created_at: datetime       # When configuration was created
    effective_from: datetime   # When config becomes active
    effective_until: Optional[datetime] # When config expires (None=permanent)
    reason: str               # Explanation for this configuration
```

#### APIUsageMetrics
Real-time tracking of external API consumption for cost management.

```python
@dataclass
class APIUsageMetrics:
    metric_id: str              # Unique identifier
    provider_id: str           # "alpha_vantage", "yfinance", etc.
    user_id: Optional[UUID]    # User generating requests (None=system)
    portfolio_id: Optional[UUID] # Portfolio being updated
    request_type: str          # "price_fetch", "bulk_update", "manual_refresh"
    requests_count: int        # Number of API requests
    data_points_fetched: int   # Number of stock prices obtained
    cost_estimate: Decimal     # Estimated cost in dollars
    recorded_at: datetime      # When usage was recorded
    time_bucket: str           # "hourly", "daily", "monthly" aggregation
    rate_limit_hit: bool       # Whether rate limit was encountered
    error_count: int           # Number of failed requests
```

#### AdministrativeOverride
Temporary controls for system maintenance and cost management.

```python
@dataclass
class AdministrativeOverride:
    override_id: str            # Unique identifier
    override_type: str         # "disable_updates", "force_interval", "emergency_stop"
    scope: str                 # "global", "user", "portfolio", "provider"
    target_id: Optional[UUID]  # User/Portfolio ID if scoped
    provider_id: Optional[str] # Data provider if scoped
    is_active: bool           # Override currently in effect
    override_value: str       # JSON configuration data
    reason: str               # Explanation for override
    created_by: UUID          # Administrator who created override
    created_at: datetime      # When override was created
    expires_at: Optional[datetime] # When override auto-expires
    auto_remove: bool         # Remove automatically when expired
```

## Database Schema Extensions

### New Tables

```sql
-- Market data providers configuration
CREATE TABLE market_data_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id VARCHAR(50) UNIQUE NOT NULL,
    provider_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    api_key VARCHAR(255),
    rate_limit_per_day INTEGER DEFAULT 500,
    rate_limit_per_minute INTEGER DEFAULT 5,
    requests_used_today INTEGER DEFAULT 0,
    last_request_at TIMESTAMP,
    priority INTEGER DEFAULT 1,
    supports_symbols TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Price update scheduling
CREATE TABLE price_update_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id VARCHAR(50) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    market_hours_interval INTEGER DEFAULT 15,
    after_hours_interval INTEGER DEFAULT 60,
    weekend_interval INTEGER DEFAULT 1440,
    market_open_time TIME DEFAULT '09:30:00',
    market_close_time TIME DEFAULT '16:00:00',
    timezone VARCHAR(50) DEFAULT 'Australia/Sydney',
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Real-time price history (extends existing pattern)
CREATE TABLE realtime_price_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stock_id UUID NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    price_datetime TIMESTAMP NOT NULL,
    price NUMERIC(10, 4) NOT NULL,
    volume BIGINT DEFAULT 0,
    source VARCHAR(50) NOT NULL,
    is_market_hours BOOLEAN DEFAULT true,
    fetch_latency_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- SSE connection tracking
CREATE TABLE sse_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id VARCHAR(100) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    connected_at TIMESTAMP DEFAULT NOW(),
    last_heartbeat TIMESTAMP DEFAULT NOW(),
    subscribed_portfolios UUID[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    user_agent TEXT,
    ip_address INET,
    disconnected_at TIMESTAMP
);

-- Cached portfolio valuations
CREATE TABLE portfolio_valuations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    total_value NUMERIC(15, 2) NOT NULL,
    total_cost_basis NUMERIC(15, 2) NOT NULL,
    unrealized_gain_loss NUMERIC(15, 2) NOT NULL,
    daily_change NUMERIC(15, 2) DEFAULT 0,
    daily_change_percent NUMERIC(5, 2) DEFAULT 0,
    calculated_at TIMESTAMP DEFAULT NOW(),
    stale_price_count INTEGER DEFAULT 0,
    last_price_update TIMESTAMP,
    cache_expires_at TIMESTAMP NOT NULL,
    UNIQUE(portfolio_id, calculated_at)
);

-- Administrative poll interval configurations
CREATE TABLE poll_interval_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id VARCHAR(100) UNIQUE NOT NULL,
    config_type VARCHAR(20) NOT NULL CHECK (config_type IN ('global', 'user', 'portfolio')),
    target_id UUID, -- User ID or Portfolio ID (NULL for global)
    interval_minutes INTEGER NOT NULL CHECK (interval_minutes > 0),
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    effective_from TIMESTAMP DEFAULT NOW(),
    effective_until TIMESTAMP,
    reason TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_target_for_type CHECK (
        (config_type = 'global' AND target_id IS NULL) OR
        (config_type IN ('user', 'portfolio') AND target_id IS NOT NULL)
    )
);

-- API usage metrics for cost tracking and reporting
CREATE TABLE api_usage_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_id VARCHAR(100) UNIQUE NOT NULL,
    provider_id VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES users(id),
    portfolio_id UUID REFERENCES portfolios(id),
    request_type VARCHAR(50) NOT NULL,
    requests_count INTEGER DEFAULT 1,
    data_points_fetched INTEGER DEFAULT 0,
    cost_estimate NUMERIC(8, 4) DEFAULT 0,
    recorded_at TIMESTAMP DEFAULT NOW(),
    time_bucket VARCHAR(20) NOT NULL CHECK (time_bucket IN ('hourly', 'daily', 'monthly')),
    rate_limit_hit BOOLEAN DEFAULT false,
    error_count INTEGER DEFAULT 0
);

-- Administrative overrides for system control
CREATE TABLE administrative_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    override_id VARCHAR(100) UNIQUE NOT NULL,
    override_type VARCHAR(50) NOT NULL CHECK (override_type IN ('disable_updates', 'force_interval', 'emergency_stop')),
    scope VARCHAR(20) NOT NULL CHECK (scope IN ('global', 'user', 'portfolio', 'provider')),
    target_id UUID, -- User/Portfolio ID if scoped
    provider_id VARCHAR(50), -- Data provider if scoped
    is_active BOOLEAN DEFAULT true,
    override_value TEXT, -- JSON configuration data
    reason TEXT NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    auto_remove BOOLEAN DEFAULT true,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Existing Table Extensions

```sql
-- Extend stocks table with real-time price fields
ALTER TABLE stocks ADD COLUMN IF NOT EXISTS current_price NUMERIC(10, 4);
ALTER TABLE stocks ADD COLUMN IF NOT EXISTS previous_close NUMERIC(10, 4);
ALTER TABLE stocks ADD COLUMN IF NOT EXISTS daily_change NUMERIC(8, 4) DEFAULT 0;
ALTER TABLE stocks ADD COLUMN IF NOT EXISTS daily_change_percent NUMERIC(5, 2) DEFAULT 0;
ALTER TABLE stocks ADD COLUMN IF NOT EXISTS last_price_update TIMESTAMP;
ALTER TABLE stocks ADD COLUMN IF NOT EXISTS price_source VARCHAR(50);
ALTER TABLE stocks ADD COLUMN IF NOT EXISTS market_status VARCHAR(20) DEFAULT 'CLOSED';

-- Performance indexes for real-time queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_stocks_symbol_hash 
    ON stocks USING hash(symbol);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_stocks_last_price_update 
    ON stocks (last_price_update DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_realtime_price_history_stock_datetime 
    ON realtime_price_history (stock_id, price_datetime DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_portfolio_valuations_portfolio_calculated 
    ON portfolio_valuations (portfolio_id, calculated_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sse_connections_user_active 
    ON sse_connections (user_id, is_active) WHERE is_active = true;

-- Performance indexes for administrative tables
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_poll_configs_active_priority 
    ON poll_interval_configs (is_active, priority, config_type) WHERE is_active = true;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_poll_configs_target 
    ON poll_interval_configs (config_type, target_id) WHERE target_id IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_usage_provider_time 
    ON api_usage_metrics (provider_id, recorded_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_usage_user_time 
    ON api_usage_metrics (user_id, recorded_at DESC) WHERE user_id IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_usage_time_bucket 
    ON api_usage_metrics (time_bucket, recorded_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_admin_overrides_active_scope 
    ON administrative_overrides (is_active, scope, override_type) WHERE is_active = true;
```

## Data Flow

### Price Update Flow
1. **Scheduled Job** runs every 15 minutes (market hours)
2. **Data Provider Service** fetches prices from Alpha Vantage API
3. **Price Update Handler** updates `stocks.current_price` and creates `realtime_price_history` records
4. **Portfolio Valuation Service** recalculates affected portfolio values
5. **SSE Broadcaster** sends updates to connected clients

### Client Connection Flow
1. **Frontend** establishes SSE connection to `/api/v1/market-data/stream`
2. **Connection Manager** tracks active connections in `sse_connections` table
3. **Client** subscribes to specific portfolio IDs
4. **Server** sends periodic updates and heartbeats

## Validation Rules

### Data Integrity
- Stock prices must be positive decimals with 4 decimal places
- Volume must be non-negative integer
- Timestamps must include timezone information
- Price changes calculated as (current_price - previous_close)

### Business Rules
- Portfolio valuations expire after 20 minutes maximum
- Stale price warnings when data > 30 minutes old
- Maximum 5 portfolios per SSE connection
- Connection timeout after 10 minutes without heartbeat

### Performance Constraints
- Realtime price history partitioned by month
- Portfolio valuation cache TTL: 15 minutes
- SSE connection limit: 50 concurrent per user
- API rate limiting enforced at provider level

## Event Schema

### SSE Message Format
```typescript
interface PortfolioUpdateEvent {
  type: 'portfolio_update';
  data: {
    portfolio_id: string;
    total_value: string;
    daily_change: string;
    daily_change_percent: string;
    last_updated: string;
    stale_price_count: number;
  };
  timestamp: string;
  sequence: number;
}

interface PriceUpdateEvent {
  type: 'price_update';
  data: {
    symbol: string;
    price: number;
    change: number;
    change_percent: number;
    volume: number;
    market_status: string;
  };
  timestamp: string;
  sequence: number;
}

interface ConnectionEvent {
  type: 'heartbeat' | 'connection_status';
  data: {
    status: 'connected' | 'reconnecting' | 'error';
    server_time: string;
    next_update_in: number; // seconds until next scheduled update
  };
  timestamp: string;
}
```

---
*Data model supports simplified scheduled updates with efficient caching and real-time UI updates via SSE*
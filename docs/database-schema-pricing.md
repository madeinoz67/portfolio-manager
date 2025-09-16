# Database Schema: Pricing and Market Data

This document details the database schema specifically related to pricing, market data, and portfolio valuation systems.

## Core Pricing Tables

### `stocks` Table

The master table for stock information and current pricing used throughout the application.

```sql
CREATE TABLE stocks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(10) UNIQUE NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    exchange VARCHAR(50) NOT NULL DEFAULT 'ASX',
    current_price DECIMAL(10,4),
    previous_close DECIMAL(10,4),
    daily_change DECIMAL(8,4),
    daily_change_percent DECIMAL(5,2),
    status stock_status DEFAULT 'ACTIVE',
    last_price_update TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_symbol (symbol),
    INDEX idx_last_price_update (last_price_update),
    INDEX idx_exchange_status (exchange, status)
);
```

**Usage:**
- Primary source for portfolio holdings calculations
- Frontend displays for holdings pages
- Real-time portfolio valuations
- Stock master data management

**Key Fields:**
- `current_price`: Latest price used for all calculations
- `last_price_update`: Timestamp of most recent price update
- `symbol`: Unique stock identifier (e.g., 'AAPL', 'CBA')
- `status`: Trading status (ACTIVE, HALTED, SUSPENDED, DELISTED)

### `realtime_price_history` Table

Comprehensive time-series storage for all price updates with provider attribution.

```sql
CREATE TABLE realtime_price_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(10,4) NOT NULL,

    -- Extended OHLC data
    opening_price DECIMAL(10,4),
    high_price DECIMAL(10,4),
    low_price DECIMAL(10,4),
    previous_close DECIMAL(10,4),

    -- Volume and market data
    volume INTEGER,
    market_cap DECIMAL(20,2),

    -- Financial metrics
    fifty_two_week_high DECIMAL(10,4),
    fifty_two_week_low DECIMAL(10,4),
    dividend_yield DECIMAL(5,2),
    pe_ratio DECIMAL(8,2),
    beta DECIMAL(5,2),

    -- Metadata
    currency VARCHAR(3) DEFAULT 'USD',
    company_name VARCHAR(255),

    -- System fields
    provider_id UUID NOT NULL REFERENCES market_data_providers(id),
    source_timestamp TIMESTAMP NOT NULL,
    fetched_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_symbol_fetched_at (symbol, fetched_at),
    INDEX idx_symbol_source_timestamp (symbol, source_timestamp),
    INDEX idx_provider_fetched_at (provider_id, fetched_at),
    INDEX idx_symbol_opening_price (symbol, opening_price)
);
```

**Usage:**
- Historical price analysis and charting
- Trend calculations and technical indicators
- Market data API responses
- Audit trail for price updates
- Provider performance tracking

**Key Fields:**
- `price`: The primary price value
- `source_timestamp`: When the price was created by the provider
- `fetched_at`: When our system retrieved the price
- `provider_id`: Which market data provider supplied the data

## Market Data Provider Tables

### `market_data_providers` Table

Configuration for external market data sources.

```sql
CREATE TABLE market_data_providers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    api_key TEXT,
    base_url VARCHAR(255),
    is_enabled BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 1,
    rate_limit_per_minute INTEGER DEFAULT 60,
    timeout_seconds INTEGER DEFAULT 30,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_enabled_priority (is_enabled, priority)
);
```

**Standard Providers:**
```sql
INSERT INTO market_data_providers (name, display_name, is_enabled, priority) VALUES
('yahoo_finance', 'Yahoo Finance', true, 1),
('alpha_vantage', 'Alpha Vantage', false, 2),
('mock_provider', 'Mock Provider', false, 999);
```

### `provider_activities` Table

Activity logging for market data operations and monitoring.

```sql
CREATE TABLE provider_activities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id UUID NOT NULL REFERENCES market_data_providers(id),
    activity_type provider_activity_type NOT NULL,
    description TEXT NOT NULL,
    status activity_status NOT NULL,
    symbols_processed TEXT[], -- Array of symbols
    response_time_ms INTEGER,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_provider_created_at (provider_id, created_at),
    INDEX idx_activity_type_status (activity_type, status),
    INDEX idx_created_at (created_at)
);
```

**Activity Types:**
- `API_CALL`: Individual market data requests
- `BULK_PRICE_UPDATE`: Multiple symbol updates
- `PROVIDER_FAILURE`: Provider-wide failures
- `API_ERROR`: Individual API errors
- `RATE_LIMIT`: Rate limiting events

## Portfolio Integration Tables

### `holdings` Table

Portfolio holdings that depend on current stock prices.

```sql
CREATE TABLE holdings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    stock_id UUID NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    quantity DECIMAL(15,8) NOT NULL,
    average_cost DECIMAL(10,4) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(portfolio_id, stock_id),
    INDEX idx_portfolio_stock (portfolio_id, stock_id),
    INDEX idx_stock_holdings (stock_id)
);
```

**Calculated Fields (via JOINs):**
```sql
-- Current value calculation
SELECT
    h.quantity,
    h.average_cost,
    s.current_price,
    h.quantity * h.average_cost as cost_basis,
    h.quantity * s.current_price as current_value,
    (h.quantity * s.current_price) - (h.quantity * h.average_cost) as unrealized_gain_loss,
    s.last_price_update
FROM holdings h
JOIN stocks s ON h.stock_id = s.id
WHERE h.portfolio_id = ?;
```

### `portfolio_valuations` Table

Cached portfolio valuations to improve performance.

```sql
CREATE TABLE portfolio_valuations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    total_value DECIMAL(15,2) NOT NULL,
    total_cost_basis DECIMAL(15,2) NOT NULL,
    total_gain_loss DECIMAL(15,2) NOT NULL,
    gain_loss_percentage DECIMAL(5,2) NOT NULL,
    holdings_count INTEGER NOT NULL,
    calculated_at TIMESTAMP DEFAULT NOW(),
    is_current BOOLEAN DEFAULT true,

    INDEX idx_portfolio_calculated_at (portfolio_id, calculated_at),
    INDEX idx_is_current (is_current),
    INDEX idx_calculated_at (calculated_at)
);
```

## Scheduling and Configuration Tables

### `poll_interval_configs` Table

Configuration for automated price update scheduling.

```sql
CREATE TABLE poll_interval_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_name VARCHAR(50) UNIQUE NOT NULL,
    interval_seconds INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT true,
    market_hours_only BOOLEAN DEFAULT true,
    max_symbols_per_batch INTEGER DEFAULT 50,
    retry_attempts INTEGER DEFAULT 3,
    circuit_breaker_threshold INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Default Configuration:**
```sql
INSERT INTO poll_interval_configs (config_name, interval_seconds, is_active) VALUES
('market_data_refresh', 900, true), -- 15 minutes
('portfolio_valuation', 1800, true), -- 30 minutes
('provider_health_check', 300, true); -- 5 minutes
```

### `scheduler_executions` Table

Execution history and monitoring for scheduled tasks.

```sql
CREATE TABLE scheduler_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_type VARCHAR(50) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status execution_status NOT NULL,
    symbols_processed INTEGER DEFAULT 0,
    symbols_succeeded INTEGER DEFAULT 0,
    symbols_failed INTEGER DEFAULT 0,
    error_message TEXT,
    execution_time_ms INTEGER,

    INDEX idx_execution_type_started_at (execution_type, started_at),
    INDEX idx_status_started_at (status, started_at)
);
```

## Data Synchronization Views

### Current Stock Prices View

Combines stocks and latest price history for comprehensive price data.

```sql
CREATE VIEW current_stock_prices AS
SELECT
    s.id,
    s.symbol,
    s.company_name,
    s.exchange,
    s.current_price,
    s.last_price_update,
    h.volume,
    h.opening_price,
    h.high_price,
    h.low_price,
    h.previous_close,
    h.market_cap,
    h.pe_ratio,
    h.dividend_yield,
    h.fetched_at as history_fetched_at,
    p.display_name as provider_name
FROM stocks s
LEFT JOIN LATERAL (
    SELECT * FROM realtime_price_history rph
    WHERE rph.symbol = s.symbol
    ORDER BY rph.fetched_at DESC
    LIMIT 1
) h ON true
LEFT JOIN market_data_providers p ON h.provider_id = p.id;
```

### Portfolio Holdings Summary View

Comprehensive portfolio holdings with current valuations.

```sql
CREATE VIEW portfolio_holdings_summary AS
SELECT
    p.id as portfolio_id,
    p.name as portfolio_name,
    u.email as owner_email,
    COUNT(h.id) as holdings_count,
    SUM(h.quantity * h.average_cost) as total_cost_basis,
    SUM(h.quantity * s.current_price) as current_value,
    SUM(h.quantity * s.current_price) - SUM(h.quantity * h.average_cost) as total_gain_loss,
    CASE
        WHEN SUM(h.quantity * h.average_cost) > 0
        THEN ((SUM(h.quantity * s.current_price) - SUM(h.quantity * h.average_cost)) / SUM(h.quantity * h.average_cost)) * 100
        ELSE 0
    END as gain_loss_percentage,
    MAX(s.last_price_update) as last_price_update
FROM portfolios p
JOIN users u ON p.user_id = u.id
LEFT JOIN holdings h ON p.id = h.portfolio_id
LEFT JOIN stocks s ON h.stock_id = s.id
GROUP BY p.id, p.name, u.email;
```

## Critical Synchronization Constraints

### Dual-Table Update Trigger

Ensures data consistency between stocks and realtime_price_history tables.

```sql
-- Function to validate price synchronization
CREATE OR REPLACE FUNCTION validate_price_sync()
RETURNS TRIGGER AS $$
BEGIN
    -- Ensure that when stocks.current_price is updated,
    -- there's a corresponding realtime_price_history record
    IF TG_OP = 'UPDATE' AND OLD.current_price != NEW.current_price THEN
        IF NOT EXISTS (
            SELECT 1 FROM realtime_price_history
            WHERE symbol = NEW.symbol
            AND price = NEW.current_price
            AND ABS(EXTRACT(EPOCH FROM (fetched_at - NEW.last_price_update))) < 60
        ) THEN
            RAISE WARNING 'Price update without corresponding history record for %', NEW.symbol;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to stocks table
CREATE TRIGGER validate_price_sync_trigger
    AFTER UPDATE ON stocks
    FOR EACH ROW
    EXECUTE FUNCTION validate_price_sync();
```

### Referential Integrity

Critical foreign key relationships:

```sql
-- Holdings must reference valid stocks
ALTER TABLE holdings
ADD CONSTRAINT fk_holdings_stock
FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE;

-- Price history must reference valid providers
ALTER TABLE realtime_price_history
ADD CONSTRAINT fk_price_history_provider
FOREIGN KEY (provider_id) REFERENCES market_data_providers(id) ON DELETE RESTRICT;

-- Portfolio valuations must reference valid portfolios
ALTER TABLE portfolio_valuations
ADD CONSTRAINT fk_valuations_portfolio
FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE;
```

## Performance Optimization

### Essential Indexes

```sql
-- Stocks table indexes
CREATE INDEX idx_stocks_symbol_price_update ON stocks(symbol, last_price_update);
CREATE INDEX idx_stocks_exchange_status ON stocks(exchange, status);

-- Price history indexes
CREATE INDEX idx_price_history_symbol_time ON realtime_price_history(symbol, fetched_at DESC);
CREATE INDEX idx_price_history_provider_time ON realtime_price_history(provider_id, fetched_at DESC);

-- Holdings calculation indexes
CREATE INDEX idx_holdings_portfolio_calculations ON holdings(portfolio_id, stock_id, quantity, average_cost);

-- Activity monitoring indexes
CREATE INDEX idx_provider_activities_recent ON provider_activities(provider_id, created_at DESC);
```

### Partitioning Strategy

For high-volume installations, partition price history by date:

```sql
-- Partition realtime_price_history by month
CREATE TABLE realtime_price_history_y2025m01
PARTITION OF realtime_price_history
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE realtime_price_history_y2025m02
PARTITION OF realtime_price_history
FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
```

## Data Retention Policies

### Historical Data Cleanup

```sql
-- Function to clean old price history data
CREATE OR REPLACE FUNCTION cleanup_old_price_history()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Keep 2 years of detailed history
    DELETE FROM realtime_price_history
    WHERE fetched_at < NOW() - INTERVAL '2 years';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    -- Log cleanup activity
    INSERT INTO provider_activities (
        provider_id,
        activity_type,
        description,
        status,
        metadata
    ) VALUES (
        (SELECT id FROM market_data_providers WHERE name = 'system'),
        'DATA_CLEANUP',
        'Cleaned old price history records',
        'SUCCESS',
        jsonb_build_object('deleted_records', deleted_count)
    );

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup monthly
SELECT cron.schedule('cleanup-price-history', '0 2 1 * *', 'SELECT cleanup_old_price_history();');
```

This database schema documentation ensures proper understanding of the pricing data architecture and relationships that support the dual-table synchronization mechanism.
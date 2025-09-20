# Data Model: Market Data Provider Adapters

## Overview
Data entities and relationships for the market data provider adapter system.

## Core Entities

### 1. MarketDataAdapter (Abstract Interface)
**Purpose**: Base interface definition for all market data providers
**Key Attributes**:
- `provider_name`: Unique identifier for the provider
- `config`: Provider-specific configuration settings
- `metrics`: Real-time performance tracking
- `circuit_breaker`: Failure resilience state

**Interface Design**:
- `fetch_prices(symbols: Union[str, List[str]])`: Single method for all price requests
  - Adapter internally determines optimal strategy (single vs bulk API calls)
  - Accepts either single symbol string or list of symbols
  - Returns standardized response format regardless of input type
  - Enables provider-specific optimization without exposing complexity

**Service Capabilities**:
- `supported_services`: Enum of services the adapter can provide
  - STOCK_PRICES: Real-time and historical stock price data
  - NEWS: Financial news and market updates
  - FUNDAMENTALS: Company financial statements and metrics
  - OPTIONS: Options pricing and Greeks
  - CRYPTO: Cryptocurrency pricing
  - FOREX: Foreign exchange rates
  - ECONOMIC_DATA: Economic indicators and statistics
- Initial implementation focuses on STOCK_PRICES only
- Framework designed for future service expansion

**Relationships**:
- Has one ProviderConfiguration
- Has many ProviderMetrics (time-series)
- Has many CostTrackingRecords

**Validation Rules**:
- provider_name must be unique across all adapters
- config must contain required fields per provider type
- metrics must be updated on every API call
- fetch_prices must handle both single symbols and symbol lists uniformly

### 2. ProviderConfiguration
**Purpose**: Stores configuration and credentials for each market data provider
**Key Attributes**:
- `id`: UUID primary key
- `provider_name`: Reference to adapter type (alpha_vantage, yahoo_finance, etc.)
- `display_name`: Human-readable name for admin UI
- `config_data`: JSON field containing provider-specific settings
- `is_active`: Boolean flag for enabling/disabling provider
- `created_at`: Timestamp of configuration creation
- `updated_at`: Timestamp of last configuration change
- `created_by_user_id`: Reference to admin user who created config

**Relationships**:
- Belongs to User (admin who created/manages it)
- Has many ProviderMetrics
- Has many CostTrackingRecords

**Validation Rules**:
- provider_name must exist in adapter registry
- config_data must pass provider-specific validation schema
- Only active configurations can be used for API calls
- display_name must be unique per user

**State Transitions**:
- Created → Active (when configuration validated and enabled)
- Active → Inactive (when disabled by admin)
- Inactive → Active (when re-enabled)
- Any state → Deleted (soft delete)

### 3. ProviderMetrics
**Purpose**: Real-time performance data for each provider
**Key Attributes**:
- `id`: UUID primary key
- `provider_config_id`: Foreign key to ProviderConfiguration
- `timestamp`: When metrics were recorded
- `request_count`: Total requests in time window
- `success_count`: Successful requests in time window
- `error_count`: Failed requests in time window
- `total_latency_ms`: Sum of all request latencies (for average calculation)
- `avg_latency_ms`: Average latency in milliseconds
- `rate_limit_hits`: Number of rate limit violations
- `circuit_breaker_state`: Current circuit breaker status (open/closed/half-open)
- `metadata`: JSON field for provider-specific metrics

**Relationships**:
- Belongs to ProviderConfiguration
- Time-series data (multiple records per provider over time)

**Validation Rules**:
- timestamp must be valid datetime
- counts must be non-negative integers
- latency values must be non-negative
- circuit_breaker_state must be valid enum value

**Aggregation Rules**:
- Metrics aggregated in 1-minute windows
- Rolling 24-hour history maintained
- Real-time metrics calculated from current window

### 4. CostTrackingRecord
**Purpose**: Track API usage costs and limits per provider
**Key Attributes**:
- `id`: UUID primary key
- `provider_config_id`: Foreign key to ProviderConfiguration
- `date`: Date of cost tracking (daily aggregation)
- `api_calls_made`: Number of API calls for the day
- `cost_units_consumed`: Cost units (varies by provider)
- `estimated_cost_usd`: Estimated cost in USD (decimal precision)
- `rate_limit_quota`: Daily/monthly quota from provider
- `rate_limit_remaining`: Remaining quota
- `billing_period_start`: When current billing period started
- `billing_period_end`: When current billing period ends

**Relationships**:
- Belongs to ProviderConfiguration
- Daily aggregation records

**Validation Rules**:
- date must be valid date
- costs must use decimal precision (no floating point)
- rate limits must be non-negative
- billing periods must be valid date ranges

**Business Rules**:
- Cost units vary by provider (Alpha Vantage = API calls, IEX = credits)
- USD conversion rates updated daily
- Rate limits reset based on provider billing cycle

### 5. AdapterRegistry
**Purpose**: Central registry of available adapters and their capabilities
**Key Attributes**:
- `id`: UUID primary key
- `adapter_name`: Unique identifier for adapter type
- `adapter_class`: Python class path for dynamic loading
- `display_name`: Human-readable name
- `description`: Adapter description and capabilities
- `supported_features`: JSON array of supported features
- `required_config_fields`: JSON schema for configuration validation
- `default_config`: JSON with default configuration values
- `is_enabled`: Whether adapter is available for use
- `version`: Adapter version for compatibility tracking

**Relationships**:
- Has many ProviderConfigurations
- Standalone entity (no foreign keys)

**Validation Rules**:
- adapter_name must be unique
- adapter_class must be valid Python import path
- required_config_fields must be valid JSON schema
- supported_features must be valid array

**Supported Features**:
- `stock_prices`: Basic stock price retrieval
- `bulk_quotes`: Multiple symbol quotes in single request
- `historical_data`: Historical price data (future extension)
- `real_time_streaming`: WebSocket data streams (future extension)
- `fundamental_data`: Company fundamentals (future extension)

### 6. AdapterHealthCheck
**Purpose**: Store health check results for each configured provider
**Key Attributes**:
- `id`: UUID primary key
- `provider_config_id`: Foreign key to ProviderConfiguration
- `check_timestamp`: When health check was performed
- `status`: Health status (healthy/degraded/unhealthy)
- `response_time_ms`: Response time for health check
- `error_message`: Error details if unhealthy
- `metadata`: JSON with additional health check data

**Relationships**:
- Belongs to ProviderConfiguration
- Time-series health check history

**Validation Rules**:
- status must be valid enum value
- response_time_ms must be non-negative
- check_timestamp must be valid datetime

## Database Schema Relationships

```
User (existing)
  ├── ProviderConfiguration (1:many)
      ├── ProviderMetrics (1:many, time-series)
      ├── CostTrackingRecord (1:many, daily)
      └── AdapterHealthCheck (1:many, time-series)

AdapterRegistry (standalone)
  └── ProviderConfiguration (1:many, via adapter_name)

RealtimeSymbol (existing master table)
  └── [No direct relationship - adapters query this table]
```

## Data Access Patterns

### Read Patterns
1. **Admin Dashboard**: Real-time metrics aggregation across all providers
2. **Provider Selection**: Active providers with health status for failover
3. **Cost Monitoring**: Daily/monthly cost aggregation by provider
4. **Performance Analysis**: Historical metrics for trend analysis

### Write Patterns
1. **Metrics Recording**: High-frequency writes (every API call)
2. **Configuration Updates**: Low-frequency admin operations
3. **Health Checks**: Periodic background writes (every minute)
4. **Cost Tracking**: Daily batch aggregation

### Query Optimization
1. **Indexes**: timestamp fields for time-series queries
2. **Partitioning**: metrics tables by date for performance
3. **Caching**: active configurations in application memory
4. **Aggregation**: pre-calculated daily/hourly summaries

## Data Retention Policy

### Metrics Data
- **Real-time**: Keep 24 hours of minute-level data
- **Hourly**: Keep 30 days of hourly aggregations
- **Daily**: Keep 1 year of daily aggregations
- **Cleanup**: Automated background job removes old data

### Cost Tracking
- **Daily records**: Keep for current and previous fiscal year
- **Monthly summaries**: Keep indefinitely for billing history
- **Archive**: Export to external storage before deletion

### Configuration History
- **Active configs**: Keep indefinitely
- **Deleted configs**: Soft delete with 90-day retention
- **Audit trail**: All configuration changes logged permanently

## Security Considerations

### Sensitive Data
- **API Keys**: Encrypted at rest using application-level encryption
- **Credentials**: Never logged or exposed in API responses
- **Configuration**: Admin-only access with audit trail

### Access Control
- **Admin Only**: All adapter management operations
- **Read Access**: Metrics viewing requires admin role
- **Audit Logging**: All configuration changes tracked with user ID

### Data Privacy
- **No PII**: Adapter system contains no personally identifiable information
- **Business Data**: Cost and usage data treated as confidential
- **Compliance**: Follows existing portfolio data handling policies
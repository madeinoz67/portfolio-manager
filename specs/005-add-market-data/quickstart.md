# Quickstart: Market Data Provider Adapters

## Overview
This quickstart guide demonstrates the complete workflow for configuring and monitoring market data provider adapters. It covers the primary user scenarios identified in the feature specification.

## Prerequisites
- Admin user account with proper JWT authentication
- Portfolio Manager system running with admin dashboard access
- At least one market data provider API key (Alpha Vantage recommended for testing)

## Scenario 1: Configure New Market Data Provider

### Step 1: Access Admin Dashboard
1. Log in to Portfolio Manager as admin user
2. Navigate to Admin Dashboard → Market Data → Adapters
3. Verify admin role permissions are working

**Expected Result**: Admin adapter management interface loads successfully

### Step 2: Review Available Adapter Types
1. Click "Add New Adapter" button
2. Review list of available adapter types
3. Select "Alpha Vantage" from the dropdown

**Expected Result**:
- Available adapter types display with descriptions
- Alpha Vantage shows required configuration fields
- Configuration form loads with proper validation

### Step 3: Configure Alpha Vantage Adapter
1. Fill in adapter configuration:
   ```
   Display Name: Alpha Vantage Production
   Provider Type: alpha_vantage
   API Key: [your_alpha_vantage_api_key]
   Rate Limit: 5 requests/minute
   Timeout: 30 seconds
   ```
2. Test configuration by clicking "Test Connection"
3. Save configuration

**Expected Result**:
- Configuration validates successfully
- Test connection returns successful response
- Adapter appears in configured adapters list
- Initial health check shows "healthy" status

### Step 4: Activate Adapter
1. Find newly created adapter in the list
2. Toggle "Active" switch to enable
3. Confirm activation dialog

**Expected Result**:
- Adapter status changes to "Active"
- System can now use adapter for market data requests
- Metrics collection begins immediately

## Scenario 2: Monitor Live Adapter Metrics

### Step 1: Generate Some Traffic
1. Navigate to Portfolio Dashboard
2. Refresh portfolio with stock holdings
3. Add new stock to trigger price fetches
4. Repeat 5-10 times to generate metrics

**Expected Result**: Market data requests processed through configured adapter

### Step 2: View Real-time Metrics
1. Return to Admin Dashboard → Market Data → Adapters
2. Click on the Alpha Vantage adapter
3. Navigate to "Metrics" tab
4. Select "Last 1 Hour" time range

**Expected Result**:
- Live metrics display with recent data points
- Charts show request count, success rate, latency
- Cost tracking shows API calls consumed
- Rate limit usage displays current quota

### Step 3: Analyze Performance Data
1. Review success rate percentage
2. Check average latency values
3. Monitor rate limit consumption
4. Verify cost tracking accuracy

**Expected Result**:
- Success rate should be >95% for healthy adapter
- Latency should be <2000ms for Alpha Vantage
- Rate limits should not be exceeded
- Cost data should match actual API usage

## Scenario 3: Handle Provider Failure Gracefully

### Step 1: Simulate Provider Failure
1. Navigate to adapter configuration
2. Change API key to invalid value
3. Save configuration
4. Trigger portfolio refresh

**Expected Result**:
- Adapter health check detects failure
- Error metrics increase
- Circuit breaker may activate
- User experience remains stable (if fallback configured)

### Step 2: Monitor Failure Response
1. Check adapter health status
2. Review error metrics
3. Verify circuit breaker state
4. Check system logs for error details

**Expected Result**:
- Health status shows "unhealthy"
- Error count increases in metrics
- Circuit breaker opens after threshold
- Detailed error messages available for debugging

### Step 3: Restore Service
1. Revert to valid API key
2. Save configuration
3. Manually trigger health check
4. Verify service restoration

**Expected Result**:
- Health check passes
- Circuit breaker resets to closed
- Success metrics resume
- Normal operation restored

## Scenario 4: Configure Multiple Providers with Fallback

### Step 1: Add Yahoo Finance Adapter
1. Add second adapter: Yahoo Finance
2. Configure with appropriate settings:
   ```
   Display Name: Yahoo Finance Backup
   Provider Type: yahoo_finance
   Rate Limit: 100 requests/minute
   Timeout: 15 seconds
   ```
3. Activate the adapter

**Expected Result**: Two active adapters configured

### Step 2: Configure Fallback Chain
1. Navigate to System Settings → Provider Failover
2. Set provider priority:
   - Primary: Alpha Vantage
   - Fallback: Yahoo Finance
3. Save fallback configuration

**Expected Result**: Failover chain configured for automatic switching

### Step 3: Test Failover Behavior
1. Disable Alpha Vantage adapter
2. Trigger portfolio data refresh
3. Monitor which provider handles requests
4. Check metrics for both providers

**Expected Result**:
- System automatically switches to Yahoo Finance
- No user-visible service interruption
- Metrics show traffic moved to fallback provider
- Logging indicates fallover occurred

## Scenario 5: Cost Monitoring and Alerting

### Step 1: Configure Cost Tracking
1. Navigate to adapter configuration
2. Set cost parameters:
   ```
   Cost per API call: $0.0025
   Monthly budget limit: $50.00
   Alert threshold: 80%
   ```
3. Save cost configuration

**Expected Result**: Cost tracking enabled with alerts

### Step 2: Monitor Daily Usage
1. Generate significant API traffic
2. Check daily cost accumulation
3. Review cost projections
4. Monitor approaching budget limits

**Expected Result**:
- Daily costs tracked accurately
- Monthly projection calculated
- Budget alerts trigger when appropriate
- Cost history maintained

### Step 3: Validate Cost Accuracy
1. Compare tracked costs with provider billing
2. Verify API call counts match
3. Check rate limit consumption accuracy
4. Validate currency conversion (if applicable)

**Expected Result**:
- Cost tracking matches actual provider billing
- API call counts are accurate
- Rate limit tracking is precise
- Currency handling is correct

## Validation Checklist

### Functional Requirements Validation
- [ ] FR-001: Standardized adapter interface implemented
- [ ] FR-002: Multiple providers supported simultaneously
- [ ] FR-003: Metrics tracking operational (latency, success rates, errors)
- [ ] FR-004: Cost tracking functional when provider supports it
- [ ] FR-005: Rate limit tracking and reporting working
- [ ] FR-006: Default metrics provided when provider doesn't supply them
- [ ] FR-007: Admin dashboard displays live, dynamic metrics
- [ ] FR-008: Extensible adapter architecture in place
- [ ] FR-009: Focus maintained on stock price data only
- [ ] FR-010: No hard-coded metrics or data values
- [ ] FR-011: Graceful handling of provider errors and rate limits
- [ ] FR-012: New providers can be added without system restart

### Technical Validation
- [ ] TDD approach followed (tests written first)
- [ ] Database migrations preserve existing data
- [ ] Single source of truth maintained for market data
- [ ] Admin authentication and authorization working
- [ ] API response times under 200ms
- [ ] System handles 1000+ requests/second
- [ ] No hard-coded configuration values
- [ ] Proper error handling and user feedback

### User Experience Validation
- [ ] Admin can configure providers without technical knowledge
- [ ] Metrics are clearly visualized and understandable
- [ ] Error messages are helpful for troubleshooting
- [ ] Provider failures don't impact user workflow
- [ ] Cost information is accurate and actionable
- [ ] Health status is clear and actionable

## Troubleshooting Common Issues

### Adapter Configuration Fails
**Symptoms**: Configuration validation errors, test connection failures
**Solutions**:
- Verify API key format and validity
- Check provider API documentation for changes
- Confirm network connectivity to provider endpoints
- Review provider rate limits and quotas

### Metrics Not Updating
**Symptoms**: Static or missing metrics data
**Solutions**:
- Verify adapter is actively handling requests
- Check database connection for metrics storage
- Confirm metrics collection service is running
- Review logging for metrics processing errors

### High Latency Issues
**Symptoms**: Response times >2000ms, timeout errors
**Solutions**:
- Check provider service status
- Review network connectivity and routing
- Adjust timeout settings if appropriate
- Consider switching to alternative provider

### Cost Tracking Inaccurate
**Symptoms**: Costs don't match provider billing
**Solutions**:
- Verify cost-per-call configuration
- Check for API calls not being tracked
- Review billing period alignment
- Confirm currency conversion rates

## Performance Benchmarks

### Expected Performance Metrics
- **API Response Time**: <200ms for adapter management operations
- **Metrics Query Time**: <500ms for 24-hour data aggregation
- **Health Check Time**: <100ms per adapter
- **Dashboard Load Time**: <1000ms for full metrics display
- **Memory Usage**: <50MB additional per active adapter

### Load Testing Scenarios
- 100 concurrent adapter management requests
- 1000 metrics data points per minute
- 24-hour metrics aggregation queries
- Simultaneous multi-provider operations
- Failover scenario performance impact
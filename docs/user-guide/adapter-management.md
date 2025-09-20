# Adapter Management User Guide

## Overview

The Portfolio Management System includes a powerful adapter management system that allows administrators to configure and monitor multiple market data providers. This guide covers how to use the admin dashboard to manage these adapters effectively.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Adapter Dashboard](#adapter-dashboard)
3. [Creating Adapters](#creating-adapters)
4. [Managing Existing Adapters](#managing-existing-adapters)
5. [Monitoring Performance](#monitoring-performance)
6. [Health Monitoring](#health-monitoring)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## Getting Started

### Prerequisites

- Admin account with appropriate permissions
- Understanding of your market data provider requirements
- API credentials for the providers you want to configure

### Accessing Adapter Management

1. Log in to the admin dashboard
2. Navigate to **Admin** → **Market Data Adapters**
3. You'll see the adapter management interface

## Adapter Dashboard

The main adapter dashboard provides an overview of all configured adapters:

### Dashboard Features

- **Adapter List**: View all configured adapters in a table format
- **Search & Filter**: Find specific adapters by name or provider
- **Status Overview**: Quick view of active/inactive adapters
- **Action Buttons**: Create, edit, delete, and monitor adapters

### Understanding Adapter Status

- **Active** (Green): Adapter is enabled and processing requests
- **Inactive** (Gray): Adapter is disabled and not processing requests

### Provider Types

The system supports multiple market data providers:

- **Alpha Vantage**: Professional-grade financial data (requires API key)
- **Yahoo Finance**: Free financial data (no API key required)
- **IEX Cloud**: Real-time and historical data (requires API token)
- **Polygon**: Stock market data (requires API key)
- **Finnhub**: Financial data provider (requires API key)

## Creating Adapters

### Step 1: Start Adapter Creation

1. Click the **"Add Adapter"** button in the top-right corner
2. The adapter configuration form will open

### Step 2: Basic Configuration

Fill out the basic information:

- **Display Name**: A unique, descriptive name for this adapter
- **Description**: Optional description explaining the adapter's purpose
- **Provider**: Select from available market data providers

### Step 3: Provider Settings

Configuration requirements vary by provider:

#### Alpha Vantage Configuration
```
Required:
- API Key: Your Alpha Vantage API key

Optional:
- Base URL: API endpoint (default: https://www.alphavantage.co/query)
- Timeout: Request timeout in seconds (default: 30)
- Requests per Minute: Rate limit (default: 5)
```

#### Yahoo Finance Configuration
```
Optional:
- Timeout: Request timeout in seconds (default: 30)
- User Agent: Custom user agent string
- Max Retries: Number of retry attempts (default: 3)
```

#### IEX Cloud Configuration
```
Required:
- API Token: Your IEX Cloud API token (publishable or secret)

Optional:
- Base URL: API endpoint (default: https://cloud.iexapis.com/stable)
- Sandbox: Use sandbox environment (true/false)
```

### Step 4: Advanced Settings

Configure advanced options:

- **Active**: Enable/disable the adapter immediately
- **Priority**: Set fallback order (1 = highest priority)

### Step 5: Test Connection

Before saving:

1. Click **"Test Connection"** to verify configuration
2. Wait for the test results
3. Fix any configuration issues if the test fails

### Step 6: Save Adapter

1. Click **"Create Adapter"** to save the configuration
2. The adapter will appear in the main list

## Managing Existing Adapters

### Viewing Adapter Details

1. Click on any adapter name in the list
2. View comprehensive adapter information:
   - Configuration details
   - Performance metrics
   - Health status
   - Recent activity

### Editing Adapter Configuration

1. Click the **Edit** button (pencil icon) next to an adapter
2. Modify any configuration fields
3. Test the connection if you changed provider settings
4. Click **"Update Adapter"** to save changes

### Enabling/Disabling Adapters

**Quick Toggle:**
1. Click the **Edit** button
2. Toggle the **Active** checkbox
3. Save changes

**Why Disable Adapters:**
- Temporarily stop using a provider
- Prevent costs during maintenance
- Troubleshoot connectivity issues

### Deleting Adapters

⚠️ **Warning**: Deletion is permanent and removes all historical data.

1. Click the **Delete** button (trash icon)
2. Confirm the deletion in the popup
3. The adapter and all associated data will be removed

## Monitoring Performance

### Accessing Metrics

1. Click the **Metrics** button (chart icon) next to an adapter
2. View comprehensive performance data

### Key Metrics

**Request Statistics:**
- Total Requests: Lifetime request count
- Success Rate: Percentage of successful requests
- Failed Requests: Count of failed requests
- Average Response Time: Mean response time in milliseconds

**Performance Metrics:**
- P95 Response Time: 95th percentile response time
- Requests Today: Today's request count
- Requests This Hour: Current hour's request count

**Cost Tracking:**
- Total Cost: Lifetime cost for this adapter
- Daily Cost: Cost incurred today
- Monthly Estimate: Projected monthly cost
- Cost per Request: Average cost per API call

**Activity Timeline:**
- Last Request: Most recent request timestamp
- Last Success: Most recent successful request
- Last Failure: Most recent failed request

### Time Range Selection

Use the time range selector to view metrics for different periods:
- Last Hour
- Last 24 Hours
- Last 7 Days
- Last 30 Days

### Auto-Refresh

Enable auto-refresh to see live metrics updates every 30 seconds.

## Health Monitoring

### Accessing Health Status

1. Click the **Health** button (shield icon) next to an adapter
2. View current health information

### Health Status Types

- **Healthy** (Green): All systems operational
- **Degraded** (Yellow): Minor issues detected
- **Down** (Red): Critical issues, adapter not operational

### Health Checks

The system performs various health checks:

**Connectivity Test:**
- Verifies connection to provider API
- Measures response time
- Status: Healthy/Warning/Critical

**Authentication Check:**
- Validates API credentials
- Confirms access permissions
- Status: Valid/Invalid/Expired

**Rate Limit Check:**
- Monitors API quota usage
- Alerts when approaching limits
- Status: Normal/Warning/Limited

### Manual Health Checks

1. Click **"Check Now"** to trigger immediate health check
2. Results update in real-time
3. Use after configuration changes or issue resolution

### Health Check Schedule

- **Automatic Checks**: Every 5 minutes
- **Check Interval**: Configurable per adapter
- **Failure Threshold**: 3 consecutive failures trigger alert

## Troubleshooting

### Common Issues

#### "Connection Failed" Error
**Possible Causes:**
- Incorrect API credentials
- Network connectivity issues
- Provider service outage

**Solutions:**
1. Verify API key/token is correct
2. Check provider service status
3. Test with different timeout values
4. Contact provider support

#### "Rate Limit Exceeded" Error
**Possible Causes:**
- Too many requests in short time
- API quota exhausted
- Multiple adapters using same credentials

**Solutions:**
1. Reduce request frequency
2. Upgrade API plan with provider
3. Distribute load across multiple adapters
4. Implement request queueing

#### "Authentication Failed" Error
**Possible Causes:**
- Invalid or expired API credentials
- Incorrect permissions
- Account suspension

**Solutions:**
1. Regenerate API credentials
2. Verify account status with provider
3. Check API key permissions
4. Update billing information

#### Poor Performance
**Possible Causes:**
- High network latency
- Provider service degradation
- Excessive timeout values

**Solutions:**
1. Check provider status page
2. Adjust timeout settings
3. Switch to backup provider
4. Contact system administrator

### Error Codes

| Code | Description | Action |
|------|-------------|---------|
| 401 | Unauthorized | Check API credentials |
| 403 | Forbidden | Verify API permissions |
| 429 | Rate Limited | Reduce request frequency |
| 500 | Server Error | Contact provider support |
| 503 | Service Unavailable | Try again later |

### Diagnostic Tools

**Test Connection:**
- Available in adapter configuration form
- Provides detailed error information
- Shows response time and status

**Health Check:**
- Real-time status monitoring
- Detailed check results
- Historical health data

**Metrics Dashboard:**
- Performance trends
- Error rate analysis
- Cost monitoring

## Best Practices

### Provider Configuration

1. **Use Multiple Providers**: Configure backup providers for redundancy
2. **Set Appropriate Priorities**: Order providers by reliability and cost
3. **Monitor Costs**: Regular review of usage and costs
4. **Test Configurations**: Always test before enabling in production

### Security

1. **Secure API Keys**: Never share or expose API credentials
2. **Regular Rotation**: Periodically rotate API keys
3. **Minimum Permissions**: Use least privilege principle
4. **Audit Access**: Regular review of admin access

### Performance Optimization

1. **Appropriate Timeouts**: Balance speed vs reliability
2. **Rate Limit Awareness**: Stay within provider limits
3. **Caching Strategy**: Leverage system caching effectively
4. **Load Distribution**: Spread requests across providers

### Monitoring

1. **Regular Health Checks**: Monitor adapter status daily
2. **Performance Reviews**: Weekly metrics review
3. **Cost Tracking**: Monthly cost analysis
4. **Alert Configuration**: Set up proactive alerts

### Maintenance

1. **Keep Configurations Updated**: Regular provider setting reviews
2. **Archive Unused Adapters**: Remove obsolete configurations
3. **Documentation**: Maintain configuration documentation
4. **Backup Configurations**: Export adapter settings regularly

### Troubleshooting Workflow

1. **Check Health Status**: Start with health dashboard
2. **Review Recent Metrics**: Look for patterns in failures
3. **Test Connection**: Verify current configuration
4. **Check Provider Status**: Visit provider status pages
5. **Review Logs**: Examine detailed error messages
6. **Contact Support**: If issues persist

## Advanced Features

### Bulk Operations

- **Export Configurations**: Download adapter settings as JSON/YAML
- **Import Configurations**: Bulk upload adapter configurations
- **Batch Updates**: Update multiple adapters simultaneously

### API Integration

- **REST API**: Programmatic adapter management
- **Webhooks**: Real-time status notifications
- **Metrics Export**: Integration with monitoring systems

### Custom Providers

Contact system administrators about:
- Adding new market data providers
- Custom provider implementations
- Integration requirements

## Support

### Getting Help

1. **Documentation**: Check this guide and API documentation
2. **System Status**: Review system health dashboard
3. **Provider Support**: Contact market data provider directly
4. **Technical Support**: Contact system administrator

### Reporting Issues

When reporting adapter issues, include:
- Adapter ID and provider name
- Error messages and timestamps
- Steps to reproduce
- Recent configuration changes
- Relevant metrics or health check results

---

*This guide covers the essential aspects of adapter management. For technical implementation details, see the [Developer Guide](../developer/adapter-development.md).*
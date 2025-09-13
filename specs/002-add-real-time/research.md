# Research: Real-Time Market Data Integration

**Branch**: `002-add-real-time` | **Date**: 2025-09-13 | **Spec**: [spec.md](./spec.md)

## Executive Summary

Based on comprehensive research into market data APIs, WebSocket implementation patterns, and portfolio calculation strategies, this document resolves all NEEDS CLARIFICATION items from the feature specification and provides technical recommendations for implementing **scheduled update-based** market data integration for the portfolio management system.

**Key Finding**: Real-time streaming is not required for MVP. The system will use **periodic updates** (5-15 minute intervals) which significantly simplifies the architecture while still providing users with current portfolio values.

## Research Findings

### 1. Market Data Source Decision

**Decision**: Use Alpha Vantage API as primary data source, with yfinance as fallback for development

**Rationale**:
- **Yahoo Finance API**: Discontinued in 2017, unofficial access unreliable for production
- **Alpha Vantage**: Official API, 500 free requests/day, $29.99/month for premium
- **ASX Data**: Alpha Vantage supports Australian markets with `.AX` suffix
- **Reliability**: Alpha Vantage provides SLA guarantees and official documentation

**Implementation**:
- Primary: Alpha Vantage API for production
- Fallback: yfinance library for development and testing
- Update frequency: **15-minute intervals** (aligns with Alpha Vantage free tier rate limits)

### 2. Update Frequency Resolution

**Decision**: 15-minute scheduled updates for MVP

**Rationale**:
- User clarified that real-time streaming is not required
- 15-minute updates provide current portfolio values without overwhelming API quotas
- During market hours: Every 15 minutes
- After hours: Every hour
- Weekends: Daily update to catch any corporate actions

**Performance**: With 500 daily requests and ~100 unique stocks, this allows 5 updates per stock per day, perfect for 15-minute intervals during 6.5-hour trading day.

### 3. WebSocket vs Polling Architecture

**Decision**: Server-sent Events (SSE) with scheduled backend updates

**Rationale**:
- **Not WebSocket**: Bi-directional communication not needed
- **Not Direct Polling**: Would overwhelm frontend with API calls
- **SSE Chosen**: Perfect for one-way server-to-client updates
- **Architecture**: Backend scheduler fetches prices → broadcasts via SSE to connected clients

**Benefits**:
- Simpler than WebSocket (no connection management complexity)
- Automatic reconnection built into EventSource API
- Works through firewalls and proxies better than WebSocket
- Single API quota shared across all users

### 4. Portfolio Calculation Strategy

**Decision**: Incremental calculation with Redis caching

**Rationale**:
- Calculate portfolio values only when underlying prices change
- Cache calculated values in Redis with 15-minute TTL
- Invalidate specific portfolio caches when constituent stock prices update
- Batch process multiple price updates to avoid calculation thrashing

**Memory Optimization**: Use materialized views for complex portfolio aggregations, refresh every 15 minutes.

### 5. Connection Resilience Approach

**Decision**: Simplified resilience for periodic updates

**Rationale**:
- With 15-minute updates, connection failures are less critical
- EventSource has built-in reconnection with exponential backoff
- Frontend shows "last updated" timestamp and staleness indicators
- Graceful degradation: Fall back to manual refresh if SSE fails

### 6. Implementation Architecture

**Simplified Architecture**:
```
┌─────────────────┐    15min     ┌─────────────────┐    SSE    ┌─────────────────┐
│   Alpha Vantage │ ◄────────────┤  Backend Cron   │ ──────────► │   Frontend UI   │
│      API        │              │   Job Runner    │           │   (EventSource) │
└─────────────────┘              └─────────────────┘           └─────────────────┘
                                          │
                                    ┌─────▼─────┐
                                    │   Redis   │
                                    │   Cache   │
                                    └───────────┘
```

## Resolved Clarifications

### Original NEEDS CLARIFICATION Items:

1. **✅ Update frequency not defined** 
   → **RESOLVED**: 15-minute intervals during market hours, hourly after hours

2. **✅ Acceptable delay for portfolio updates**
   → **RESOLVED**: 15-minute maximum staleness acceptable for MVP

3. **✅ Update interval not specified**
   → **RESOLVED**: 15-minute intervals chosen based on API rate limits and user requirements

## Technical Decisions Summary

| Aspect | Decision | Alternative Considered |
|--------|----------|----------------------|
| **Data Source** | Alpha Vantage (production), yfinance (development) | Yahoo Finance unofficial API |
| **Architecture** | SSE with scheduled updates | WebSocket real-time streaming |
| **Update Frequency** | 15 minutes (market hours), 1 hour (after hours) | Real-time streaming, 1-minute polling |
| **Calculation Strategy** | Incremental with Redis caching | Real-time calculation, batch processing |
| **Resilience Pattern** | EventSource auto-reconnect + staleness indicators | Complex WebSocket resilience |
| **Fallback Strategy** | Manual refresh button | Multiple transport fallbacks |

## Implementation Benefits

1. **Simplified Development**: No complex WebSocket state management
2. **Cost Effective**: Stays within free API quotas
3. **Reliable**: Official APIs with SLA guarantees
4. **Scalable**: Single backend fetches data for all users
5. **User-Friendly**: Clear staleness indicators and manual refresh option
6. **Maintainable**: Standard REST + SSE patterns, well-documented

## Risk Mitigation

1. **API Rate Limits**: Alpha Vantage provides 500 requests/day, sufficient for 15-minute updates
2. **Market Data Delays**: Users understand 15-minute delay acceptable for portfolio tracking
3. **Connection Issues**: EventSource provides automatic reconnection, manual refresh as fallback
4. **Data Accuracy**: Official APIs reduce risk of data corruption or service interruption
5. **Scalability**: Current architecture supports up to 50 concurrent users with single API key

## Next Steps

This research resolves all ambiguities from the specification. The system is ready for Phase 1: Design & Contracts with the simplified scheduled update architecture.

---
*Research completed: 2025-09-13 | All NEEDS CLARIFICATION items resolved*
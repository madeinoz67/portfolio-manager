# Quick Start: Real-Time Market Data Integration

**Branch**: `002-add-real-time` | **Date**: 2025-09-13 | **Spec**: [spec.md](./spec.md)

## Overview

This feature adds scheduled market data updates (every 15 minutes) with Server-Sent Events to provide users with current portfolio values without manual refresh. Updates are pushed to the frontend automatically while users view their portfolios.

## Key Benefits

- **Automatic Updates**: Portfolio values update every 15 minutes during market hours
- **Real-time UI**: Changes appear in the UI without page refresh
- **Cost Effective**: Uses free Alpha Vantage API tier (500 requests/day)
- **Simple Architecture**: SSE-based updates, no complex WebSocket management
- **Reliable**: Official market data APIs with fallback to development sources

## Architecture

```
Alpha Vantage API → Backend Scheduler → SSE Stream → Frontend UI
     ↓               ↓                   ↓           ↓
  (15min)        (Redis Cache)       (EventSource) (Auto Update)
```

## Quick Demo

### 1. Start the Services

```bash
# Backend with market data scheduler
cd backend
uv run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload

# Frontend with SSE connection
cd frontend  
npm run dev
```

### 2. View Real-time Updates

1. **Open Portfolio Page**: Navigate to `/portfolios/[id]`
2. **Connection Indicator**: Look for "Live" indicator in top-right
3. **Automatic Updates**: Portfolio values update every 15 minutes
4. **Manual Refresh**: Click refresh icon to force immediate update

### 3. Monitor via API

```bash
# Check market data status
curl -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:8001/api/v1/market-data/status

# Get current prices
curl -H "Authorization: Bearer $JWT_TOKEN" \
  "http://localhost:8001/api/v1/market-data/prices?symbols=CBA.AX,BHP.AX"

# Connect to SSE stream
curl -H "Authorization: Bearer $JWT_TOKEN" \
  "http://localhost:8001/api/v1/market-data/stream?portfolio_ids=your-portfolio-id"
```

## Implementation Steps

### Phase 1: Backend Setup (2-3 hours)

1. **Install Dependencies**:
   ```bash
   cd backend
   uv add requests python-dotenv apscheduler redis
   ```

2. **Environment Configuration**:
   ```bash
   # Add to .env
   ALPHA_VANTAGE_API_KEY=your_key_here
   REDIS_URL=redis://localhost:6379
   MARKET_UPDATE_INTERVAL=15  # minutes
   ```

3. **Database Migration**:
   ```bash
   # Apply schema changes from data-model.md
   alembic revision --autogenerate -m "Add market data tables"
   alembic upgrade head
   ```

### Phase 2: Core Services (4-5 hours)

1. **Market Data Service** (`src/services/market_data_service.py`):
   - Alpha Vantage API integration
   - Price fetching and validation
   - Redis caching with TTL

2. **Scheduler Service** (`src/services/scheduler_service.py`):
   - APScheduler for 15-minute intervals
   - Market hours detection
   - Error handling and retry logic

3. **SSE Endpoint** (`src/api/market_data.py`):
   - EventSource connection management
   - Portfolio subscription handling
   - Heartbeat and status messages

### Phase 3: Frontend Integration (2-3 hours)

1. **SSE Hook** (`src/hooks/useMarketDataStream.ts`):
   - EventSource connection with auto-reconnect
   - Portfolio value state management
   - Connection status indicators

2. **UI Updates** (Portfolio components):
   - Real-time value display
   - Connection status indicator
   - Manual refresh button
   - Staleness warnings

### Phase 4: Testing & Polish (2-3 hours)

1. **Unit Tests**:
   - Market data fetching
   - Price calculation accuracy
   - SSE message formatting

2. **Integration Tests**:
   - End-to-end price update flow
   - Portfolio value recalculation
   - Frontend SSE connection

## Key Files to Modify

### Backend Files
```
backend/src/
├── services/
│   ├── market_data_service.py    # NEW: Alpha Vantage integration
│   ├── scheduler_service.py      # NEW: Update scheduling
│   └── portfolio_service.py      # MODIFY: Add real-time calculations
├── api/
│   └── market_data.py           # NEW: SSE endpoints
├── models/
│   ├── market_data.py           # NEW: Data provider models
│   └── stock.py                 # MODIFY: Add current_price fields
└── main.py                      # MODIFY: Add scheduler startup
```

### Frontend Files
```
frontend/src/
├── hooks/
│   ├── useMarketDataStream.ts   # NEW: SSE connection hook
│   └── useMarketData.ts         # MODIFY: Integrate SSE updates
├── components/
│   ├── Portfolio/
│   │   ├── PortfolioValue.tsx   # MODIFY: Real-time display
│   │   └── ConnectionStatus.tsx # NEW: Connection indicator
│   └── ui/
│       └── RealtimeIndicator.tsx # NEW: Live/stale indicator
└── types/
    └── marketData.ts            # MODIFY: Add SSE event types
```

## Configuration

### Development Setup

```bash
# Backend environment
ALPHA_VANTAGE_API_KEY=demo  # Use demo key for development
MARKET_DATA_PROVIDER=yfinance  # Fallback for development
UPDATE_INTERVAL_MINUTES=15
CACHE_TTL_MINUTES=20

# Frontend environment  
NEXT_PUBLIC_SSE_URL=http://localhost:8001/api/v1/market-data/stream
NEXT_PUBLIC_MARKET_DATA_URL=http://localhost:8001/api/v1/market-data
```

### Production Setup

```bash
# Backend environment
ALPHA_VANTAGE_API_KEY=your_production_key
MARKET_DATA_PROVIDER=alpha_vantage
REDIS_URL=redis://production-redis:6379
UPDATE_INTERVAL_MINUTES=15
RATE_LIMIT_ENABLED=true

# Frontend environment
NEXT_PUBLIC_SSE_URL=https://api.yourdomain.com/api/v1/market-data/stream
NEXT_PUBLIC_MARKET_DATA_URL=https://api.yourdomain.com/api/v1/market-data
```

## Testing the Integration

### Manual Testing Checklist

- [ ] **Backend scheduler runs**: Check logs for price update jobs
- [ ] **Prices are fetched**: Verify `stocks.current_price` is populated
- [ ] **SSE connection works**: Browser EventSource connects successfully
- [ ] **Portfolio values update**: Frontend shows new values automatically
- [ ] **Connection resilience**: SSE reconnects after network interruption
- [ ] **Rate limiting**: Manual refresh respects 1-minute cooldown
- [ ] **Error handling**: Graceful degradation when API is unavailable

### API Testing

```bash
# Test SSE connection
curl -N -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/v1/market-data/stream?portfolio_ids=test-id"

# Expected output:
# event: heartbeat
# data: {"type":"heartbeat","data":{"status":"connected","server_time":"2025-09-13T10:30:00Z","next_update_in":870}}
#
# event: portfolio_update  
# data: {"type":"portfolio_update","data":{"portfolio_id":"test-id","total_value":"15750.25",...}}
```

## Troubleshooting

### Common Issues

1. **SSE Connection Fails**:
   - Check JWT token is valid
   - Verify CORS settings for EventSource
   - Confirm portfolio access permissions

2. **No Price Updates**:
   - Check Alpha Vantage API key and quota
   - Verify scheduler is running
   - Check Redis cache connectivity

3. **Stale Data Warnings**:
   - Normal during market close or weekends
   - Check if market hours detection is correct
   - Verify timezone configuration

4. **High API Usage**:
   - Monitor `requests_used_today` in provider status
   - Increase cache TTL if needed
   - Consider upgrading Alpha Vantage plan

## Performance Expectations

- **Update Frequency**: Every 15 minutes during market hours (9:30 AM - 4:00 PM AEST)
- **Data Latency**: 0-15 minutes maximum staleness
- **API Usage**: ~32 requests per day per unique stock (within 500 daily limit)
- **Memory Usage**: ~50MB additional for Redis cache
- **Connection Overhead**: ~1KB/minute per active SSE connection

## Next Steps

After implementing the basic integration:

1. **Enhanced Error Handling**: Implement circuit breaker for API failures
2. **Performance Monitoring**: Add metrics for update success rates
3. **User Preferences**: Allow users to configure update frequency
4. **Historical Charts**: Integrate real-time prices with chart displays
5. **Notifications**: Add alerts for significant portfolio changes

---
*Total implementation time: 10-14 hours over 2-3 days*
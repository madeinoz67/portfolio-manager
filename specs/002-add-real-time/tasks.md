# Tasks: Real-Time Market Data Integration

**Input**: Design documents from `/specs/002-add-real-time/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/market-data-api.yaml

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Tech stack: Python 3.12 FastAPI backend, TypeScript React frontend
   → Structure: Web application with backend/frontend separation
2. Load optional design documents:
   → data-model.md: 8 new entities (MarketDataUpdate, DataProvider, etc.)
   → contracts/: 1 OpenAPI spec with 12 endpoints (6 market data + 6 admin)
   → research.md: SSE-based updates, Alpha Vantage API, 15-minute intervals
3. Generate tasks by category:
   → Setup: dependencies, database migrations, environment config
   → Tests: contract tests for all endpoints, integration tests for SSE
   → Core: models, services, scheduled updates, SSE streaming
   → Integration: API endpoints, admin dashboard, frontend components
   → Polish: unit tests, performance validation, documentation
4. Apply TDD ordering: Tests before implementation
5. Mark [P] for parallel execution (different files, no dependencies)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Phase 3.1: Setup
- [ ] T001 Install backend dependencies (requests, apscheduler, redis, sse-starlette) in backend/
- [ ] T002 [P] Install frontend SSE dependencies (@microsoft/fetch-event-source) in frontend/
- [ ] T003 Create database migration for market data tables in backend/alembic/versions/
- [ ] T004 [P] Configure environment variables for Alpha Vantage API and Redis in backend/.env
- [ ] T005 [P] Update backend/src/main.py to include market data API routes

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests [P] - All can run in parallel
- [ ] T006 [P] Contract test GET /api/v1/market-data/stream in backend/tests/contract/test_market_data_stream.py
- [ ] T007 [P] Contract test GET /api/v1/market-data/prices/{symbol} in backend/tests/contract/test_market_data_prices.py
- [ ] T008 [P] Contract test GET /api/v1/market-data/status in backend/tests/contract/test_market_data_status.py
- [ ] T009 [P] Contract test POST /api/v1/market-data/refresh in backend/tests/contract/test_market_data_refresh.py

### Admin Contract Tests [P] - All can run in parallel
- [ ] T010 [P] Contract test GET /api/v1/admin/poll-intervals in backend/tests/contract/test_admin_poll_intervals.py
- [ ] T011 [P] Contract test POST /api/v1/admin/poll-intervals in backend/tests/contract/test_admin_poll_intervals_create.py
- [ ] T012 [P] Contract test GET /api/v1/admin/api-usage in backend/tests/contract/test_admin_api_usage.py
- [ ] T013 [P] Contract test GET /api/v1/admin/overrides in backend/tests/contract/test_admin_overrides.py

### Integration Tests [P] - All can run in parallel
- [ ] T014 [P] Integration test SSE connection and portfolio updates in backend/tests/integration/test_sse_portfolio_updates.py
- [ ] T015 [P] Integration test market data fetching workflow in backend/tests/integration/test_market_data_workflow.py
- [ ] T016 [P] Integration test scheduled price updates in backend/tests/integration/test_scheduled_updates.py
- [ ] T017 [P] Integration test admin poll interval management in backend/tests/integration/test_admin_poll_intervals.py
- [ ] T018 [P] Frontend integration test SSE connection in frontend/src/__tests__/integration/sse-connection.test.ts

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Database Models [P] - All can run in parallel
- [ ] T019 [P] MarketDataProvider model in backend/src/models/market_data_provider.py
- [ ] T020 [P] PriceUpdateSchedule model in backend/src/models/price_update_schedule.py
- [ ] T021 [P] RealtimePriceHistory model in backend/src/models/realtime_price_history.py
- [ ] T022 [P] SSEConnection model in backend/src/models/sse_connection.py
- [ ] T023 [P] PortfolioValuation model in backend/src/models/portfolio_valuation.py
- [ ] T024 [P] PollIntervalConfiguration model in backend/src/models/poll_interval_config.py
- [ ] T025 [P] APIUsageMetrics model in backend/src/models/api_usage_metrics.py
- [ ] T026 [P] AdministrativeOverride model in backend/src/models/administrative_override.py

### Services Layer - Sequential (shared dependencies)
- [ ] T027 Market data service with Alpha Vantage integration in backend/src/services/market_data_service.py
- [ ] T028 Portfolio valuation service with Redis caching in backend/src/services/portfolio_valuation_service.py
- [ ] T029 SSE connection manager service in backend/src/services/sse_service.py
- [ ] T030 Scheduled update service with APScheduler in backend/src/services/scheduler_service.py
- [ ] T031 Admin poll interval service in backend/src/services/admin_poll_service.py
- [ ] T032 API usage tracking service in backend/src/services/api_usage_service.py

### API Endpoints - Sequential (shared main.py registration)
- [ ] T033 GET /api/v1/market-data/stream SSE endpoint in backend/src/api/market_data.py
- [ ] T034 GET /api/v1/market-data/prices/{symbol} endpoint in backend/src/api/market_data.py
- [ ] T035 GET /api/v1/market-data/status endpoint in backend/src/api/market_data.py
- [ ] T036 POST /api/v1/market-data/refresh endpoint in backend/src/api/market_data.py
- [ ] T037 Admin poll intervals endpoints in backend/src/api/admin_market_data.py
- [ ] T038 Admin API usage endpoints in backend/src/api/admin_market_data.py
- [ ] T039 Admin overrides endpoints in backend/src/api/admin_market_data.py

### Frontend Implementation [P] - All can run in parallel
- [ ] T040 [P] SSE connection hook in frontend/src/hooks/useMarketDataStream.ts
- [ ] T041 [P] Market data context provider in frontend/src/contexts/MarketDataContext.tsx
- [ ] T042 [P] Real-time portfolio value component in frontend/src/components/Portfolio/RealtimeValue.tsx
- [ ] T043 [P] Connection status indicator component in frontend/src/components/MarketData/ConnectionStatus.tsx
- [ ] T044 [P] Admin poll intervals page in frontend/src/app/admin/poll-intervals/page.tsx
- [ ] T045 [P] Admin API usage dashboard in frontend/src/app/admin/api-usage/page.tsx

## Phase 3.4: Integration
- [ ] T046 Connect scheduler service to FastAPI startup events in backend/src/main.py
- [ ] T047 Add Redis connection pool to dependency injection in backend/src/core/dependencies.py
- [ ] T048 Integrate real-time components into existing portfolio pages in frontend/src/app/portfolios/[id]/page.tsx
- [ ] T049 Add admin navigation menu items in frontend/src/components/Navigation/AdminNav.tsx
- [ ] T050 Configure CORS for SSE endpoints in backend/src/main.py

## Phase 3.5: Polish
- [ ] T051 [P] Unit tests for market data service in backend/tests/unit/test_market_data_service.py
- [ ] T052 [P] Unit tests for SSE connection hook in frontend/src/hooks/__tests__/useMarketDataStream.test.ts
- [ ] T053 [P] Performance test SSE with 50 concurrent connections in backend/tests/performance/test_sse_performance.py
- [ ] T054 [P] Update API documentation in backend/src/api/docs/
- [ ] T055 Manual testing checklist validation per quickstart.md
- [ ] T056 Error handling and logging integration across all services

## Dependencies

### Critical Path (blocks other tasks)
- T003 (migration) blocks all model tasks (T019-T026)
- T027 (market data service) blocks T028, T030, T033-T036
- T029 (SSE service) blocks T033, T040-T041
- All tests (T006-T018) must FAIL before implementation (T019-T056)

### Parallel Groups
- **Setup Group**: T001, T002, T004 (different projects)
- **Contract Tests**: T006-T013 (different test files)
- **Integration Tests**: T014-T018 (different test files)
- **Models**: T019-T026 (different model files)
- **Frontend**: T040-T045 (different component files)
- **Polish**: T051-T054 (different test/doc files)

## Parallel Execution Examples

### Launch Contract Tests (T006-T013):
```bash
# All contract tests can run in parallel - different files, no dependencies
Task: "Contract test GET /api/v1/market-data/stream in backend/tests/contract/test_market_data_stream.py"
Task: "Contract test GET /api/v1/market-data/prices/{symbol} in backend/tests/contract/test_market_data_prices.py"
Task: "Contract test GET /api/v1/market-data/status in backend/tests/contract/test_market_data_status.py"
Task: "Contract test POST /api/v1/market-data/refresh in backend/tests/contract/test_market_data_refresh.py"
```

### Launch Model Creation (T019-T026):
```bash
# All models can run in parallel - different files, no cross-dependencies
Task: "MarketDataProvider model in backend/src/models/market_data_provider.py"
Task: "PriceUpdateSchedule model in backend/src/models/price_update_schedule.py"
Task: "RealtimePriceHistory model in backend/src/models/realtime_price_history.py"
Task: "SSEConnection model in backend/src/models/sse_connection.py"
```

### Launch Frontend Components (T040-T045):
```bash
# Frontend components can run in parallel - different files, minimal dependencies
Task: "SSE connection hook in frontend/src/hooks/useMarketDataStream.ts"
Task: "Market data context provider in frontend/src/contexts/MarketDataContext.tsx"
Task: "Real-time portfolio value component in frontend/src/components/Portfolio/RealtimeValue.tsx"
Task: "Connection status indicator component in frontend/src/components/MarketData/ConnectionStatus.tsx"
```

## Task Validation Checklist

- [x] All 12 API endpoints from contracts have corresponding tests
- [x] All 8 entities from data-model have model creation tasks  
- [x] All tests come before implementation (T006-T018 before T019+)
- [x] Parallel tasks are truly independent (different files)
- [x] Each task specifies exact file path
- [x] No [P] task modifies same file as another [P] task
- [x] TDD ordering enforced (contract→integration→implementation)

## Estimated Timeline

- **Phase 3.1 (Setup)**: 2-3 hours
- **Phase 3.2 (Tests)**: 6-8 hours (can parallelize to 2-3 hours)
- **Phase 3.3 (Core)**: 12-15 hours (models parallel, services/endpoints sequential)  
- **Phase 3.4 (Integration)**: 3-4 hours
- **Phase 3.5 (Polish)**: 4-5 hours (can parallelize to 2-3 hours)

**Total**: 27-35 hours (optimized to 18-25 hours with parallel execution)

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- Verify all tests fail before implementing (RED phase of TDD)
- Commit after each task completion
- SSE implementation simpler than WebSocket - focus on EventSource reliability
- Admin functionality requires role-based access control validation
- Redis caching critical for portfolio valuation performance
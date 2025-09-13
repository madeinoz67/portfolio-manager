# Implementation Plan: Real-Time Market Data Integration

**Branch**: `002-add-real-time` | **Date**: 2025-09-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-add-real-time/spec.md`

## Summary
Primary requirement: Enable real-time portfolio value updates through WebSocket streaming using Yahoo Finance free API as initial data source. Technical approach involves creating a market data service with extensible provider architecture, WebSocket server for real-time updates, and frontend integration for live UI updates.

## Technical Context
**Language/Version**: Python 3.12+ (backend), TypeScript/JavaScript (frontend React 19.1.0)  
**Primary Dependencies**: FastAPI 0.116.1, SQLAlchemy 2.0.43, Next.js 15.5.3, WebSockets, Yahoo Finance API client  
**Storage**: Existing SQLite/PostgreSQL with price_history table extensions  
**Testing**: pytest 8.4.2 (backend), Jest 30.1.2 (frontend)  
**Target Platform**: Web application (Linux server backend, browser frontend)
**Project Type**: web (existing frontend + backend structure)  
**Performance Goals**: 15-minute update intervals (market hours), 1-hour intervals (after hours)  
**Constraints**: <2 second update latency, graceful degradation on connection loss, 1-2 concurrent users initially  
**Scale/Scope**: 1-2 simultaneous users initially, extensible to multiple market data providers

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 2 (backend + frontend - existing web app structure)
- Using framework directly? Yes (FastAPI, Next.js without wrappers)
- Single data model? Yes (extending existing models with real-time price data)
- Avoiding patterns? Yes (direct WebSocket implementation, no unnecessary abstractions)

**Architecture**:
- EVERY feature as library? Planning market-data-service library for backend, real-time-client library for frontend
- Libraries listed: 
  - market-data-service: Yahoo Finance API integration, price fetching, WebSocket broadcasting
  - real-time-client: WebSocket connection management, portfolio value calculation, UI updates
- CLI per library: market-data-service supports --start-server, --test-connection; real-time-client supports --connect, --simulate
- Library docs: llms.txt format planned for each library

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? Yes - contract tests first, then implementation
- Git commits show tests before implementation? Will enforce
- Order: Contract→Integration→E2E→Unit strictly followed? Yes
- Real dependencies used? Yes (actual Yahoo Finance API, real WebSocket connections)
- Integration tests for: WebSocket connections, market data fetching, portfolio calculations
- FORBIDDEN: Implementation before test, skipping RED phase

**Observability**:
- Structured logging included? Yes (extending existing logging.py)
- Frontend logs → backend? Yes (WebSocket connection status, errors)
- Error context sufficient? Yes (connection state, data freshness indicators)

**Versioning**:
- Version number assigned? 0.2.0 (MINOR feature addition)
- BUILD increments on every change? Yes
- Breaking changes handled? None anticipated (purely additive feature)

## Project Structure

### Documentation (this feature)
```
specs/002-add-real-time/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 2: Web application (existing structure)
backend/
├── src/
│   ├── models/          # Extend with real-time price models
│   ├── services/        # Add market_data_service.py
│   ├── api/            # Add WebSocket endpoints
│   └── lib/            # Market data libraries
└── tests/
    ├── contract/        # WebSocket and API contract tests
    ├── integration/     # End-to-end real-time data tests
    └── unit/           # Service and model unit tests

frontend/
├── src/
│   ├── components/      # Real-time price display components
│   ├── hooks/          # useRealTimeData hook
│   ├── services/       # WebSocket client service
│   └── lib/            # Real-time client libraries
└── tests/
    ├── integration/     # Real-time UI update tests
    └── unit/           # Component and hook tests
```

**Structure Decision**: Option 2 (Web application) - existing frontend/backend structure

## Phase 0: Outline & Research

1. **Extract unknowns from Technical Context** above:
   - Update frequency specification [NEEDS CLARIFICATION]
   - Yahoo Finance API rate limits and WebSocket capabilities
   - WebSocket implementation patterns for FastAPI
   - Frontend WebSocket integration with React hooks
   - Real-time portfolio calculation strategies

2. **Generate and dispatch research agents**:
   ```
   Task: "Research Yahoo Finance API capabilities and rate limits for real-time data"
   Task: "Find WebSocket implementation best practices for FastAPI applications"
   Task: "Research React hooks patterns for WebSocket real-time data management"
   Task: "Investigate portfolio valuation calculation strategies for real-time updates"
   Task: "Research connection resilience patterns for WebSocket applications"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [Yahoo Finance API approach, WebSocket architecture, update frequency]
   - Rationale: [performance, reliability, cost considerations]
   - Alternatives considered: [other data providers, polling vs WebSocket, calculation approaches]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - MarketPriceUpdate: symbol, price, timestamp, volume, source
   - DataProvider: provider_type, connection_status, last_update
   - RealtimePriceHistory: extends price_history with real-time fields
   - ConnectionStatus: websocket_id, user_id, connected_at, portfolio_ids

2. **Generate API contracts** from functional requirements:
   - WebSocket `/ws/real-time-prices/{portfolio_id}` endpoint
   - GET `/api/v1/market-data/status` for connection health
   - POST `/api/v1/market-data/subscribe/{symbol}` for price subscriptions
   - Output OpenAPI schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - WebSocket connection and message format tests
   - Market data subscription endpoint tests
   - Real-time price update flow tests
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - User views portfolio → receives real-time updates
   - Connection lost → shows stale data indicator
   - Market closed → graceful handling
   - Multiple users → consistent price updates

5. **Update agent file incrementally**:
   - Run `/scripts/update-agent-context.sh claude` to update CLAUDE.md
   - Add WebSocket, Yahoo Finance API, real-time data patterns
   - Preserve existing context, add only new technical context

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs
- Each WebSocket contract → WebSocket integration test task [P]
- Each market data model → model extension task [P]
- Each user story → end-to-end test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Contract tests → Integration tests → Implementation
- Dependency order: Models → Services → WebSocket → Frontend → Integration
- Mark [P] for parallel execution where no dependencies exist

**Estimated Output**: 20-25 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (TDD cycle: RED → GREEN → REFACTOR)  
**Phase 5**: Validation (real-time data tests, performance validation, user acceptance)

## Complexity Tracking
*Constitution check passed - no violations to document*

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) - ✅ 2025-09-13
- [x] Phase 1: Design complete (/plan command) - ✅ 2025-09-13
- [x] Phase 2: Task planning approach documented (/plan command) - ✅ 2025-09-13
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS  
- [x] All NEEDS CLARIFICATION resolved - ✅ 15-minute update frequency clarified
- [x] Complexity deviations documented (none required)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
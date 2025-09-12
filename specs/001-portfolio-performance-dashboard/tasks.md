# Tasks: Multi-Portfolio Performance Dashboard with Email Transaction Processing

**Input**: Design documents from `/specs/001-portfolio-performance-dashboard/`
**Prerequisites**: plan.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

## Execution Summary

Based on implementation plan analysis:
- **Tech Stack**: Python 3.11+ FastAPI + React/Next.js + SQLite
- **Structure**: Web application (backend + frontend)
- **Package Management**: uv for Python dependencies
- **Entities**: 9 core models (User, Portfolio, Stock, Holding, Transaction, etc.)
- **API Endpoints**: 25+ RESTful endpoints across 6 functional areas
- **User Stories**: 6 primary scenarios for MVP validation

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`
- **Root**: Repository root for shared configs

## Phase 3.1: Setup & Project Initialization

- [ ] T001 Create web application project structure (backend/, frontend/, docs/)
- [ ] T002 Initialize Python backend with uv project in backend/pyproject.toml
- [ ] T003 Initialize React frontend with Next.js in frontend/package.json
- [ ] T004 [P] Configure Python linting (ruff, black, mypy) in backend/pyproject.toml
- [ ] T005 [P] Configure TypeScript linting (eslint, prettier) in frontend/.eslintrc.js
- [ ] T006 Setup SQLite database with Alembic in backend/alembic.ini
- [ ] T007 Create FastAPI project structure in backend/src/main.py

## Phase 3.2: Contract Tests (TDD - MUST COMPLETE BEFORE 3.3)
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Authentication Contract Tests
- [ ] T008 [P] Contract test POST /auth/register in backend/tests/contract/test_auth_register.py
- [ ] T009 [P] Contract test POST /auth/login in backend/tests/contract/test_auth_login.py
- [ ] T010 [P] Contract test GET /users/me in backend/tests/contract/test_users_me.py

### Portfolio Contract Tests  
- [ ] T011 [P] Contract test GET /portfolios in backend/tests/contract/test_portfolios_list.py
- [ ] T012 [P] Contract test POST /portfolios in backend/tests/contract/test_portfolios_create.py
- [ ] T013 [P] Contract test GET /portfolios/{id} in backend/tests/contract/test_portfolios_get.py
- [ ] T014 [P] Contract test PUT /portfolios/{id} in backend/tests/contract/test_portfolios_update.py

### Holdings & Transactions Contract Tests
- [ ] T015 [P] Contract test GET /portfolios/{id}/holdings in backend/tests/contract/test_holdings_list.py
- [ ] T016 [P] Contract test GET /portfolios/{id}/transactions in backend/tests/contract/test_transactions_list.py  
- [ ] T017 [P] Contract test POST /portfolios/{id}/transactions in backend/tests/contract/test_transactions_create.py

### Stock & Performance Contract Tests
- [ ] T018 [P] Contract test GET /stocks in backend/tests/contract/test_stocks_search.py
- [ ] T019 [P] Contract test GET /stocks/{symbol} in backend/tests/contract/test_stocks_get.py
- [ ] T020 [P] Contract test GET /portfolios/{id}/performance in backend/tests/contract/test_performance.py

### API Key Management Contract Tests
- [ ] T021 [P] Contract test GET /users/me/api-keys in backend/tests/contract/test_api_keys_list.py
- [ ] T022 [P] Contract test POST /users/me/api-keys in backend/tests/contract/test_api_keys_create.py

## Phase 3.3: Integration Tests (User Stories)
**CRITICAL: Integration tests must also be written and fail before implementation**

- [ ] T023 [P] Integration test user registration flow in backend/tests/integration/test_user_registration.py
- [ ] T024 [P] Integration test portfolio creation and management in backend/tests/integration/test_portfolio_management.py  
- [ ] T025 [P] Integration test manual transaction entry in backend/tests/integration/test_transaction_entry.py
- [ ] T026 [P] Integration test stock information retrieval in backend/tests/integration/test_stock_information.py
- [ ] T027 [P] Integration test portfolio performance calculation in backend/tests/integration/test_performance_calculation.py
- [ ] T028 [P] Integration test API key generation and usage in backend/tests/integration/test_api_key_usage.py

## Phase 3.4: Core Data Models (ONLY after contract tests are failing)

- [ ] T029 [P] User model with authentication in backend/src/models/user.py
- [ ] T030 [P] Portfolio model with validations in backend/src/models/portfolio.py
- [ ] T031 [P] Stock model with price tracking in backend/src/models/stock.py
- [ ] T032 [P] Holding model with calculations in backend/src/models/holding.py
- [ ] T033 [P] Transaction model with validation in backend/src/models/transaction.py
- [ ] T034 [P] Dividend Payment model in backend/src/models/dividend_payment.py
- [ ] T035 [P] Price History model in backend/src/models/price_history.py
- [ ] T036 [P] API Key model in backend/src/models/api_key.py
- [ ] T037 [P] Email Processing Log model in backend/src/models/email_processing_log.py

## Phase 3.5: Database Schema & Migrations

- [ ] T038 Create SQLite database schema migration in backend/alembic/versions/001_initial_schema.py
- [ ] T039 Database connection and session management in backend/src/database.py
- [ ] T040 Model relationships and foreign key constraints in backend/src/models/__init__.py

## Phase 3.6: Authentication System

- [ ] T041 JWT authentication service in backend/src/services/auth_service.py
- [ ] T042 Password hashing utilities in backend/src/utils/security.py
- [ ] T043 Authentication middleware in backend/src/middleware/auth.py
- [ ] T044 API key authentication in backend/src/middleware/api_key.py

## Phase 3.7: Core Business Services

- [ ] T045 [P] User management service in backend/src/services/user_service.py
- [ ] T046 [P] Portfolio CRUD service in backend/src/services/portfolio_service.py
- [ ] T047 [P] Stock data service in backend/src/services/stock_service.py
- [ ] T048 [P] Transaction processing service in backend/src/services/transaction_service.py
- [ ] T049 [P] Holdings calculation service in backend/src/services/holdings_service.py
- [ ] T050 [P] Performance metrics service in backend/src/services/performance_service.py
- [ ] T051 [P] API key management service in backend/src/services/api_key_service.py

## Phase 3.8: API Endpoints Implementation

### Authentication Endpoints
- [ ] T052 POST /auth/register endpoint in backend/src/api/auth.py
- [ ] T053 POST /auth/login endpoint in backend/src/api/auth.py
- [ ] T054 GET /users/me endpoint in backend/src/api/users.py  
- [ ] T055 PUT /users/me endpoint in backend/src/api/users.py

### Portfolio Endpoints
- [ ] T056 GET /portfolios endpoint in backend/src/api/portfolios.py
- [ ] T057 POST /portfolios endpoint in backend/src/api/portfolios.py
- [ ] T058 GET /portfolios/{id} endpoint in backend/src/api/portfolios.py
- [ ] T059 PUT /portfolios/{id} endpoint in backend/src/api/portfolios.py
- [ ] T060 DELETE /portfolios/{id} endpoint in backend/src/api/portfolios.py

### Holdings & Transactions Endpoints
- [ ] T061 GET /portfolios/{id}/holdings endpoint in backend/src/api/holdings.py
- [ ] T062 GET /portfolios/{id}/transactions endpoint in backend/src/api/transactions.py
- [ ] T063 POST /portfolios/{id}/transactions endpoint in backend/src/api/transactions.py

### Stock Information Endpoints
- [ ] T064 GET /stocks search endpoint in backend/src/api/stocks.py
- [ ] T065 GET /stocks/{symbol} endpoint in backend/src/api/stocks.py
- [ ] T066 GET /stocks/{symbol}/price-history endpoint in backend/src/api/stocks.py

### Performance & API Key Endpoints
- [ ] T067 GET /portfolios/{id}/performance endpoint in backend/src/api/performance.py
- [ ] T068 GET /users/me/api-keys endpoint in backend/src/api/api_keys.py
- [ ] T069 POST /users/me/api-keys endpoint in backend/src/api/api_keys.py

## Phase 3.9: Frontend Core Components

- [ ] T070 [P] Authentication components (Login, Register) in frontend/src/components/Auth/
- [ ] T071 [P] Portfolio dashboard layout in frontend/src/components/Dashboard/PortfolioDashboard.tsx
- [ ] T072 [P] Portfolio list component in frontend/src/components/Portfolio/PortfolioList.tsx
- [ ] T073 [P] Portfolio detail view in frontend/src/components/Portfolio/PortfolioDetail.tsx
- [ ] T074 [P] Transaction entry form in frontend/src/components/Transaction/TransactionForm.tsx
- [ ] T075 [P] Holdings display component in frontend/src/components/Holdings/HoldingsTable.tsx
- [ ] T076 [P] Performance charts with Chart.js in frontend/src/components/Charts/PerformanceChart.tsx
- [ ] T077 [P] Stock search component in frontend/src/components/Stock/StockSearch.tsx

## Phase 3.10: Frontend Services & Integration

- [ ] T078 API client service in frontend/src/services/api.ts
- [ ] T079 Authentication context and hooks in frontend/src/context/AuthContext.tsx
- [ ] T080 Portfolio state management in frontend/src/context/PortfolioContext.tsx
- [ ] T081 React Router setup and protected routes in frontend/src/App.tsx

## Phase 3.11: Frontend Pages & Routing

- [ ] T082 Home/Landing page in frontend/src/pages/index.tsx
- [ ] T083 Login page in frontend/src/pages/auth/login.tsx
- [ ] T084 Register page in frontend/src/pages/auth/register.tsx
- [ ] T085 Dashboard page in frontend/src/pages/dashboard.tsx
- [ ] T086 Portfolio detail page in frontend/src/pages/portfolio/[id].tsx
- [ ] T087 Account settings page in frontend/src/pages/account.tsx

## Phase 3.12: Integration & System Tests

- [ ] T088 Backend API integration in backend/src/main.py
- [ ] T089 CORS configuration for frontend in backend/src/middleware/cors.py
- [ ] T090 Error handling and logging in backend/src/middleware/error_handler.py
- [ ] T091 Database seeding script in backend/scripts/seed_data.py

## Phase 3.13: End-to-End Testing

- [ ] T092 [P] E2E test user registration flow in frontend/tests/e2e/test_user_registration.spec.ts
- [ ] T093 [P] E2E test portfolio management in frontend/tests/e2e/test_portfolio_management.spec.ts
- [ ] T094 [P] E2E test transaction entry in frontend/tests/e2e/test_transaction_entry.spec.ts
- [ ] T095 [P] E2E test performance dashboard in frontend/tests/e2e/test_performance_dashboard.spec.ts

## Phase 3.14: Polish & Optimization

- [ ] T096 [P] Unit tests for utility functions in backend/tests/unit/
- [ ] T097 [P] Frontend component unit tests in frontend/tests/unit/
- [ ] T098 Performance optimization and caching in backend/src/middleware/cache.py
- [ ] T099 Responsive design improvements in frontend/src/styles/
- [ ] T100 API documentation generation in backend/docs/
- [ ] T101 Security headers and rate limiting in backend/src/middleware/security.py
- [ ] T102 Frontend build optimization in frontend/next.config.js

## Phase 3.15: MVP Validation

- [ ] T103 Execute quickstart user story 1 (User Registration and Login)
- [ ] T104 Execute quickstart user story 2 (Create and Manage Portfolio)
- [ ] T105 Execute quickstart user story 3 (Add Manual Transaction)
- [ ] T106 Execute quickstart user story 4 (View Stock Information)
- [ ] T107 Execute quickstart user story 5 (View Portfolio Performance)
- [ ] T108 Execute quickstart user story 6 (API Key Management)

## Dependencies

**Critical TDD Dependencies**:
- Contract Tests (T008-T022) MUST complete and FAIL before Models (T029-T037)
- Integration Tests (T023-T028) MUST complete and FAIL before Services (T045-T051)
- All tests MUST fail before implementation begins

**Sequential Dependencies**:
- T001-T007 (Setup) → All other tasks
- T038-T040 (Database) → T041-T051 (Services)
- T041-T044 (Auth) → T052-T069 (API endpoints)
- T045-T051 (Services) → T052-T069 (API endpoints)
- T078-T081 (Frontend services) → T082-T087 (Frontend pages)
- T052-T069 (Backend APIs) → T088-T091 (Integration)
- All implementation → T092-T095 (E2E tests)
- T103-T108 (Validation) must be last

**Parallel Groups** (can run simultaneously):
- Contract Tests: T008-T022
- Integration Tests: T023-T028
- Models: T029-T037 (after contract tests fail)
- Services: T045-T051 (after integration tests fail)
- Frontend Components: T070-T077
- E2E Tests: T092-T095
- Polish: T096-T102

## Parallel Execution Examples

```bash
# Phase 3.2 - Launch contract tests together (MUST fail):
Task: "Contract test POST /auth/register in backend/tests/contract/test_auth_register.py"
Task: "Contract test POST /auth/login in backend/tests/contract/test_auth_login.py" 
Task: "Contract test GET /users/me in backend/tests/contract/test_users_me.py"
Task: "Contract test GET /portfolios in backend/tests/contract/test_portfolios_list.py"

# Phase 3.4 - Launch model creation together (after tests fail):
Task: "User model with authentication in backend/src/models/user.py"
Task: "Portfolio model with validations in backend/src/models/portfolio.py"
Task: "Stock model with price tracking in backend/src/models/stock.py"
Task: "Transaction model with validation in backend/src/models/transaction.py"

# Phase 3.9 - Launch frontend components together:
Task: "Authentication components (Login, Register) in frontend/src/components/Auth/"
Task: "Portfolio dashboard layout in frontend/src/components/Dashboard/PortfolioDashboard.tsx"
Task: "Transaction entry form in frontend/src/components/Transaction/TransactionForm.tsx"
```

## Validation Checklist
*GATE: All items must be checked before MVP completion*

- [x] All contracts have corresponding tests (T008-T022)
- [x] All entities have model tasks (T029-T037)
- [x] All tests come before implementation (TDD enforced)
- [x] Parallel tasks truly independent (different files/modules)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] User stories have validation tasks (T103-T108)
- [x] MVP scope maintained (no email processing, price updates, AI in this phase)

## Notes

- **MVP Focus**: Core portfolio management, manual transactions, basic performance metrics
- **TDD Mandatory**: Red-Green-Refactor cycle strictly enforced
- **uv Usage**: All Python dependency management through uv commands
- **SQLite**: Database starts simple, PostgreSQL upgrade path planned
- **Testing**: Contract → Integration → E2E → Unit test coverage
- **Commit Strategy**: Commit after each task completion
- **Path Consistency**: All paths relative to repository root
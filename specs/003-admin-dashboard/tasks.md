# Tasks: Admin Dashboard

**Input**: Design documents from `/specs/003-admin-dashboard/`
**Prerequisites**: research.md, data-model.md, contracts/admin-api.openapi.yaml, quickstart.md

## Execution Flow
Based on analysis of design documents:
1. **Backend**: ✅ Complete - Admin APIs functional, role-based auth implemented
2. **Frontend**: ❌ Required - Role awareness, admin routes, UI components
3. **Tech Stack**: Next.js 15.5.3, TypeScript, Tailwind CSS (existing)
4. **Contracts**: 4 admin API endpoints defined and working
5. **Integration**: Frontend-backend integration for admin workflows

## Phase 3.1: Setup
- [ ] T001 Verify backend admin API functionality and role enforcement
- [ ] T002 [P] Set up frontend TypeScript types for admin data models

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T003 [P] Contract test GET /api/v1/admin/users in backend/tests/contract/test_admin_users_list.py
- [ ] T004 [P] Contract test GET /api/v1/admin/users/{user_id} in backend/tests/contract/test_admin_users_detail.py
- [ ] T005 [P] Contract test GET /api/v1/admin/system/metrics in backend/tests/contract/test_admin_system_metrics.py
- [ ] T006 [P] Contract test GET /api/v1/admin/market-data/status in backend/tests/contract/test_admin_market_data_status.py
- [ ] T007 [P] Integration test admin authentication flow in frontend/src/__tests__/integration/admin-auth.test.tsx
- [ ] T008 [P] Integration test admin user management workflow in frontend/src/__tests__/integration/admin-user-management.test.tsx
- [ ] T009 [P] Integration test admin dashboard overview in frontend/src/__tests__/integration/admin-dashboard.test.tsx

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T010 [P] Extend User interface with role field in frontend/src/types/auth.ts
- [ ] T011 [P] Add AdminUserListItem and SystemMetrics types in frontend/src/types/admin.ts
- [ ] T012 [P] Add MarketDataStatus interface in frontend/src/types/admin.ts
- [ ] T013 Extend AuthContext with role utilities in frontend/src/contexts/AuthContext.tsx
- [ ] T014 [P] Create admin API service functions in frontend/src/services/adminService.ts
- [ ] T015 [P] Create AdminRoute guard component in frontend/src/components/auth/AdminRoute.tsx
- [ ] T016 [P] Create admin layout component in frontend/src/components/admin/AdminLayout.tsx
- [ ] T017 Create admin dashboard page in frontend/src/app/admin/page.tsx
- [ ] T018 Create admin users list page in frontend/src/app/admin/users/page.tsx
- [ ] T019 Create admin user detail page in frontend/src/app/admin/users/[id]/page.tsx
- [ ] T020 Create admin system page in frontend/src/app/admin/system/page.tsx

## Phase 3.4: UI Components
- [ ] T021 [P] Create SystemMetricsCard component in frontend/src/components/admin/SystemMetricsCard.tsx
- [ ] T022 [P] Create UserManagementTable component in frontend/src/components/admin/UserManagementTable.tsx
- [ ] T023 [P] Create UserDetailView component in frontend/src/components/admin/UserDetailView.tsx
- [ ] T024 [P] Create MarketDataStatusTable component in frontend/src/components/admin/MarketDataStatusTable.tsx
- [ ] T025 Update main navigation with conditional admin menu items in frontend/src/components/layout/Navigation.tsx

## Phase 3.5: Integration & Polish
- [ ] T026 Connect admin pages to API services with error handling
- [ ] T027 Add loading states and error boundaries for admin components
- [ ] T028 Implement role-based conditional rendering throughout app
- [ ] T029 [P] Unit tests for admin utility functions in frontend/src/__tests__/unit/admin-utils.test.ts
- [ ] T030 [P] Unit tests for admin components in frontend/src/__tests__/unit/admin-components.test.ts
- [ ] T031 Execute complete quickstart test scenarios from quickstart.md
- [ ] T032 Performance optimization for admin data loading and caching

## Dependencies
- Tests (T003-T009) before implementation (T010-T020)
- T010-T012 (types) before T013 (AuthContext)
- T013 (AuthContext) before T015 (AdminRoute)
- T014 (API service) before T017-T020 (pages)
- T015-T016 (guards/layout) before T017-T020 (pages)
- T017-T020 (pages) before T021-T025 (components)
- Implementation before integration (T026-T028)
- Integration before polish (T029-T032)

## Parallel Execution Examples

### Contract Tests (T003-T006)
```bash
# Launch backend contract tests together:
Task: "Contract test GET /api/v1/admin/users in backend/tests/contract/test_admin_users_list.py"
Task: "Contract test GET /api/v1/admin/users/{user_id} in backend/tests/contract/test_admin_users_detail.py"
Task: "Contract test GET /api/v1/admin/system/metrics in backend/tests/contract/test_admin_system_metrics.py"
Task: "Contract test GET /api/v1/admin/market-data/status in backend/tests/contract/test_admin_market_data_status.py"
```

### Frontend Integration Tests (T007-T009)
```bash
# Launch frontend integration tests together:
Task: "Integration test admin authentication flow in frontend/src/__tests__/integration/admin-auth.test.tsx"
Task: "Integration test admin user management workflow in frontend/src/__tests__/integration/admin-user-management.test.tsx"
Task: "Integration test admin dashboard overview in frontend/src/__tests__/integration/admin-dashboard.test.tsx"
```

### TypeScript Types (T010-T012)
```bash
# Launch type definitions together:
Task: "Extend User interface with role field in frontend/src/types/auth.ts"
Task: "Add AdminUserListItem and SystemMetrics types in frontend/src/types/admin.ts"
Task: "Add MarketDataStatus interface in frontend/src/types/admin.ts"
```

### UI Components (T021-T024)
```bash
# Launch admin UI components together:
Task: "Create SystemMetricsCard component in frontend/src/components/admin/SystemMetricsCard.tsx"
Task: "Create UserManagementTable component in frontend/src/components/admin/UserManagementTable.tsx"
Task: "Create UserDetailView component in frontend/src/components/admin/UserDetailView.tsx"
Task: "Create MarketDataStatusTable component in frontend/src/components/admin/MarketDataStatusTable.tsx"
```

## Key Implementation Notes

### Backend Status ✅ COMPLETE
- User roles (ADMIN/USER) implemented in UserRole enum
- Admin authentication working via get_current_admin_user() dependency
- All 4 admin API endpoints functional: users list, user detail, system metrics, market data status
- Role-based access control enforced at API level
- No backend changes required

### Frontend Requirements ❌ IMPLEMENTATION NEEDED
- **Role Awareness**: Extend AuthContext to include user role from JWT
- **Route Protection**: Admin-only routes using role-based guards
- **Navigation**: Conditional admin menu items based on user role
- **Admin Pages**: Dashboard, user management, system monitoring
- **UI Components**: Tables, cards, status indicators for admin data
- **Integration**: Connect frontend to existing admin APIs

### Security Architecture
- **Backend**: Role enforcement via JWT validation and admin dependencies
- **Frontend**: Role-based conditional rendering (not security boundary)
- **Database**: User roles properly stored and validated
- **API**: All admin endpoints require authenticated admin role

### Test Coverage Requirements
- Contract tests for all 4 admin API endpoints
- Integration tests for complete admin workflows
- Unit tests for role utilities and admin components
- End-to-end validation using quickstart scenarios

## Validation Checklist
*GATE: Verified before task execution*

- [x] All contracts have corresponding tests (T003-T006)
- [x] All entities have type definitions (T010-T012)
- [x] All tests come before implementation (T003-T009 before T010+)
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Admin authentication flow thoroughly tested
- [x] Role-based access control validated at all levels
# Tasks: Portfolio Tile/Table View Toggle

**Input**: Design documents from `/specs/004-user-portfolio-list/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory ✓
   → Tech stack: TypeScript 5.x, React 19.1.0, Next.js 15.5.3, Tailwind CSS
   → Structure: Web app (frontend/backend)
   → Scope: Frontend-only enhancement
2. Load optional design documents ✓
   → data-model.md: ViewMode, PortfolioViewState, TableConfig entities
   → contracts/: ViewToggle, PortfolioTable, usePortfolioView contracts
   → research.md: Responsive table patterns, state management decisions
3. Generate tasks by category ✓
   → Setup: TypeScript types, component structure
   → Tests: Component contracts, integration scenarios
   → Core: Hook implementation, component development
   → Integration: Page integration, responsive behavior
   → Polish: Performance, accessibility, documentation
4. Apply task rules ✓
   → Different files = [P] for parallel
   → Same file = sequential
   → Tests before implementation (TDD)
5. Number tasks sequentially T001-T025 ✓
6. Generate dependency graph ✓
7. Create parallel execution examples ✓
8. Validate task completeness ✓
   → All contracts have tests ✓
   → All entities have type definitions ✓
   → All components implemented ✓
9. Return: SUCCESS (tasks ready for execution) ✓
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: `frontend/src/`, `frontend/src/__tests__/`
- All paths relative to repository root

## Phase 3.1: Setup
- [ ] **T001** Create TypeScript type definitions in `frontend/src/types/portfolioView.ts`
- [ ] **T002** [P] Set up test utilities for portfolio view components in `frontend/src/__tests__/utils/portfolioViewTestUtils.ts`

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] **T003** [P] Contract test for ViewToggle component in `frontend/src/__tests__/components/Portfolio/ViewToggle.test.tsx`
- [ ] **T004** [P] Contract test for PortfolioTable component in `frontend/src/__tests__/components/Portfolio/PortfolioTable.test.tsx`
- [ ] **T005** [P] Contract test for usePortfolioView hook in `frontend/src/__tests__/hooks/usePortfolioView.test.ts`
- [ ] **T006** [P] Integration test for view toggle functionality in `frontend/src/__tests__/integration/portfolioViewToggle.test.tsx`
- [ ] **T007** [P] Integration test for table responsive behavior in `frontend/src/__tests__/integration/portfolioTableResponsive.test.tsx`
- [ ] **T008** [P] Integration test for view persistence in `frontend/src/__tests__/integration/portfolioViewPersistence.test.tsx`

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] **T009** [P] Implement ViewMode and PortfolioViewState types in `frontend/src/types/portfolioView.ts`
- [ ] **T010** [P] Create usePortfolioView hook with localStorage persistence in `frontend/src/hooks/usePortfolioView.ts`
- [ ] **T011** [P] Implement ViewToggle component with accessibility in `frontend/src/components/Portfolio/ViewToggle.tsx`
- [ ] **T012** [P] Create TableColumn configuration utilities in `frontend/src/utils/tableColumns.ts`
- [ ] **T013** [P] Implement PortfolioTable component with sorting in `frontend/src/components/Portfolio/PortfolioTable.tsx`
- [ ] **T014** [P] Create PortfolioTableRow component for table rows in `frontend/src/components/Portfolio/PortfolioTableRow.tsx`

## Phase 3.4: Integration
- [ ] **T015** Update portfolios page to use view toggle in `frontend/src/app/portfolios/page.tsx`
- [ ] **T016** Add responsive CSS classes for table layout in existing Tailwind configuration
- [ ] **T017** Integrate view state management with existing search/sort functionality in portfolios page
- [ ] **T018** Add loading states for view transitions in both tile and table modes

## Phase 3.5: Polish
- [ ] **T019** [P] Unit tests for table column utilities in `frontend/src/__tests__/utils/tableColumns.test.ts`
- [ ] **T020** [P] Unit tests for view state persistence logic in `frontend/src/__tests__/utils/portfolioViewPersistence.test.ts`
- [ ] **T021** Performance optimization: Add React.memo to table row components
- [ ] **T022** Accessibility audit: Ensure ARIA roles and keyboard navigation work correctly
- [ ] **T023** [P] Add JSDoc documentation to all new components and hooks
- [ ] **T024** Mobile testing: Verify horizontal scroll and priority columns work on small screens
- [ ] **T025** Execute quickstart guide manual testing scenarios from `specs/004-user-portfolio-list/quickstart.md`

## Dependencies
- Setup (T001-T002) before all tests and implementation
- Tests (T003-T008) before any implementation (T009-T014)
- T009 (types) blocks T010-T014 (components using types)
- T010 (hook) blocks T015 (page integration)
- T012 (table config) blocks T013-T014 (table components)
- Core implementation (T009-T014) before integration (T015-T018)
- Integration (T015-T018) before polish (T019-T025)

## Parallel Execution Examples

### Setup Phase (can run together)
```bash
# T001-T002 can run in parallel:
Task: "Create TypeScript type definitions in frontend/src/types/portfolioView.ts"
Task: "Set up test utilities in frontend/src/__tests__/utils/portfolioViewTestUtils.ts"
```

### Contract Tests Phase (MUST fail before implementation)
```bash
# T003-T008 can run in parallel:
Task: "Contract test for ViewToggle component in frontend/src/__tests__/components/Portfolio/ViewToggle.test.tsx"
Task: "Contract test for PortfolioTable component in frontend/src/__tests__/components/Portfolio/PortfolioTable.test.tsx"
Task: "Contract test for usePortfolioView hook in frontend/src/__tests__/hooks/usePortfolioView.test.ts"
Task: "Integration test for view toggle in frontend/src/__tests__/integration/portfolioViewToggle.test.tsx"
Task: "Integration test for table responsive in frontend/src/__tests__/integration/portfolioTableResponsive.test.tsx"
Task: "Integration test for view persistence in frontend/src/__tests__/integration/portfolioViewPersistence.test.tsx"
```

### Core Implementation Phase (after tests fail)
```bash
# T009-T014 can run in parallel after T009 (types):
# First: T009 (creates types needed by others)
Task: "Implement ViewMode and PortfolioViewState types in frontend/src/types/portfolioView.ts"

# Then T010-T014 in parallel:
Task: "Create usePortfolioView hook in frontend/src/hooks/usePortfolioView.ts"
Task: "Implement ViewToggle component in frontend/src/components/Portfolio/ViewToggle.tsx"
Task: "Create TableColumn utilities in frontend/src/utils/tableColumns.ts"
Task: "Implement PortfolioTable component in frontend/src/components/Portfolio/PortfolioTable.tsx"
Task: "Create PortfolioTableRow component in frontend/src/components/Portfolio/PortfolioTableRow.tsx"
```

### Polish Phase (can run in parallel)
```bash
# T019, T020, T023 can run in parallel:
Task: "Unit tests for table column utilities in frontend/src/__tests__/utils/tableColumns.test.ts"
Task: "Unit tests for view state persistence in frontend/src/__tests__/utils/portfolioViewPersistence.test.ts"
Task: "Add JSDoc documentation to all new components and hooks"
```

## Critical Success Factors

### TDD Compliance ⚠️
1. **Contract tests MUST be written first** (T003-T008)
2. **All tests MUST fail** before writing any implementation code
3. **Tests must be committed** before implementation commits
4. **Green phase**: Implement minimal code to make tests pass
5. **Refactor phase**: Clean up implementation while keeping tests green

### File Organization
- **Types**: Central type definitions in `types/portfolioView.ts`
- **Components**: Portfolio-specific components in `components/Portfolio/`
- **Hooks**: Custom React hooks in `hooks/`
- **Utils**: Pure utility functions in `utils/`
- **Tests**: Mirror source structure in `__tests__/`

### Integration Points
- **Existing portfolios page**: Minimal changes, preserve functionality
- **Current search/sort**: Must work in both tile and table views
- **Responsive design**: Table must work on mobile with horizontal scroll
- **User preferences**: localStorage persistence, no backend changes

## Notes
- [P] tasks target different files with no dependencies
- Verify ALL tests fail before implementing (RED phase)
- Commit after each task completion
- Maintain existing functionality throughout integration
- Focus on component reusability and testability

## Task Generation Rules Applied

1. **From Contracts**:
   - ViewToggle contract → T003 contract test → T011 implementation
   - PortfolioTable contract → T004 contract test → T013 implementation
   - usePortfolioView contract → T005 contract test → T010 implementation

2. **From Data Model**:
   - ViewMode, PortfolioViewState → T001, T009 type definitions
   - TableConfig → T012 utility functions

3. **From User Stories**:
   - View toggle scenarios → T006 integration test
   - Responsive behavior → T007 integration test
   - Persistence → T008 integration test
   - Quickstart validation → T025 manual testing

4. **Ordering Applied**:
   - Setup → Tests → Types → Components → Integration → Polish
   - Dependencies respect TDD cycle and component relationships

## Validation Checklist ✓

- [x] All contracts have corresponding tests (T003-T005)
- [x] All entities have type definition tasks (T001, T009)
- [x] All tests come before implementation (T003-T008 before T009-T014)
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path
- [x] No [P] task modifies same file as another [P] task
- [x] Integration scenarios covered (T006-T008, T015-T018)
- [x] Performance and accessibility addressed (T021-T022, T024)
- [x] Manual validation included (T025)
# Implementation Plan: Portfolio Tile/Table View Toggle

**Branch**: `004-user-portfolio-list` | **Date**: 2025-09-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-user-portfolio-list/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path ✓
   → Feature spec loaded successfully
2. Fill Technical Context (scan for NEEDS CLARIFICATION) ✓
   → Resolved based on user request: "tile and table view of their portfolios"
   → Detected web application (frontend+backend structure)
   → Set Structure Decision: Option 2 (Web application)
3. Evaluate Constitution Check section below ✓
   → No violations found, follows existing patterns
   → Update Progress Tracking: Initial Constitution Check PASS
4. Execute Phase 0 → research.md ✓
   → All NEEDS CLARIFICATION resolved with user context
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md ✓
6. Re-evaluate Constitution Check section ✓
   → No new violations detected
   → Update Progress Tracking: Post-Design Constitution Check PASS
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md) ✓
8. STOP - Ready for /tasks command ✓
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Add tile/table view toggle to portfolio list page, allowing users to switch between current card layout (tiles) and new tabular layout (table) that displays the same portfolio information in a comparative table format with user preference persistence.

## Technical Context
**Language/Version**: TypeScript 5.x, Python 3.12
**Primary Dependencies**: Next.js 15.5.3, React 19.1.0, FastAPI 0.116.1, Tailwind CSS
**Storage**: PostgreSQL (existing portfolios), localStorage (view preferences)
**Testing**: Jest + React Testing Library (frontend), pytest (backend)
**Target Platform**: Web browsers with responsive design
**Project Type**: web - frontend/backend structure detected
**Performance Goals**: <300ms view toggle transitions, smooth animations
**Constraints**: No breaking changes to existing functionality, maintain responsive design
**Scale/Scope**: Frontend-only enhancement, existing portfolio API endpoints

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 2 (frontend, backend) - within limit ✓
- Using framework directly? Yes (React state, Tailwind classes) ✓
- Single data model? Yes (existing Portfolio schema) ✓
- Avoiding patterns? Yes (no unnecessary abstractions) ✓

**Architecture**:
- EVERY feature as library? Frontend components as reusable modules ✓
- Libraries listed: ViewToggle (toggle control), PortfolioTable (table view), usePortfolioView (state hook)
- CLI per library: N/A (frontend components)
- Library docs: JSDoc format with component contracts ✓

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? Yes, TDD approach mandatory ✓
- Git commits show tests before implementation? Will ensure this ✓
- Order: Contract→Integration→E2E→Unit strictly followed? Yes ✓
- Real dependencies used? Yes (actual DOM, localStorage) ✓
- Integration tests for: component interactions, view state management ✓
- FORBIDDEN: Implementation before test, skipping RED phase ✓

**Observability**:
- Structured logging included? Console logging for view state changes ✓
- Frontend logs → backend? User interaction events tracked ✓
- Error context sufficient? Component error boundaries ✓

**Versioning**:
- Version number assigned? Will increment BUILD version ✓
- BUILD increments on every change? Yes ✓
- Breaking changes handled? N/A (additive feature) ✓

## Project Structure

### Documentation (this feature)
```
specs/004-user-portfolio-list/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/
```

**Structure Decision**: Option 2 (Web application) - existing frontend/backend detected

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - RESOLVED: Default sort order → By total value (highest first)
   - RESOLVED: Filtering capabilities → Existing search functionality maintained
   - RESOLVED: Holdings summary level → Holdings count with tooltip
   - Research responsive table patterns for financial data
   - Research React state management for view toggles

2. **Generate and dispatch research agents**:
   ```
   Task: "Research responsive table design patterns for portfolio financial data"
   Task: "Find best practices for React view toggle components with accessibility"
   Task: "Research performance optimization for table rendering with large datasets"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: Responsive table with horizontal scroll and priority columns
   - Rationale: Maintains data integrity while supporting mobile devices
   - Alternatives considered: Hidden columns, stacked layouts

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - ViewMode: 'tiles' | 'table' enumeration
   - PortfolioViewState: view preferences container
   - TableColumn: column configuration interface
   - ResponsiveConfig: mobile/tablet behavior rules

2. **Generate API contracts** from functional requirements:
   - Frontend component interfaces (no new backend APIs needed)
   - ViewToggle component props and events
   - PortfolioTable component props and events
   - Hook contracts for usePortfolioView

3. **Generate contract tests** from contracts:
   - Component prop validation tests
   - View toggle interaction tests
   - Table rendering and sorting tests
   - State persistence tests

4. **Extract test scenarios** from user stories:
   - Toggle between tile and table views
   - Preserve existing search/sort functionality
   - Mobile responsive behavior
   - User preference persistence

5. **Update agent file incrementally**:
   - Add view toggle patterns to CLAUDE.md
   - Include responsive table implementation guidance
   - Document state management patterns

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, CLAUDE.md updates

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Component contract tests first (RED phase)
- ViewToggle component implementation
- PortfolioTable component implementation
- usePortfolioView hook implementation
- Integration with existing portfolio page
- Responsive design testing and optimization

**Ordering Strategy**:
- TDD order: Tests → Implementation → Integration
- Dependency order: Hooks → Components → Page integration
- Mark [P] for parallel execution where components are independent

**Estimated Output**: 15-20 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following TDD principles)
**Phase 5**: Validation (run tests, execute quickstart.md scenarios)

## Complexity Tracking
*No constitutional violations detected - feature follows existing patterns*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented

---
*Based on existing project patterns and portfolio management domain requirements*
# Implementation Plan: Market Data Provider Adapters

**Branch**: `005-add-market-data` | **Date**: 2025-09-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-add-market-data/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 8. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Implement a standardized adapter pattern for market data providers with unified metrics tracking, cost monitoring, and extensible architecture. Admin dashboard integration for live monitoring of provider performance, latency, and usage metrics without hard-coded data.

## Technical Context
**Language/Version**: Python 3.12
**Primary Dependencies**: FastAPI 0.116.1, SQLAlchemy 2.0.43, Pydantic
**Storage**: PostgreSQL with Alembic migrations
**Testing**: pytest with contract and integration tests
**Target Platform**: Linux server deployment
**Project Type**: web (backend API + frontend admin dashboard)
**Performance Goals**: <200ms API response time, support 1000+ req/s
**Constraints**: Real-time metrics tracking, no hard-coded data, extensible adapter design
**Scale/Scope**: Multiple provider adapters, admin dashboard integration, metrics persistence

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**I. Test-First Development**: ✅ TDD approach required - contract tests before implementation
**II. Financial Data Integrity**: ✅ Adapters handle cost data with decimal precision, no financial calculations modified
**III. Database Schema Safety**: ✅ New adapter tables via Alembic migrations, no existing data impact
**IV. Market Data Single Source**: ✅ Adapters standardize access to existing realtime_symbols master table
**V. Security and Access Control**: ✅ Admin dashboard uses existing JWT + role-based access

## Project Structure

### Documentation (this feature)
```
specs/005-add-market-data/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 2: Web application (backend + frontend admin dashboard)
backend/
├── src/
│   ├── models/           # Adapter registry, metrics models
│   ├── services/         # Adapter base classes, metrics services
│   └── api/              # Admin adapter management endpoints
└── tests/
    ├── contract/         # Adapter API contract tests
    ├── integration/      # End-to-end adapter tests
    └── unit/             # Adapter unit tests

frontend/
├── src/
│   ├── components/       # Admin dashboard adapter components
│   ├── pages/            # Admin adapter management pages
│   └── services/         # Frontend adapter API services
└── tests/
```

**Structure Decision**: Option 2 (web application) - extends existing backend/frontend structure

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context**:
   - No NEEDS CLARIFICATION items identified
   - Research adapter pattern best practices for Python/FastAPI
   - Research metrics collection patterns for external APIs
   - Research provider configuration management

2. **Generate and dispatch research agents**:
   ```
   Task: "Research adapter pattern implementation in Python for external API wrappers"
   Task: "Find best practices for API metrics collection and storage in FastAPI"
   Task: "Research provider configuration management with dynamic registration"
   Task: "Find patterns for extensible plugin architecture in Python"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with design decisions documented

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Market Data Adapter interface definition
   - Provider Configuration with credentials and limits
   - Provider Metrics with real-time performance data
   - Cost Tracking for usage monitoring
   - Adapter Registry for dynamic management

2. **Generate API contracts** from functional requirements:
   - GET /api/v1/admin/adapters - List configured adapters
   - POST /api/v1/admin/adapters - Register new adapter
   - GET /api/v1/admin/adapters/{id}/metrics - Get live metrics
   - PUT /api/v1/admin/adapters/{id} - Update adapter config
   - DELETE /api/v1/admin/adapters/{id} - Remove adapter
   - Output OpenAPI schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Admin configures new provider scenario
   - Dashboard displays live metrics scenario
   - Provider failure handling scenario
   - Quickstart test = admin workflow validation

5. **Update agent file incrementally**:
   - Update CLAUDE.md with adapter pattern decisions
   - Add metrics tracking requirements
   - Document admin dashboard extensions

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, updated CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each adapter API endpoint → contract test task [P]
- Each entity (AdapterRegistry, Metrics, etc.) → model creation task [P]
- Admin dashboard integration → frontend component tasks
- Adapter base class and concrete implementations → service tasks

**Ordering Strategy**:
- TDD order: Contract tests → Models → Services → API endpoints → Frontend
- Dependency order: Base adapter → Concrete adapters → Metrics → Dashboard
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 20-25 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*No constitutional violations identified - adapter pattern aligns with existing architecture*

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
*Based on Constitution v1.0.0 - See `/memory/constitution.md`*
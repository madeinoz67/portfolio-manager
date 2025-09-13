# Implementation Plan: Multi-Portfolio Performance Dashboard with Email Transaction Processing

**Branch**: `001-portfolio-performance-dashboard` | **Date**: 2025-09-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-portfolio-performance-dashboard/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, or `GEMINI.md` for Gemini CLI).
6. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
8. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Intelligent share portfolio management system with multi-user collaboration, automated email transaction processing, AI-powered analysis, and comprehensive performance dashboards. The system monitors broker emails, processes transactions, tracks daily price updates, manages news archival via paperless-ngx integration, provides portfolio analytics with rebalancing recommendations, and offers RESTful API access with configurable AI providers (Ollama, OpenAI, etc.) for extensible agentic workflows.

## Technical Context
**Language/Version**: Python 3.11+ with FastAPI  
**Primary Dependencies**: FastAPI, SQLAlchemy, React, Next.js, TypeScript, Chart.js  
**Storage**: SQLite (MVP), Redis (optional caching)  
**Testing**: pytest (backend), Jest (frontend), Playwright (E2E)  
**Target Platform**: Web application (Linux server + modern browsers)
**Project Type**: web - determines source structure  
**Performance Goals**: <500ms API responses, <2s dashboard updates, 1-2 concurrent users initially  
**Constraints**: OAuth2 email integration, paperless-ngx REST API, single AI provider initially  
**Scale/Scope**: MVP for 1-2 users, core portfolio management with 20-30 essential requirements

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 3 (backend API, frontend UI, tests) ✓
- Using framework directly? TBD in research phase
- Single data model? TBD - complex domain may require DTOs
- Avoiding patterns? TBD - Repository pattern may be needed for multi-provider data access

**Architecture**:
- EVERY feature as library? Planned - email processor, price tracker, AI analysis as separate libraries
- Libraries listed: [email-processor, price-tracker, ai-analysis, portfolio-engine, news-tracker]
- CLI per library: Planned for each library component
- Library docs: llms.txt format planned? Yes

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? Will be enforced
- Git commits show tests before implementation? Will be followed
- Order: Contract→Integration→E2E→Unit strictly followed? Yes
- Real dependencies used? Yes - actual PostgreSQL, Redis, email providers
- Integration tests for: email processing, AI providers, paperless-ngx integration
- FORBIDDEN: Implementation before test, skipping RED phase ✓

**Observability**:
- Structured logging included? Planned - comprehensive audit trails required
- Frontend logs → backend? Yes - unified logging stream
- Error context sufficient? Yes - workflow failure tracking required

**Versioning**:
- Version number assigned? 0.1.0 (initial)
- BUILD increments on every change? Yes
- Breaking changes handled? Migration plan for API changes

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

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

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: Option 2 - Web application (backend + frontend detected from requirements)

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `/scripts/update-agent-context.sh [claude|gemini|copilot]` for your AI assistant
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each API contract endpoint → contract test task [P]
- Each data model entity → model creation task [P]
- Each quickstart user story → integration test task
- Implementation tasks to make tests pass (following TDD)

**MVP-Specific Ordering Strategy**:
1. **Setup & Infrastructure** (Tasks 1-5):
   - uv project initialization and dependency management
   - SQLite database setup with Alembic migrations
   - FastAPI project structure with basic auth
   - React/Next.js frontend scaffolding
   - Basic CI/CD pipeline setup

2. **Core Models & Tests** (Tasks 6-12) [P]:
   - User model and authentication tests
   - Portfolio/Stock/Transaction models
   - Database schema and relationship tests
   - API contract tests for each endpoint

3. **Authentication & User Management** (Tasks 13-17):
   - JWT authentication implementation
   - API key management system
   - User registration/login endpoints
   - Frontend auth components and routing

4. **Portfolio Management Core** (Tasks 18-25) [P]:
   - Portfolio CRUD operations and tests  
   - Manual transaction entry system
   - Holdings calculation and updates
   - Performance metrics calculation

5. **Frontend Dashboard** (Tasks 26-32):
   - Portfolio dashboard components
   - Transaction entry forms
   - Basic charting with Chart.js
   - Responsive design and mobile support

6. **Integration & E2E** (Tasks 33-38):
   - Full user journey tests (quickstart scenarios)
   - API integration testing
   - Frontend-backend integration
   - Performance validation and optimization

**Estimated Output**: 35-40 numbered, ordered tasks in tasks.md for MVP

**Parallel Execution Markers**:
- [P] indicates tasks that can run in parallel (independent modules)
- Sequential tasks handle integration points and dependencies
- TDD workflow: Contract/Integration/Unit tests before implementation

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


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
- [x] Complexity deviations documented (none required for MVP)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
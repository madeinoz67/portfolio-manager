# Implementation Plan: Admin Dashboard

**Branch**: `003-admin-dashboard` | **Date**: 2025-09-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-admin-dashboard/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path ✅
   → Found complete feature spec with admin dashboard requirements
2. Fill Technical Context (scan for NEEDS CLARIFICATION) ✅
   → Detected Project Type: web (frontend+backend)
   → Set Structure Decision: Option 2 (web application)
3. Evaluate Constitution Check section below ✅
   → No violations detected - simple admin dashboard extension
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md ✅
   → All NEEDS CLARIFICATION resolved through codebase analysis
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md 🟡
6. Re-evaluate Constitution Check section 🟡
   → Post-Design Constitution Check pending
7. Plan Phase 2 → Describe task generation approach 🟡
8. STOP - Ready for /tasks command 🟡
```

## Summary
Implement an admin dashboard feature that extends the existing portfolio management system with administrative capabilities. The backend already has complete admin authentication and API endpoints. Frontend needs admin-specific pages, role-based routing, and UI components to expose existing admin functionality to authenticated admin users.

## Technical Context
**Language/Version**: Python 3.12, TypeScript (Next.js 15.5.3)
**Primary Dependencies**: FastAPI 0.116.1, SQLAlchemy 2.0.43, React 19.1.0, Tailwind CSS
**Storage**: SQLite (development), PostgreSQL (production-ready)
**Testing**: pytest (backend), Jest + React Testing Library (frontend)
**Target Platform**: Web application (Linux server + modern browsers)
**Project Type**: web - determines source structure
**Performance Goals**: <200ms API response times, smooth UI interactions
**Constraints**: JWT-based authentication, role-based access control
**Scale/Scope**: Single admin dashboard with user management and system monitoring

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 2 (backend API, frontend UI) ✅
- Using framework directly? Yes (FastAPI, Next.js) ✅
- Single data model? Yes (extends existing User model) ✅
- Avoiding patterns? No unnecessary Repository/UoW patterns ✅

**Architecture**:
- EVERY feature as library? Admin features built as UI components and API endpoints ✅
- Libraries listed: Admin UI components, Admin API services ✅
- CLI per library: N/A for web UI feature ✅
- Library docs: Will update CLAUDE.md with new admin context ✅

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? Yes - tests before implementation ✅
- Git commits show tests before implementation? Will be enforced ✅
- Order: Contract→Integration→E2E→Unit strictly followed? Yes ✅
- Real dependencies used? Yes (actual database, JWT auth) ✅
- Integration tests for: Admin API contracts, role-based access ✅
- FORBIDDEN: Implementation before test, skipping RED phase ✅

**Observability**:
- Structured logging included? Uses existing FastAPI logging ✅
- Frontend logs → backend? Can use existing error handling ✅
- Error context sufficient? Admin actions will be logged with context ✅

**Versioning**:
- Version number assigned? Will follow existing MAJOR.MINOR.BUILD ✅
- BUILD increments on every change? Yes ✅
- Breaking changes handled? N/A - additive feature ✅

## Project Structure

### Documentation (this feature)
```
specs/003-admin-dashboard/
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
│   ├── models/          # Existing user models with roles ✅
│   ├── services/        # Admin services (planned)
│   └── api/             # Admin API endpoints ✅ (exist)
└── tests/
    ├── contract/        # Admin API contract tests (planned)
    ├── integration/     # Admin integration tests (planned)
    └── unit/           # Admin unit tests (planned)

frontend/
├── src/
│   ├── components/      # Admin UI components (planned)
│   ├── app/            # Admin pages via Next.js app router (planned)
│   └── services/       # Admin API client services (planned)
└── tests/
    ├── components/     # Admin component tests (planned)
    └── integration/    # Admin E2E tests (planned)
```

**Structure Decision**: Option 2 (web application) - extends existing backend/frontend structure

## Phase 0: Outline & Research ✅

Research completed through comprehensive codebase analysis:

### Key Findings:
- **Backend**: Complete admin authentication system exists with UserRole enum, admin API endpoints
- **Authentication**: JWT-based with `get_current_admin_user()` dependency for role verification
- **Database**: User model has role field, admin users can be created
- **API**: `/api/v1/admin/users` and admin market data endpoints already functional
- **Frontend Gap**: No admin UI - AuthContext missing role info, no admin routes/components

### Technology Decisions:
- **Decision**: Extend existing authentication system
- **Rationale**: Backend admin functionality is complete, only frontend needed
- **Alternatives considered**: Separate admin app - rejected due to complexity

### Implementation Approach:
- **Decision**: Frontend-focused implementation extending existing patterns
- **Rationale**: Backend APIs exist, auth is working, minimal backend changes needed
- **Alternatives considered**: Full redesign - rejected due to working backend

**Output**: research.md with all technical unknowns resolved ✅

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

### Data Model Extensions
Will extend existing models minimally:
- User model: Already has role field ✅
- Frontend User type: Add role field to TypeScript interfaces
- Admin-specific response types: Leverage existing UserResponse schema

### API Contract Design
Leverage existing admin endpoints:
- `GET /api/v1/admin/users` - List users for admin dashboard ✅
- `GET /api/v1/admin/users/{user_id}` - User details ✅
- Market data admin endpoints for system monitoring ✅
- Future: Admin actions (suspend user, reset password) - extend existing patterns

### Frontend Contract Requirements
- Admin route protection (role-based guards)
- Admin navigation components
- User management interface
- System monitoring dashboard
- Integration with existing AuthContext + role awareness

**Outputs Planned**: data-model.md, /contracts/*, failing tests, quickstart.md, CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Frontend-heavy tasks leveraging existing backend APIs
- Extend authentication context with role information
- Create admin routes using Next.js app router patterns
- Build admin UI components following existing component patterns
- Add role-based navigation and route guards

**Task Breakdown Strategy**:
- **Authentication Phase**: Extend frontend auth context with role support
- **Route Infrastructure**: Create admin route structure and protection
- **Core Components**: Build reusable admin UI components
- **Feature Pages**: Implement specific admin functionality (dashboard, user management)
- **Integration**: Connect frontend components to existing backend APIs
- **Testing**: Contract tests for admin components and integration flows

**Ordering Strategy**:
- TDD: Frontend tests for admin components before implementation
- Auth first: Role context → route guards → admin pages
- Component hierarchy: Layout → pages → specific admin features
- Integration: API integration tests with existing admin endpoints

**Dependency Ordering**:
1. Frontend auth extensions (role context, types)
2. Admin route guards and protection
3. Basic admin layout and navigation
4. System metrics dashboard
5. User management interface
6. Market data monitoring (if applicable)
7. Integration tests and error handling

**Estimated Output**: 18-22 frontend-focused tasks leveraging existing backend APIs

## Complexity Tracking
*No constitutional violations detected - admin dashboard extends existing patterns*

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
- [x] Complexity deviations documented (none)

---
*Based on Constitution v2.1.1 - See `/.specify/memory/constitution.md`*
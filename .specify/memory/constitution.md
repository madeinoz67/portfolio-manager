<!--
Sync Impact Report:
Version change: 1.0.0 → 1.1.0
Modified principles: None
Added sections: VI. Continuous Integration (new principle)
Removed sections: None
Templates requiring updates:
  ✅ .specify/templates/plan-template.md - updated with new principle check
  ✅ .specify/templates/spec-template.md - reviewed, no changes needed
  ✅ .specify/templates/tasks-template.md - reviewed, no changes needed
Follow-up TODOs: None
-->

# Portfolio Manager Constitution

## Core Principles

### I. Test-First Development (NON-NEGOTIABLE)

TDD MUST be followed for all development: Tests written → Tests fail → Implementation → Tests pass. Every feature starts with failing tests. Red-Green-Refactor cycle is mandatory. All tests MUST pass before code review or merge.

*Rationale: Portfolio management involves financial calculations where bugs can cause monetary loss. Test-first ensures reliability and prevents regression in critical financial logic.*

### II. Financial Data Integrity

All financial calculations MUST use decimal precision (never floats). Database schema changes MUST preserve existing data through Alembic migrations. No data corruption or loss is acceptable during migrations. Store facts, calculate opinions.

*Rationale: Financial applications require precise decimal arithmetic. Loss of user portfolio data or calculation errors undermine trust and violate fiduciary responsibility.*

### III. Database Schema Safety

ALL database changes MUST use Alembic migrations. Migrations MUST migrate existing data safely. When column changes cause conflicts, use rename-create-migrate-validate-remove pattern. Single source of truth for each data type.

*Rationale: Portfolio data is irreplaceable user asset information. Schema changes must be reversible and data-preserving to maintain system reliability.*

### IV. Market Data Single Source

One master table for each data type (realtime_symbols for current prices). No duplicate data tables. APIs MUST query the authoritative source. Historical data separate from current data tables.

*Rationale: Multiple price sources create inconsistency and staleness issues. Single source of truth ensures data consistency and simplifies debugging.*

### V. Security and Access Control

Role-based access control MUST be enforced at API level. JWT authentication required for all protected endpoints. Admin functions isolated with separate validation. Audit trails for security-sensitive operations.

*Rationale: Portfolio data is sensitive financial information requiring proper access controls and audit capabilities for compliance and security.*

### VI. Continuous Integration

Working code MUST be committed and pushed frequently. Commits MUST represent functional, tested increments. Code MUST be pushed to remote repositories regularly to prevent loss and enable collaboration. Work-in-progress MUST be committed often with clear commit messages.

*Rationale: Financial software development requires robust backup and collaboration practices. Frequent commits provide granular rollback points and prevent code loss. Regular pushes ensure team visibility and enable continuous integration workflows.*

## Development Standards

### Code Quality Requirements

All code MUST pass linting and type checking before merge. Frontend date/time handling MUST convert UTC backend data to local timezone for display. Error handling MUST be graceful with user-friendly messages.

### Documentation Standards

All architectural decisions MUST be documented in /docs/architecture. API changes MUST update OpenAPI specifications. Breaking changes MUST include migration guides.

## Testing Requirements

### Coverage Requirements

Contract tests MUST exist for all API endpoints. Integration tests MUST cover end-to-end user workflows. Performance tests MUST validate financial calculation speed requirements.

### Test Environment

Tests MUST use isolated database instances. Market data tests MUST use mock data to avoid external API dependencies. All tests MUST be deterministic and repeatable.

## Governance

### Amendment Process

Constitution changes require documentation of impact and rationale. All dependent templates MUST be updated for consistency. Version increments follow semantic versioning: MAJOR for incompatible changes, MINOR for additions, PATCH for clarifications.

### Compliance Review

All pull requests MUST verify constitutional compliance. Complexity deviations MUST be justified with rationale. CLAUDE.md provides runtime development guidance supplementing this constitution.

### Quality Gates

Database migrations MUST be tested in staging environment. Financial calculations MUST be verified against known test cases. Security changes MUST include threat model review.

**Version**: 1.1.0 | **Ratified**: 2025-09-19 | **Last Amended**: 2025-09-20
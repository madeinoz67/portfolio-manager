# Technology Stack Research for Portfolio Management System

**Scope**: 1-2 users initially (MVP version)
**Research Date**: 2025-09-12

## Language/Version Selection

**Decision**: Python 3.11+ with FastAPI

**Rationale**: 
- FastAPI provides excellent async support for concurrent email processing and price updates
- Strong ecosystem for financial data processing and AI integration
- Type safety with Pydantic reduces bugs in financial calculations
- Automatic OpenAPI documentation generation supports API requirements
- Excellent integration with AI providers (Ollama, OpenAI, Anthropic)

**Alternatives Considered**:
- Node.js: Good for real-time features but Python superior for AI/ML integration
- Django: More heavyweight than needed for API-first architecture
- Go: High performance but smaller ecosystem for financial libraries

## Primary Dependencies

**Decision**: FastAPI + React ecosystem

**Backend** (managed with uv):
- FastAPI (web framework)
- SQLAlchemy (ORM)  
- Pydantic (data validation)
- Celery (background tasks)
- httpx (async HTTP client)
- uv (Python package and project management)

**Frontend**:
- React 18+ with Next.js
- TypeScript for type safety
- Chart.js/D3.js for financial charts
- Material-UI or Ant Design for components

**Rationale**: 
- Proven stack for financial applications with strong type safety and async capabilities
- uv provides fast Python package management and dependency resolution
- Modern tooling for dependency management replaces pip/poetry with better performance

**Alternatives Considered**:
- Vue.js: Simpler but smaller ecosystem for financial charting
- Plain React: Next.js provides better SSR and routing

## Storage Strategy

**Decision**: SQLite initially, upgrade path to PostgreSQL

**Rationale**:
- SQLite perfect for 1-2 user MVP - zero configuration, embedded database
- ACID compliance for financial transaction integrity
- JSON support available for storing AI results and email metadata
- Easy development setup with no external dependencies
- Clear upgrade path to PostgreSQL when scaling beyond 2-3 users

**Alternatives Considered**:
- PostgreSQL: Excellent for production but overkill for MVP development
- MongoDB: Insufficient transaction guarantees for financial data
- MySQL: More complex than needed for initial development

## Testing Framework

**Decision**: pytest + Jest + Playwright

**Rationale**:
- pytest: Excellent Python testing with fixtures and parameterization
- Jest: Industry standard for React/TypeScript testing
- Playwright: Superior cross-browser E2E testing with visual capabilities
- Supports TDD workflow required by specification

**Alternatives Considered**:
- Cypress: Good but Playwright offers better reliability and cross-browser support
- Selenium: Older technology, less reliable than Playwright

## Target Platform

**Decision**: Web application (Linux server + modern browsers)

**Rationale**:
- Cross-platform compatibility for 1-2 initial users
- Responsive design works across desktop, tablet, mobile
- Easier deployment and maintenance than native apps
- API-first design enables future mobile app development

**Alternatives Considered**:
- Desktop apps: Limited cross-platform compatibility
- Mobile-first: Desktop experience important for financial analysis

## Performance Goals (MVP Scale)

**Decision**: Conservative targets for 1-2 users

- API responses: < 500ms for standard operations
- Dashboard updates: < 2 seconds for chart rendering
- Daily batch processing: Complete within 30 minutes
- Email polling: Every 15 minutes (configurable)
- Concurrent users: 2-5 without performance degradation

**Rationale**: Realistic targets for MVP that can scale up with infrastructure

## Constraints and Integration Requirements

**Decision**: OAuth2 + Simplified integrations for MVP

**Email Integration**:
- OAuth2 with Gmail/Outlook APIs (security requirement)
- Start with Westpac broker format, add generic heuristics later
- Human intervention workflow for parsing failures

**AI Provider Integration**:
- Start with one provider (Ollama for local, OpenAI for cloud)
- Extensible interface for adding providers later
- Simple confidence calculation initially

**Paperless-ngx Integration**:
- REST API integration for document storage
- Simple tagging initially, enhance with AI later

**Performance Considerations**:
- Connection pooling for database
- Simple caching strategy with Redis
- Async processing for email and price updates

## Scale/Scope (MVP)

**Decision**: Core functionality for 1-2 users

**Initial Features**:
- Single portfolio management
- Basic email transaction processing
- Daily price updates with simple adapter pattern
- Basic dashboard with essential charts
- Simple user authentication (no multi-user permissions initially)
- API with key-based authentication
- Basic AI recommendations (recommendations only, no trading)

**Future Scaling Path**:
- Multi-portfolio support
- Multi-user collaboration with permissions
- Advanced AI analysis and confidence calculations
- Enhanced news integration and intelligent tagging
- Portfolio rebalancing recommendations
- Advanced performance metrics

**Rationale**: Focus on core value proposition first, then expand based on user feedback

## Technical Architecture Summary

**MVP Architecture**:
1. **Backend**: FastAPI + PostgreSQL + Redis + Celery
2. **Frontend**: React + Next.js + TypeScript + Chart.js
3. **AI**: Single provider initially (Ollama or OpenAI)
4. **Email**: OAuth2 + basic Westpac parsing
5. **News**: Simple ASX web scraping
6. **Auth**: Basic user auth + API keys

**Development Approach**:
- Test-driven development with pytest/Jest
- Library-first architecture for each major component
- CLI interfaces for each library component
- Containerized development environment with Docker
- Simple CI/CD pipeline for MVP deployment

**Estimated Timeline**: 2-3 months for MVP with core features
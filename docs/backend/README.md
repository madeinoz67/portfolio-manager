# Backend Documentation

This directory contains backend-specific documentation for the Portfolio Manager application.

## Backend Guides

- [Backend README](backend-readme.md) - Backend overview and quick start guide
- [Deployment Guide](deployment-guide.md) - Production deployment instructions
- [Debugging Notes](debugging-notes.md) - Common debugging scenarios and solutions
- [Developer Notes](developer-notes.md) - Backend development notes and improvements

## Backend Architecture

The backend is built with:
- **Python 3.12** with FastAPI 0.116.1
- **SQLAlchemy 2.0.43** for database ORM
- **Alembic** for database migrations
- **PostgreSQL/SQLite** for data storage
- **JWT Authentication** with role-based access control

## Quick Start

```bash
# Install dependencies
uv sync

# Apply database migrations
uv run alembic upgrade head

# Start development server
uv run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

## Key Components

### Database
- Single master symbol table architecture (`realtime_symbols`)
- Proper fact vs. opinion separation
- UTC timestamps with frontend conversion

### API Structure
- RESTful API with OpenAPI/Swagger documentation
- Role-based endpoints (Admin/User)
- Real-time updates via Server-Sent Events

### Market Data
- 15-minute update intervals
- Provider failover (Yahoo Finance → Alpha Vantage)
- Comprehensive error handling and retry logic

## Related Documentation

- [Architecture](../architecture/) - System design and database schema
- [Developer](../developer/) - Development guidelines and patterns
- [Reference](../reference/) - API reference documentation
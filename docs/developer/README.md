# Developer Documentation

This directory contains guides and documentation specifically for developers working on the Portfolio Manager application.

## Development Guides

- [Audit Developer Guide](audit-developer-guide.md) - Technical guide for implementing audit system features
- [Frontend Date Handling](frontend-date-handling.md) - Date/time patterns and timezone handling in the frontend
- [Authentication Testing](authentication-testing.md) - Authentication system testing procedures and results

## Development Principles

### Key Guidelines
1. **Test-Driven Development**: Always use TDD when making changes, all tests MUST pass
2. **Single Instance**: Always check that only one backend and frontend is running to prevent contention
3. **Database Changes**: Always use Alembic for database schema changes
4. **Commit Often**: Always commit changes frequently
5. **Check Metrics**: Always verify metrics are working when making core changes

### Data Freshness
- Always use `fetched_at` when determining freshness of market data
- Single source of truth for market data - don't create other tables to store market data

### Alembic Best Practices
When encountering append errors when changing columns:
1. Rename the old column
2. Create a new column
3. Migrate data from old column
4. Validate data
5. Remove the old column

## Getting Started

1. **Setup Development Environment**
   ```bash
   cd backend
   uv sync
   alembic upgrade head
   ```

2. **Run Tests**
   ```bash
   uv run pytest tests/ -v
   ```

3. **Start Development Servers**
   ```bash
   # Backend
   uv run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload

   # Frontend (separate terminal)
   cd frontend && npm run dev
   ```

## Working Notes

Always check and update working notes when working on problems. See [working-notes/](../working-notes/) for current development status.

## Related Documentation

- [Architecture](../architecture/) - System architecture and design
- [Backend](../backend/) - Backend-specific documentation
- [Frontend](../frontend/) - Frontend-specific documentation
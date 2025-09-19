# Portfolio Manager Backend

FastAPI backend for the Portfolio Manager application with market data provider adapters.

## Features

- Portfolio management and tracking
- Market data integration with multiple providers
- Real-time metrics and monitoring
- Admin dashboard with adapter management
- JWT authentication and role-based access

## Dependencies

This backend uses the adapter pattern for market data providers with the following key dependencies:

- **FastAPI**: Modern web framework
- **SQLAlchemy**: ORM and database management
- **dependency-injector**: Dependency injection framework
- **aioprometheus**: Async Prometheus metrics
- **pybreaker**: Circuit breaker pattern
- **tenacity**: Retry mechanisms
- **class-registry**: Dynamic provider registration

## Installation

```bash
uv sync
```

## Running

```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```
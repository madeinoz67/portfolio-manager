# Portfolio Manager Backend

A modern portfolio management system backend built with Python FastAPI, featuring real-time market data integration and a single master symbol table architecture.

## =€ Quick Start

```bash
# Install dependencies
uv sync

# Apply database migrations
uv run alembic upgrade head

# Start development server
uv run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

## <× Architecture

### Single Master Symbol Table
The backend implements a **Single Master Symbol Table** architecture that eliminates dual-table synchronization complexity:

- **`realtime_symbols`**: Master table containing current prices (single source of truth)
- **`realtime_price_history`**: Time-series data for historical analysis
- **Single-write pattern**: All price updates go through master table
- **Consistent APIs**: All pricing APIs read from the same authoritative source

**Benefits:**
-  Eliminates holdings timestamp bugs
-  Prevents price inconsistencies
-  Simplifies data access patterns
-  Improves performance with optimized indexes

### Core Components

- **FastAPI**: High-performance async web framework
- **SQLAlchemy 2.0**: Modern ORM with async support
- **Alembic**: Database migration management
- **Pydantic**: Data validation and serialization
- **PostgreSQL/SQLite**: Production/development databases

## =' Configuration

Create `.env` file:

```env
PM_DATABASE_URL="sqlite:///./portfolio_manager.db"
PM_JWT_SECRET_KEY="your-secret-key"
PM_ALPHA_VANTAGE_API_KEY="your-api-key"
PM_CORS_ORIGINS="http://localhost:3000"
```

## =Ê Database

### Migrations

```bash
# Create new migration
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head

# Check current version
uv run alembic current
```

### Key Tables

- `realtime_symbols` - Master symbol pricing table
- `realtime_price_history` - Historical price data
- `portfolios` - User portfolio management
- `holdings` - Portfolio stock holdings
- `market_data_providers` - API provider configuration

## =à Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/test_single_master_symbol_table_tdd.py -v
```

### Code Quality

```bash
# Format code
uv run black src tests

# Type checking
uv run mypy src

# Linting
uv run ruff check src
```

## =á API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/refresh` - Token refresh

### Portfolios
- `GET /api/v1/portfolios` - List user portfolios
- `POST /api/v1/portfolios` - Create portfolio
- `GET /api/v1/portfolios/{id}` - Get portfolio details
- `GET /api/v1/portfolios/{id}/holdings` - Get portfolio holdings

### Market Data
- `GET /api/v1/market-data/prices/{symbol}` - Get current price
- `GET /api/v1/market-data/prices?symbols=...` - Bulk price fetch
- `GET /api/v1/market-data/stream` - SSE price updates
- `GET /api/v1/market-data/status` - Service status

### Admin
- `GET /api/v1/admin/users` - User management
- `GET /api/v1/admin/dashboard/metrics` - System metrics
- `GET /api/v1/admin/scheduler/status` - Scheduler status

## = Security

- JWT-based authentication with configurable expiry
- Role-based access control (Admin/User)
- CORS protection with configurable origins
- Rate limiting on market data endpoints
- Input validation with Pydantic schemas

## =È Market Data

### Supported Providers
- **Alpha Vantage**: Production API with rate limiting
- **Yahoo Finance**: Development fallback via yfinance

### Features
- 15-minute polling intervals
- Automatic retry with exponential backoff
- Provider failover and health monitoring
- Real-time SSE streaming to frontend
- Historical data preservation

## =€ Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment instructions including:

- Docker containerization
- Production PostgreSQL setup
- Nginx reverse proxy configuration
- SSL/TLS setup with Let's Encrypt
- Systemd service management
- Monitoring and logging

## =Ú Documentation

- [Single Master Symbol Table Architecture](docs/single-master-symbol-table-architecture.md)
- [Scheduler API Architecture](docs/scheduler-api-architecture.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Working Notes](../WORKING_NOTES.md)

## >ê Testing Strategy

The project follows Test-Driven Development (TDD) principles:

- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **TDD Test Suites**: Comprehensive behavior validation
- **Contract Tests**: API specification compliance

Example TDD test results:
```bash
$ uv run pytest tests/test_single_master_symbol_table_tdd.py -v
======================= 11 passed ========================
```

## = Debugging

Set environment variables for detailed logging:

```env
PM_LOG_LEVEL="DEBUG"
PM_DEBUG=true
```

Monitor logs:
```bash
# Application logs
tail -f logs/portfolio_manager.log

# Database queries (SQLAlchemy)
# Set SQLALCHEMY_LOG_LEVEL=DEBUG in .env
```

## > Contributing

1. Follow TDD approach for new features
2. Use Alembic for database changes
3. Maintain test coverage above 80%
4. Follow existing code patterns and conventions
5. Update documentation for architectural changes

## =Ä License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Built with d using FastAPI, SQLAlchemy, and modern Python development practices.
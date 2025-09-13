# Portfolio Management System

A full-stack portfolio management application built with FastAPI (backend) and Next.js (frontend), featuring JWT authentication, real-time portfolio tracking, and comprehensive API endpoints.

## 🚀 Features

- **User Authentication**: Secure JWT-based authentication with API key support
- **Portfolio Management**: Create, read, update, and delete investment portfolios
- **Transaction Tracking**: Record and manage buy/sell transactions
- **Real-time Data**: Portfolio performance tracking with daily changes
- **Responsive UI**: Modern React-based frontend with dark/light theme support
- **RESTful API**: Comprehensive backend API with OpenAPI documentation

## 🏗️ Architecture

```
portfolio-manager/
├── backend/                 # FastAPI backend
│   ├── src/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core utilities (auth, config)
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   └── services/       # Business logic services
│   ├── tests/              # Backend tests
│   └── alembic/            # Database migrations
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/            # Next.js 13+ app router pages
│   │   ├── components/     # React components
│   │   ├── contexts/       # React contexts (Auth, Theme)
│   │   ├── hooks/          # Custom React hooks
│   │   └── types/          # TypeScript type definitions
├── specs/                  # Project specifications
└── docs/                   # Additional documentation
```

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.115+
- **Database**: SQLite (production-ready with PostgreSQL support)
- **ORM**: SQLAlchemy 2.0+
- **Authentication**: JWT tokens + bcrypt password hashing
- **API Documentation**: OpenAPI/Swagger
- **Testing**: Pytest
- **Migration**: Alembic

### Frontend
- **Framework**: Next.js 15.5+ with App Router
- **UI Library**: React 19+ with TypeScript
- **Styling**: Tailwind CSS 3.4+
- **State Management**: React Context + Custom Hooks
- **HTTP Client**: Fetch API with custom error handling
- **Charts**: Chart.js with react-chartjs-2

## 🚦 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- uv (Python package manager)
- npm or yarn

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies
uv sync

# Run database migrations
uv run alembic upgrade head

# Start development server
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```

The backend will be available at: http://localhost:8001
API documentation: http://localhost:8001/docs

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at: http://localhost:3000 (or 3001 if 3000 is in use)

## 🔐 Authentication

The system supports two authentication methods:

### 1. JWT Bearer Tokens
```bash
# Register a new user
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123", "first_name": "John", "last_name": "Doe"}'

# Login to get JWT token
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Use token in requests
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:8001/api/v1/auth/me
```

### 2. API Keys
```bash
# Create an API key (requires JWT authentication first)
curl -X POST http://localhost:8001/api/v1/auth/me/api-keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My API Key"}'

# Use API key in requests
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8001/api/v1/portfolios
```

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user profile
- `PUT /api/v1/auth/me` - Update user profile
- `GET /api/v1/auth/me/api-keys` - List API keys
- `POST /api/v1/auth/me/api-keys` - Create API key
- `DELETE /api/v1/auth/me/api-keys/{key_id}` - Delete API key

### Portfolios
- `GET /api/v1/portfolios` - List user's portfolios
- `POST /api/v1/portfolios` - Create new portfolio
- `GET /api/v1/portfolios/{id}` - Get portfolio details
- `PUT /api/v1/portfolios/{id}` - Update portfolio
- `DELETE /api/v1/portfolios/{id}` - Delete portfolio (soft delete)
- `GET /api/v1/portfolios/{id}/holdings` - Get portfolio holdings

### Transactions
- `GET /api/v1/portfolios/{id}/transactions` - List portfolio transactions
- `POST /api/v1/portfolios/{id}/transactions` - Add new transaction
- `GET /api/v1/transactions/{id}` - Get transaction details
- `PUT /api/v1/transactions/{id}` - Update transaction
- `DELETE /api/v1/transactions/{id}` - Delete transaction

### Stocks & Market Data
- `GET /api/v1/stocks` - List available stocks
- `GET /api/v1/stocks/{id}` - Get stock details
- `POST /api/v1/stocks` - Add new stock
- `GET /api/v1/stocks/{id}/price-history` - Get price history

## 🖥️ Frontend Components

### Authentication
- **AuthContext**: Global authentication state management
- **LoginForm**: User login component with validation
- **RegisterForm**: User registration with form validation
- **AuthModal**: Modal wrapper for login/register forms

### Portfolio Management
- **PortfolioCard**: Individual portfolio display card
- **CreatePortfolioForm**: Form for creating new portfolios
- **PortfolioList**: Grid display of user portfolios
- **PortfolioDetails**: Detailed portfolio view with transactions

### UI Components
- **Navigation**: Main navigation bar with auth state
- **ThemeToggle**: Dark/light theme switcher
- **LoadingSpinner**: Loading state indicator
- **ErrorMessage**: Error display component
- **Toast**: Notification system

## 🗄️ Database Schema

### Users Table
- `id` (UUID, Primary Key)
- `email` (String, Unique)
- `password_hash` (String)
- `first_name` (String, Optional)
- `last_name` (String, Optional)
- `is_active` (Boolean)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### Portfolios Table
- `id` (UUID, Primary Key)
- `name` (String)
- `description` (String, Optional)
- `owner_id` (UUID, Foreign Key to Users)
- `total_value` (Decimal)
- `daily_change` (Decimal)
- `daily_change_percent` (Decimal)
- `is_active` (Boolean)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### Transactions Table
- `id` (UUID, Primary Key)
- `portfolio_id` (UUID, Foreign Key to Portfolios)
- `stock_id` (UUID, Foreign Key to Stocks)
- `transaction_type` (Enum: BUY, SELL)
- `quantity` (Integer)
- `price_per_share` (Decimal)
- `total_amount` (Decimal)
- `fees` (Decimal, Optional)
- `transaction_date` (DateTime)
- `notes` (String, Optional)

### API Keys Table
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key to Users)
- `name` (String)
- `key_hash` (String)
- `permissions` (JSON, Optional)
- `last_used_at` (DateTime, Optional)
- `expires_at` (DateTime, Optional)
- `is_active` (Boolean)
- `created_at` (DateTime)

## 🧪 Testing

### Backend Tests
```bash
cd backend

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test suite
uv run pytest tests/contract/
```

### Frontend Tests
```bash
cd frontend

# Run tests (when implemented)
npm test
```

## 🚀 Deployment

### Backend Deployment
1. Set environment variables:
   ```bash
   export DATABASE_URL=postgresql://user:pass@localhost/dbname
   export SECRET_KEY=your-secret-key
   export ACCESS_TOKEN_EXPIRE_MINUTES=10080
   ```

2. Run migrations:
   ```bash
   uv run alembic upgrade head
   ```

3. Start production server:
   ```bash
   uv run uvicorn src.main:app --host 0.0.0.0 --port 8001
   ```

### Frontend Deployment
1. Build the application:
   ```bash
   npm run build
   ```

2. Set environment variables:
   ```bash
   export NEXT_PUBLIC_API_URL=https://your-api-domain.com
   ```

3. Start production server:
   ```bash
   npm start
   ```

## 📈 Performance

- **Backend**: FastAPI provides automatic API documentation and high performance
- **Database**: Optimized queries with SQLAlchemy ORM and proper indexing
- **Frontend**: Next.js App Router with automatic code splitting and optimization
- **Authentication**: JWT tokens with configurable expiration times
- **Caching**: Request-level caching for frequently accessed data

## 🔧 Configuration

### Backend Configuration
Configuration is handled through environment variables and the `src/core/config.py` file:

- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT signing secret
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time
- `ALGORITHM`: JWT signing algorithm (default: HS256)

### Frontend Configuration
Configuration through environment variables:

- `NEXT_PUBLIC_API_URL`: Backend API base URL
- `NODE_ENV`: Environment mode (development/production)

## 📝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the API documentation at `/docs` endpoint
- Review the test files for usage examples

## 🔄 Changelog

### v1.0.0 (Current)
- ✅ Complete authentication system (JWT + API keys)
- ✅ Full CRUD operations for portfolios and transactions
- ✅ Responsive React frontend with TypeScript
- ✅ Comprehensive API documentation
- ✅ Database migrations and models
- ✅ End-to-end testing setup
- ✅ Dark/light theme support
- ✅ Real-time portfolio tracking
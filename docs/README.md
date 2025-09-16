# Portfolio Manager Documentation

This repository contains comprehensive documentation for the Portfolio Manager application, a full-stack portfolio management system built with Python FastAPI backend and Next.js TypeScript frontend.

## Documentation Structure

The documentation is organized according to CLAUDE.md specifications into the following directories:

### 📁 [Architecture](architecture/)
Technical architecture documentation, design decisions, and system implementation details:
- Database schema and design patterns
- System component architecture
- Market data fetching and processing
- Performance optimizations and troubleshooting

### 📁 [Backend](backend/)
Backend-specific documentation and guides:
- Backend setup and deployment
- Database management and migrations
- API implementation details
- Debugging and troubleshooting

### 📁 [Frontend](frontend/)
Frontend-specific documentation:
- React/Next.js implementation details
- UI components and patterns
- Real-time data handling
- Performance optimizations

### 📁 [Developer](developer/)
Developer guides and development documentation:
- Development workflow and guidelines
- Testing patterns and TDD practices
- Code conventions and best practices
- Integration guides

### 📁 [Design](design/)
Design-related documentation:
- User experience principles
- Visual design guidelines
- Component design patterns
- Responsive design approach

### 📁 [Reference](reference/)
Reference documentation and API specifications:
- Complete API documentation
- Request/response schemas
- Authentication and authorization
- Error codes and handling

### 📁 [User Guide](user-guide/)
End-user documentation and guides:
- Admin dashboard features
- Portfolio management guides
- User interface help
- Feature documentation

### 📁 [Release Notes](release_notes/)
Version history, feature releases, and changelog:
- Current version status
- Recent fixes and improvements
- Upcoming releases and roadmap

### 📁 [Working Notes](working-notes/)
Development notes and temporary documentation (internal use)

## Quick Navigation

| For | Start Here | Key Documents |
|-----|------------|---------------|
| **New Users** | [User Guide](user-guide/README.md) | [Admin Dashboard](user-guide/admin-dashboard.md) |
| **API Integration** | [Reference](reference/README.md) | [API Reference](reference/api-reference.md) |
| **Development** | [Developer](developer/README.md) | [Authentication Testing](developer/authentication-testing.md) |
| **Backend Development** | [Backend](backend/README.md) | [Deployment Guide](backend/deployment-guide.md) |
| **Frontend Development** | [Frontend](frontend/README.md) | [P&L Improvements](frontend/frontend-pl-improvements.md) |
| **System Architecture** | [Architecture](architecture/README.md) | [Database Schema](architecture/database-schema-pricing.md) |
| **Troubleshooting** | [Architecture](architecture/README.md) | [Debugging Notes](backend/debugging-notes.md) |

## Key Features

### ✅ Currently Implemented
- **Portfolio Management**: Multi-portfolio tracking with real-time valuations
- **Holdings Management**: Stock tracking with cost basis and P&L calculations
- **Admin Dashboard**: System administration with live activity monitoring
- **User Management**: Role-based access control (Admin/User)
- **Audit System**: Comprehensive activity logging and audit trails
- **Real-time Updates**: Server-Sent Events for live market data

### 🚧 In Development
- **Market Data Integration**: 15-minute interval updates with Alpha Vantage API
- **Advanced Analytics**: Enhanced portfolio performance metrics
- **Mobile Responsiveness**: Improved mobile user experience

## Technology Stack

- **Backend**: Python 3.12, FastAPI 0.116.1, SQLAlchemy 2.0.43, PostgreSQL
- **Frontend**: Next.js 15.5.3, React 19.1.0, TypeScript, Tailwind CSS
- **Real-time**: Server-Sent Events (SSE)
- **Authentication**: JWT with role-based access control
- **Testing**: pytest (backend), Jest + React Testing Library (frontend)

## Quick Start

### 🚀 For Developers

1. **Backend Setup:**
   ```bash
   cd backend
   uv sync
   alembic upgrade head
   uv run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
   ```

2. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Access Application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8001
   - Admin Dashboard: http://localhost:3000/admin (requires admin user)

### 👥 For Administrators

1. **Create Admin User:**
   ```sql
   UPDATE users SET role = 'ADMIN' WHERE email = 'admin@example.com';
   ```

2. **Access Admin Features:**
   - User Management: http://localhost:3000/admin/users
   - System Monitoring: http://localhost:3000/admin/system
   - Market Data: http://localhost:3000/admin/market-data

## Development Status

The application is in active development:
- **Feature 003**: Admin Dashboard ✅ COMPLETE
- **Feature 002**: Market Data Integration 🚧 IN PLANNING
- **Feature 001**: Portfolio Performance Dashboard ✅ COMPLETE

## Development Guidelines

Key principles from CLAUDE.md:
- **TDD**: Always use Test-Driven Development, all tests must pass
- **Single Instance**: Ensure only one backend/frontend instance running
- **Database Changes**: Always use Alembic for schema changes
- **Data Freshness**: Use `fetched_at` for market data freshness
- **Commit Often**: Frequent commits with clear messages
- **Check Metrics**: Verify metrics work after core changes

## Support

For technical issues and troubleshooting:
- **Architecture Issues**: See [Architecture Documentation](architecture/README.md)
- **Backend Problems**: Check [Backend Debugging](backend/debugging-notes.md)
- **API Questions**: Review [API Reference](reference/api-reference.md)
- **Development Help**: See [Developer Guide](developer/README.md)

---

For specific implementation details, please refer to the individual documentation directories. Each section provides comprehensive coverage with practical examples and troubleshooting information.
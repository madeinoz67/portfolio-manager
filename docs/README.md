# Portfolio Manager Documentation

This repository contains comprehensive documentation for the Portfolio Manager application, a full-stack portfolio management system built with Python FastAPI backend and Next.js TypeScript frontend.

## Documentation Structure

The documentation is organized into the following directories:

### 📁 [Architecture](architecture/)
Technical architecture documentation, design decisions, and system implementation details:
- Database schema and design patterns
- System component architecture
- Market data fetching and processing
- Performance optimizations and troubleshooting

### 📁 [User](user/)
User-facing documentation, guides, and API references:
- Admin dashboard guides
- API documentation
- User role and permission guides
- Portfolio monitoring and management

### 📁 [Release Notes](release_notes/)
Version history, feature releases, and changelog:
- Current version status
- Recent fixes and improvements
- Upcoming releases and roadmap

### 📁 [Working Notes](working-notes/)
Development notes and temporary documentation (not for end users)

## Quick Navigation

| Category | Key Documents |
|----------|---------------|
| **Getting Started** | [User Guide](user/README.md), [API Reference](user/api-reference.md) |
| **Admin Features** | [Admin Dashboard](user/admin-dashboard.md), [Audit Guide](user/admin-audit-guide.md) |
| **Architecture** | [Database Schema](architecture/database-schema-pricing.md), [System Design](architecture/single-master-symbol-table-architecture.md) |
| **Development** | [Architecture Overview](architecture/README.md), [Troubleshooting](architecture/troubleshooting-pricing-issues.md) |

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
   - Portfolio Metrics: http://localhost:3000/admin/portfolio-metrics

## Getting Started

1. **New Users**: Start with the [User Documentation](user/README.md)
2. **Developers**: Review the [Architecture Documentation](architecture/README.md) and [API Reference](user/api-reference.md)
3. **System Admins**: Check the [Admin Dashboard Guide](user/admin-dashboard.md)

## Development Status

The application is in active development:
- **Feature 003**: Admin Dashboard ✅ COMPLETE
- **Feature 002**: Market Data Integration 🚧 IN PLANNING
- **Feature 001**: Portfolio Performance Dashboard ✅ COMPLETE

## Support

For technical issues and troubleshooting, consult the [Architecture Documentation](architecture/README.md) which contains detailed troubleshooting guides and system information.

---

For specific implementation details, please refer to the individual documentation files linked above. Each guide provides comprehensive coverage of its respective system area with practical examples and troubleshooting information.
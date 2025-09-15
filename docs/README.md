# Portfolio Manager Documentation

## 📚 Documentation Index

Welcome to the Portfolio Manager documentation. This directory contains comprehensive guides for developers, administrators, and users.

### 🏗️ System Architecture
- **[Admin Dashboard](./admin-dashboard.md)** - Complete admin dashboard features and functionality
- **[Portfolio Monitoring](./portfolio-monitoring.md)** - Real-time portfolio update monitoring system
- **[Metric Monitoring System](./metric-monitoring-system.md)** - System-specific metrics tracking and API usage monitoring
- **[API Reference](./api-reference.md)** - Comprehensive API endpoint documentation

### 🚀 Quick Start

#### For Developers
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

#### For Administrators
1. **Create Admin User:**
   ```sql
   UPDATE users SET role = 'ADMIN' WHERE email = 'admin@example.com';
   ```

2. **Access Admin Features:**
   - User Management: http://localhost:3000/admin/users
   - System Monitoring: http://localhost:3000/admin/system
   - Market Data: http://localhost:3000/admin/market-data
   - Portfolio Metrics: http://localhost:3000/admin/portfolio-metrics

### 📖 Documentation Structure

```
docs/
├── README.md                    # This file - documentation index
├── admin-dashboard.md           # Admin dashboard comprehensive guide
├── portfolio-monitoring.md      # Portfolio monitoring system details
├── metric-monitoring-system.md  # System-specific metrics tracking and API usage
└── api-reference.md            # Complete API endpoint reference
```

### 🔧 Key Features Documented

#### Admin Dashboard ([Full Guide](./admin-dashboard.md))
- **User Management**: Role-based access control, user administration
- **System Monitoring**: Real-time health metrics, performance tracking
- **Market Data**: Provider management, API usage statistics
- **Audit Logging**: Comprehensive activity tracking and compliance

#### Portfolio Monitoring ([Full Guide](./portfolio-monitoring.md))
- **Real-time Metrics**: Automatic collection on portfolio updates
- **Performance Analytics**: Success rates, response times, queue health
- **Storm Protection**: Update coalescing and bulk operation tracking
- **Monitoring Dashboard**: Live metrics with 10-second auto-refresh

#### Metric Monitoring System ([Full Guide](./metric-monitoring-system.md))
- **System-Specific Tables**: Dedicated metrics tables per system (market_data_api_usage_metrics)
- **API Usage Tracking**: Comprehensive logging of all market data provider calls
- **Performance Monitoring**: Response times, rate limits, and error tracking
- **Admin Analytics**: Real-time metrics visibility and cost estimation

#### API Reference ([Full Guide](./api-reference.md))
- **Authentication**: JWT-based auth with role-based access
- **Portfolio Management**: CRUD operations for portfolios and holdings
- **Market Data**: Real-time price fetching and provider status
- **Admin Endpoints**: System administration and monitoring APIs

### 🎯 Key Use Cases

#### For System Administrators
- **Monitor System Health**: Track API response times, error rates, and system status
- **Manage Users**: View, modify, and control user access and roles
- **Analyze Performance**: Deep dive into portfolio update performance and bottlenecks
- **Troubleshoot Issues**: Comprehensive logging and error tracking

#### For Developers
- **API Integration**: Complete endpoint reference with request/response examples
- **Testing**: Test data and example scenarios for development
- **Architecture Understanding**: System design and component interactions
- **Monitoring Setup**: Metrics collection and alerting configuration

#### For Operations Teams
- **Deployment**: Configuration and environment setup
- **Monitoring**: External monitoring integration (Prometheus, Grafana)
- **Alerting**: Performance thresholds and notification setup
- **Maintenance**: Database migrations and system updates

### 🔍 Advanced Topics

#### Monitoring & Alerting
- **Portfolio Update Performance**: Track success rates, response times, and queue health
- **Market Data Reliability**: Monitor provider status and API performance
- **System Health**: Database connectivity, memory usage, and error tracking
- **User Activity**: Authentication events, portfolio operations, and admin actions

#### Security & Compliance
- **Role-Based Access**: Admin vs. user permissions and capabilities
- **Audit Trails**: Complete activity logging for compliance requirements
- **Data Protection**: Secure handling of financial and personal data
- **API Security**: JWT authentication and rate limiting

#### Performance Optimization
- **Database Indexing**: Optimized queries for portfolio calculations
- **Caching Strategies**: Redis integration for market data and portfolio values
- **Background Jobs**: Efficient processing of market data updates
- **Queue Management**: Handling high-volume portfolio update scenarios

### 🛠️ Development Workflow

#### Testing
```bash
# Backend tests
cd backend
uv run pytest tests/integration/ -v
uv run pytest tests/unit/ -v

# Frontend tests
cd frontend
npm test
npm run test:e2e
```

#### Database Management
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Check current version
alembic current
```

#### Monitoring Setup
```bash
# View portfolio metrics
curl -H "Authorization: Bearer <admin_token>" \
  http://localhost:8001/api/v1/admin/portfolio-updates/stats/24h

# Export Prometheus metrics
curl -H "Authorization: Bearer <admin_token>" \
  http://localhost:8001/api/v1/admin/portfolio-updates/metrics/export
```

### 📞 Support & Troubleshooting

#### Common Issues
1. **Admin Access Denied**: Verify user role in database and JWT token validity
2. **Missing Metrics Data**: Check database migrations and background services
3. **API Performance**: Review database query performance and system resources
4. **Market Data Issues**: Verify provider configuration and API key validity

#### Debug Commands
```bash
# Check database connectivity
alembic current

# Verify admin users
echo "SELECT email, role FROM users WHERE role = 'ADMIN';" | sqlite3 portfolio.db

# Check recent errors
tail -f logs/application.log | grep ERROR

# Test API endpoints
curl -H "Authorization: Bearer <token>" http://localhost:8001/api/v1/auth/me
```

#### Getting Help
- **Issues**: Check logs and error messages first
- **Performance**: Use admin dashboard monitoring tools
- **API Questions**: Reference the complete API documentation
- **Feature Requests**: Review architecture documentation for extensibility

### 🔄 Updates & Maintenance

This documentation is maintained alongside the codebase. Key areas that receive regular updates:

- **API Reference**: Updated with new endpoints and schema changes
- **Admin Features**: Enhanced with new monitoring and management capabilities
- **Performance Metrics**: Expanded monitoring and alerting features
- **Security**: Updated authentication and authorization procedures

### 📈 Roadmap

#### Planned Documentation Additions
- **Deployment Guide**: Production deployment and scaling
- **Integration Guide**: Third-party service integrations
- **Performance Tuning**: Advanced optimization techniques
- **Backup & Recovery**: Data protection and disaster recovery

#### Feature Documentation Pipeline
- Real-time streaming updates (SSE)
- Advanced analytics and reporting
- Multi-tenant architecture
- External API integrations

---

For specific implementation details, please refer to the individual documentation files linked above. Each guide provides comprehensive coverage of its respective system area with practical examples and troubleshooting information.
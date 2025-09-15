# Admin Dashboard Documentation

## Overview

The Admin Dashboard provides comprehensive system administration and monitoring capabilities for the Portfolio Manager application. It includes user management, system monitoring, market data oversight, and portfolio update analytics.

## Access Control

### Authentication & Authorization
- **Admin Role Required**: All admin dashboard features require `UserRole.ADMIN`
- **JWT Authentication**: Admin users must be authenticated with valid JWT tokens
- **Role-based UI**: Frontend conditionally renders admin navigation based on user role
- **Backend Security**: All admin API endpoints enforce admin role validation

### Admin User Management
```sql
-- Create admin user (via database or admin interface)
UPDATE users SET role = 'ADMIN' WHERE email = 'admin@example.com';
```

## Dashboard Sections

### 1. Main Dashboard (`/admin`)

**Key Metrics Display:**
- Total Users and Active Users
- Total Portfolios across all users
- Admin Users count
- System Status indicators

**Quick Actions:**
- Navigate to User Management
- Access System Monitoring
- View Market Data Status
- Portfolio Update Monitoring

**Live Components:**
- Portfolio Update Metrics (integrated)
- Recent System Activities
- Real-time status indicators

### 2. User Management (`/admin/users`)

**Features:**
- View all registered users
- User role management (Admin/User)
- Account status monitoring (Active/Inactive)
- User activity tracking
- Bulk user operations

**User Information:**
- Email and profile details
- Registration dates
- Last login tracking
- Portfolio counts per user

### 3. System Monitoring (`/admin/system`)

**System Health:**
- Application uptime and status
- Database connectivity
- API response times
- Memory and resource usage

**Performance Metrics:**
- Request/response statistics
- Error rates and types
- Database query performance
- Background job status

### 4. Market Data Management (`/admin/market-data`)

**Provider Management:**
- Yahoo Finance provider status
- Alpha Vantage configuration
- API usage statistics
- Rate limiting monitoring

**Data Quality:**
- Price update frequencies
- Data freshness indicators
- Provider reliability metrics
- Error tracking and alerts

**Live Activities:**
- Real-time API call monitoring
- Success/failure tracking
- Response time analytics
- Provider switching logic

### 5. Portfolio Update Monitoring (`/admin/portfolio-metrics`)

**Comprehensive Metrics:**
- 24-hour update statistics
- Success/failure rates
- Response time analytics
- Queue health monitoring

**Performance Analysis:**
- Update frequency patterns
- Storm protection metrics
- Bulk operation efficiency
- Error categorization

**Real-time Features:**
- 10-second auto-refresh
- Live update indicators
- Performance trends
- Alert notifications

### 6. Audit Logs (`/admin/audit-logs`)

**Activity Tracking:**
- User login/logout events
- Portfolio creation/modification
- Transaction additions
- Administrative actions

**Audit Features:**
- Searchable event logs
- Timestamp tracking
- User attribution
- Event metadata
- Compliance reporting

## API Endpoints

### System Management
```
GET /api/v1/admin/system/metrics       # System performance metrics
GET /api/v1/admin/users                # User management
GET /api/v1/admin/users/{id}           # Specific user details
POST /api/v1/admin/users/{id}/role     # Update user role
```

### Market Data Administration
```
GET /api/v1/admin/market-data/status        # Provider status
GET /api/v1/admin/market-data/providers     # All providers
POST /api/v1/admin/market-data/refresh      # Manual refresh
GET /api/v1/admin/api-usage                 # API usage stats
```

### Portfolio Monitoring
```
GET /api/v1/admin/portfolio-updates/stats/24h         # 24-hour statistics
GET /api/v1/admin/portfolio-updates/queue/health      # Queue health
GET /api/v1/admin/portfolio-updates/storm-protection  # Coalescing metrics
GET /api/v1/admin/portfolio-updates/performance       # Performance breakdown
GET /api/v1/admin/portfolio-updates/lag-analysis      # Update lag analysis
GET /api/v1/admin/portfolio-updates/metrics/export    # Prometheus export
```

### Activity & Audit
```
GET /api/v1/admin/dashboard/recent-activities  # Recent system activities
GET /api/v1/admin/audit-logs                   # Comprehensive audit logs
GET /api/v1/admin/scheduler/status             # Background job status
```

## Live Activity System

### Real-time Monitoring
The admin dashboard includes live activity feeds showing:

**Market Data Activities:**
- API calls to Yahoo Finance/Alpha Vantage
- Stock price fetches with symbols and prices
- Response times and success rates
- Provider performance comparisons

**Portfolio Activities:**
- Real-time portfolio updates
- Update triggers and sources
- Performance metrics
- Error tracking

**System Activities:**
- User authentication events
- Administrative actions
- System health changes
- Background job executions

### Activity Types
```
API_CALL              # Individual market data requests
BULK_PRICE_UPDATE     # Multiple symbol updates
PROVIDER_FAILURE      # Provider unavailability
API_ERROR             # Individual API failures
RATE_LIMIT            # Rate limiting events
PORTFOLIO_UPDATE      # Portfolio value updates
USER_LOGIN            # Authentication events
ADMIN_ACTION          # Administrative operations
```

## Frontend Components

### Navigation Structure
```
/admin/
├── Dashboard (Main overview)
├── Users (User management)
├── System (System monitoring)
├── Market Data (Provider management)
├── Portfolio Metrics (Update monitoring)
└── Audit Logs (Activity tracking)
```

### Component Architecture
```
AdminLayout
├── AdminNavigation (Role-based menu)
├── AdminDashboard (Main dashboard)
├── UserManagement (User admin)
├── SystemMonitoring (Health metrics)
├── MarketDataAdmin (Provider management)
├── PortfolioUpdateMetrics (Update monitoring)
└── AuditLogTable (Activity logs)
```

### Authentication Context
```typescript
// Admin role checking
const { user } = useAuth()
const isAdmin = user?.role === 'ADMIN'

// Conditional rendering
{isAdmin && (
  <AdminNavigation />
)}
```

## Monitoring & Alerting

### System Health Indicators
- **Healthy**: All systems operational
- **Warning**: Performance degradation detected
- **Error**: Critical system failures

### Alert Thresholds
- **API Response Time**: > 2 seconds average
- **Error Rate**: > 5% over 1 hour
- **Queue Backup**: > 100 pending operations
- **Provider Failures**: > 3 consecutive failures

### Notification Systems
- Dashboard visual indicators
- Real-time status updates
- Email notifications (configurable)
- Slack integration (optional)

## Security Considerations

### Access Control
- Role-based access control (RBAC)
- JWT token validation on all endpoints
- Admin role required for all operations
- Session management and timeout

### Data Protection
- Sensitive information masking
- Audit trail for all admin actions
- Secure API key management
- Database access controls

### Monitoring
- Failed authentication tracking
- Suspicious activity detection
- Admin action logging
- Rate limiting on admin endpoints

## Development & Testing

### Local Development
```bash
# Start backend with admin features
uv run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload

# Start frontend
npm run dev

# Access admin dashboard (requires admin user)
open http://localhost:3000/admin
```

### Creating Admin Users
```python
# Via Python script or database migration
from src.models import User, UserRole
from src.core.auth import hash_password

admin_user = User(
    email="admin@example.com",
    password_hash=hash_password("admin123"),
    first_name="Admin",
    last_name="User",
    role=UserRole.ADMIN
)
db.add(admin_user)
db.commit()
```

### Testing Admin Features
```bash
# Test admin API endpoints
uv run pytest tests/integration/test_admin_*.py -v

# Test user management
uv run pytest tests/integration/test_user_management.py -v

# Test role-based access
uv run pytest tests/unit/test_auth.py::test_admin_role_required -v
```

## Configuration

### Environment Variables
```bash
# Admin Dashboard Configuration
ADMIN_SESSION_TIMEOUT=3600          # Session timeout in seconds
ADMIN_MAX_CONCURRENT_SESSIONS=3     # Max concurrent admin sessions
ADMIN_AUDIT_RETENTION_DAYS=90       # Audit log retention
ADMIN_ALERT_EMAIL_ENABLED=true      # Enable email alerts
```

### Feature Flags
```bash
ENABLE_USER_MANAGEMENT=true         # Enable user admin features
ENABLE_SYSTEM_MONITORING=true       # Enable system monitoring
ENABLE_AUDIT_LOGGING=true           # Enable audit trails
ENABLE_PORTFOLIO_MONITORING=true    # Enable portfolio metrics
```

## Troubleshooting

### Common Issues

#### Access Denied
1. Verify user has `ADMIN` role in database
2. Check JWT token validity and expiration
3. Ensure proper authentication headers
4. Review role assignment and permissions

#### Missing Data/Metrics
1. Verify database migrations are up to date
2. Check background job execution
3. Review API endpoint connectivity
4. Ensure data collection services are running

#### Performance Issues
1. Check database query performance
2. Review API response times
3. Monitor system resource usage
4. Analyze concurrent user load

### Debug Commands
```bash
# Check admin user roles
SELECT email, role FROM users WHERE role = 'ADMIN';

# Verify recent admin activities
SELECT * FROM audit_logs WHERE event_type LIKE 'ADMIN_%'
ORDER BY created_at DESC LIMIT 10;

# Check system metrics collection
SELECT COUNT(*) FROM portfolio_update_metrics
WHERE created_at > NOW() - INTERVAL '1 hour';
```

## Future Enhancements

### Planned Features
- **Advanced Analytics**: Deeper system insights and reporting
- **Custom Dashboards**: User-configurable dashboard layouts
- **Alert Management**: Advanced alerting rules and escalation
- **Bulk Operations**: Mass user/portfolio management tools
- **System Configuration**: Runtime configuration management

### Integration Opportunities
- **External Monitoring**: Grafana, DataDog, New Relic integration
- **Notification Systems**: Slack, Teams, PagerDuty integration
- **Single Sign-On**: SAML/OAuth integration for admin access
- **API Gateway**: Enhanced security and rate limiting
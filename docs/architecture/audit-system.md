# Audit System Documentation

## Overview

The Portfolio Manager includes a comprehensive audit logging system that tracks all user actions across portfolios and transactions. This system provides complete accountability, regulatory compliance, and administrative oversight capabilities.

## Table of Contents

- [System Architecture](#system-architecture)
- [What is Audited](#what-is-audited)
- [What is NOT Audited](#what-is-not-audited)
- [Audit Log Structure](#audit-log-structure)
- [Admin Dashboard](#admin-dashboard)
- [API Endpoints](#api-endpoints)
- [Security Considerations](#security-considerations)
- [Compliance Features](#compliance-features)

## System Architecture

### Components

1. **Database Layer**: `audit_logs` table with comprehensive schema
2. **Service Layer**: `AuditService` class for creating audit entries
3. **API Integration**: Automatic audit logging in portfolio and transaction endpoints
4. **Admin Interface**: Frontend dashboard for viewing and searching audit logs

### Data Flow

```
User Action → API Endpoint → Business Logic → AuditService → Database → Admin Dashboard
```

## What is Audited

### ✅ Portfolio Operations

| Action | Event Type | Details Captured |
|--------|------------|------------------|
| **Create Portfolio** | `PORTFOLIO_CREATED` | Portfolio name, description, user ID, timestamp |
| **Update Portfolio** | `PORTFOLIO_UPDATED` | Changed fields (before/after values), user ID |
| **Soft Delete Portfolio** | `PORTFOLIO_SOFT_DELETED` | Portfolio name, user ID, deletion timestamp |
| **Hard Delete Portfolio** | `PORTFOLIO_HARD_DELETED` | Portfolio name, user ID, permanent deletion |

### ✅ Transaction Operations

| Action | Event Type | Details Captured |
|--------|------------|------------------|
| **Create Transaction** | `TRANSACTION_CREATED` | Transaction type, symbol, quantity, price, portfolio ID |
| **Update Transaction** | `TRANSACTION_UPDATED` | Changed fields (before/after values), transaction details |
| **Delete Transaction** | `TRANSACTION_DELETED` | Transaction type, symbol, portfolio ID, user ID |

### ✅ User Context (All Operations)

- **User Attribution**: Every action linked to specific user ID
- **IP Address**: Source IP address of the request
- **User Agent**: Browser/client information
- **Timestamp**: Precise UTC timestamp of the action
- **Request Context**: Additional metadata from HTTP request

## What is NOT Audited

### ❌ Read-Only Operations

- **Portfolio Viewing**: Listing or viewing portfolio details
- **Transaction Viewing**: Browsing transaction history
- **Holdings Viewing**: Checking current holdings
- **Performance Queries**: Portfolio performance calculations

### ❌ System Operations

- **Market Data Updates**: Automatic price updates from external APIs
- **Background Jobs**: Scheduled tasks and maintenance operations
- **Health Checks**: System monitoring and status checks
- **Authentication Events**: Login/logout events (separate auth logging)

### ❌ Admin Operations (Partially)

- **Audit Log Viewing**: Admins viewing audit logs (prevents infinite loops)
- **System Settings**: Configuration changes (should be added if needed)
- **User Management**: Admin actions on user accounts (should be added if needed)

## Audit Log Structure

### Database Schema

```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,           -- Enum: PORTFOLIO_CREATED, etc.
    event_description TEXT NOT NULL,           -- Human-readable description
    user_id UUID NOT NULL,                     -- Foreign key to users.id
    entity_type VARCHAR(50) NOT NULL,          -- portfolio, transaction, holding
    entity_id VARCHAR(100) NOT NULL,           -- ID of affected entity
    timestamp DATETIME NOT NULL,               -- When event occurred (UTC)
    event_metadata JSON,                       -- Additional structured data
    ip_address VARCHAR(45),                    -- IPv4/IPv6 address
    user_agent TEXT,                           -- Browser/client info
    created_at DATETIME NOT NULL,              -- When audit record was created
    updated_at DATETIME NOT NULL               -- When audit record was updated
);
```

### Event Types

```typescript
enum AuditEventType {
    // Portfolio events
    PORTFOLIO_CREATED = "portfolio_created",
    PORTFOLIO_UPDATED = "portfolio_updated",
    PORTFOLIO_DELETED = "portfolio_deleted",
    PORTFOLIO_SOFT_DELETED = "portfolio_soft_deleted",
    PORTFOLIO_HARD_DELETED = "portfolio_hard_deleted",

    // Transaction events
    TRANSACTION_CREATED = "transaction_created",
    TRANSACTION_UPDATED = "transaction_updated",
    TRANSACTION_DELETED = "transaction_deleted",

    // Future expansion
    HOLDING_CREATED = "holding_created",
    HOLDING_UPDATED = "holding_updated",
    HOLDING_DELETED = "holding_deleted",
    USER_LOGIN = "user_login",
    USER_LOGOUT = "user_logout",
    ADMIN_ACTION_PERFORMED = "admin_action_performed"
}
```

### Metadata Examples

#### Portfolio Creation
```json
{
    "portfolio_name": "My Investment Portfolio",
    "portfolio_description": "Long-term investment strategy"
}
```

#### Portfolio Update
```json
{
    "portfolio_name": "My Investment Portfolio",
    "changes": {
        "name": {
            "old": "Old Portfolio Name",
            "new": "My Investment Portfolio"
        },
        "description": {
            "old": "Old description",
            "new": "Updated description"
        }
    }
}
```

#### Transaction Creation
```json
{
    "transaction_type": "BUY",
    "symbol": "AAPL",
    "quantity": 100.0,
    "price_per_share": 150.25,
    "portfolio_id": "uuid-portfolio-id"
}
```

## Admin Dashboard

### Access Requirements

- **Admin Role Required**: Only users with `UserRole.ADMIN` can access audit logs
- **Authentication**: Valid JWT token required
- **Route**: `/admin/audit-logs`

### Features

#### Search and Filtering
- **Full-text Search**: Search across event descriptions
- **Event Type Filter**: Filter by specific event types
- **Entity Type Filter**: Filter by portfolio, transaction, etc.
- **User Filter**: Filter by user ID or email
- **Date Range Filter**: Filter by timestamp range

#### Display Features
- **Pagination**: Efficient handling of large datasets
- **Sorting**: Sort by timestamp, event type, or user
- **Real-time Updates**: New audit entries appear immediately
- **Metadata Viewer**: Hover to view detailed event metadata

#### Export Capabilities (Future)
- **CSV Export**: Export filtered results
- **Date Range Export**: Bulk export for compliance reporting
- **Scheduled Reports**: Automated audit reports

## API Endpoints

### Get Audit Logs
```http
GET /api/v1/admin/audit-logs
Authorization: Bearer <admin-jwt-token>
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50, max: 1000)
- `user_id`: Filter by user ID
- `event_type`: Filter by event type
- `entity_type`: Filter by entity type
- `entity_id`: Filter by specific entity
- `date_from`: Filter from date (ISO format)
- `date_to`: Filter to date (ISO format)
- `search`: Full-text search
- `sort_by`: Sort field (timestamp, event_type, user_id)
- `sort_order`: Sort order (asc, desc)

**Response Format:**
```json
{
    "data": [
        {
            "id": 1,
            "event_type": "portfolio_created",
            "event_description": "Portfolio 'My Portfolio' created",
            "user_id": "uuid",
            "user_email": "user@example.com",
            "entity_type": "portfolio",
            "entity_id": "portfolio-uuid",
            "timestamp": "2025-09-15T06:32:10.764147Z",
            "event_metadata": {...},
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0...",
            "created_at": "2025-09-15T06:32:10.764147Z"
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 10,
        "total_items": 500,
        "items_per_page": 50
    },
    "filters": {
        "user_id": null,
        "event_type": null,
        "search": null
    },
    "meta": {
        "request_timestamp": "2025-09-15T06:32:10.764147Z",
        "processing_time_ms": 45,
        "total_events_in_system": 1250
    }
}
```

### Get Specific Audit Entry
```http
GET /api/v1/admin/audit-logs/{audit_id}
Authorization: Bearer <admin-jwt-token>
```

### Get Audit Statistics
```http
GET /api/v1/admin/audit-logs/stats
Authorization: Bearer <admin-jwt-token>
```

## Security Considerations

### Data Protection
- **Sensitive Data**: Audit logs may contain sensitive financial information
- **Access Control**: Strict admin-only access with role verification
- **Encryption**: Database encryption recommended for compliance
- **Retention**: Consider data retention policies for audit logs

### Preventing Audit Tampering
- **Immutable Records**: Audit logs should never be modified after creation
- **Database Permissions**: Restrict direct database access to audit tables
- **Backup Strategy**: Regular backups of audit data for integrity
- **Monitoring**: Monitor for unusual audit log access patterns

### Privacy Considerations
- **User Attribution**: All actions are linked to specific users
- **IP Tracking**: IP addresses are logged for security purposes
- **Data Minimization**: Only necessary data is captured in metadata
- **GDPR Compliance**: Consider right to be forgotten vs. audit requirements

## Compliance Features

### Regulatory Requirements
- **SOX Compliance**: Financial transaction tracking for public companies
- **GDPR**: User consent and data protection considerations
- **Industry Standards**: Meets common financial services audit requirements

### Audit Trail Features
- **Complete History**: All portfolio and transaction changes tracked
- **Temporal Integrity**: Precise timestamps for all events
- **User Attribution**: Every action linked to authenticated user
- **Change Tracking**: Before/after values for all modifications
- **Non-Repudiation**: IP and user agent tracking for accountability

### Reporting Capabilities
- **Time-based Reports**: Activity reports by date range
- **User Activity Reports**: Individual user action summaries
- **Entity Change Reports**: Complete history for specific portfolios/transactions
- **Compliance Dashboards**: High-level audit statistics and trends

## Implementation Notes

### Error Handling
- **Graceful Degradation**: Audit failures do not break main operations
- **Logging**: Audit service errors are logged separately
- **Retry Logic**: Consider implementing retry for transient failures
- **Monitoring**: Monitor audit service health and performance

### Performance Considerations
- **Database Indexes**: Optimized indexes for common query patterns
- **Pagination**: Efficient handling of large audit datasets
- **Background Processing**: Consider async audit logging for high-volume systems
- **Archival Strategy**: Plan for long-term audit data management

### Future Enhancements
- **Real-time Notifications**: Alert on suspicious activity patterns
- **Advanced Analytics**: Machine learning for anomaly detection
- **Integration**: Export to external SIEM or compliance systems
- **Enhanced Metadata**: Capture additional context for specific event types

## Troubleshooting

### Common Issues

#### Audit Logs Not Appearing
1. Check user has admin role
2. Verify audit service is properly integrated in API endpoints
3. Check database connectivity and table existence
4. Review application logs for audit service errors

#### Performance Issues
1. Check database indexes on audit_logs table
2. Consider pagination limits and query complexity
3. Monitor audit service performance metrics
4. Review large metadata objects in audit entries

#### Missing Context Information
1. Verify request context extraction in API endpoints
2. Check IP address forwarding in production environments
3. Ensure user agent headers are properly captured
4. Review audit service integration for all CRUD operations
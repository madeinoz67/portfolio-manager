# Audit Log API Reference

## Overview

The Audit Log API provides endpoints for administrators to view, search, and analyze audit logs. All endpoints require admin authentication and return comprehensive audit trail information.

## Authentication

All audit log endpoints require:
- Valid JWT token in Authorization header
- User role must be `ADMIN`
- Active user session

```http
Authorization: Bearer <jwt_token>
```

## Base URL

```
/api/v1/admin/audit-logs
```

## Endpoints

### 1. List Audit Logs

Retrieve paginated list of audit logs with optional filtering and searching.

```http
GET /api/v1/admin/audit-logs
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | `1` | Page number (1-based) |
| `limit` | integer | `50` | Items per page (max: 1000) |
| `user_id` | string | - | Filter by user ID (UUID) |
| `event_type` | string | - | Filter by event type |
| `entity_type` | string | - | Filter by entity type |
| `entity_id` | string | - | Filter by specific entity ID |
| `date_from` | string | - | Filter from date (ISO 8601 format) |
| `date_to` | string | - | Filter to date (ISO 8601 format) |
| `search` | string | - | Full-text search in descriptions |
| `sort_by` | string | `timestamp` | Sort field |
| `sort_order` | string | `desc` | Sort order (`asc` or `desc`) |

#### Valid Event Types

- `portfolio_created`
- `portfolio_updated`
- `portfolio_deleted`
- `portfolio_soft_deleted`
- `portfolio_hard_deleted`
- `transaction_created`
- `transaction_updated`
- `transaction_deleted`

#### Valid Entity Types

- `portfolio`
- `transaction`
- `user`
- `api_key`

#### Valid Sort Fields

- `timestamp`
- `event_type`
- `user_id`
- `entity_type`
- `created_at`

#### Example Request

```http
GET /api/v1/admin/audit-logs?page=1&limit=25&event_type=portfolio_created&date_from=2025-09-01T00:00:00Z&date_to=2025-09-30T23:59:59Z&sort_by=timestamp&sort_order=desc
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Format

```json
{
    "data": [
        {
            "id": 1,
            "event_type": "portfolio_created",
            "event_description": "Portfolio 'Tech Investments' created",
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "user_email": "john.doe@company.com",
            "entity_type": "portfolio",
            "entity_id": "987fcdeb-51a2-43d7-8c9e-123456789abc",
            "timestamp": "2025-09-15T14:32:10.764147Z",
            "event_metadata": {
                "portfolio_name": "Tech Investments",
                "portfolio_description": "Technology sector investments"
            },
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "created_at": "2025-09-15T14:32:10.764147Z"
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 20,
        "total_items": 500,
        "items_per_page": 25
    },
    "filters": {
        "user_id": null,
        "event_type": "portfolio_created",
        "entity_type": null,
        "entity_id": null,
        "date_from": "2025-09-01T00:00:00Z",
        "date_to": "2025-09-30T23:59:59Z",
        "search": null,
        "sort_by": "timestamp",
        "sort_order": "desc"
    },
    "meta": {
        "request_timestamp": "2025-09-15T14:35:22.123456Z",
        "processing_time_ms": 42,
        "total_events_in_system": 15420
    }
}
```

#### Response Status Codes

- `200 OK` - Success
- `400 Bad Request` - Invalid query parameters
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - User is not an admin
- `422 Unprocessable Entity` - Invalid date format or other validation errors
- `500 Internal Server Error` - Server error

### 2. Get Specific Audit Entry

Retrieve detailed information about a specific audit log entry.

```http
GET /api/v1/admin/audit-logs/{audit_id}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `audit_id` | integer | ID of the audit log entry |

#### Example Request

```http
GET /api/v1/admin/audit-logs/123
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Format

```json
{
    "id": 123,
    "event_type": "transaction_updated",
    "event_description": "Transaction BUY AAPL updated",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_email": "jane.smith@company.com",
    "entity_type": "transaction",
    "entity_id": "456e7890-a12b-34c5-d678-901234567def",
    "timestamp": "2025-09-15T14:45:30.123456Z",
    "event_metadata": {
        "transaction_type": "BUY",
        "symbol": "AAPL",
        "portfolio_id": "987fcdeb-51a2-43d7-8c9e-123456789abc",
        "changes": {
            "quantity": {
                "old": 100,
                "new": 150
            },
            "price_per_share": {
                "old": 120.50,
                "new": 125.00
            }
        }
    },
    "ip_address": "10.0.1.50",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "created_at": "2025-09-15T14:45:30.123456Z",
    "updated_at": "2025-09-15T14:45:30.123456Z"
}
```

#### Response Status Codes

- `200 OK` - Success
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - User is not an admin
- `404 Not Found` - Audit entry not found
- `500 Internal Server Error` - Server error

### 3. Get Audit Statistics

Retrieve aggregated statistics about audit logs for dashboards and reporting.

```http
GET /api/v1/admin/audit-logs/stats
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `date_from` | string | 30 days ago | Statistics from date (ISO 8601) |
| `date_to` | string | now | Statistics to date (ISO 8601) |
| `user_id` | string | - | Filter statistics by user |

#### Example Request

```http
GET /api/v1/admin/audit-logs/stats?date_from=2025-09-01T00:00:00Z&date_to=2025-09-30T23:59:59Z
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response Format

```json
{
    "stats": {
        "total_events": 15420,
        "events_today": 145,
        "events_this_week": 987,
        "events_this_month": 4234,
        "event_types_breakdown": {
            "portfolio_created": 234,
            "portfolio_updated": 567,
            "portfolio_deleted": 12,
            "transaction_created": 1890,
            "transaction_updated": 456,
            "transaction_deleted": 78
        },
        "user_activity_breakdown": {
            "john.doe@company.com": 456,
            "jane.smith@company.com": 234,
            "admin@company.com": 123
        },
        "entity_types_breakdown": {
            "portfolio": 813,
            "transaction": 2424,
            "user": 5,
            "api_key": 12
        },
        "daily_activity": [
            {
                "date": "2025-09-01",
                "count": 45
            },
            {
                "date": "2025-09-02",
                "count": 67
            }
        ],
        "hourly_pattern": {
            "00": 5,
            "01": 2,
            "09": 45,
            "10": 67,
            "14": 89
        }
    },
    "generated_at": "2025-09-15T14:50:15.789012Z",
    "date_range": {
        "from": "2025-09-01T00:00:00Z",
        "to": "2025-09-30T23:59:59Z"
    }
}
```

#### Response Status Codes

- `200 OK` - Success
- `400 Bad Request` - Invalid date parameters
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - User is not an admin
- `500 Internal Server Error` - Server error

### 4. Export Audit Logs

Export audit logs in various formats for compliance reporting.

```http
POST /api/v1/admin/audit-logs/export
```

#### Request Body

```json
{
    "format": "csv",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "event_type": "portfolio_created",
    "entity_type": "portfolio",
    "entity_id": "987fcdeb-51a2-43d7-8c9e-123456789abc",
    "date_from": "2025-09-01T00:00:00Z",
    "date_to": "2025-09-30T23:59:59Z",
    "search": "investment",
    "include_metadata": true
}
```

#### Request Body Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `format` | string | Yes | Export format (`csv` or `json`) |
| `user_id` | string | No | Filter by user ID |
| `event_type` | string | No | Filter by event type |
| `entity_type` | string | No | Filter by entity type |
| `entity_id` | string | No | Filter by entity ID |
| `date_from` | string | No | Filter from date |
| `date_to` | string | No | Filter to date |
| `search` | string | No | Full-text search |
| `include_metadata` | boolean | No | Include event metadata (default: true) |

#### Example Request

```http
POST /api/v1/admin/audit-logs/export
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
    "format": "csv",
    "date_from": "2025-09-01T00:00:00Z",
    "date_to": "2025-09-30T23:59:59Z",
    "include_metadata": true
}
```

#### Response Format (CSV)

```http
Content-Type: text/csv
Content-Disposition: attachment; filename="audit_logs_2025-09-01_to_2025-09-30.csv"

ID,Event Type,Description,User Email,Entity Type,Entity ID,Timestamp,IP Address,User Agent,Metadata
1,portfolio_created,"Portfolio 'Tech Investments' created",john.doe@company.com,portfolio,987fcdeb-51a2-43d7-8c9e-123456789abc,2025-09-15T14:32:10.764147Z,192.168.1.100,"Mozilla/5.0...","{""portfolio_name"":""Tech Investments""}"
```

#### Response Format (JSON)

```http
Content-Type: application/json
Content-Disposition: attachment; filename="audit_logs_2025-09-01_to_2025-09-30.json"

{
    "export_info": {
        "format": "json",
        "generated_at": "2025-09-15T14:55:30.123456Z",
        "filters_applied": {
            "date_from": "2025-09-01T00:00:00Z",
            "date_to": "2025-09-30T23:59:59Z"
        },
        "total_records": 234
    },
    "audit_logs": [
        {
            "id": 1,
            "event_type": "portfolio_created",
            "event_description": "Portfolio 'Tech Investments' created",
            "user_email": "john.doe@company.com",
            "entity_type": "portfolio",
            "entity_id": "987fcdeb-51a2-43d7-8c9e-123456789abc",
            "timestamp": "2025-09-15T14:32:10.764147Z",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0...",
            "event_metadata": {
                "portfolio_name": "Tech Investments",
                "portfolio_description": "Technology sector investments"
            }
        }
    ]
}
```

#### Response Status Codes

- `200 OK` - Success (file download)
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - User is not an admin
- `413 Payload Too Large` - Export request too large
- `500 Internal Server Error` - Server error

## Error Response Format

All error responses follow this format:

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid date format",
        "details": {
            "field": "date_from",
            "received": "invalid-date",
            "expected": "ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)"
        }
    },
    "timestamp": "2025-09-15T14:30:45.123456Z",
    "path": "/api/v1/admin/audit-logs"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `UNAUTHORIZED` | Missing or invalid authentication |
| `FORBIDDEN` | User lacks admin privileges |
| `VALIDATION_ERROR` | Invalid request parameters |
| `NOT_FOUND` | Requested resource not found |
| `RATE_LIMITED` | Too many requests |
| `INTERNAL_ERROR` | Server error |

## Rate Limiting

Audit log endpoints are rate-limited to prevent abuse:

- **Standard requests**: 100 requests per minute per user
- **Export requests**: 5 requests per minute per user
- **Statistics requests**: 20 requests per minute per user

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642492800
```

## Query Optimization Tips

### 1. Use Specific Filters

```http
# Good: Specific filters reduce database load
GET /api/v1/admin/audit-logs?user_id=123&event_type=portfolio_created&date_from=2025-09-01

# Avoid: Broad queries without filters
GET /api/v1/admin/audit-logs?limit=1000
```

### 2. Reasonable Date Ranges

```http
# Good: Limited date range
GET /api/v1/admin/audit-logs?date_from=2025-09-01&date_to=2025-09-30

# Avoid: Very large date ranges
GET /api/v1/admin/audit-logs?date_from=2020-01-01&date_to=2025-12-31
```

### 3. Pagination

```http
# Good: Use pagination for large datasets
GET /api/v1/admin/audit-logs?page=1&limit=50

# Avoid: Requesting too many items at once
GET /api/v1/admin/audit-logs?limit=10000
```

## Metadata Examples

### Portfolio Events

#### Portfolio Created
```json
{
    "portfolio_name": "Tech Investments",
    "portfolio_description": "Technology sector focused portfolio"
}
```

#### Portfolio Updated
```json
{
    "portfolio_name": "Tech Investments",
    "changes": {
        "name": {
            "old": "Old Portfolio Name",
            "new": "Tech Investments"
        },
        "description": {
            "old": "Old description",
            "new": "Technology sector focused portfolio"
        }
    }
}
```

#### Portfolio Deleted
```json
{
    "portfolio_name": "Tech Investments",
    "is_hard_delete": false,
    "holdings_count": 5,
    "total_value": 15420.50
}
```

### Transaction Events

#### Transaction Created
```json
{
    "transaction_type": "BUY",
    "symbol": "AAPL",
    "quantity": 100.0,
    "price_per_share": 150.25,
    "total_amount": 15025.00,
    "fees": 9.95,
    "portfolio_id": "987fcdeb-51a2-43d7-8c9e-123456789abc"
}
```

#### Transaction Updated
```json
{
    "transaction_type": "BUY",
    "symbol": "AAPL",
    "portfolio_id": "987fcdeb-51a2-43d7-8c9e-123456789abc",
    "changes": {
        "quantity": {
            "old": 100.0,
            "new": 150.0
        },
        "price_per_share": {
            "old": 150.25,
            "new": 148.75
        },
        "notes": {
            "old": "Initial purchase",
            "new": "Adjusted purchase - corrected quantity"
        }
    }
}
```

#### Transaction Deleted
```json
{
    "transaction_type": "SELL",
    "symbol": "TSLA",
    "quantity": 50.0,
    "portfolio_id": "987fcdeb-51a2-43d7-8c9e-123456789abc",
    "deletion_reason": "User requested removal"
}
```

## Integration Examples

### JavaScript/TypeScript Client

```typescript
interface AuditLogResponse {
    data: AuditLogEntry[]
    pagination: PaginationInfo
    filters: FilterInfo
    meta: MetaInfo
}

interface AuditLogEntry {
    id: number
    event_type: string
    event_description: string
    user_id: string
    user_email: string
    entity_type: string
    entity_id: string
    timestamp: string
    event_metadata: Record<string, any>
    ip_address?: string
    user_agent?: string
    created_at: string
}

class AuditLogClient {
    private baseUrl = '/api/v1/admin/audit-logs'
    private token: string

    constructor(authToken: string) {
        this.token = authToken
    }

    async getAuditLogs(params: {
        page?: number
        limit?: number
        user_id?: string
        event_type?: string
        date_from?: string
        date_to?: string
        search?: string
    }): Promise<AuditLogResponse> {
        const searchParams = new URLSearchParams()

        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) {
                searchParams.append(key, value.toString())
            }
        })

        const response = await fetch(`${this.baseUrl}?${searchParams}`, {
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            }
        })

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`)
        }

        return response.json()
    }

    async getAuditEntry(auditId: number): Promise<AuditLogEntry> {
        const response = await fetch(`${this.baseUrl}/${auditId}`, {
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            }
        })

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`)
        }

        return response.json()
    }

    async exportAuditLogs(params: {
        format: 'csv' | 'json'
        date_from?: string
        date_to?: string
        user_id?: string
        event_type?: string
    }): Promise<Blob> {
        const response = await fetch(`${this.baseUrl}/export`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        })

        if (!response.ok) {
            throw new Error(`Export Error: ${response.status}`)
        }

        return response.blob()
    }
}

// Usage example
const auditClient = new AuditLogClient('your-jwt-token')

// Get recent portfolio events
const portfolioEvents = await auditClient.getAuditLogs({
    entity_type: 'portfolio',
    date_from: '2025-09-01T00:00:00Z',
    limit: 50
})

// Export transaction events as CSV
const csvBlob = await auditClient.exportAuditLogs({
    format: 'csv',
    entity_type: 'transaction',
    date_from: '2025-09-01T00:00:00Z',
    date_to: '2025-09-30T23:59:59Z'
})
```

### Python Client

```python
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime

class AuditLogClient:
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = f"{base_url}/api/v1/admin/audit-logs"
        self.headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }

    def get_audit_logs(
        self,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get paginated audit logs with optional filtering."""
        params = {k: v for k, v in locals().items()
                 if v is not None and k != 'self'}

        response = requests.get(
            self.base_url,
            params=params,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_audit_entry(self, audit_id: int) -> Dict[str, Any]:
        """Get specific audit log entry."""
        response = requests.get(
            f"{self.base_url}/{audit_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_statistics(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get audit log statistics."""
        params = {k: v for k, v in locals().items()
                 if v is not None and k != 'self'}

        response = requests.get(
            f"{self.base_url}/stats",
            params=params,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def export_audit_logs(
        self,
        format: str,
        **filters
    ) -> bytes:
        """Export audit logs in specified format."""
        data = {'format': format, **filters}

        response = requests.post(
            f"{self.base_url}/export",
            json=data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.content

# Usage example
client = AuditLogClient('https://api.example.com', 'your-jwt-token')

# Get recent activity
recent_logs = client.get_audit_logs(
    date_from='2025-09-01T00:00:00Z',
    limit=100
)

# Get user-specific activity
user_activity = client.get_audit_logs(
    user_id='123e4567-e89b-12d3-a456-426614174000',
    event_type='portfolio_created'
)

# Export compliance report
csv_data = client.export_audit_logs(
    format='csv',
    date_from='2025-09-01T00:00:00Z',
    date_to='2025-09-30T23:59:59Z'
)

with open('audit_report.csv', 'wb') as f:
    f.write(csv_data)
```

## Webhook Integration (Future Enhancement)

Future versions may support webhook notifications for real-time audit monitoring:

```json
POST /api/v1/admin/audit-logs/webhooks

{
    "url": "https://your-server.com/audit-webhook",
    "events": ["portfolio_deleted", "transaction_created"],
    "filters": {
        "user_id": "high-privilege-user-id"
    },
    "secret": "webhook-signing-secret"
}
```

Webhook payload format:
```json
{
    "event": "audit_log_created",
    "timestamp": "2025-09-15T14:30:45.123456Z",
    "data": {
        "audit_entry": { /* full audit log entry */ },
        "severity": "medium",
        "triggers": ["high_value_transaction", "after_hours_activity"]
    },
    "signature": "sha256=..."
}
```
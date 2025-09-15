# API Reference

## Overview

This document provides a comprehensive reference for all API endpoints in the Portfolio Manager application, including authentication, portfolio management, market data, and administrative functions.

## Base URL

```
Local Development: http://localhost:8001/api/v1
Production: https://your-domain.com/api/v1
```

## Authentication

### JWT Token Authentication

All authenticated endpoints require a Bearer token in the Authorization header:

```http
Authorization: Bearer <jwt_token>
```

### Login
```http
POST /auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "USER"
  }
}
```

### Register
```http
POST /auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "first_name": "John",
  "last_name": "Doe"
}
```

### Get Current User
```http
GET /auth/me
```

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "USER",
  "created_at": "2025-01-15T10:00:00Z"
}
```

## Portfolio Management

### List Portfolios
```http
GET /portfolios
```

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "My Portfolio",
    "description": "Investment portfolio",
    "total_value": 10000.00,
    "daily_change": -150.25,
    "daily_change_percent": -1.48,
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-15T15:30:00Z"
  }
]
```

### Get Portfolio Details
```http
GET /portfolios/{portfolio_id}
```

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": "uuid",
  "name": "My Portfolio",
  "description": "Investment portfolio",
  "total_value": 10000.00,
  "daily_change": -150.25,
  "daily_change_percent": -1.48,
  "holdings": [
    {
      "id": "uuid",
      "stock": {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "current_price": 150.00
      },
      "quantity": 10,
      "average_cost": 145.00,
      "current_value": 1500.00,
      "unrealized_gain_loss": 50.00,
      "unrealized_gain_loss_percent": 3.45
    }
  ],
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T15:30:00Z"
}
```

### Create Portfolio
```http
POST /portfolios
```

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "New Portfolio",
  "description": "My investment portfolio"
}
```

### Update Portfolio
```http
PUT /portfolios/{portfolio_id}
```

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "Updated Portfolio Name",
  "description": "Updated description"
}
```

### Delete Portfolio
```http
DELETE /portfolios/{portfolio_id}
```

**Headers:** `Authorization: Bearer <token>`

## Holdings Management

### Add Holding
```http
POST /portfolios/{portfolio_id}/holdings
```

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "symbol": "AAPL",
  "quantity": 10,
  "average_cost": 145.00
}
```

### Update Holding
```http
PUT /portfolios/{portfolio_id}/holdings/{holding_id}
```

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "quantity": 15,
  "average_cost": 147.50
}
```

### Delete Holding
```http
DELETE /portfolios/{portfolio_id}/holdings/{holding_id}
```

**Headers:** `Authorization: Bearer <token>`

## Transactions

### List Transactions
```http
GET /portfolios/{portfolio_id}/transactions
```

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional): Number of transactions to return (default: 50)
- `offset` (optional): Pagination offset (default: 0)

### Add Transaction
```http
POST /portfolios/{portfolio_id}/transactions
```

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "symbol": "AAPL",
  "transaction_type": "BUY",
  "quantity": 10,
  "price": 150.00,
  "transaction_date": "2025-01-15T10:00:00Z",
  "notes": "Monthly investment"
}
```

## Market Data

### Get Stock Price
```http
GET /market-data/price/{symbol}
```

**Response:**
```json
{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "current_price": 150.00,
  "previous_close": 148.50,
  "change": 1.50,
  "change_percent": 1.01,
  "last_updated": "2025-01-15T15:30:00Z"
}
```

### Get Multiple Stock Prices
```http
GET /market-data/prices?symbols=AAPL,GOOGL,MSFT
```

**Response:**
```json
{
  "AAPL": {
    "symbol": "AAPL",
    "current_price": 150.00,
    "change": 1.50,
    "change_percent": 1.01
  },
  "GOOGL": {
    "symbol": "GOOGL",
    "current_price": 2800.00,
    "change": -25.50,
    "change_percent": -0.90
  }
}
```

### Market Data Status
```http
GET /market-data/status
```

**Response:**
```json
{
  "status": "operational",
  "last_update": "2025-01-15T15:30:00Z",
  "next_update": "2025-01-15T15:45:00Z",
  "providers": {
    "yahoo_finance": "active",
    "alpha_vantage": "inactive"
  }
}
```

## Admin Endpoints

> **Note:** All admin endpoints require `UserRole.ADMIN` and valid JWT authentication.

### System Metrics
```http
GET /admin/system/metrics
```

**Headers:** `Authorization: Bearer <admin_token>`

**Response:**
```json
{
  "totalUsers": 150,
  "activeUsers": 89,
  "totalPortfolios": 342,
  "adminUsers": 3,
  "systemStatus": "healthy",
  "lastUpdated": "2025-01-15T15:30:00Z"
}
```

### User Management
```http
GET /admin/users
```

**Headers:** `Authorization: Bearer <admin_token>`

**Response:**
```json
[
  {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "USER",
    "is_active": true,
    "created_at": "2025-01-10T10:00:00Z",
    "last_login": "2025-01-15T14:30:00Z"
  }
]
```

### Update User Role
```http
POST /admin/users/{user_id}/role
```

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body:**
```json
{
  "role": "ADMIN"
}
```

### Market Data Administration
```http
GET /admin/market-data/status
```

**Headers:** `Authorization: Bearer <admin_token>`

**Response:**
```json
{
  "providers": [
    {
      "id": "uuid",
      "name": "yahoo_finance",
      "display_name": "Yahoo Finance",
      "is_enabled": true,
      "last_successful_call": "2025-01-15T15:29:00Z",
      "calls_today": 1247,
      "avg_response_time": 245.5,
      "status": "healthy"
    }
  ],
  "total_calls_today": 1247,
  "avg_response_time": 245.5,
  "error_rate": 0.02
}
```

### API Usage Statistics
```http
GET /admin/api-usage
```

**Headers:** `Authorization: Bearer <admin_token>`

**Response:**
```json
{
  "today": {
    "total_calls": 1247,
    "successful_calls": 1225,
    "failed_calls": 22,
    "avg_response_time": 245.5
  },
  "yesterday": {
    "total_calls": 1189,
    "successful_calls": 1176,
    "failed_calls": 13,
    "avg_response_time": 223.1
  },
  "last_7_days": [
    {
      "date": "2025-01-15",
      "total_calls": 1247,
      "error_rate": 0.018
    }
  ]
}
```

## Portfolio Update Monitoring

### 24-Hour Statistics
```http
GET /admin/portfolio-updates/stats/24h
```

**Headers:** `Authorization: Bearer <admin_token>`

**Response:**
```json
{
  "totalUpdates": 1523,
  "successfulUpdates": 1498,
  "failedUpdates": 25,
  "successRate": 98.36,
  "avgUpdateDurationMs": 234,
  "uniquePortfolios": 89,
  "updateFrequencyPerHour": 63.46,
  "commonErrorTypes": {
    "database_timeout": 12,
    "portfolio_update_error": 8,
    "network_error": 5
  }
}
```

### Queue Health
```http
GET /admin/portfolio-updates/queue/health
```

**Headers:** `Authorization: Bearer <admin_token>`

**Response:**
```json
{
  "currentQueueSize": 15,
  "avgProcessingRate": 12.5,
  "maxQueueSize1h": 45,
  "rateLimitHits1h": 0,
  "memoryUsageTrend": "stable",
  "queueHealthStatus": "healthy"
}
```

### Storm Protection Metrics
```http
GET /admin/portfolio-updates/storm-protection
```

**Headers:** `Authorization: Bearer <admin_token>`

**Response:**
```json
{
  "coalescedUpdates24h": 234,
  "coalescingEfficiency": 15.4,
  "avgCoalescedCount": 3.2,
  "maxCoalescedCount": 12,
  "bulkUpdateOperations": 89,
  "avgBulkSize": 4.7
}
```

### Performance Breakdown
```http
GET /admin/portfolio-updates/performance
```

**Headers:** `Authorization: Bearer <admin_token>`

**Response:**
```json
{
  "byPortfolio": [
    {
      "portfolioId": "uuid",
      "updateCount": 45,
      "avgDuration": 189,
      "successRate": 100.0,
      "lastUpdate": "2025-01-15T15:29:00Z"
    }
  ],
  "bySymbol": [
    {
      "symbol": "AAPL",
      "updateCount": 234,
      "avgDuration": 156,
      "affectedPortfolios": 67
    }
  ],
  "performanceTrends": {
    "hourly": [
      {
        "hour": 15,
        "avgDuration": 234,
        "updateCount": 89,
        "successRate": 98.9
      }
    ]
  }
}
```

### Update Lag Analysis
```http
GET /admin/portfolio-updates/lag-analysis
```

**Headers:** `Authorization: Bearer <admin_token>`

**Response:**
```json
{
  "avgLagMs": 1247,
  "medianLagMs": 856,
  "p95LagMs": 3421,
  "p99LagMs": 5678,
  "lagDistribution": {
    "0-500ms": 45.2,
    "500ms-1s": 23.8,
    "1s-2s": 18.9,
    "2s-5s": 9.4,
    ">5s": 2.7
  }
}
```

### Metrics Export (Prometheus)
```http
GET /admin/portfolio-updates/metrics/export
```

**Headers:** `Authorization: Bearer <admin_token>`

**Response:** (Prometheus format)
```
# HELP portfolio_updates_total Total number of portfolio updates
# TYPE portfolio_updates_total counter
portfolio_updates_total{status="success"} 1498
portfolio_updates_total{status="error"} 25

# HELP portfolio_update_duration_ms Portfolio update duration in milliseconds
# TYPE portfolio_update_duration_ms histogram
portfolio_update_duration_ms_bucket{le="100"} 234
portfolio_update_duration_ms_bucket{le="250"} 1156
portfolio_update_duration_ms_bucket{le="500"} 1445
```

## Audit Logs

### Get Audit Logs
```http
GET /admin/audit-logs
```

**Headers:** `Authorization: Bearer <admin_token>`

**Query Parameters:**
- `limit` (optional): Number of logs to return (default: 50)
- `offset` (optional): Pagination offset (default: 0)
- `event_type` (optional): Filter by event type
- `user_id` (optional): Filter by user ID
- `start_date` (optional): Filter from date (ISO 8601)
- `end_date` (optional): Filter to date (ISO 8601)

**Response:**
```json
[
  {
    "id": "uuid",
    "event_type": "USER_LOGIN",
    "event_description": "User logged in",
    "user_id": "uuid",
    "entity_type": "user",
    "entity_id": "uuid",
    "timestamp": "2025-01-15T14:30:00Z",
    "event_metadata": {
      "login_timestamp": "2025-01-15T14:30:00Z",
      "ip_address": "192.168.1.1"
    },
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0..."
  }
]
```

## Recent Activities

### Dashboard Recent Activities
```http
GET /admin/dashboard/recent-activities
```

**Headers:** `Authorization: Bearer <admin_token>`

**Query Parameters:**
- `limit` (optional): Number of activities to return (default: 10)

**Response:**
```json
[
  {
    "id": "uuid",
    "provider_id": "uuid",
    "activity_type": "API_CALL",
    "description": "Fetched price for AAPL: $150.00",
    "status": "success",
    "timestamp": "2025-01-15T15:29:00Z",
    "activity_metadata": {
      "symbol": "AAPL",
      "price": 150.00,
      "response_time_ms": 234
    }
  }
]
```

## Error Responses

### Error Format
All error responses follow this format:

```json
{
  "error": "error_code",
  "message": "Human readable error message",
  "details": {
    "field": "Additional context if applicable"
  }
}
```

### Common Error Codes
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

### Example Error Responses

**401 Unauthorized:**
```json
{
  "error": "unauthorized",
  "message": "Authentication required"
}
```

**403 Forbidden:**
```json
{
  "error": "forbidden",
  "message": "Admin role required"
}
```

**422 Validation Error:**
```json
{
  "error": "validation_error",
  "message": "Invalid input data",
  "details": {
    "email": "Invalid email format",
    "password": "Password must be at least 8 characters"
  }
}
```

## Rate Limiting

### Limits
- **General API**: 1000 requests per hour per user
- **Market Data**: 500 requests per hour per user
- **Admin API**: 2000 requests per hour per admin user

### Headers
Rate limit information is included in response headers:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1642259400
```

## Pagination

For endpoints that return lists, pagination is handled via query parameters:

**Query Parameters:**
- `limit`: Number of items per page (default: 50, max: 100)
- `offset`: Number of items to skip (default: 0)

**Response Headers:**
```http
X-Total-Count: 1523
X-Page-Count: 31
Link: </api/v1/resource?offset=50&limit=50>; rel="next"
```

## Webhooks (Future)

### Portfolio Update Webhooks
```http
POST /webhooks/portfolio-updates
```

**Payload:**
```json
{
  "event": "portfolio.updated",
  "portfolio_id": "uuid",
  "timestamp": "2025-01-15T15:30:00Z",
  "data": {
    "old_value": 9850.00,
    "new_value": 10000.00,
    "change": 150.00,
    "change_percent": 1.52
  }
}
```
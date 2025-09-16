# Reference Documentation

This directory contains reference documentation and API specifications for the Portfolio Manager application.

## API References

- [API Reference](api-reference.md) - Complete REST API documentation with endpoints, request/response schemas
- [Audit API Reference](audit-api-reference.md) - Audit system API endpoints and functionality

## API Overview

### Authentication
All API endpoints use JWT Bearer token authentication:
```http
Authorization: Bearer <your-jwt-token>
```

### Base URLs
- **Development**: `http://localhost:8001`
- **Production**: `https://your-domain.com`

### Response Format
All API responses follow consistent JSON structure:
```json
{
  "data": {},
  "message": "Success",
  "timestamp": "2025-09-16T12:00:00Z"
}
```

## Key Endpoint Categories

### Authentication (`/api/v1/auth`)
- User registration and login
- Token refresh and validation
- Role-based access control

### Portfolios (`/api/v1/portfolios`)
- CRUD operations for portfolios
- Holdings management
- Performance calculations

### Market Data (`/api/v1/market-data`)
- Real-time price streaming (SSE)
- Price history and current quotes
- Provider status and configuration

### Admin (`/api/v1/admin`)
- User management (Admin only)
- System monitoring and metrics
- Audit log access

### Audit (`/api/v1/audit`)
- Activity logging
- Compliance reporting
- Event tracking

## Usage Examples

### Get Portfolio List
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8001/api/v1/portfolios
```

### Stream Market Data
```javascript
const eventSource = new EventSource('/api/v1/market-data/stream', {
  headers: { 'Authorization': 'Bearer <token>' }
});
```

### Create Portfolio
```bash
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Portfolio", "description": "Test portfolio"}' \
  http://localhost:8001/api/v1/portfolios
```

## Error Handling

All endpoints return standard HTTP status codes:
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden (insufficient role)
- `404` - Not Found
- `500` - Internal Server Error

## Related Documentation

- [Developer](../developer/) - Development guides and patterns
- [Backend](../backend/) - Backend implementation details
- [User Guide](../user-guide/) - End-user documentation
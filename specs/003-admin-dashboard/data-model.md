# Data Model: Admin Dashboard

**Generated**: 2025-09-14 | **Feature**: Admin Dashboard | **Branch**: 003-admin-dashboard

## Overview

This document defines the data models and entities for the admin dashboard feature. The admin dashboard leverages existing user and authentication models while extending frontend types to support role-based functionality.

## Existing Models (Backend) ✅

### User Model
**Location**: `backend/src/models/user.py`

```python
class User(Base):
    id: str = Field(primary_key=True, default_factory=lambda: str(uuid.uuid4()))
    email: str = Field(unique=True, index=True)
    password_hash: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole = Field(default=UserRole.USER)  # ✅ Role field exists
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**Validation Rules**:
- Email must be unique and valid format
- Role must be valid UserRole enum value
- Default role is USER for new registrations
- Admin role assignment requires explicit action

### UserRole Enum
**Location**: `backend/src/models/user_role.py`

```python
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
```

**State Transitions**:
- USER → ADMIN: Admin promotion (admin action required)
- ADMIN → USER: Admin demotion (admin action required)
- No self-modification of roles allowed

### UserResponse Schema
**Location**: `backend/src/models/user.py`

```python
class UserResponse(BaseModel):
    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str  # ✅ Role included in API responses
    is_active: bool
    created_at: str
```

**Usage**: Admin API endpoints return this schema with role information

## Frontend Type Extensions (Required)

### User Interface (TypeScript)
**Location**: `frontend/src/types/auth.ts` (to be extended)

```typescript
// Current interface (missing role)
interface User {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  isActive: boolean;
  createdAt: string;
}

// Required extension
interface User {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  role: 'admin' | 'user';  // ✅ Add role field
  isActive: boolean;
  createdAt: string;
}
```

**Validation Rules**:
- Role must match backend UserRole enum values
- Role determines UI access and navigation visibility
- Default to 'user' role for type safety

### AuthContext State Extension
**Location**: `frontend/src/contexts/AuthContext.tsx` (to be extended)

```typescript
// Current context state
interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

// Required extension
interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
  isAdmin: () => boolean;  // ✅ Add role utility
}
```

**State Management**:
- `isAdmin()` helper function returns `user?.role === 'admin'`
- Role persisted with JWT token information
- Role checked during route navigation

## Admin-Specific Data Models

### AdminUserListItem
**Purpose**: Enhanced user information for admin user management

```typescript
interface AdminUserListItem {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  role: 'admin' | 'user';
  isActive: boolean;
  createdAt: string;
  portfolioCount?: number;  // Admin-specific metadata
  lastLoginAt?: string;     // Admin-specific metadata
}
```

**Data Source**: Combined from user API and portfolio aggregation
**Usage**: Admin user management table display

### SystemMetrics
**Purpose**: Dashboard overview statistics

```typescript
interface SystemMetrics {
  totalUsers: number;
  totalPortfolios: number;
  activeUsers: number;
  adminUsers: number;
  systemStatus: 'healthy' | 'warning' | 'error';
  lastUpdated: string;
}
```

**Data Source**: Aggregated from admin API endpoints
**Usage**: Admin dashboard overview cards

### MarketDataStatus
**Purpose**: External data feed monitoring

```typescript
interface MarketDataStatus {
  providerId: string;
  providerName: string;
  isEnabled: boolean;
  lastUpdate: string;
  apiCallsToday: number;
  monthlyLimit: number;
  monthlyUsage: number;
  costPerCall: number;
  status: 'active' | 'disabled' | 'error' | 'rate_limited';
}
```

**Data Source**: Admin market data API
**Usage**: Data feed management interface

## Entity Relationships

### User → Portfolio (Existing)
- One user can have multiple portfolios
- Admin users can view all portfolios across users
- Regular users can only access their own portfolios

### User → AdminUserListItem (New)
- One-to-one relationship for admin views
- Enhanced with portfolio count and activity metadata
- Only accessible by admin users

### User → AuditLog (Future)
- One admin user can have multiple audit log entries
- Tracks administrative actions and system changes
- Required for compliance and security monitoring

## Access Control Matrix

| Entity | Regular User | Admin User |
|--------|-------------|------------|
| Own User Profile | Read/Update | Read/Update |
| Other User Profiles | None | Read/Update/Suspend |
| System Metrics | None | Read |
| Market Data Config | None | Read/Update |
| Audit Logs | None | Read |
| User Role Changes | None | Update |

## Data Validation Rules

### Role Assignment
- Only admin users can modify user roles
- Cannot demote the last admin user in the system
- Role changes must be logged in audit trail
- Self-role modification is forbidden

### System Metrics
- Metrics calculated in real-time from database queries
- Cached for 5 minutes to reduce database load
- Admin-only access with proper authentication

### Market Data Configuration
- Configuration changes require admin role
- Changes logged with timestamp and admin user
- Invalid configurations rejected with validation errors

## Data Flow Patterns

### Admin Authentication Flow
1. User logs in with credentials
2. JWT token includes user role information
3. Frontend stores user object with role
4. Role checked before admin route access
5. Backend validates admin role on API calls

### Admin Data Loading Flow
1. Admin user navigates to admin section
2. Frontend verifies admin role from context
3. Multiple API calls fetch admin data in parallel
4. Error boundaries handle unauthorized access
5. Loading states manage asynchronous data

### User Management Flow
1. Admin requests user list from API
2. Backend filters and paginates user data
3. Frontend displays users in management interface
4. Admin actions trigger API calls with optimistic updates
5. Success/error feedback updates UI accordingly

## Implementation Notes

### Backend Changes
- **Minimal**: Existing models and APIs support admin functionality
- **Potential Extensions**: Additional admin action endpoints (suspend, reset)
- **Database**: No schema changes required

### Frontend Changes
- **Type Extensions**: Add role to existing User interface
- **Context Updates**: Include role utilities in AuthContext
- **New Components**: Admin-specific UI components and pages
- **Route Guards**: Role-based access control for admin routes

### Testing Strategy
- **Unit Tests**: Role-based utility functions
- **Integration Tests**: Admin API access control
- **E2E Tests**: Complete admin workflows
- **Security Tests**: Unauthorized access attempts

## Security Considerations

### Role Validation
- Backend enforces role requirements on all admin endpoints
- Frontend role checks prevent UI exposure but not security
- Token validation includes role verification
- API responses filtered based on user role

### Data Protection
- Admin access logged for audit compliance
- Sensitive user data requires explicit admin permissions
- System configuration changes tracked with admin attribution
- Rate limiting on admin actions to prevent abuse

This data model supports the admin dashboard feature while maintaining security, leveraging existing infrastructure, and following established patterns in the codebase.
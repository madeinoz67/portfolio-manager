# Developer Guide: Implementing Audit Logging

## Overview

This guide explains how to implement audit logging in the Portfolio Manager system, including adding new event types, integrating audit logging into new endpoints, and extending the audit system functionality.

## Architecture Overview

### Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Endpoint  │───▶│  Audit Service  │───▶│  Database       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌─────────┐         ┌─────────────────┐    ┌─────────────────┐
    │ Request │         │    AuditLog     │    │   audit_logs    │
    │ Context │         │     Model       │    │     Table       │
    └─────────┘         └─────────────────┘    └─────────────────┘
```

### Key Files

- `src/models/audit_log.py` - Database model and enums
- `src/services/audit_service.py` - Core audit logging service
- `src/api/admin.py` - Admin API endpoints for viewing audit logs
- `src/schemas/audit_log.py` - Pydantic schemas for API responses
- Frontend components in `frontend/src/components/admin/`

## Adding New Event Types

### 1. Update the Enum

Edit `src/models/audit_log.py`:

```python
class AuditEventType(str, Enum):
    # Existing events...
    PORTFOLIO_CREATED = "portfolio_created"
    TRANSACTION_CREATED = "transaction_created"

    # Add new event types
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
```

### 2. Add Service Methods

Add corresponding methods to `src/services/audit_service.py`:

```python
def log_user_created(
    self,
    user: User,
    admin_user_id: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None:
    """Log user creation by admin."""
    self.create_audit_entry(
        event_type=AuditEventType.USER_CREATED,
        event_description=f"User '{user.email}' created by admin",
        user_id=admin_user_id,
        entity_type="user",
        entity_id=str(user.id),
        event_metadata={
            "user_email": user.email,
            "user_role": user.role.value,
            "user_first_name": user.first_name,
            "user_last_name": user.last_name
        },
        ip_address=ip_address,
        user_agent=user_agent
    )

def log_api_key_created(
    self,
    api_key: ApiKey,
    user_id: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None:
    """Log API key creation."""
    self.create_audit_entry(
        event_type=AuditEventType.API_KEY_CREATED,
        event_description=f"API key '{api_key.name}' created",
        user_id=user_id,
        entity_type="api_key",
        entity_id=str(api_key.id),
        event_metadata={
            "key_name": api_key.name,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            "permissions": api_key.permissions
        },
        ip_address=ip_address,
        user_agent=user_agent
    )
```

### 3. Test the New Event Types

Create tests in `tests/contract/test_audit_service.py`:

```python
def test_audit_service_log_user_created(self, db_session, test_user):
    """Test logging user creation events."""
    audit_service = AuditService(db_session)

    new_user = User(
        email="newuser@example.com",
        first_name="New",
        last_name="User",
        role=UserRole.USER
    )

    audit_service.log_user_created(
        user=new_user,
        admin_user_id=str(test_user.id),
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0..."
    )

    # Verify audit entry was created
    audit_entry = db_session.query(AuditLog).filter(
        AuditLog.event_type == AuditEventType.USER_CREATED
    ).first()

    assert audit_entry is not None
    assert audit_entry.user_id == test_user.id
    assert audit_entry.entity_type == "user"
    assert "newuser@example.com" in audit_entry.event_description
```

## Integrating Audit Logging into API Endpoints

### 1. Import Required Components

```python
from fastapi import Request
from src.services.audit_service import AuditService
from src.core.dependencies import get_current_user_flexible
```

### 2. Add Audit Logging to Endpoints

#### For Create Operations

```python
@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_flexible)]
) -> UserResponse:
    """Create a new user (admin only)."""
    # Verify admin permissions
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Create user
    user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Create audit log
    try:
        audit_service = AuditService(db)
        audit_service.log_user_created(
            user=user,
            admin_user_id=str(current_user.id),
            ip_address=getattr(request.client, 'host', None) if request.client else None,
            user_agent=request.headers.get('User-Agent')
        )
        db.commit()  # Commit audit log
    except Exception as e:
        # Log error but don't fail the operation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create audit log for user creation: {e}")

    return UserResponse.model_validate(user)
```

#### For Update Operations

```python
@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_flexible)]
) -> UserResponse:
    """Update user (admin only)."""
    # Get existing user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Capture changes for audit log
    changes = {}
    for field, value in user_data.model_dump(exclude_unset=True).items():
        old_value = getattr(user, field)
        if old_value != value:
            changes[field] = {"old": old_value, "new": value}
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    # Create audit log (only if there were actual changes)
    if changes:
        try:
            audit_service = AuditService(db)
            audit_service.log_user_updated(
                user=user,
                admin_user_id=str(current_user.id),
                changes=changes,
                ip_address=getattr(request.client, 'host', None) if request.client else None,
                user_agent=request.headers.get('User-Agent')
            )
            db.commit()  # Commit audit log
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for user update: {e}")

    return UserResponse.model_validate(user)
```

#### For Delete Operations

```python
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_flexible)]
) -> dict:
    """Delete user (admin only)."""
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Store user details for audit log before deletion
    user_email = user.email
    user_role = user.role.value

    # Create audit log before deletion
    try:
        audit_service = AuditService(db)
        audit_service.log_user_deleted(
            user_id=str(user_id),
            user_email=user_email,
            user_role=user_role,
            admin_user_id=str(current_user.id),
            ip_address=getattr(request.client, 'host', None) if request.client else None,
            user_agent=request.headers.get('User-Agent')
        )
        # Don't commit yet - we'll commit after the deletion
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create audit log for user deletion: {e}")

    # Delete user
    db.delete(user)
    db.commit()  # Commit both deletion and audit log

    return {"message": "User deleted successfully"}
```

## Error Handling Best Practices

### 1. Graceful Degradation

Audit logging should never break the main operation:

```python
def safe_audit_log(audit_function, *args, **kwargs):
    """Safely execute audit logging with error handling."""
    try:
        audit_function(*args, **kwargs)
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Audit logging failed: {e}", exc_info=True)
        return False

# Usage in endpoints
if not safe_audit_log(audit_service.log_portfolio_created, portfolio=portfolio, user_id=str(current_user.id)):
    # Audit failed but operation succeeded
    pass
```

### 2. Transaction Management

For critical operations, consider using database transactions:

```python
try:
    # Begin transaction
    user = User(...)
    db.add(user)
    db.flush()  # Get user ID without committing

    # Create audit log in same transaction
    audit_service.log_user_created(user=user, admin_user_id=str(current_user.id))

    # Commit both user creation and audit log together
    db.commit()

except Exception as e:
    # Rollback both operations if either fails
    db.rollback()
    raise
```

## Testing Guidelines

### 1. Unit Tests for Audit Service

```python
class TestAuditServiceExtensions:
    """Test new audit service methods."""

    def test_log_user_created_captures_all_fields(self, db_session, test_admin_user):
        """Test that user creation audit captures all required fields."""
        audit_service = AuditService(db_session)

        new_user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            role=UserRole.USER
        )

        audit_service.log_user_created(
            user=new_user,
            admin_user_id=str(test_admin_user.id),
            ip_address="192.168.1.100",
            user_agent="Test Agent"
        )

        audit_entry = db_session.query(AuditLog).first()
        assert audit_entry.event_type == AuditEventType.USER_CREATED
        assert audit_entry.user_id == test_admin_user.id
        assert audit_entry.entity_type == "user"
        assert audit_entry.ip_address == "192.168.1.100"
        assert audit_entry.user_agent == "Test Agent"

        metadata = audit_entry.event_metadata
        assert metadata["user_email"] == "test@example.com"
        assert metadata["user_role"] == "USER"
```

### 2. Integration Tests for API Endpoints

```python
def test_user_creation_creates_audit_log(client, admin_headers, test_db):
    """Test that creating a user through API creates audit log."""
    initial_audit_count = test_db.query(AuditLog).count()

    response = client.post(
        "/api/v1/users",
        json={
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "role": "USER"
        },
        headers=admin_headers
    )

    assert response.status_code == 201

    # Check audit log was created
    final_audit_count = test_db.query(AuditLog).count()
    assert final_audit_count == initial_audit_count + 1

    # Verify audit log details
    audit_log = test_db.query(AuditLog).filter(
        AuditLog.event_type == AuditEventType.USER_CREATED
    ).first()

    assert audit_log is not None
    assert "newuser@example.com" in audit_log.event_description
```

## Performance Considerations

### 1. Async Audit Logging (Future Enhancement)

For high-volume systems, consider async audit logging:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncAuditService:
    def __init__(self, db: Session):
        self.db = db
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def log_async(self, audit_function, *args, **kwargs):
        """Log audit entry asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, audit_function, *args, **kwargs
        )

# Usage in FastAPI endpoints
async def create_portfolio_async(
    portfolio_data: PortfolioCreate,
    # ... other parameters
):
    # Create portfolio synchronously
    portfolio = Portfolio(...)
    db.add(portfolio)
    db.commit()

    # Log audit entry asynchronously (fire and forget)
    async_audit = AsyncAuditService(db)
    asyncio.create_task(
        async_audit.log_async(
            audit_service.log_portfolio_created,
            portfolio=portfolio,
            user_id=str(current_user.id)
        )
    )

    return PortfolioResponse.model_validate(portfolio)
```

### 2. Batch Audit Logging

For bulk operations, consider batching audit entries:

```python
def create_multiple_portfolios(
    portfolios_data: List[PortfolioCreate],
    db: Session,
    current_user: User
):
    """Create multiple portfolios with batch audit logging."""
    created_portfolios = []

    # Create all portfolios first
    for portfolio_data in portfolios_data:
        portfolio = Portfolio(...)
        db.add(portfolio)
        created_portfolios.append(portfolio)

    db.commit()  # Commit all portfolios

    # Batch create audit entries
    audit_service = AuditService(db)
    for portfolio in created_portfolios:
        audit_service.log_portfolio_created(
            portfolio=portfolio,
            user_id=str(current_user.id)
        )

    db.commit()  # Commit all audit entries

    return created_portfolios
```

## Database Migration for New Event Types

When adding new event types, ensure the database can handle them:

### 1. Check Enum Constraints

If using PostgreSQL with enum constraints:

```sql
-- Add new values to existing enum
ALTER TYPE auditeventtype ADD VALUE 'user_created';
ALTER TYPE auditeventtype ADD VALUE 'user_updated';
ALTER TYPE auditeventtype ADD VALUE 'user_deleted';
```

### 2. Update Alembic Migration

```python
# In your Alembic migration file
from alembic import op
import sqlalchemy as sa

def upgrade():
    # For SQLite (development), no enum constraint to update
    # For PostgreSQL (production), add enum values
    op.execute("ALTER TYPE auditeventtype ADD VALUE IF NOT EXISTS 'user_created'")
    op.execute("ALTER TYPE auditeventtype ADD VALUE IF NOT EXISTS 'user_updated'")
    op.execute("ALTER TYPE auditeventtype ADD VALUE IF NOT EXISTS 'user_deleted'")

def downgrade():
    # Note: PostgreSQL doesn't support removing enum values easily
    # Consider data migration strategy for rollbacks
    pass
```

## Frontend Integration

### 1. Update TypeScript Types

Update `frontend/src/types/audit.ts`:

```typescript
export enum AuditEventType {
  // Existing types...
  PORTFOLIO_CREATED = 'portfolio_created',
  TRANSACTION_CREATED = 'transaction_created',

  // New types
  USER_CREATED = 'user_created',
  USER_UPDATED = 'user_updated',
  USER_DELETED = 'user_deleted',
  API_KEY_CREATED = 'api_key_created',
  API_KEY_REVOKED = 'api_key_revoked',
}

// Update event type display mapping
export const EVENT_TYPE_LABELS: Record<AuditEventType, string> = {
  [AuditEventType.PORTFOLIO_CREATED]: 'Portfolio Created',
  [AuditEventType.TRANSACTION_CREATED]: 'Transaction Created',
  [AuditEventType.USER_CREATED]: 'User Created',
  [AuditEventType.USER_UPDATED]: 'User Updated',
  [AuditEventType.USER_DELETED]: 'User Deleted',
  [AuditEventType.API_KEY_CREATED]: 'API Key Created',
  [AuditEventType.API_KEY_REVOKED]: 'API Key Revoked',
}
```

### 2. Update Audit Log Table Component

Modify `frontend/src/components/admin/AuditLogTable.tsx`:

```typescript
const getEventIcon = (eventType: AuditEventType) => {
  switch (eventType) {
    case AuditEventType.USER_CREATED:
      return <UserPlusIcon className="w-4 h-4 text-green-500" />
    case AuditEventType.USER_UPDATED:
      return <UserIcon className="w-4 h-4 text-blue-500" />
    case AuditEventType.USER_DELETED:
      return <UserMinusIcon className="w-4 h-4 text-red-500" />
    case AuditEventType.API_KEY_CREATED:
      return <KeyIcon className="w-4 h-4 text-purple-500" />
    case AuditEventType.API_KEY_REVOKED:
      return <NoSymbolIcon className="w-4 h-4 text-gray-500" />
    // ... existing cases
    default:
      return <DocumentTextIcon className="w-4 h-4 text-gray-400" />
  }
}
```

## Monitoring and Alerting

### 1. Audit Service Health Monitoring

```python
from src.core.logging import LoggerMixin

class AuditServiceMonitor(LoggerMixin):
    """Monitor audit service health and performance."""

    def __init__(self):
        self.error_count = 0
        self.last_error_time = None

    def record_audit_success(self):
        """Record successful audit operation."""
        self.log_debug("Audit operation successful")

    def record_audit_failure(self, error: Exception):
        """Record audit operation failure."""
        self.error_count += 1
        self.last_error_time = datetime.utcnow()
        self.log_error(f"Audit operation failed: {error}", exc_info=True)

        # Alert if error rate is high
        if self.error_count > 10:  # Threshold
            self.send_alert("High audit service error rate detected")

    def send_alert(self, message: str):
        """Send alert to monitoring system."""
        # Integrate with your monitoring system (Slack, email, etc.)
        self.log_critical(f"AUDIT ALERT: {message}")
```

### 2. Performance Metrics

```python
import time
from contextlib import contextmanager

@contextmanager
def audit_performance_tracking():
    """Track audit operation performance."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        if duration > 1.0:  # Alert if audit takes > 1 second
            logger.warning(f"Slow audit operation: {duration:.2f}s")

# Usage
with audit_performance_tracking():
    audit_service.log_portfolio_created(...)
```

## Security Considerations

### 1. Sensitive Data Handling

Be careful with sensitive data in audit logs:

```python
def sanitize_metadata(metadata: dict) -> dict:
    """Remove sensitive data from audit metadata."""
    sensitive_fields = ['password', 'token', 'api_key', 'secret']

    sanitized = {}
    for key, value in metadata.items():
        if any(sensitive in key.lower() for sensitive in sensitive_fields):
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = value

    return sanitized

# Use in audit service
self.create_audit_entry(
    # ... other parameters
    event_metadata=sanitize_metadata(original_metadata)
)
```

### 2. Access Control Verification

Always verify permissions before creating audit entries:

```python
def verify_audit_permissions(user: User, operation: str) -> bool:
    """Verify user has permission to perform audited operation."""
    if operation in ['user_create', 'user_delete'] and user.role != UserRole.ADMIN:
        return False
    return True

# Use in endpoints
if not verify_audit_permissions(current_user, 'user_create'):
    raise HTTPException(status_code=403, detail="Insufficient permissions")
```

## Common Pitfalls and Solutions

### 1. Circular Dependencies

**Problem**: Audit service depends on models that might depend on audit service.

**Solution**: Keep audit service lightweight and avoid complex dependencies.

### 2. Transaction Management

**Problem**: Audit entries committed even when main operation fails.

**Solution**: Use proper transaction boundaries and rollback strategies.

### 3. Performance Impact

**Problem**: Audit logging slows down main operations.

**Solution**: Consider async logging, proper indexing, and monitoring.

### 4. Data Consistency

**Problem**: Audit logs don't match actual data state.

**Solution**: Create audit entries as close to the actual operation as possible, within the same transaction.

## Code Review Checklist

When adding audit logging to new endpoints:

- [ ] Import AuditService and required dependencies
- [ ] Add Request parameter to endpoint signature
- [ ] Add current_user dependency if not present
- [ ] Create audit entry after successful operation
- [ ] Include proper error handling for audit failures
- [ ] Capture relevant context (IP, user agent)
- [ ] Include meaningful metadata
- [ ] Write tests for audit functionality
- [ ] Update TypeScript types if needed
- [ ] Consider transaction boundaries
- [ ] Verify no sensitive data in audit logs
- [ ] Document new event types in enum
- [ ] Add appropriate service methods for new event types
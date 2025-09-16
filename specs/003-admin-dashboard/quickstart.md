# Quickstart: Admin Dashboard Testing

**Generated**: 2025-09-14 | **Feature**: Admin Dashboard | **Branch**: 003-admin-dashboard

## Overview

This quickstart guide provides step-by-step instructions for testing the admin dashboard feature once implemented. It covers the complete admin workflow from authentication to user management.

## Prerequisites

### System Setup
```bash
# Backend running on port 8001
cd backend && uv run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload

# Frontend running on port 3000
cd frontend && npm run dev

# Database with test data
uv run alembic upgrade head
```

### Test Data Setup
```bash
# Create admin user (via backend CLI or SQL)
# This will be part of the implementation tasks
# Example SQL for testing:
# INSERT INTO users (id, email, password_hash, role) VALUES
# ('admin-user-id', 'admin@test.com', 'hashed-password', 'admin');
```

## Test Scenarios

### 1. Admin Authentication Flow

**Objective**: Verify admin users can access admin dashboard while regular users cannot.

**Steps**:
1. Open browser to `http://localhost:3000`
2. Login with regular user credentials
3. Verify no admin menu items visible in navigation
4. Attempt to navigate to `http://localhost:3000/admin`
5. **Expected**: Access denied or redirect to dashboard
6. Logout and login with admin user credentials
7. **Expected**: Admin menu items appear in navigation
8. Click admin menu or navigate to `http://localhost:3000/admin`
9. **Expected**: Admin dashboard loads successfully

**Pass Criteria**:
- ✅ Regular users cannot access `/admin/*` routes
- ✅ Admin users see admin navigation items
- ✅ Admin dashboard loads without errors
- ✅ Role-based UI components render correctly

### 2. System Metrics Display

**Objective**: Verify admin dashboard shows accurate system metrics.

**Steps**:
1. Login as admin user
2. Navigate to admin dashboard
3. Observe system metrics cards:
   - Total Users count
   - Total Portfolios count
   - Active Users count
   - Admin Users count
   - System Status indicator
4. **Expected**: Metrics display actual data from database
5. Create a new regular user account
6. Refresh admin dashboard
7. **Expected**: User count increments by 1

**Pass Criteria**:
- ✅ All metric cards display numeric values
- ✅ Metrics reflect actual database state
- ✅ System status shows "healthy" for normal operation
- ✅ Real-time updates work when data changes

### 3. User Management Interface

**Objective**: Verify admin can view and manage all user accounts.

**Steps**:
1. Login as admin user
2. Navigate to Admin → User Management
3. **Expected**: Table showing all users with columns:
   - Email
   - Name (first/last)
   - Role (admin/user)
   - Status (active/inactive)
   - Portfolio Count
   - Last Login
   - Actions
4. Test search functionality (type in search box)
5. **Expected**: User list filters based on search term
6. Test role filter (select "admin" or "user" from dropdown)
7. **Expected**: List shows only users with selected role
8. Click on a specific user row
9. **Expected**: User detail page loads with comprehensive info

**Pass Criteria**:
- ✅ All registered users visible in table
- ✅ Search functionality works correctly
- ✅ Role filtering works correctly
- ✅ User details accessible via click
- ✅ Portfolio count accurate for each user
- ✅ Responsive design works on mobile

### 4. User Detail View

**Objective**: Verify detailed user information displays correctly.

**Steps**:
1. From user management, click on any user
2. **Expected**: User detail page shows:
   - Basic info (name, email, role, status)
   - Account metadata (created date, last login)
   - Portfolio summary (list of portfolios with values)
   - Admin action buttons (if applicable)
3. Verify all displayed information matches user's actual data
4. Test navigation back to user list
5. **Expected**: Breadcrumb or back button returns to user management

**Pass Criteria**:
- ✅ All user information displays accurately
- ✅ Portfolio data correctly aggregated
- ✅ Navigation between views works smoothly
- ✅ Loading states handle async data properly

### 5. Market Data Monitoring

**Objective**: Verify admin can monitor external data feed status.

**Steps**:
1. Navigate to Admin → System → Market Data
2. **Expected**: Table showing all market data providers:
   - Provider name (Alpha Vantage, etc.)
   - Status (active/disabled/error)
   - Last update timestamp
   - API usage (calls today/month)
   - Cost tracking
3. Verify status indicators reflect actual provider state
4. Check that usage numbers align with actual API calls
5. Test any toggle controls (enable/disable providers)
6. **Expected**: Changes persist and reflect in system behavior

**Pass Criteria**:
- ✅ All configured providers visible
- ✅ Status indicators accurate
- ✅ Usage metrics display correctly
- ✅ Cost calculations accurate
- ✅ Enable/disable toggles work properly

### 6. Error Handling

**Objective**: Verify proper error handling for admin functions.

**Steps**:
1. **Network Error Test**: Disconnect from internet
2. Navigate admin pages
3. **Expected**: Appropriate error messages, no crashes
4. **Permission Error Test**: Revoke admin role via database
5. Refresh admin page
6. **Expected**: Access denied, redirect to regular dashboard
7. **Invalid Data Test**: Navigate to `/admin/users/invalid-id`
8. **Expected**: User-friendly "not found" message
9. **API Error Test**: Stop backend server
10. Try admin actions
11. **Expected**: Connection error messages, graceful degradation

**Pass Criteria**:
- ✅ Network errors handled gracefully
- ✅ Permission changes enforced immediately
- ✅ Invalid routes show proper error pages
- ✅ API failures don't crash the UI
- ✅ Error messages are user-friendly

### 7. Performance & Responsiveness

**Objective**: Verify admin dashboard performs well under load.

**Steps**:
1. **Load Test**: Create 100+ test users in database
2. Navigate to user management page
3. **Expected**: Page loads within 3 seconds
4. Test pagination (if implemented)
5. **Expected**: Smooth navigation between pages
6. **Mobile Test**: Resize browser to mobile width
7. **Expected**: Admin interface adapts responsively
8. **Concurrent Test**: Open multiple admin tabs
9. **Expected**: Data stays consistent across tabs

**Pass Criteria**:
- ✅ Large datasets load within acceptable time
- ✅ UI remains responsive during data operations
- ✅ Mobile interface fully functional
- ✅ Multi-tab usage works correctly
- ✅ No memory leaks or performance degradation

## Integration Testing

### API Contract Validation
```bash
# Test admin API endpoints directly
curl -H "Authorization: Bearer <admin-jwt>" \
     http://localhost:8001/api/v1/admin/users

# Expected: 200 OK with user list JSON

curl -H "Authorization: Bearer <user-jwt>" \
     http://localhost:8001/api/v1/admin/users

# Expected: 403 Forbidden with error JSON
```

### Frontend-Backend Integration
1. Monitor browser Network tab during admin operations
2. Verify API calls use correct endpoints and headers
3. Check response parsing and error handling
4. Confirm loading states during async operations

## Security Verification

### Role-Based Access
1. **JWT Token Test**: Inspect JWT payload for role claim
2. **Route Protection Test**: Direct URL access attempts
3. **API Security Test**: Backend endpoint role enforcement
4. **Session Management Test**: Role changes during active session

### Data Protection
1. **Sensitive Data Test**: Verify no passwords/secrets in responses
2. **Audit Trail Test**: Admin actions logged appropriately
3. **Rate Limiting Test**: Excessive admin API calls handled properly

## Success Criteria Summary

The admin dashboard is ready for production when:

- ✅ All 7 test scenarios pass completely
- ✅ Role-based access control enforced at all levels
- ✅ System metrics display accurately
- ✅ User management functions work correctly
- ✅ Market data monitoring operational
- ✅ Error handling graceful and user-friendly
- ✅ Performance meets requirements (< 3s load times)
- ✅ Security measures properly implemented
- ✅ Mobile responsiveness fully functional
- ✅ No browser console errors during normal operation

## Troubleshooting Common Issues

### "Access Denied" for Admin User
- Verify user role in database: `SELECT email, role FROM users WHERE email='admin@test.com'`
- Check JWT token includes role claim
- Confirm `get_current_admin_user()` dependency working

### Admin Menu Not Appearing
- Verify AuthContext includes role information
- Check role-based conditional rendering logic
- Inspect browser developer tools for JavaScript errors

### API Calls Failing
- Confirm backend server running on port 8001
- Verify JWT token in Authorization header
- Check CORS configuration for admin endpoints
- Review backend logs for authentication errors

### Performance Issues
- Enable database query logging to identify slow queries
- Check network requests in browser developer tools
- Monitor memory usage for potential leaks
- Consider implementing pagination for large datasets

This quickstart guide ensures comprehensive testing of the admin dashboard feature and provides debugging guidance for common implementation issues.
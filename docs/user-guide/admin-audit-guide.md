# Admin Guide: Using the Audit Log System

## Quick Start Guide

This guide provides step-by-step instructions for administrators to use the audit log system for monitoring user activity, compliance reporting, and security oversight.

## Accessing Audit Logs

### Prerequisites
- Admin user account with `UserRole.ADMIN`
- Access to the Portfolio Manager admin dashboard
- Valid authentication session

### Navigation
1. Log in to the Portfolio Manager application
2. Navigate to the admin section (red navigation bar)
3. Click on **"Audit Logs"** in the navigation menu
4. You'll arrive at `/admin/audit-logs`

## Understanding the Audit Log Interface

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Audit Logs                                                  │
│ Track all portfolio and transaction events                  │
├─────────────────────────────────────────────────────────────┤
│ [Search Box] [Event Type ▼] [Entity Type ▼] [User Filter]  │
│ [From Date] [To Date]                                       │
├─────────────────────────────────────────────────────────────┤
│ Page 1 of 10 • 500 total items        [Previous] [Next]    │
├─────────────────────────────────────────────────────────────┤
│ Event              User         Entity      Timestamp       │
│ Portfolio Created  john@co.com  portfolio   2 hours ago     │
│ Transaction Buy    jane@co.com  transaction 5 hours ago     │
│ Portfolio Updated  bob@co.com   portfolio   1 day ago       │
└─────────────────────────────────────────────────────────────┘
```

### Key Information Displayed

- **Event**: Type of action performed (Portfolio Created, Transaction Updated, etc.)
- **User**: Email address of the user who performed the action
- **Entity**: Type of object affected (portfolio, transaction)
- **Timestamp**: When the action occurred (displayed in local time)
- **Details**: Additional context like IP address and metadata

## Common Use Cases

### 1. Investigating User Activity

**Scenario**: Need to see all actions performed by a specific user.

**Steps**:
1. In the **User** filter field, enter the user's email or ID
2. Click outside the field or press Enter to apply the filter
3. Review all actions performed by that user
4. Use date filters to narrow down to specific time periods

**Example**: Investigating user `john.doe@company.com`:
- Filter shows all portfolios created/modified by John
- Timestamps show when each action occurred
- IP addresses help verify legitimate access

### 2. Tracking Portfolio Changes

**Scenario**: A portfolio's values seem incorrect - need to see all changes made.

**Steps**:
1. Set **Entity Type** filter to "portfolio"
2. In the search box, enter the portfolio name or ID
3. Look for `PORTFOLIO_UPDATED` events
4. Click "View metadata" to see exactly what changed

**What You'll See**:
```json
{
    "portfolio_name": "Investment Portfolio",
    "changes": {
        "name": {
            "old": "Old Portfolio Name",
            "new": "Investment Portfolio"
        }
    }
}
```

### 3. Compliance Reporting

**Scenario**: Need to generate a compliance report for the last quarter.

**Steps**:
1. Set **From Date** to the start of the quarter
2. Set **To Date** to the end of the quarter
3. Leave other filters empty to see all activity
4. Use pagination to review all entries
5. Export results (if export feature is available)

**Key Metrics to Track**:
- Total number of transactions created/modified/deleted
- Number of portfolios created/deleted
- User activity patterns
- After-hours activity (potential security concern)

### 4. Security Investigation

**Scenario**: Suspicious activity detected - need to investigate potential unauthorized access.

**Steps**:
1. Filter by suspicious time periods (evenings, weekends)
2. Look for unusual IP addresses in the "Details" column
3. Check for rapid succession of actions from the same user
4. Cross-reference user agent strings for consistency

**Red Flags to Look For**:
- Actions from unexpected IP addresses
- Bulk operations in short time periods
- User agents that don't match typical user patterns
- Actions outside normal business hours

### 5. Debugging Data Issues

**Scenario**: User reports their transaction was modified incorrectly.

**Steps**:
1. Filter by the specific user
2. Set **Entity Type** to "transaction"
3. Look for `TRANSACTION_UPDATED` events
4. Check the metadata to see exactly what changed
5. Verify the IP address matches the user's location

**Information Available**:
- Exact fields that were changed
- Before and after values
- Timestamp of the change
- User who made the change
- Source IP address for verification

## Advanced Filtering Techniques

### Combining Filters

Use multiple filters together for precise investigation:

```
User: john@company.com
Event Type: transaction_created
Date From: 2025-09-01
Date To: 2025-09-15
```

This shows all transactions created by John in the first half of September.

### Search Syntax

The search box supports:
- **Portfolio names**: "Investment Portfolio"
- **Transaction symbols**: "AAPL", "TSLA"
- **Partial matches**: "Portfolio" matches "Investment Portfolio"
- **Event descriptions**: "created", "updated", "deleted"

### Date Range Best Practices

- **Daily Investigation**: Use same start and end date
- **Weekly Reports**: Set 7-day ranges
- **Monthly Compliance**: Use first and last day of month
- **Incident Investigation**: Use narrow ranges around incident time

## Reading Audit Entries

### Event Types Explained

| Event Type | What It Means | When It Occurs |
|------------|---------------|----------------|
| `portfolio_created` | New portfolio added | User creates a portfolio |
| `portfolio_updated` | Portfolio modified | User changes name, description |
| `portfolio_soft_deleted` | Portfolio deactivated | User deletes portfolio (recoverable) |
| `portfolio_hard_deleted` | Portfolio permanently removed | Admin permanent deletion |
| `transaction_created` | New transaction added | User adds buy/sell transaction |
| `transaction_updated` | Transaction modified | User edits transaction details |
| `transaction_deleted` | Transaction removed | User deletes transaction |

### Understanding Metadata

Click "View metadata" to see detailed information:

#### Portfolio Creation
```json
{
    "portfolio_name": "Tech Stocks",
    "portfolio_description": "Technology sector investments"
}
```

#### Transaction Update
```json
{
    "transaction_type": "BUY",
    "symbol": "AAPL",
    "changes": {
        "quantity": {"old": 100, "new": 150},
        "price_per_share": {"old": 120.50, "new": 125.00}
    },
    "portfolio_id": "uuid-of-portfolio"
}
```

## Security Best Practices

### Regular Monitoring

**Daily Tasks**:
- Review activity from the previous 24 hours
- Check for after-hours activity
- Verify IP addresses for remote users

**Weekly Tasks**:
- Review user activity patterns
- Check for unusual transaction volumes
- Verify all portfolio changes have valid business reasons

**Monthly Tasks**:
- Generate compliance reports
- Review user access patterns
- Check for abandoned or suspicious accounts

### Incident Response

When suspicious activity is detected:

1. **Document Everything**: Screenshot relevant audit entries
2. **Gather Context**: Check surrounding time periods
3. **Verify User**: Contact user to confirm legitimate activity
4. **Check IP Geolocation**: Verify access from expected locations
5. **Review Patterns**: Look for similar suspicious activity
6. **Escalate if Needed**: Involve security team for serious concerns

## Troubleshooting Common Issues

### "No audit logs found"

**Possible Causes**:
- User doesn't have admin privileges
- Database connectivity issues
- Audit service not properly configured

**Solutions**:
1. Verify admin role in user profile
2. Check with IT about system status
3. Try refreshing the page
4. Clear browser cache and reload

### "Slow loading performance"

**Possible Causes**:
- Large date ranges selected
- Database performance issues
- High system load

**Solutions**:
1. Use smaller date ranges
2. Add more specific filters
3. Reduce page size (use pagination)
4. Contact IT if persistent

### "Missing details in audit entries"

**Possible Causes**:
- Audit integration incomplete on some endpoints
- User agent or IP not captured
- Metadata not properly formatted

**Solutions**:
1. Report missing information to development team
2. Check if issue affects all entries or specific types
3. Verify user has proper network configuration

## Compliance and Reporting

### Required Information for Audits

Financial compliance typically requires:
- **Who**: User identification and authentication
- **What**: Specific action performed
- **When**: Precise timestamp (UTC and local)
- **Where**: Source IP address and location
- **Why**: Business context (if available in notes)

### Report Generation Tips

1. **Use Consistent Date Ranges**: Align with business periods
2. **Include All Activity**: Don't filter out "minor" changes
3. **Document Methodology**: Note which filters were used
4. **Cross-Reference**: Verify audit data against business records
5. **Maintain Records**: Save audit reports for required retention periods

### Regulatory Considerations

- **SOX Compliance**: Focus on financial transaction changes
- **GDPR**: Be aware of personal data in audit logs
- **Industry Standards**: Follow sector-specific audit requirements
- **Data Retention**: Comply with legal retention requirements

## Frequently Asked Questions

### Q: How long are audit logs retained?
A: Check with your system administrator about data retention policies. Typically 7+ years for financial data.

### Q: Can audit logs be modified or deleted?
A: No, audit logs are immutable once created. This ensures integrity for compliance purposes.

### Q: What if a user denies performing an action shown in audit logs?
A: Audit logs include IP address and user agent for verification. Cross-reference with IT access logs.

### Q: How real-time are the audit logs?
A: Audit entries are created immediately when actions occur. They appear in the dashboard within seconds.

### Q: Can I export audit logs?
A: Export functionality may be available through the API. Check with your development team for current capabilities.

### Q: What happens if the audit system fails?
A: User operations continue normally. Audit failures are logged separately and don't impact business functionality.

### Q: How do I report suspicious activity?
A: Document the audit entries and follow your organization's security incident response procedures.

## Contact and Support

For technical issues with the audit system:
- Contact your IT department
- Report bugs to the development team
- For compliance questions, consult with your legal/compliance team

For urgent security concerns:
- Follow your organization's incident response procedures
- Preserve audit log evidence
- Document all findings thoroughly
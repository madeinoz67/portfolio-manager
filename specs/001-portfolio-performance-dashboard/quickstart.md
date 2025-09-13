# Portfolio Management System - Quickstart Guide

**Version**: 0.1.0 MVP  
**Target Users**: 1-2 initial users  
**Platform**: Web application

## Prerequisites

- Python 3.11+
- Node.js 18+
- uv (Python package manager)
- Git
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Quick Start (Development)

### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd portfolio-manager

# Setup Python backend with uv
cd backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip sync requirements.txt

# Setup React frontend
cd ../frontend
npm install
```

### 2. Initialize Database

```bash
# From backend directory
python -m alembic upgrade head

# Seed with sample data (optional)
python scripts/seed_data.py
```

### 3. Start Development Servers

**Terminal 1 - Backend API**:
```bash
cd backend
source .venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

### 4. Access Application

- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API**: http://localhost:8000/api/v1

## User Stories Validation

### Story 1: User Registration and Login

**As a new user, I want to create an account and log in**

**Steps**:
1. Open http://localhost:3000
2. Click "Register" 
3. Fill form:
   - Email: test@example.com
   - Password: testpass123
   - First Name: Test
   - Last Name: User
4. Click "Create Account"
5. Verify redirect to login page
6. Log in with credentials
7. Verify dashboard access

**Expected Result**: User authenticated and sees empty portfolio dashboard

**API Test**:
```bash
# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123","first_name":"Test","last_name":"User"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'
```

### Story 2: Create and Manage Portfolio

**As a logged-in user, I want to create a portfolio**

**Steps**:
1. From dashboard, click "Create Portfolio"
2. Fill form:
   - Name: "My First Portfolio"
   - Description: "Test portfolio for ASX stocks"
3. Click "Create"
4. Verify portfolio appears in list
5. Click portfolio name to view details

**Expected Result**: Portfolio created with zero holdings and $0.00 value

**API Test**:
```bash
# Get auth token first (from login response)
export TOKEN="your-jwt-token-here"

# Create portfolio
curl -X POST http://localhost:8000/api/v1/portfolios \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"My First Portfolio","description":"Test portfolio"}'
```

### Story 3: Add Manual Transaction

**As a portfolio owner, I want to manually add a stock transaction**

**Steps**:
1. Navigate to portfolio details
2. Click "Add Transaction"
3. Fill transaction form:
   - Stock Symbol: "CBA" (Commonwealth Bank)
   - Transaction Type: "BUY"
   - Quantity: 10
   - Price per Share: 105.50
   - Transaction Date: Today's date
   - Notes: "Initial purchase"
4. Click "Add Transaction"
5. Verify transaction appears in history
6. Verify holding appears with correct quantity and value

**Expected Result**: 
- Transaction recorded with total amount $1,055.00
- Holding shows 10 shares of CBA
- Portfolio value reflects current stock price

**API Test**:
```bash
# Add transaction (replace portfolio_id)
curl -X POST http://localhost:8000/api/v1/portfolios/{portfolio_id}/transactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_symbol":"CBA",
    "transaction_type":"BUY",
    "quantity":10,
    "price_per_share":105.50,
    "transaction_date":"2025-09-12",
    "notes":"Initial purchase"
  }'
```

### Story 4: View Stock Information

**As a user, I want to see current stock prices and information**

**Steps**:
1. Use stock search: search for "CBA"
2. Click on Commonwealth Bank result
3. Verify stock details show:
   - Current price
   - Daily change (amount and percentage)
   - Company name
   - Exchange (ASX)
4. Check price history chart (if available)

**Expected Result**: Current CBA stock information displayed with price chart

**API Test**:
```bash
# Search stocks
curl -X GET "http://localhost:8000/api/v1/stocks?q=CBA" \
  -H "Authorization: Bearer $TOKEN"

# Get stock details
curl -X GET http://localhost:8000/api/v1/stocks/CBA \
  -H "Authorization: Bearer $TOKEN"
```

### Story 5: View Portfolio Performance

**As a portfolio owner, I want to see my portfolio's performance metrics**

**Steps**:
1. Navigate to portfolio details
2. Check performance section shows:
   - Total return
   - Daily change (amount and percentage)  
   - Current total value
3. Select different time periods (1W, 1M, 3M)
4. Verify charts update accordingly

**Expected Result**: Performance metrics calculated correctly for selected periods

**API Test**:
```bash
# Get performance metrics
curl -X GET "http://localhost:8000/api/v1/portfolios/{portfolio_id}/performance?period=1M" \
  -H "Authorization: Bearer $TOKEN"
```

### Story 6: API Key Management

**As a user, I want to generate API keys for programmatic access**

**Steps**:
1. Navigate to Account Settings
2. Click "API Keys" tab
3. Click "Generate New Key"
4. Enter key name: "Test Integration"
5. Copy the generated key (shown once)
6. Test API access using the key

**Expected Result**: API key generated and can be used for API authentication

**API Test**:
```bash
# Create API key
curl -X POST http://localhost:8000/api/v1/users/me/api-keys \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Integration"}'

# Test with API key (replace with generated key)
curl -X GET http://localhost:8000/api/v1/portfolios \
  -H "X-API-Key: your-generated-api-key"
```

## Development Validation Checklist

**Backend API**:
- [ ] FastAPI server starts successfully on port 8000
- [ ] SQLite database initializes with correct schema
- [ ] All API endpoints return expected responses
- [ ] API documentation accessible at /docs
- [ ] Authentication (JWT) working correctly
- [ ] API key authentication functioning

**Frontend**:
- [ ] React development server starts on port 3000
- [ ] User registration and login forms work
- [ ] Portfolio creation and management interface functional
- [ ] Transaction entry form working
- [ ] Dashboard displays portfolio data correctly
- [ ] Charts render with sample data

**Integration**:
- [ ] Frontend successfully calls backend API
- [ ] Authentication state managed correctly
- [ ] Error handling displays user-friendly messages
- [ ] Form validation prevents invalid data submission
- [ ] Real-time updates work (if implemented)

**Data Flow**:
- [ ] User registration creates database record
- [ ] Portfolio creation stores correctly
- [ ] Transactions update holdings automatically
- [ ] Portfolio values calculated correctly
- [ ] Performance metrics computed accurately

## Common Issues and Troubleshooting

**Database Connection**:
- Ensure SQLite file has write permissions
- Check database file location in config
- Run database migrations if schema errors occur

**API Errors**:
- Verify Python dependencies installed correctly
- Check FastAPI logs for detailed error messages
- Ensure correct environment variables set

**Frontend Issues**:
- Clear browser cache if seeing stale data
- Check browser console for JavaScript errors
- Verify API endpoint URLs in frontend config

**Authentication Problems**:
- Check JWT secret key configuration
- Verify token expiration settings
- Ensure API key headers formatted correctly

## Next Steps

After validating the quickstart scenarios:

1. **Email Integration**: Configure OAuth for broker email processing
2. **Price Updates**: Implement daily price fetching from ASX
3. **AI Analysis**: Add stock recommendation engine
4. **Enhanced UI**: Improve charts and dashboard visuals
5. **Testing**: Expand automated test coverage
6. **Deployment**: Set up staging and production environments

## MVP Scope Reminder

This quickstart covers the **core MVP functionality**:
- Single user authentication
- Basic portfolio management
- Manual transaction entry
- Simple performance metrics
- API access with keys

**Not included in MVP**:
- Multi-user collaboration
- Email transaction processing
- Automated price updates
- AI recommendations
- Advanced analytics
- News integration
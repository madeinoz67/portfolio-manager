# Data Model for Portfolio Management System

**Version**: 0.1.0  
**Target**: MVP for 1-2 users initially

## Core Entities

### User
**Purpose**: System authentication and profile management

**Fields**:
- `id`: UUID (Primary Key)
- `email`: String (Unique, required)
- `password_hash`: String (required)
- `first_name`: String (optional)
- `last_name`: String (optional)
- `created_at`: DateTime (auto)
- `updated_at`: DateTime (auto)
- `is_active`: Boolean (default: true)
- `email_config`: JSON (OAuth tokens, broker settings)

**Relationships**:
- One-to-Many: Portfolios (owner)
- One-to-Many: API Keys

### Portfolio
**Purpose**: Collection of investments with tracking and analysis

**Fields**:
- `id`: UUID (Primary Key)
- `name`: String (required, max 100 chars)
- `description`: String (optional, max 500 chars)
- `owner_id`: UUID (Foreign Key to User, required)
- `total_value`: Decimal(15,2) (calculated)
- `daily_change`: Decimal(10,2) (calculated)
- `daily_change_percent`: Decimal(5,2) (calculated)
- `created_at`: DateTime (auto)
- `updated_at`: DateTime (auto)
- `is_active`: Boolean (default: true)

**Relationships**:
- Many-to-One: User (owner)
- One-to-Many: Holdings
- One-to-Many: Transactions
- One-to-Many: Dividend Payments

**Validation Rules**:
- Name must be unique per user
- Total value auto-calculated from holdings
- Daily change calculated from price updates

### Stock
**Purpose**: Master data for tradeable securities

**Fields**:
- `id`: UUID (Primary Key)
- `symbol`: String (required, unique, max 10 chars)
- `company_name`: String (required, max 200 chars)
- `exchange`: String (required, default: "ASX")
- `current_price`: Decimal(10,4) (nullable)
- `previous_close`: Decimal(10,4) (nullable)
- `daily_change`: Decimal(8,4) (calculated)
- `daily_change_percent`: Decimal(5,2) (calculated)
- `status`: Enum ['ACTIVE', 'HALTED', 'SUSPENDED', 'DELISTED'] (default: 'ACTIVE')
- `last_price_update`: DateTime (nullable)
- `created_at`: DateTime (auto)
- `updated_at`: DateTime (auto)

**Relationships**:
- One-to-Many: Holdings
- One-to-Many: Transactions
- One-to-Many: Price History
- One-to-Many: News Articles

**Validation Rules**:
- Symbol format: uppercase alphanumeric
- Price must be positive when set
- Status transitions logged

### Holding
**Purpose**: Current position in a stock within a portfolio

**Fields**:
- `id`: UUID (Primary Key)
- `portfolio_id`: UUID (Foreign Key to Portfolio, required)
- `stock_id`: UUID (Foreign Key to Stock, required)
- `quantity`: Decimal(12,4) (required, must be positive)
- `average_cost`: Decimal(10,4) (calculated from transactions)
- `current_value`: Decimal(15,2) (calculated: quantity * current_price)
- `unrealized_gain_loss`: Decimal(15,2) (calculated)
- `unrealized_gain_loss_percent`: Decimal(5,2) (calculated)
- `created_at`: DateTime (auto)
- `updated_at`: DateTime (auto)

**Relationships**:
- Many-to-One: Portfolio
- Many-to-One: Stock
- One-to-Many: Transactions (related)

**Validation Rules**:
- Unique constraint: (portfolio_id, stock_id)
- Quantity updated by transaction processing
- Values recalculated on price updates

### Transaction
**Purpose**: Record of buy/sell activities

**Fields**:
- `id`: UUID (Primary Key)
- `portfolio_id`: UUID (Foreign Key to Portfolio, required)
- `stock_id`: UUID (Foreign Key to Stock, required)
- `transaction_type`: Enum ['BUY', 'SELL'] (required)
- `quantity`: Decimal(12,4) (required, positive)
- `price_per_share`: Decimal(10,4) (required, positive)
- `total_amount`: Decimal(15,2) (calculated: quantity * price_per_share)
- `fees`: Decimal(10,2) (default: 0)
- `transaction_date`: Date (required)
- `processed_date`: DateTime (auto)
- `source_type`: Enum ['EMAIL', 'MANUAL', 'API'] (required)
- `source_reference`: String (email ID, user input, etc.)
- `broker_reference`: String (optional)
- `notes`: String (optional, max 1000 chars)
- `is_verified`: Boolean (default: false)

**Relationships**:
- Many-to-One: Portfolio
- Many-to-One: Stock

**Validation Rules**:
- Total amount auto-calculated
- Transaction date cannot be future
- Source reference required for EMAIL type

### Dividend Payment
**Purpose**: Income tracking from stock dividends

**Fields**:
- `id`: UUID (Primary Key)
- `portfolio_id`: UUID (Foreign Key to Portfolio, required)
- `stock_id`: UUID (Foreign Key to Stock, required)
- `payment_date`: Date (required)
- `ex_dividend_date`: Date (optional)
- `amount_per_share`: Decimal(8,4) (required, positive)
- `total_amount`: Decimal(15,2) (calculated)
- `tax_withheld`: Decimal(15,2) (default: 0)
- `currency`: String (default: "AUD", max 3 chars)
- `source_reference`: String (email ID, etc.)
- `is_verified`: Boolean (default: false)
- `created_at`: DateTime (auto)

**Relationships**:
- Many-to-One: Portfolio
- Many-to-One: Stock

**Validation Rules**:
- Total amount calculated from holding quantity at ex-dividend date
- Payment date cannot be future

### Price History
**Purpose**: Historical price data for analysis and charting

**Fields**:
- `id`: UUID (Primary Key)
- `stock_id`: UUID (Foreign Key to Stock, required)
- `price_date`: Date (required)
- `open_price`: Decimal(10,4) (optional)
- `high_price`: Decimal(10,4) (optional)
- `low_price`: Decimal(10,4) (optional)
- `close_price`: Decimal(10,4) (required)
- `volume`: BigInteger (optional)
- `adjusted_close`: Decimal(10,4) (optional)
- `created_at`: DateTime (auto)

**Relationships**:
- Many-to-One: Stock

**Validation Rules**:
- Unique constraint: (stock_id, price_date)
- Prices must be positive
- OHLC validation: open/high/low/close relationships

### Email Processing Log
**Purpose**: Audit trail for email transaction processing

**Fields**:
- `id`: UUID (Primary Key)
- `email_id`: String (required, email message ID)
- `from_address`: String (required)
- `subject`: String (required)
- `received_date`: DateTime (required)
- `processing_status`: Enum ['PENDING', 'PROCESSED', 'FAILED', 'MANUAL_REVIEW'] (required)
- `extracted_data`: JSON (parsed transaction data)
- `error_message`: String (optional)
- `processed_at`: DateTime (nullable)
- `transaction_id`: UUID (Foreign Key to Transaction, nullable)

**Validation Rules**:
- Email ID unique per processing attempt
- Status transitions logged with timestamps

### API Key
**Purpose**: Authentication tokens for API access

**Fields**:
- `id`: UUID (Primary Key)
- `user_id`: UUID (Foreign Key to User, required)
- `key_name`: String (required, max 100 chars)
- `key_hash`: String (required, hashed API key)
- `permissions`: JSON (API scope definitions)
- `last_used_at`: DateTime (nullable)
- `expires_at`: DateTime (nullable)
- `is_active`: Boolean (default: true)
- `created_at`: DateTime (auto)

**Relationships**:
- Many-to-One: User

**Validation Rules**:
- Key name unique per user
- Key hash securely generated and stored

## State Transitions

### Stock Status Transitions
- `ACTIVE` → `HALTED` (trading halt)
- `ACTIVE` → `SUSPENDED` (regulatory suspension)
- `HALTED` → `ACTIVE` (resume trading)
- `HALTED` → `SUSPENDED` (escalation)
- `SUSPENDED` → `ACTIVE` (reinstatement)
- Any status → `DELISTED` (permanent removal)

### Transaction Processing Flow
1. `Email Received` → `PENDING` (EmailProcessingLog)
2. `PENDING` → `PROCESSED` (successful parsing)
3. `PENDING` → `FAILED` (parsing error)
4. `PENDING` → `MANUAL_REVIEW` (ambiguous data)
5. `MANUAL_REVIEW` → `PROCESSED` (human verification)

### Portfolio Value Calculation
- Triggered by: price updates, new transactions, dividend payments
- Formula: Sum of (holding.quantity * stock.current_price) for all active holdings
- Daily change: current_value - previous_day_value

## Data Integrity Rules

### Financial Data Integrity
- All monetary amounts stored as DECIMAL for precision
- Currency codes follow ISO 4217 standard
- Negative quantities not allowed for holdings
- Transaction amounts must balance with fees

### Audit Trail Requirements
- All financial records immutable after verification
- Change history tracked via updated_at timestamps
- Source references maintained for all automated entries
- Manual overrides require user attribution

### Performance Considerations
- Indexes on frequently queried fields (user_id, portfolio_id, stock_symbol)
- Partitioning for price_history by date ranges
- Calculated fields cached and updated via triggers
- Batch processing for daily value recalculations

## MVP Simplifications

**Initially Excluded** (Future Phases):
- Multi-user portfolio permissions
- Currency conversion for international stocks
- Advanced corporate actions (splits, mergers)
- Real-time streaming price updates
- Complex tax calculations
- Portfolio rebalancing recommendations
- Advanced AI analysis results storage

**Included in MVP**:
- Single-user portfolio management
- Basic transaction tracking
- Daily price updates
- Email processing audit trail
- Simple dividend tracking
- API authentication
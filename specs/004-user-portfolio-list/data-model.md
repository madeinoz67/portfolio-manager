# Data Model: Portfolio List View Enhancement

## Overview
The portfolio list view enhancement introduces new frontend-only data structures for managing view state and table configuration. No backend database changes are required as the feature utilizes the existing Portfolio entity structure.

## Core Entities

### ViewMode
```typescript
type ViewMode = 'tiles' | 'table'
```
**Purpose**: Enumeration defining the two available portfolio display modes
**Attributes**:
- `'tiles'`: Grid-based card layout (current default)
- `'table'`: Tabular row-based layout (new feature)

**Validation Rules**:
- Must be one of the two defined string literals
- Required field, no null/undefined values allowed

### PortfolioViewState
```typescript
interface PortfolioViewState {
  viewMode: ViewMode
  tableConfig: TableConfig
  lastUpdated: Date
}
```
**Purpose**: Container for user's current view preferences and configuration
**Attributes**:
- `viewMode`: Current display mode selection
- `tableConfig`: Configuration specific to table view
- `lastUpdated`: Timestamp for preference persistence validation

**Relationships**:
- Aggregates ViewMode enum
- Contains TableConfig entity

**State Transitions**:
- Initial state: `{ viewMode: 'tiles', tableConfig: defaultConfig, lastUpdated: new Date() }`
- Toggle transition: `viewMode` changes between 'tiles' and 'table'
- Configuration updates modify `tableConfig` and update `lastUpdated`

### TableConfig
```typescript
interface TableConfig {
  columns: TableColumn[]
  sortable: boolean
  responsive: ResponsiveConfig
}
```
**Purpose**: Configuration object for table view display options
**Attributes**:
- `columns`: Array of column definitions for table display
- `sortable`: Boolean flag enabling/disabling column sorting
- `responsive`: Mobile and tablet display behavior configuration

**Validation Rules**:
- `columns`: Must contain at least 1 column, maximum 10 columns
- `sortable`: Boolean, defaults to true
- `responsive`: Must contain valid breakpoint configurations

### TableColumn
```typescript
interface TableColumn {
  key: keyof Portfolio
  label: string
  visible: boolean
  sortable: boolean
  width?: string
  align: 'left' | 'center' | 'right'
  priority: number
  formatter?: (value: any) => string
}
```
**Purpose**: Individual column configuration for table display
**Attributes**:
- `key`: Portfolio property key that this column displays
- `label`: Human-readable column header text
- `visible`: Whether column appears in current view
- `sortable`: Whether column supports click-to-sort
- `width`: Optional CSS width value (e.g., '150px', '20%')
- `align`: Text alignment within column
- `priority`: Ordering priority (1 = highest, shown first on mobile)
- `formatter`: Optional function to format cell values

**Validation Rules**:
- `key`: Must be valid Portfolio property key
- `label`: Non-empty string, max 50 characters
- `priority`: Integer between 1-10, no duplicates within TableConfig
- `align`: Must be one of the three literal values
- `formatter`: If provided, must be valid function

### ResponsiveConfig
```typescript
interface ResponsiveConfig {
  mobile: {
    maxColumns: number
    hiddenColumns: string[]
    scrollDirection: 'horizontal' | 'vertical'
  }
  tablet: {
    maxColumns: number
    hiddenColumns: string[]
  }
}
```
**Purpose**: Responsive behavior configuration for different screen sizes
**Attributes**:
- `mobile`: Configuration for screens < 768px
- `tablet`: Configuration for screens 768px - 1024px
- Column visibility and display behavior per breakpoint

## Data Flow Relationships

### Portfolio Entity (Existing)
The existing Portfolio entity serves as the data source for both view modes:
```typescript
interface Portfolio {
  id: string
  name: string
  description?: string
  total_value: string
  daily_change: string
  daily_change_percent: string
  unrealized_gain_loss: string
  unrealized_gain_loss_percent: string
  created_at: string
  updated_at: string
  price_last_updated?: string
  // ... other existing fields
}
```

**Relationships**:
- One Portfolio → Many TableColumn references (via key property)
- Portfolio data displayed in both ViewModes without transformation

### Persistence Strategy
```typescript
interface PersistedViewState {
  viewMode: ViewMode
  tableColumns: Partial<TableColumn>[]  // Only user customizations
  timestamp: number
}
```
**Storage**: Browser localStorage
**Key**: `portfolio-view-preferences`
**TTL**: No expiration, persists until manually cleared

## Default Configuration

### Default Table Columns
```typescript
const DEFAULT_TABLE_COLUMNS: TableColumn[] = [
  {
    key: 'name',
    label: 'Portfolio Name',
    visible: true,
    sortable: true,
    align: 'left',
    priority: 1,
    width: '200px'
  },
  {
    key: 'total_value',
    label: 'Total Value',
    visible: true,
    sortable: true,
    align: 'right',
    priority: 2,
    formatter: (value) => `$${parseFloat(value).toLocaleString()}`
  },
  {
    key: 'daily_change',
    label: 'Daily Change',
    visible: true,
    sortable: true,
    align: 'right',
    priority: 3,
    formatter: (value) => formatCurrencyChange(value)
  },
  {
    key: 'unrealized_gain_loss',
    label: 'Unrealized P&L',
    visible: true,
    sortable: true,
    align: 'right',
    priority: 4,
    formatter: (value) => formatCurrencyChange(value)
  },
  {
    key: 'created_at',
    label: 'Created',
    visible: true,
    sortable: true,
    align: 'center',
    priority: 5,
    formatter: (value) => new Date(value).toLocaleDateString()
  },
  {
    key: 'price_last_updated',
    label: 'Last Updated',
    visible: true,
    sortable: false,
    align: 'center',
    priority: 6,
    formatter: (value) => getRelativeTime(value)
  }
]
```

## State Management Integration

### Existing State Compatibility
The view enhancement must coexist with existing portfolio page state:
- Search query filtering
- Sort by/order controls
- Portfolio CRUD operations
- Loading and error states

### State Isolation
View state management is isolated from business logic:
```typescript
// Existing business state (unchanged)
const { portfolios, loading, error, createPortfolio } = usePortfolios()

// New view state (isolated)
const { viewMode, tableConfig, toggleView, updateTableConfig } = usePortfolioView()
```

## Migration Strategy
Since this is a new feature with no existing data to migrate:
1. Initial deployment sets all users to default 'tiles' mode
2. User preferences begin persisting on first interaction
3. No database migrations required
4. Backward compatibility maintained (graceful fallback to tiles mode)
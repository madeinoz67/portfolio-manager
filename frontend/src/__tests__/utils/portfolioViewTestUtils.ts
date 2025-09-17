// Portfolio View Test Utilities - Feature 004: Tile/Table View Toggle
// Shared utilities and mock data for testing portfolio view components

import { Portfolio } from '@/types/portfolio'
import {
  ViewMode,
  PortfolioViewState,
  TableColumn,
  TableConfig,
  ResponsiveConfig,
  PersistedViewState
} from '@/types/portfolioView'

// ============================================================================
// MOCK PORTFOLIO DATA
// ============================================================================

/**
 * Creates a mock portfolio for testing
 */
export const createMockPortfolio = (overrides: Partial<Portfolio> = {}): Portfolio => ({
  id: 'portfolio-1',
  name: 'Tech Growth Portfolio',
  description: 'Technology focused growth portfolio',
  total_value: '125432.50',
  daily_change: '2341.25',
  daily_change_percent: '1.87',
  unrealized_gain_loss: '15234.75',
  unrealized_gain_loss_percent: '13.78',
  created_at: '2024-01-15T10:30:00Z',
  updated_at: '2024-09-16T14:22:00Z',
  price_last_updated: '2024-09-16T14:20:00Z',
  ...overrides
})

/**
 * Creates multiple mock portfolios for testing
 */
export const createMockPortfolios = (count: number = 3): Portfolio[] => {
  const portfolios: Portfolio[] = []

  for (let i = 0; i < count; i++) {
    portfolios.push(createMockPortfolio({
      id: `portfolio-${i + 1}`,
      name: `Portfolio ${i + 1}`,
      description: `Test portfolio number ${i + 1}`,
      total_value: (100000 + (i * 25000)).toString(),
      daily_change: (1000 + (i * 500)).toString(),
      daily_change_percent: (1.5 + (i * 0.5)).toString(),
      unrealized_gain_loss: (5000 + (i * 2500)).toString(),
      unrealized_gain_loss_percent: (5.0 + (i * 2.5)).toString(),
      created_at: new Date(2024, 0, 15 + i).toISOString(),
      updated_at: new Date(2024, 8, 16, 14, 20 + i).toISOString(),
      price_last_updated: new Date(2024, 8, 16, 14, 18 + i).toISOString()
    }))
  }

  return portfolios
}

// ============================================================================
// MOCK TABLE CONFIGURATION
// ============================================================================

/**
 * Creates default table column configuration for testing
 */
export const createMockTableColumns = (): TableColumn[] => [
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
    formatter: (value: string) => `$${parseFloat(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  },
  {
    key: 'daily_change',
    label: 'Daily Change',
    visible: true,
    sortable: true,
    align: 'right',
    priority: 3,
    formatter: (value: string) => {
      const num = parseFloat(value)
      const sign = num >= 0 ? '+' : ''
      return `${sign}$${Math.abs(num).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    }
  },
  {
    key: 'unrealized_gain_loss',
    label: 'Unrealized P&L',
    visible: true,
    sortable: true,
    align: 'right',
    priority: 4,
    formatter: (value: string) => {
      const num = parseFloat(value)
      const sign = num >= 0 ? '+' : ''
      return `${sign}$${Math.abs(num).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    }
  },
  {
    key: 'created_at',
    label: 'Created',
    visible: true,
    sortable: true,
    align: 'center',
    priority: 5,
    formatter: (value: string) => new Date(value).toLocaleDateString()
  }
]

/**
 * Creates mock responsive configuration for testing
 */
export const createMockResponsiveConfig = (): ResponsiveConfig => ({
  mobile: {
    maxColumns: 3,
    hiddenColumns: ['unrealized_gain_loss', 'created_at'],
    scrollDirection: 'horizontal'
  },
  tablet: {
    maxColumns: 4,
    hiddenColumns: ['created_at']
  }
})

/**
 * Creates mock table configuration for testing
 */
export const createMockTableConfig = (): TableConfig => ({
  columns: createMockTableColumns(),
  sortable: true,
  responsive: createMockResponsiveConfig()
})

// ============================================================================
// MOCK VIEW STATE
// ============================================================================

/**
 * Creates mock portfolio view state for testing
 */
export const createMockViewState = (overrides: Partial<PortfolioViewState> = {}): PortfolioViewState => ({
  viewMode: 'tiles' as ViewMode,
  tableConfig: createMockTableConfig(),
  lastUpdated: new Date(),
  ...overrides
})

/**
 * Creates mock persisted view state for testing
 */
export const createMockPersistedState = (overrides: Partial<PersistedViewState> = {}): PersistedViewState => ({
  viewMode: 'table' as ViewMode,
  timestamp: Date.now(),
  version: '1.0.0',
  ...overrides
})

// ============================================================================
// TEST UTILITIES
// ============================================================================

/**
 * Mock localStorage for testing
 */
export const createMockLocalStorage = () => {
  const storage: { [key: string]: string } = {}

  return {
    getItem: jest.fn((key: string) => storage[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      storage[key] = value
    }),
    removeItem: jest.fn((key: string) => {
      delete storage[key]
    }),
    clear: jest.fn(() => {
      Object.keys(storage).forEach(key => delete storage[key])
    }),
    get length() {
      return Object.keys(storage).length
    },
    key: jest.fn((index: number) => Object.keys(storage)[index] || null)
  }
}

/**
 * Waits for view transition animation to complete
 */
export const waitForViewTransition = async (duration: number = 300): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, duration))
}

/**
 * Simulates responsive breakpoint changes for testing
 */
export const mockViewportSize = (width: number, height: number = 768): void => {
  Object.defineProperty(window, 'innerWidth', { value: width, writable: true })
  Object.defineProperty(window, 'innerHeight', { value: height, writable: true })

  // Trigger resize event
  window.dispatchEvent(new Event('resize'))
}

/**
 * Helper to create mock event handlers for testing
 */
export const createMockEventHandlers = () => ({
  onViewModeChange: jest.fn(),
  onPortfolioClick: jest.fn(),
  onSort: jest.fn(),
  onViewDetails: jest.fn(),
  onAddTrade: jest.fn(),
  onDelete: jest.fn()
})

// ============================================================================
// ASSERTION HELPERS
// ============================================================================

/**
 * Asserts that a view mode is valid
 */
export const assertValidViewMode = (viewMode: any): asserts viewMode is ViewMode => {
  if (viewMode !== 'tiles' && viewMode !== 'table') {
    throw new Error(`Invalid view mode: ${viewMode}. Must be 'tiles' or 'table'`)
  }
}

/**
 * Asserts that table columns are valid
 */
export const assertValidTableColumns = (columns: any[]): asserts columns is TableColumn[] => {
  if (!Array.isArray(columns)) {
    throw new Error('Table columns must be an array')
  }

  columns.forEach((column, index) => {
    if (!column.key || !column.label || typeof column.priority !== 'number') {
      throw new Error(`Invalid column at index ${index}: missing required fields`)
    }
  })
}

/**
 * Custom Jest matcher for portfolio view state
 */
export const expectViewStateToMatch = (actual: PortfolioViewState, expected: Partial<PortfolioViewState>) => {
  expect(actual).toMatchObject(expected)
  expect(actual.lastUpdated).toBeInstanceOf(Date)
  expect(actual.viewMode).toMatch(/^(tiles|table)$/)
}

// ============================================================================
// TEST SETUP HELPERS
// ============================================================================

/**
 * Sets up common test environment for portfolio view tests
 */
export const setupPortfolioViewTest = () => {
  const mockLocalStorage = createMockLocalStorage()
  const mockEventHandlers = createMockEventHandlers()
  const mockPortfolios = createMockPortfolios()
  const mockViewState = createMockViewState()

  // Mock localStorage
  Object.defineProperty(window, 'localStorage', {
    value: mockLocalStorage,
    writable: true
  })

  return {
    mockLocalStorage,
    mockEventHandlers,
    mockPortfolios,
    mockViewState,
    cleanup: () => {
      jest.clearAllMocks()
      mockLocalStorage.clear()
    }
  }
}

/**
 * Test data constants
 */
export const TEST_CONSTANTS = {
  STORAGE_KEY: 'portfolio-view-preferences',
  ANIMATION_DURATION: 300,
  MOBILE_BREAKPOINT: 768,
  TABLET_BREAKPOINT: 1024,
  DEFAULT_VIEW_MODE: 'tiles' as ViewMode,
  TEST_PORTFOLIOS_COUNT: 5
} as const
/**
 * TDD tests for HoldingsDisplay component Last Updated column visibility
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import HoldingsDisplay from '@/components/Portfolio/HoldingsDisplay'
import { useHoldings } from '@/hooks/useHoldings'

// Mock the useHoldings hook
jest.mock('@/hooks/useHoldings')
const mockUseHoldings = useHoldings as jest.MockedFunction<typeof useHoldings>

// Mock timezone utils
jest.mock('@/utils/timezone', () => ({
  getRelativeTime: jest.fn((dateString: string) => '5 minutes ago')
}))

describe('HoldingsDisplay Last Updated Column', () => {
  const mockHoldings = [
    {
      id: '1',
      portfolio_id: 'portfolio1',
      stock: {
        id: 'stock1',
        symbol: 'AAPL',
        company_name: 'Apple Inc.',
        current_price: '150.00',
        last_price_update: '2025-09-16T03:05:01.686816Z'
      },
      quantity: '100',
      average_cost: '140.00',
      current_value: '15000.00',
      unrealized_gain_loss: '1000.00',
      unrealized_gain_loss_percent: '7.14',
      created_at: '2025-09-16T00:00:00Z',
      updated_at: '2025-09-16T03:05:01Z'
    }
  ]

  beforeEach(() => {
    mockUseHoldings.mockReturnValue({
      holdings: mockHoldings,
      loading: false,
      error: null,
      fetchHoldings: jest.fn(),
      calculatePortfolioSummary: jest.fn(() => ({
        totalValue: 15000,
        totalCost: 14000,
        totalGainLoss: 1000,
        totalGainLossPercent: 7.14
      })),
      clearError: jest.fn()
    })
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  test('should display Last Updated column header', () => {
    render(<HoldingsDisplay portfolioId="portfolio1" />)

    const lastUpdatedHeader = screen.getByText('Last Updated')
    expect(lastUpdatedHeader).toBeInTheDocument()
  })

  test('should display Last Updated column data for each holding', () => {
    render(<HoldingsDisplay portfolioId="portfolio1" />)

    const lastUpdatedValue = screen.getByText('5 minutes ago')
    expect(lastUpdatedValue).toBeInTheDocument()
  })

  test('should display dash when last_price_update is not available', () => {
    const holdingsWithoutTimestamp = [{
      ...mockHoldings[0],
      stock: {
        ...mockHoldings[0].stock,
        last_price_update: undefined
      }
    }]

    mockUseHoldings.mockReturnValue({
      holdings: holdingsWithoutTimestamp,
      loading: false,
      error: null,
      fetchHoldings: jest.fn(),
      calculatePortfolioSummary: jest.fn(() => ({
        totalValue: 15000,
        totalCost: 14000,
        totalGainLoss: 1000,
        totalGainLossPercent: 7.14
      })),
      clearError: jest.fn()
    })

    render(<HoldingsDisplay portfolioId="portfolio1" />)

    const dashValue = screen.getByText('—')
    expect(dashValue).toBeInTheDocument()
  })

  test('Last Updated column should be visible on all screen sizes', () => {
    render(<HoldingsDisplay portfolioId="portfolio1" />)

    const lastUpdatedHeader = screen.getByText('Last Updated')
    const headerElement = lastUpdatedHeader.closest('th')

    // Check that the header does NOT have responsive hiding classes
    expect(headerElement).not.toHaveClass('hidden')
    expect(headerElement).not.toHaveClass('sm:table-cell')

    const lastUpdatedValue = screen.getByText('5 minutes ago')
    const dataElement = lastUpdatedValue.closest('td')

    // Check that the data cell does NOT have responsive hiding classes
    expect(dataElement).not.toHaveClass('hidden')
    expect(dataElement).not.toHaveClass('sm:table-cell')
  })

  test('Last Updated column should have proper CSS classes for styling', () => {
    render(<HoldingsDisplay portfolioId="portfolio1" />)

    const lastUpdatedHeader = screen.getByText('Last Updated')
    const headerElement = lastUpdatedHeader.closest('th')

    // Verify header has expected styling classes
    expect(headerElement).toHaveClass('px-6', 'py-3', 'text-right')
    expect(headerElement).toHaveClass('text-xs', 'font-medium')
    expect(headerElement).toHaveClass('uppercase', 'tracking-wider')

    const lastUpdatedValue = screen.getByText('5 minutes ago')
    const dataElement = lastUpdatedValue.closest('td')

    // Verify data cell has expected styling classes
    expect(dataElement).toHaveClass('px-6', 'py-4', 'whitespace-nowrap')
    expect(dataElement).toHaveClass('text-sm', 'text-right')
  })

  test('Last Updated column renders in browser DOM structure', () => {
    const { container } = render(<HoldingsDisplay portfolioId="portfolio1" />)

    // Find the table element
    const table = container.querySelector('table')
    expect(table).toBeInTheDocument()

    // Find all table headers
    const headers = table?.querySelectorAll('th')
    expect(headers).toHaveLength(9) // All columns including Trend and Last Updated

    // Verify Last Updated is the 9th column (last one)
    const lastUpdatedHeader = headers?.[8]
    expect(lastUpdatedHeader).toHaveTextContent('Last Updated')

    // Find all data cells in the first row
    const firstRow = table?.querySelector('tbody tr')
    const dataCells = firstRow?.querySelectorAll('td')
    expect(dataCells).toHaveLength(9) // All data cells including Trend and Last Updated

    // Verify Last Updated data cell exists and has content
    const lastUpdatedCell = dataCells?.[8]
    expect(lastUpdatedCell).toHaveTextContent('5 minutes ago')
  })

  test('Last Updated column properly converts UTC to local time', () => {
    // Mock getRelativeTime to verify it's called with UTC timestamp
    const mockGetRelativeTime = require('@/utils/timezone').getRelativeTime as jest.Mock
    mockGetRelativeTime.mockReturnValue('2 hours ago (local)')

    // Holdings with UTC timestamp
    const holdingsWithUTCTime = [{
      ...mockHoldings[0],
      stock: {
        ...mockHoldings[0].stock,
        last_price_update: '2025-09-16T10:00:00Z' // UTC timestamp
      }
    }]

    mockUseHoldings.mockReturnValue({
      holdings: holdingsWithUTCTime,
      loading: false,
      error: null,
      fetchHoldings: jest.fn(),
      calculatePortfolioSummary: jest.fn(() => ({
        totalValue: 15000,
        totalCost: 14000,
        totalGainLoss: 1000,
        totalGainLossPercent: 7.14
      })),
      clearError: jest.fn()
    })

    render(<HoldingsDisplay portfolioId="portfolio1" />)

    // Verify getRelativeTime was called with the UTC timestamp
    expect(mockGetRelativeTime).toHaveBeenCalledWith('2025-09-16T10:00:00Z')

    // Verify the converted time is displayed
    expect(screen.getByText('2 hours ago (local)')).toBeInTheDocument()
  })
})

/**
 * TDD tests for Trend Indicators in Holdings table
 * Following the same style as market-data table view
 */
describe('HoldingsDisplay Trend Indicators', () => {
  const mockHoldingsWithTrends = [
    {
      id: '1',
      portfolio_id: 'portfolio1',
      stock: {
        id: 'stock1',
        symbol: 'AAPL',
        company_name: 'Apple Inc.',
        current_price: '155.00',
        daily_change: '5.00',
        daily_change_percent: '3.33',
        last_price_update: '2025-09-16T03:05:01.686816Z'
      },
      quantity: '100',
      average_cost: '140.00',
      current_value: '15500.00',
      unrealized_gain_loss: '1500.00',
      unrealized_gain_loss_percent: '10.71',
      created_at: '2025-09-16T00:00:00Z',
      updated_at: '2025-09-16T03:05:01Z'
    },
    {
      id: '2',
      portfolio_id: 'portfolio1',
      stock: {
        id: 'stock2',
        symbol: 'MSFT',
        company_name: 'Microsoft Corp.',
        current_price: '280.00',
        daily_change: '-2.50',
        daily_change_percent: '-0.88',
        last_price_update: '2025-09-16T03:05:01.686816Z'
      },
      quantity: '50',
      average_cost: '290.00',
      current_value: '14000.00',
      unrealized_gain_loss: '-500.00',
      unrealized_gain_loss_percent: '-3.45',
      created_at: '2025-09-16T00:00:00Z',
      updated_at: '2025-09-16T03:05:01Z'
    },
    {
      id: '3',
      portfolio_id: 'portfolio1',
      stock: {
        id: 'stock3',
        symbol: 'GOOGL',
        company_name: 'Alphabet Inc.',
        current_price: '100.00',
        daily_change: '0.00',
        daily_change_percent: '0.00',
        last_price_update: '2025-09-16T03:05:01.686816Z'
      },
      quantity: '25',
      average_cost: '95.00',
      current_value: '2500.00',
      unrealized_gain_loss: '125.00',
      unrealized_gain_loss_percent: '5.26',
      created_at: '2025-09-16T00:00:00Z',
      updated_at: '2025-09-16T03:05:01Z'
    }
  ]

  beforeEach(() => {
    mockUseHoldings.mockReturnValue({
      holdings: mockHoldingsWithTrends,
      loading: false,
      error: null,
      fetchHoldings: jest.fn(),
      calculatePortfolioSummary: jest.fn(() => ({
        totalValue: 32000,
        totalCost: 30125,
        totalGainLoss: 1875,
        totalGainLossPercent: 6.22
      })),
      clearError: jest.fn()
    })
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  test('should display Trend column header in Holdings table', () => {
    render(<HoldingsDisplay portfolioId="portfolio1" />)

    const trendHeader = screen.getByText('Trend')
    expect(trendHeader).toBeInTheDocument()
  })

  test('should display upward trend indicator for positive daily change', () => {
    render(<HoldingsDisplay portfolioId="portfolio1" />)

    // Look for upward trend icon in AAPL row (first stock with +5.00 change)
    const appleRow = screen.getByText('AAPL').closest('tr')
    expect(appleRow).toBeInTheDocument()

    // Should have green upward arrow icon
    const trendCell = appleRow?.querySelector('[aria-label="Upward trend"]')
    expect(trendCell).toBeInTheDocument()
  })

  test('should display downward trend indicator for negative daily change', () => {
    render(<HoldingsDisplay portfolioId="portfolio1" />)

    // Look for downward trend icon in MSFT row (second stock with -2.50 change)
    const msftRow = screen.getByText('MSFT').closest('tr')
    expect(msftRow).toBeInTheDocument()

    // Should have red downward arrow icon
    const trendCell = msftRow?.querySelector('[aria-label="Downward trend"]')
    expect(trendCell).toBeInTheDocument()
  })

  test('should display neutral trend indicator for zero daily change', () => {
    render(<HoldingsDisplay portfolioId="portfolio1" />)

    // Look for neutral trend icon in GOOGL row (third stock with 0.00 change)
    const googlRow = screen.getByText('GOOGL').closest('tr')
    expect(googlRow).toBeInTheDocument()

    // Should have neutral (horizontal line) icon
    const trendCell = googlRow?.querySelector('[aria-label="Neutral trend"]')
    expect(trendCell).toBeInTheDocument()
  })

  test('should display change amount and percentage in trend column', () => {
    render(<HoldingsDisplay portfolioId="portfolio1" />)

    // Check AAPL positive change display
    expect(screen.getByText('+$5.00')).toBeInTheDocument()
    expect(screen.getByText('(+3.33%)')).toBeInTheDocument()

    // Check MSFT negative change display
    expect(screen.getByText('-$2.50')).toBeInTheDocument()
    expect(screen.getByText('(-0.88%)')).toBeInTheDocument()

    // Check GOOGL neutral change display
    expect(screen.getByText('$0.00')).toBeInTheDocument()
    expect(screen.getByText('(0.00%)')).toBeInTheDocument()
  })

  test('should apply correct color styling for trend indicators', () => {
    render(<HoldingsDisplay portfolioId="portfolio1" />)

    // Find trend cells by their content - look for the parent container with color classes
    const positiveTrendContainer = screen.getByText('+$5.00').closest('.text-green-600')
    const negativeTrendContainer = screen.getByText('-$2.50').closest('.text-red-600')
    const neutralTrendContainer = screen.getByText('$0.00').closest('.text-gray-600')

    // Check color classes are present on the container
    expect(positiveTrendContainer).toHaveClass('text-green-600', 'dark:text-green-400')
    expect(negativeTrendContainer).toHaveClass('text-red-600', 'dark:text-red-400')
    expect(neutralTrendContainer).toHaveClass('text-gray-600', 'dark:text-gray-400')
  })

  test('should handle missing trend data gracefully', () => {
    const holdingsWithoutTrends = [{
      ...mockHoldingsWithTrends[0],
      stock: {
        ...mockHoldingsWithTrends[0].stock,
        daily_change: undefined,
        daily_change_percent: undefined
      }
    }]

    mockUseHoldings.mockReturnValue({
      holdings: holdingsWithoutTrends,
      loading: false,
      error: null,
      fetchHoldings: jest.fn(),
      calculatePortfolioSummary: jest.fn(() => ({
        totalValue: 15500,
        totalCost: 14000,
        totalGainLoss: 1500,
        totalGainLossPercent: 10.71
      })),
      clearError: jest.fn()
    })

    render(<HoldingsDisplay portfolioId="portfolio1" />)

    // Should show no trend data indicator
    const noTrendCell = screen.getByLabelText('No trend data')
    expect(noTrendCell).toBeInTheDocument()
  })

  test('Holdings table should have 9 columns including new Trend column', () => {
    const { container } = render(<HoldingsDisplay portfolioId="portfolio1" />)

    const table = container.querySelector('table')
    const headers = table?.querySelectorAll('th')

    // Should now have 9 columns: Stock, Quantity, Avg Cost, Current Price, Market Value, Gain/Loss, Return %, Trend, Last Updated
    expect(headers).toHaveLength(9)

    // Verify Trend column position (should be 8th column, before Last Updated)
    const trendHeader = headers?.[7]
    expect(trendHeader).toHaveTextContent('Trend')
  })

  test('Trend column should be properly centered in table layout', () => {
    render(<HoldingsDisplay portfolioId="portfolio1" />)

    const trendHeader = screen.getByText('Trend')
    const headerElement = trendHeader.closest('th')

    // Should have center alignment classes
    expect(headerElement).toHaveClass('text-center')
  })
})
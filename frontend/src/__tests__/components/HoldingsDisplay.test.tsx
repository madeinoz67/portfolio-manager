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
    expect(headers).toHaveLength(8) // All columns including Last Updated

    // Verify Last Updated is the 8th column (last one)
    const lastUpdatedHeader = headers?.[7]
    expect(lastUpdatedHeader).toHaveTextContent('Last Updated')

    // Find all data cells in the first row
    const firstRow = table?.querySelector('tbody tr')
    const dataCells = firstRow?.querySelectorAll('td')
    expect(dataCells).toHaveLength(8) // All data cells including Last Updated

    // Verify Last Updated data cell exists and has content
    const lastUpdatedCell = dataCells?.[7]
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
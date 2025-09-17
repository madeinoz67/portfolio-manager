// PortfolioTable Component Contract Tests - Feature 004: Tile/Table View Toggle
// These tests MUST FAIL before implementation (TDD Red phase)

import React from 'react'
import { render, screen, fireEvent, within } from '@testing-library/react'
import '@testing-library/jest-dom'
import PortfolioTable from '@/components/Portfolio/PortfolioTable'
import { PortfolioTableProps } from '@/types/portfolioView'
import { Portfolio } from '@/types/portfolio'
import {
  createMockPortfolios,
  createMockTableColumns,
  createMockEventHandlers
} from '@/__tests__/utils/portfolioViewTestUtils'

describe('PortfolioTable Component Contract', () => {
  const mockPortfolios = createMockPortfolios(3)
  const mockColumns = createMockTableColumns()
  const mockHandlers = createMockEventHandlers()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Basic Rendering', () => {
    it('should render table with portfolio data', () => {
      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns
      }

      render(<PortfolioTable {...props} />)

      // Should render as a table
      expect(screen.getByRole('table')).toBeInTheDocument()

      // Should render column headers
      expect(screen.getByRole('columnheader', { name: /portfolio name/i })).toBeInTheDocument()
      expect(screen.getByRole('columnheader', { name: /total value/i })).toBeInTheDocument()
      expect(screen.getByRole('columnheader', { name: /daily change/i })).toBeInTheDocument()

      // Should render portfolio data rows
      expect(screen.getAllByRole('row')).toHaveLength(mockPortfolios.length + 1) // +1 for header
      expect(screen.getByText('Portfolio 1')).toBeInTheDocument()
      expect(screen.getByText('Portfolio 2')).toBeInTheDocument()
      expect(screen.getByText('Portfolio 3')).toBeInTheDocument()
    })

    it('should apply custom className when provided', () => {
      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns,
        className: 'custom-table-class'
      }

      render(<PortfolioTable {...props} />)

      expect(screen.getByRole('table')).toHaveClass('custom-table-class')
    })

    it('should render empty state when no portfolios provided', () => {
      const props: PortfolioTableProps = {
        portfolios: [],
        columns: mockColumns,
        emptyMessage: 'No portfolios found'
      }

      render(<PortfolioTable {...props} />)

      expect(screen.getByText('No portfolios found')).toBeInTheDocument()
      expect(screen.queryByRole('table')).not.toBeInTheDocument()
    })

    it('should use default empty message when none provided', () => {
      const props: PortfolioTableProps = {
        portfolios: [],
        columns: mockColumns
      }

      render(<PortfolioTable {...props} />)

      expect(screen.getByText(/no portfolios/i)).toBeInTheDocument()
    })
  })

  describe('Column Configuration', () => {
    it('should only render visible columns', () => {
      const columnsWithHidden = mockColumns.map((col, index) => ({
        ...col,
        visible: index < 2 // Only first 2 columns visible
      }))

      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: columnsWithHidden
      }

      render(<PortfolioTable {...props} />)

      // Should only show first 2 column headers
      expect(screen.getByRole('columnheader', { name: /portfolio name/i })).toBeInTheDocument()
      expect(screen.getByRole('columnheader', { name: /total value/i })).toBeInTheDocument()
      expect(screen.queryByRole('columnheader', { name: /daily change/i })).not.toBeInTheDocument()
    })

    it('should apply column alignment classes', () => {
      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns
      }

      render(<PortfolioTable {...props} />)

      // Check alignment for different columns
      const nameHeader = screen.getByRole('columnheader', { name: /portfolio name/i })
      const valueHeader = screen.getByRole('columnheader', { name: /total value/i })

      expect(nameHeader).toHaveClass(expect.stringMatching(/left|text-left/))
      expect(valueHeader).toHaveClass(expect.stringMatching(/right|text-right/))
    })

    it('should apply column width styles when specified', () => {
      const columnsWithWidth = mockColumns.map(col => ({
        ...col,
        width: col.key === 'name' ? '300px' : undefined
      }))

      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: columnsWithWidth
      }

      render(<PortfolioTable {...props} />)

      const nameHeader = screen.getByRole('columnheader', { name: /portfolio name/i })
      expect(nameHeader).toHaveStyle('width: 300px')
    })

    it('should format values using column formatters', () => {
      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns
      }

      render(<PortfolioTable {...props} />)

      // Should format currency values (depends on formatter implementation)
      expect(screen.getByText(/\$125,432\.50/)).toBeInTheDocument()
      expect(screen.getByText(/\+\$2,341\.25/)).toBeInTheDocument()
    })
  })

  describe('Sorting Functionality', () => {
    it('should render sortable column headers with sort indicators', () => {
      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns,
        onSort: mockHandlers.onSort
      }

      render(<PortfolioTable {...props} />)

      const sortableHeaders = screen.getAllByRole('columnheader').filter(header =>
        mockColumns.find(col => col.sortable && header.textContent?.includes(col.label))
      )

      sortableHeaders.forEach(header => {
        expect(header).toHaveAttribute('role', 'columnheader')
        expect(header).toHaveClass(expect.stringMatching(/sortable|cursor-pointer/))
      })
    })

    it('should call onSort when sortable column header is clicked', () => {
      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns,
        onSort: mockHandlers.onSort
      }

      render(<PortfolioTable {...props} />)

      const nameHeader = screen.getByRole('columnheader', { name: /portfolio name/i })
      fireEvent.click(nameHeader)

      expect(mockHandlers.onSort).toHaveBeenCalledTimes(1)
      expect(mockHandlers.onSort).toHaveBeenCalledWith('name')
    })

    it('should show current sort state with indicators', () => {
      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns,
        sortBy: 'total_value',
        sortOrder: 'desc',
        onSort: mockHandlers.onSort
      }

      render(<PortfolioTable {...props} />)

      const valueHeader = screen.getByRole('columnheader', { name: /total value/i })

      // Should show sort indicator for active column
      expect(valueHeader).toHaveAttribute('aria-sort', 'descending')
      expect(within(valueHeader).getByRole('img', { hidden: true })).toBeInTheDocument() // Sort icon
    })

    it('should not make non-sortable columns clickable', () => {
      const columnsWithNonSortable = mockColumns.map(col => ({
        ...col,
        sortable: col.key === 'name' ? false : col.sortable
      }))

      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: columnsWithNonSortable,
        onSort: mockHandlers.onSort
      }

      render(<PortfolioTable {...props} />)

      const nameHeader = screen.getByRole('columnheader', { name: /portfolio name/i })
      expect(nameHeader).not.toHaveClass(expect.stringMatching(/sortable|cursor-pointer/))

      fireEvent.click(nameHeader)
      expect(mockHandlers.onSort).not.toHaveBeenCalled()
    })
  })

  describe('Row Interactions', () => {
    it('should call onPortfolioClick when row is clicked', () => {
      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns,
        onPortfolioClick: mockHandlers.onPortfolioClick
      }

      render(<PortfolioTable {...props} />)

      const firstRow = screen.getAllByRole('row')[1] // Skip header row
      fireEvent.click(firstRow)

      expect(mockHandlers.onPortfolioClick).toHaveBeenCalledTimes(1)
      expect(mockHandlers.onPortfolioClick).toHaveBeenCalledWith(mockPortfolios[0])
    })

    it('should render action buttons when showActions is true', () => {
      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns,
        showActions: true,
        onPortfolioClick: mockHandlers.onPortfolioClick,
        onPortfolioDelete: jest.fn()
      }

      render(<PortfolioTable {...props} />)

      // Should have action column header
      expect(screen.getByRole('columnheader', { name: /actions/i })).toBeInTheDocument()

      // Should have action buttons in each row
      expect(screen.getAllByRole('button', { name: /view/i })).toHaveLength(mockPortfolios.length)
      expect(screen.getAllByRole('button', { name: /add trade/i })).toHaveLength(mockPortfolios.length)
      expect(screen.getAllByRole('button', { name: /delete/i })).toHaveLength(mockPortfolios.length)
    })

    it('should call appropriate handlers when action buttons are clicked', () => {
      const mockDelete = jest.fn()
      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns,
        showActions: true,
        onPortfolioClick: mockHandlers.onPortfolioClick,
        onPortfolioDelete: mockDelete
      }

      render(<PortfolioTable {...props} />)

      const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
      fireEvent.click(deleteButtons[0])

      expect(mockDelete).toHaveBeenCalledTimes(1)
      expect(mockDelete).toHaveBeenCalledWith(mockPortfolios[0])
    })
  })

  describe('Loading State', () => {
    it('should show loading skeleton when loading prop is true', () => {
      const props: PortfolioTableProps = {
        portfolios: [],
        columns: mockColumns,
        loading: true
      }

      render(<PortfolioTable {...props} />)

      // Should show loading indicators
      expect(screen.getByRole('table')).toBeInTheDocument()
      expect(screen.getAllByTestId('table-skeleton-row')).toHaveLength(3) // Default skeleton rows
    })

    it('should disable interactions during loading', () => {
      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns,
        loading: true,
        onSort: mockHandlers.onSort,
        onPortfolioClick: mockHandlers.onPortfolioClick
      }

      render(<PortfolioTable {...props} />)

      // Sort should be disabled
      const nameHeader = screen.getByRole('columnheader', { name: /portfolio name/i })
      fireEvent.click(nameHeader)
      expect(mockHandlers.onSort).not.toHaveBeenCalled()

      // Row clicks should be disabled
      const firstRow = screen.getAllByRole('row')[1]
      fireEvent.click(firstRow)
      expect(mockHandlers.onPortfolioClick).not.toHaveBeenCalled()
    })
  })

  describe('Responsive Behavior', () => {
    it('should apply responsive classes for mobile layout', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', { value: 600, writable: true })

      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns
      }

      render(<PortfolioTable {...props} />)

      const table = screen.getByRole('table')
      expect(table).toHaveClass(expect.stringMatching(/mobile|responsive|overflow-x/))
    })

    it('should prioritize columns based on responsive configuration', () => {
      const responsiveColumns = mockColumns.map((col, index) => ({
        ...col,
        priority: index + 1,
        visible: index < 3 // Hide less important columns on mobile
      }))

      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: responsiveColumns
      }

      render(<PortfolioTable {...props} />)

      // High priority columns should be visible
      expect(screen.getByRole('columnheader', { name: /portfolio name/i })).toBeInTheDocument()
      expect(screen.getByRole('columnheader', { name: /total value/i })).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper table accessibility attributes', () => {
      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns
      }

      render(<PortfolioTable {...props} />)

      const table = screen.getByRole('table')
      expect(table).toHaveAttribute('aria-label', expect.stringMatching(/portfolios|table/i))

      // Column headers should have proper scope
      const headers = screen.getAllByRole('columnheader')
      headers.forEach(header => {
        expect(header).toHaveAttribute('scope', 'col')
      })
    })

    it('should support keyboard navigation', () => {
      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns,
        onPortfolioClick: mockHandlers.onPortfolioClick
      }

      render(<PortfolioTable {...props} />)

      const firstRow = screen.getAllByRole('row')[1]

      // Should be focusable
      expect(firstRow).toHaveAttribute('tabIndex', '0')

      // Should respond to keyboard events
      firstRow.focus()
      fireEvent.keyDown(firstRow, { key: 'Enter', code: 'Enter' })
      expect(mockHandlers.onPortfolioClick).toHaveBeenCalledWith(mockPortfolios[0])
    })

    it('should announce sort changes to screen readers', () => {
      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns,
        sortBy: 'name',
        sortOrder: 'asc',
        onSort: mockHandlers.onSort
      }

      render(<PortfolioTable {...props} />)

      const nameHeader = screen.getByRole('columnheader', { name: /portfolio name/i })
      expect(nameHeader).toHaveAttribute('aria-sort', 'ascending')

      // Should have screen reader announcements for sort state
      expect(nameHeader).toHaveAttribute('aria-label', expect.stringMatching(/sorted|ascending/i))
    })
  })

  describe('Error Handling', () => {
    it('should handle malformed portfolio data gracefully', () => {
      const malformedPortfolios = [
        { ...mockPortfolios[0], total_value: null },
        { ...mockPortfolios[1], name: undefined }
      ] as Portfolio[]

      const props: PortfolioTableProps = {
        portfolios: malformedPortfolios,
        columns: mockColumns
      }

      expect(() => render(<PortfolioTable {...props} />)).not.toThrow()

      // Should render fallback values for missing data
      expect(screen.getByText(/--/)).toBeInTheDocument() // Fallback for null value
    })

    it('should handle missing formatter functions', () => {
      const columnsWithoutFormatter = mockColumns.map(col => ({
        ...col,
        formatter: undefined
      }))

      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: columnsWithoutFormatter
      }

      expect(() => render(<PortfolioTable {...props} />)).not.toThrow()

      // Should display raw values when no formatter provided
      expect(screen.getByText('125432.50')).toBeInTheDocument()
    })
  })
})
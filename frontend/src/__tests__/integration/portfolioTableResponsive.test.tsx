// Portfolio Table Responsive Integration Tests - Feature 004: Tile/Table View Toggle
// These tests MUST FAIL before implementation (TDD Red phase)

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import PortfolioTable from '@/components/Portfolio/PortfolioTable'
import { PortfolioTableProps } from '@/types/portfolioView'
import {
  createMockPortfolios,
  createMockTableColumns,
  mockViewportSize
} from '@/__tests__/utils/portfolioViewTestUtils'

describe('Portfolio Table Responsive Integration', () => {
  const mockPortfolios = createMockPortfolios(5)
  const mockColumns = createMockTableColumns()

  beforeEach(() => {
    jest.clearAllMocks()
    // Reset to desktop size
    mockViewportSize(1200, 800)
  })

  describe('Desktop Responsive Behavior', () => {
    it('should display all columns on desktop', () => {
      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns
      }

      render(<PortfolioTable {...props} />)

      // All columns should be visible on desktop
      mockColumns.forEach(column => {
        if (column.visible) {
          expect(screen.getByRole('columnheader', { name: new RegExp(column.label, 'i') }))
            .toBeInTheDocument()
        }
      })
    })

    it('should not apply mobile responsive classes on desktop', () => {
      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns
      }

      render(<PortfolioTable {...props} />)

      const table = screen.getByRole('table')
      expect(table).not.toHaveClass(/mobile|scroll-x|overflow-x-auto/)
    })
  })

  describe('Tablet Responsive Behavior', () => {
    it('should hide lower priority columns on tablet', () => {
      mockViewportSize(800, 600) // Tablet size

      const responsiveColumns = mockColumns.map((col, index) => ({
        ...col,
        priority: index + 1,
        visible: index < 4 // Hide last column on tablet
      }))

      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: responsiveColumns
      }

      render(<PortfolioTable {...props} />)

      // First 4 columns should be visible
      expect(screen.getByRole('columnheader', { name: /portfolio name/i })).toBeInTheDocument()
      expect(screen.getByRole('columnheader', { name: /total value/i })).toBeInTheDocument()
      expect(screen.getByRole('columnheader', { name: /daily change/i })).toBeInTheDocument()
      expect(screen.getByRole('columnheader', { name: /unrealized p&l/i })).toBeInTheDocument()

      // Last column should be hidden
      expect(screen.queryByRole('columnheader', { name: /created/i })).not.toBeInTheDocument()
    })

    it('should apply tablet responsive classes', () => {
      mockViewportSize(800, 600)

      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns
      }

      render(<PortfolioTable {...props} />)

      const table = screen.getByRole('table')
      expect(table).toHaveClass(expect.stringMatching(/tablet|md:|lg:/))
    })
  })

  describe('Mobile Responsive Behavior', () => {
    it('should show only priority columns on mobile', () => {
      mockViewportSize(600, 800) // Mobile size

      const mobileColumns = mockColumns.map((col, index) => ({
        ...col,
        priority: index + 1,
        visible: index < 3 // Only first 3 columns on mobile
      }))

      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mobileColumns
      }

      render(<PortfolioTable {...props} />)

      // High priority columns should be visible
      expect(screen.getByRole('columnheader', { name: /portfolio name/i })).toBeInTheDocument()
      expect(screen.getByRole('columnheader', { name: /total value/i })).toBeInTheDocument()
      expect(screen.getByRole('columnheader', { name: /daily change/i })).toBeInTheDocument()

      // Lower priority columns should be hidden
      expect(screen.queryByRole('columnheader', { name: /unrealized p&l/i })).not.toBeInTheDocument()
      expect(screen.queryByRole('columnheader', { name: /created/i })).not.toBeInTheDocument()
    })

    it('should enable horizontal scrolling on mobile', () => {
      mockViewportSize(400, 600)

      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns
      }

      render(<PortfolioTable {...props} />)

      const tableContainer = screen.getByRole('table').parentElement
      expect(tableContainer).toHaveClass(/overflow-x-auto|scroll-x|horizontal-scroll/)
    })

    it('should maintain touch scrolling performance', () => {
      mockViewportSize(400, 600)

      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns
      }

      render(<PortfolioTable {...props} />)

      const tableContainer = screen.getByRole('table').parentElement
      expect(tableContainer).toHaveStyle('-webkit-overflow-scrolling: touch')
    })

    it('should adjust row height for touch targets', () => {
      mockViewportSize(400, 600)

      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns,
        onPortfolioClick: jest.fn()
      }

      render(<PortfolioTable {...props} />)

      const tableRows = screen.getAllByRole('row').slice(1) // Skip header
      tableRows.forEach(row => {
        expect(row).toHaveClass(expect.stringMatching(/h-12|h-14|min-h|touch-target/))
      })
    })
  })

  describe('Dynamic Responsive Updates', () => {
    it('should update layout when viewport changes', () => {
      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns
      }

      const { rerender } = render(<PortfolioTable {...props} />)

      // Start desktop - all columns visible
      expect(screen.getAllByRole('columnheader')).toHaveLength(mockColumns.filter(c => c.visible).length)

      // Change to mobile
      mockViewportSize(400, 600)
      rerender(<PortfolioTable {...props} />)

      // Should apply mobile layout
      const table = screen.getByRole('table')
      expect(table.parentElement).toHaveClass(/overflow-x/)
    })

    it('should handle orientation changes', () => {
      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns
      }

      render(<PortfolioTable {...props} />)

      // Portrait mobile
      mockViewportSize(400, 800)
      window.dispatchEvent(new Event('orientationchange'))

      let table = screen.getByRole('table')
      expect(table.parentElement).toHaveClass(/overflow-x/)

      // Landscape mobile (more space for columns)
      mockViewportSize(800, 400)
      window.dispatchEvent(new Event('orientationchange'))

      table = screen.getByRole('table')
      // Should show more columns in landscape
      expect(screen.getAllByRole('columnheader').length).toBeGreaterThan(3)
    })
  })

  describe('Column Priority System', () => {
    it('should respect column priority ordering', () => {
      mockViewportSize(600, 800)

      const prioritizedColumns = [
        { ...mockColumns[0], priority: 3 }, // name - lower priority
        { ...mockColumns[1], priority: 1 }, // value - highest priority
        { ...mockColumns[2], priority: 2 }, // change - medium priority
        { ...mockColumns[3], priority: 4, visible: false }, // p&l - hidden
        { ...mockColumns[4], priority: 5, visible: false }  // created - hidden
      ]

      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: prioritizedColumns
      }

      render(<PortfolioTable {...props} />)

      const headers = screen.getAllByRole('columnheader')

      // Should show in priority order: value (1), change (2), name (3)
      expect(headers[0]).toHaveTextContent(/total value/i)
      expect(headers[1]).toHaveTextContent(/daily change/i)
      expect(headers[2]).toHaveTextContent(/portfolio name/i)
    })

    it('should handle equal priority columns', () => {
      const equalPriorityColumns = mockColumns.map(col => ({
        ...col,
        priority: 1 // All same priority
      }))

      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: equalPriorityColumns
      }

      expect(() => render(<PortfolioTable {...props} />)).not.toThrow()

      // Should render all columns when priorities are equal
      equalPriorityColumns.forEach(column => {
        if (column.visible) {
          expect(screen.getByRole('columnheader', { name: new RegExp(column.label, 'i') }))
            .toBeInTheDocument()
        }
      })
    })
  })

  describe('Content Overflow Handling', () => {
    it('should truncate long content in narrow columns', () => {
      mockViewportSize(400, 600)

      const portfoliosWithLongNames = mockPortfolios.map((p, i) => ({
        ...p,
        name: `Very Long Portfolio Name That Should Be Truncated ${i + 1}`
      }))

      const props: PortfolioTableProps = {
        portfolios: portfoliosWithLongNames,
        columns: mockColumns
      }

      render(<PortfolioTable {...props} />)

      // Long content should be truncated with ellipsis
      const nameCells = screen.getAllByText(/Very Long Portfolio Name/)
      nameCells.forEach(cell => {
        expect(cell).toHaveClass(/truncate|ellipsis|overflow-hidden/)
      })
    })

    it('should show tooltips for truncated content', () => {
      mockViewportSize(400, 600)

      const portfoliosWithLongNames = mockPortfolios.map(p => ({
        ...p,
        name: 'Very Long Portfolio Name That Needs Tooltip'
      }))

      const props: PortfolioTableProps = {
        portfolios: portfoliosWithLongNames,
        columns: mockColumns
      }

      render(<PortfolioTable {...props} />)

      const nameCell = screen.getAllByText(/Very Long Portfolio Name/)[0]
      expect(nameCell).toHaveAttribute('title', 'Very Long Portfolio Name That Needs Tooltip')
    })
  })

  describe('Performance Optimization', () => {
    it('should virtualize rows for large datasets on mobile', () => {
      mockViewportSize(400, 600)

      const manyPortfolios = createMockPortfolios(100) // Large dataset

      const props: PortfolioTableProps = {
        portfolios: manyPortfolios,
        columns: mockColumns
      }

      render(<PortfolioTable {...props} />)

      // Should only render visible rows (virtualization)
      const visibleRows = screen.getAllByRole('row')
      expect(visibleRows.length).toBeLessThan(50) // Less than total dataset
      expect(visibleRows.length).toBeGreaterThan(5) // But more than just header
    })

    it('should maintain scroll position during responsive changes', () => {
      const manyPortfolios = createMockPortfolios(50)

      const props: PortfolioTableProps = {
        portfolios: manyPortfolios,
        columns: mockColumns
      }

      render(<PortfolioTable {...props} />)

      const tableContainer = screen.getByRole('table').parentElement!

      // Scroll to middle
      tableContainer.scrollTop = 500

      // Change viewport
      mockViewportSize(400, 600)
      window.dispatchEvent(new Event('resize'))

      // Scroll position should be preserved
      expect(tableContainer.scrollTop).toBeCloseTo(500, 1)
    })
  })

  describe('Accessibility on Different Viewports', () => {
    it('should maintain accessibility on mobile', () => {
      mockViewportSize(400, 600)

      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns
      }

      render(<PortfolioTable {...props} />)

      const table = screen.getByRole('table')

      // Should maintain table semantics
      expect(table).toHaveAttribute('aria-label')

      // Headers should have proper scope
      const headers = screen.getAllByRole('columnheader')
      headers.forEach(header => {
        expect(header).toHaveAttribute('scope', 'col')
      })
    })

    it('should announce responsive layout changes', () => {
      const props: PortfolioTableProps = {
        portfolios: mockPortfolios,
        columns: mockColumns
      }

      render(<PortfolioTable {...props} />)

      // Change to mobile
      mockViewportSize(400, 600)
      window.dispatchEvent(new Event('resize'))

      // Should announce layout change to screen readers
      const announcement = screen.getByRole('status', { hidden: true })
      expect(announcement).toHaveTextContent(/mobile layout|columns adjusted/i)
    })
  })
})
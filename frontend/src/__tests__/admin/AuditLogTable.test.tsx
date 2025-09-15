/**
 * TDD tests for AuditLogTable component.
 * Tests the admin audit log viewing interface with search and filtering.
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AuditLogTable } from '@/components/admin/AuditLogTable'

// Mock fetch for API calls
global.fetch = jest.fn()

const mockAuditLogs = {
  data: [
    {
      id: 1,
      event_type: 'portfolio_created',
      event_description: 'Portfolio "Test Portfolio" created',
      user_email: 'test@example.com',
      entity_type: 'portfolio',
      entity_id: 'portfolio-123',
      timestamp: '2025-01-15T10:30:00Z',
      ip_address: '192.168.1.1',
      user_agent: 'Mozilla/5.0...'
    },
    {
      id: 2,
      event_type: 'transaction_created',
      event_description: 'Transaction created: BUY AAPL',
      user_email: 'trader@example.com',
      entity_type: 'transaction',
      entity_id: 'txn-456',
      timestamp: '2025-01-15T11:15:00Z',
      ip_address: '192.168.1.2',
      user_agent: 'Mozilla/5.0...'
    }
  ],
  pagination: {
    current_page: 1,
    total_pages: 5,
    total_items: 95,
    items_per_page: 20
  },
  filters: {
    search: null,
    event_type: null,
    user_id: null
  },
  meta: {
    processing_time_ms: 45,
    total_events_in_system: 1250
  }
}

describe('AuditLogTable', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => mockAuditLogs
    })
  })

  describe('TDD - Component Creation Tests', () => {
    it('should render AuditLogTable component successfully', () => {
      // This test now passes - component has been created
      const { container } = render(<AuditLogTable />)
      expect(container).toBeInTheDocument()
    })
  })

  describe('TDD - Basic Functionality Tests', () => {
    it('should display loading state initially', async () => {
      // This test will pass once we implement basic loading
      const { container } = render(<AuditLogTable />)
      expect(container.textContent).toContain('Loading')
    })

    it('should fetch and display audit logs', async () => {
      render(<AuditLogTable />)

      await waitFor(() => {
        expect(screen.getByText('Portfolio "Test Portfolio" created')).toBeInTheDocument()
        expect(screen.getByText('Transaction created: BUY AAPL')).toBeInTheDocument()
      })
    })

    it('should display user emails and timestamps', async () => {
      render(<AuditLogTable />)

      await waitFor(() => {
        expect(screen.getByText('test@example.com')).toBeInTheDocument()
        expect(screen.getByText('trader@example.com')).toBeInTheDocument()
      })
    })
  })

  describe('TDD - Search Functionality Tests', () => {
    it('should have a search input field', async () => {
      render(<AuditLogTable />)

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/search audit logs/i)).toBeInTheDocument()
      })
    })

    it('should make API call with search term when searching', async () => {
      render(<AuditLogTable />)

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(/search audit logs/i)
        fireEvent.change(searchInput, { target: { value: 'portfolio' } })
        fireEvent.keyDown(searchInput, { key: 'Enter' })
      })

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('search=portfolio'),
          expect.any(Object)
        )
      })
    })
  })

  describe('TDD - Filtering Tests', () => {
    it('should have event type filter dropdown', async () => {
      render(<AuditLogTable />)

      await waitFor(() => {
        expect(screen.getByLabelText(/event type/i)).toBeInTheDocument()
      })
    })

    it('should have user filter dropdown', async () => {
      render(<AuditLogTable />)

      await waitFor(() => {
        expect(screen.getByLabelText(/user/i)).toBeInTheDocument()
      })
    })

    it('should apply filters when changed', async () => {
      render(<AuditLogTable />)

      await waitFor(() => {
        const eventTypeFilter = screen.getByLabelText(/event type/i)
        fireEvent.change(eventTypeFilter, { target: { value: 'portfolio_created' } })
      })

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('event_type=portfolio_created'),
          expect.any(Object)
        )
      })
    })
  })

  describe('TDD - Pagination Tests', () => {
    it('should display pagination controls', async () => {
      render(<AuditLogTable />)

      await waitFor(() => {
        expect(screen.getByText('Page 1 of 5')).toBeInTheDocument()
        expect(screen.getByText('95 total items')).toBeInTheDocument()
      })
    })

    it('should handle page navigation', async () => {
      render(<AuditLogTable />)

      await waitFor(() => {
        const nextButton = screen.getByText(/next/i)
        fireEvent.click(nextButton)
      })

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('page=2'),
          expect.any(Object)
        )
      })
    })
  })

  describe('TDD - Date Range Filtering Tests', () => {
    it('should have date range inputs', async () => {
      render(<AuditLogTable />)

      await waitFor(() => {
        expect(screen.getByLabelText(/from date/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/to date/i)).toBeInTheDocument()
      })
    })

    it('should apply date range filters', async () => {
      render(<AuditLogTable />)

      await waitFor(() => {
        const fromDateInput = screen.getByLabelText(/from date/i)
        fireEvent.change(fromDateInput, { target: { value: '2025-01-01' } })
      })

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('date_from=2025-01-01'),
          expect.any(Object)
        )
      })
    })
  })

  describe('TDD - Error Handling Tests', () => {
    it('should display error message when API fails', async () => {
      ;(fetch as jest.Mock).mockRejectedValue(new Error('API Error'))

      render(<AuditLogTable />)

      await waitFor(() => {
        expect(screen.getByText(/error loading audit logs/i)).toBeInTheDocument()
      })
    })

    it('should allow retry after error', async () => {
      ;(fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'))
        .mockResolvedValue({
          ok: true,
          json: async () => mockAuditLogs
        })

      render(<AuditLogTable />)

      await waitFor(() => {
        const retryButton = screen.getByText(/retry/i)
        fireEvent.click(retryButton)
      })

      await waitFor(() => {
        expect(screen.getByText('Portfolio "Test Portfolio" created')).toBeInTheDocument()
      })
    })
  })

  describe('TDD - Performance and UX Tests', () => {
    it('should display processing time', async () => {
      render(<AuditLogTable />)

      await waitFor(() => {
        expect(screen.getByText(/45ms/)).toBeInTheDocument()
      })
    })

    it('should display total events count', async () => {
      render(<AuditLogTable />)

      await waitFor(() => {
        expect(screen.getByText(/1,250 total events/i)).toBeInTheDocument()
      })
    })

    it('should debounce search input', async () => {
      jest.useFakeTimers()
      render(<AuditLogTable />)

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(/search audit logs/i)
        fireEvent.change(searchInput, { target: { value: 'test' } })
        fireEvent.change(searchInput, { target: { value: 'testing' } })
        fireEvent.change(searchInput, { target: { value: 'test search' } })
      })

      // Should only make one API call after debounce
      jest.advanceTimersByTime(500)

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(2) // Initial load + debounced search
      })

      jest.useRealTimers()
    })
  })
})
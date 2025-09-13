/**
 * Tests for usePerformance hook
 * RED phase - These tests will fail initially
 */
import { renderHook, waitFor } from '@testing-library/react'
import { usePerformance } from '../usePerformance'

// Mock fetch globally
global.fetch = jest.fn()
const mockFetch = fetch as jest.MockedFunction<typeof fetch>

describe('usePerformance', () => {
  beforeEach(() => {
    mockFetch.mockClear()
  })

  it('should fetch portfolio performance metrics', async () => {
    const mockPerformance = {
      total_return: "1250.50",
      annualized_return: "8.75",
      max_drawdown: "-5.20",
      dividend_yield: "2.15",
      period_start_value: "10000.00",
      period_end_value: "11250.50",
      total_dividends: "215.00",
      period: "1M",
      calculated_at: "2025-09-13T10:00:00Z"
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockPerformance,
    } as Response)

    const { result } = renderHook(() => usePerformance('test-portfolio-id'))

    // Should start with loading state
    expect(result.current.loading).toBe(true)
    expect(result.current.performance).toBe(null)
    expect(result.current.error).toBe(null)

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.performance).toEqual(mockPerformance)
    expect(result.current.error).toBe(null)
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8001/api/v1/portfolios/test-portfolio-id/performance?period=1M',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json'
        })
      })
    )
  })

  it('should handle different performance periods', async () => {
    const mockPerformance = {
      total_return: "2500.00",
      annualized_return: "12.30",
      max_drawdown: "-8.50",
      dividend_yield: "2.80",
      period_start_value: "10000.00",
      period_end_value: "12500.00",
      total_dividends: "280.00",
      period: "1Y",
      calculated_at: "2025-09-13T10:00:00Z"
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockPerformance,
    } as Response)

    const { result } = renderHook(() => usePerformance('test-portfolio-id', '1Y'))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8001/api/v1/portfolios/test-portfolio-id/performance?period=1Y',
      expect.anything()
    )
  })

  it('should handle API errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Portfolio not found' }),
    } as Response)

    const { result } = renderHook(() => usePerformance('invalid-portfolio-id'))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.performance).toBe(null)
    expect(result.current.error).toBe('Portfolio not found')
  })

  it('should provide refresh functionality', async () => {
    const mockPerformance = {
      total_return: "1250.50",
      annualized_return: "8.75",
      max_drawdown: "-5.20",
      dividend_yield: "2.15",
      period_start_value: "10000.00",
      period_end_value: "11250.50",
      total_dividends: "215.00",
      period: "1M",
      calculated_at: "2025-09-13T10:00:00Z"
    }

    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => mockPerformance,
    } as Response)

    const { result } = renderHook(() => usePerformance('test-portfolio-id'))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    // Call refresh
    result.current.refreshPerformance()

    expect(result.current.loading).toBe(true)

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    // Should have called fetch twice (initial + refresh)
    expect(mockFetch).toHaveBeenCalledTimes(2)
  })
})
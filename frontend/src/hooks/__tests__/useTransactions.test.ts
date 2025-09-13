/**
 * Comprehensive test suite for transaction processing
 * RED phase - These tests will fail initially as the features don't exist yet
 */
import { renderHook, waitFor, act } from '@testing-library/react'
import { useTransactions } from '../useTransactions'
import { Transaction, TransactionType } from '@/types/transaction'

// Mock fetch globally
global.fetch = jest.fn()
const mockFetch = fetch as jest.MockedFunction<typeof fetch>

// Mock auth context
const mockUseAuth = {
  token: 'test-token',
  user: { id: '1', email: 'test@example.com' }
}

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth
}))

// Mock portfolio context
const mockPortfolio = {
  id: 'portfolio-1',
  name: 'Test Portfolio',
  description: 'Test portfolio for transactions'
}

jest.mock('../usePortfolios', () => ({
  usePortfolios: () => ({
    currentPortfolio: mockPortfolio
  })
}))

describe('useTransactions', () => {
  beforeEach(() => {
    mockFetch.mockClear()
    jest.clearAllTimers()
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.runOnlyPendingTimers()
    jest.useRealTimers()
  })

  describe('Transaction CRUD Operations', () => {
    it('should fetch transactions for a portfolio', async () => {
      const mockTransactions: Transaction[] = [
        {
          id: '1',
          portfolio_id: 'portfolio-1',
          symbol: 'AAPL',
          type: 'buy' as TransactionType,
          quantity: 100,
          price: 150.25,
          total_amount: 15025.00,
          date: '2024-01-15T10:30:00Z',
          fees: 9.99,
          notes: 'Initial purchase'
        },
        {
          id: '2',
          portfolio_id: 'portfolio-1',
          symbol: 'GOOGL',
          type: 'buy' as TransactionType,
          quantity: 50,
          price: 2800.50,
          total_amount: 140025.00,
          date: '2024-01-16T14:20:00Z',
          fees: 14.99
        }
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTransactions
      } as Response)

      const { result } = renderHook(() => useTransactions('portfolio-1'))

      await waitFor(() => {
        expect(result.current.transactions).toEqual(mockTransactions)
        expect(result.current.loading).toBe(false)
        expect(result.current.error).toBe(null)
      })

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/portfolios/portfolio-1/transactions',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token'
          })
        })
      )
    })

    it('should create a new transaction', async () => {
      const newTransaction = {
        symbol: 'MSFT',
        type: 'buy' as TransactionType,
        quantity: 75,
        price: 380.75,
        date: '2024-01-17T09:15:00Z',
        fees: 12.50,
        notes: 'Tech stock purchase'
      }

      const createdTransaction = {
        id: '3',
        portfolio_id: 'portfolio-1',
        total_amount: 28568.75,
        ...newTransaction
      }

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => []
        } as Response) // Initial fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => createdTransaction
        } as Response) // Create transaction

      const { result } = renderHook(() => useTransactions('portfolio-1'))

      await act(async () => {
        await result.current.createTransaction(newTransaction)
      })

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/portfolios/portfolio-1/transactions',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json'
          }),
          body: JSON.stringify(newTransaction)
        })
      )

      expect(result.current.error).toBe(null)
    })

    it('should update an existing transaction', async () => {
      const transactionId = '1'
      const updateData = {
        quantity: 120,
        price: 155.50,
        notes: 'Updated purchase amount'
      }

      const updatedTransaction = {
        id: transactionId,
        portfolio_id: 'portfolio-1',
        symbol: 'AAPL',
        type: 'buy' as TransactionType,
        total_amount: 18660.00,
        date: '2024-01-15T10:30:00Z',
        fees: 9.99,
        ...updateData
      }

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => []
        } as Response) // Initial fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => updatedTransaction
        } as Response) // Update transaction

      const { result } = renderHook(() => useTransactions('portfolio-1'))

      await act(async () => {
        await result.current.updateTransaction(transactionId, updateData)
      })

      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8001/api/v1/portfolios/portfolio-1/transactions/${transactionId}`,
        expect.objectContaining({
          method: 'PUT',
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json'
          }),
          body: JSON.stringify(updateData)
        })
      )

      expect(result.current.error).toBe(null)
    })

    it('should delete a transaction', async () => {
      const transactionId = '1'

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => []
        } as Response) // Initial fetch
        .mockResolvedValueOnce({
          ok: true
        } as Response) // Delete transaction

      const { result } = renderHook(() => useTransactions('portfolio-1'))

      await act(async () => {
        await result.current.deleteTransaction(transactionId)
      })

      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8001/api/v1/portfolios/portfolio-1/transactions/${transactionId}`,
        expect.objectContaining({
          method: 'DELETE',
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token'
          })
        })
      )

      expect(result.current.error).toBe(null)
    })
  })

  describe('Transaction Filtering and Sorting', () => {
    const mockTransactions: Transaction[] = [
      {
        id: '1',
        portfolio_id: 'portfolio-1',
        symbol: 'AAPL',
        type: 'buy' as TransactionType,
        quantity: 100,
        price: 150.25,
        total_amount: 15025.00,
        date: '2024-01-15T10:30:00Z',
        fees: 9.99
      },
      {
        id: '2',
        portfolio_id: 'portfolio-1',
        symbol: 'AAPL',
        type: 'sell' as TransactionType,
        quantity: 50,
        price: 160.75,
        total_amount: 8037.50,
        date: '2024-01-20T11:15:00Z',
        fees: 7.50
      },
      {
        id: '3',
        portfolio_id: 'portfolio-1',
        symbol: 'GOOGL',
        type: 'buy' as TransactionType,
        quantity: 25,
        price: 2800.00,
        total_amount: 70000.00,
        date: '2024-01-18T14:45:00Z',
        fees: 15.00
      }
    ]

    beforeEach(() => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTransactions
      } as Response)
    })

    it('should filter transactions by symbol', async () => {
      const { result } = renderHook(() => useTransactions('portfolio-1'))

      await waitFor(() => {
        expect(result.current.transactions).toHaveLength(3)
      })

      await act(async () => {
        result.current.setFilters({ symbol: 'AAPL' })
      })

      expect(result.current.filteredTransactions).toHaveLength(2)
      expect(result.current.filteredTransactions.every(t => t.symbol === 'AAPL')).toBe(true)
    })

    it('should filter transactions by type', async () => {
      const { result } = renderHook(() => useTransactions('portfolio-1'))

      await waitFor(() => {
        expect(result.current.transactions).toHaveLength(3)
      })

      await act(async () => {
        result.current.setFilters({ type: 'buy' as TransactionType })
      })

      expect(result.current.filteredTransactions).toHaveLength(2)
      expect(result.current.filteredTransactions.every(t => t.type === TransactionType.BUY)).toBe(true)
    })

    it('should filter transactions by date range', async () => {
      const { result } = renderHook(() => useTransactions('portfolio-1'))

      await waitFor(() => {
        expect(result.current.transactions).toHaveLength(3)
      })

      await act(async () => {
        result.current.setFilters({
          dateFrom: '2024-01-16',
          dateTo: '2024-01-19'
        })
      })

      expect(result.current.filteredTransactions).toHaveLength(1)
      expect(result.current.filteredTransactions[0].symbol).toBe('GOOGL')
    })

    it('should sort transactions by date (newest first)', async () => {
      const { result } = renderHook(() => useTransactions('portfolio-1'))

      await waitFor(() => {
        expect(result.current.transactions).toHaveLength(3)
      })

      await act(async () => {
        result.current.setSortBy('date')
        result.current.setSortOrder('desc')
      })

      const sorted = result.current.filteredTransactions
      expect(sorted[0].date).toBe('2024-01-20T11:15:00Z') // AAPL sell
      expect(sorted[1].date).toBe('2024-01-18T14:45:00Z') // GOOGL buy
      expect(sorted[2].date).toBe('2024-01-15T10:30:00Z') // AAPL buy
    })

    it('should sort transactions by amount', async () => {
      const { result } = renderHook(() => useTransactions('portfolio-1'))

      await waitFor(() => {
        expect(result.current.transactions).toHaveLength(3)
      })

      await act(async () => {
        result.current.setSortBy('total_amount')
        result.current.setSortOrder('desc')
      })

      const sorted = result.current.filteredTransactions
      expect(sorted[0].total_amount).toBe(70000.00) // GOOGL
      expect(sorted[1].total_amount).toBe(15025.00) // AAPL buy
      expect(sorted[2].total_amount).toBe(8037.50)  // AAPL sell
    })
  })

  describe('Transaction Statistics', () => {
    const mockTransactions: Transaction[] = [
      {
        id: '1',
        portfolio_id: 'portfolio-1',
        symbol: 'AAPL',
        type: 'buy' as TransactionType,
        quantity: 100,
        price: 150.00,
        total_amount: 15000.00,
        date: '2024-01-15T10:30:00Z',
        fees: 10.00
      },
      {
        id: '2',
        portfolio_id: 'portfolio-1',
        symbol: 'AAPL',
        type: 'sell' as TransactionType,
        quantity: 50,
        price: 160.00,
        total_amount: 8000.00,
        date: '2024-01-20T11:15:00Z',
        fees: 8.00
      }
    ]

    beforeEach(() => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockTransactions
      } as Response)
    })

    it('should calculate transaction statistics', async () => {
      const { result } = renderHook(() => useTransactions('portfolio-1'))

      await waitFor(() => {
        expect(result.current.transactions).toHaveLength(2)
      })

      const stats = result.current.transactionStats
      expect(stats.totalTransactions).toBe(2)
      expect(stats.totalBuyAmount).toBe(15000.00)
      expect(stats.totalSellAmount).toBe(8000.00)
      expect(stats.totalFees).toBe(18.00)
      expect(stats.netAmount).toBe(-7000.00) // 15000 - 8000
    })

    it('should group transactions by symbol', async () => {
      const { result } = renderHook(() => useTransactions('portfolio-1'))

      await waitFor(() => {
        expect(result.current.transactions).toHaveLength(2)
      })

      const grouped = result.current.transactionsBySymbol
      expect(grouped['AAPL']).toHaveLength(2)
      expect(grouped['AAPL'][0].type).toBe(TransactionType.BUY)
      expect(grouped['AAPL'][1].type).toBe(TransactionType.SELL)
    })

    it('should calculate average transaction size', async () => {
      const { result } = renderHook(() => useTransactions('portfolio-1'))

      await waitFor(() => {
        expect(result.current.transactions).toHaveLength(2)
      })

      const stats = result.current.transactionStats
      expect(stats.averageTransactionSize).toBe(11500.00) // (15000 + 8000) / 2
    })
  })

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network Error'))

      const { result } = renderHook(() => useTransactions('portfolio-1'))

      await waitFor(() => {
        expect(result.current.error).toBe('Failed to fetch transactions')
        expect(result.current.transactions).toEqual([])
        expect(result.current.loading).toBe(false)
      })
    })

    it('should handle HTTP error responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Portfolio not found' })
      } as Response)

      const { result } = renderHook(() => useTransactions('invalid-portfolio'))

      await waitFor(() => {
        expect(result.current.error).toBe('Portfolio not found')
        expect(result.current.loading).toBe(false)
      })
    })

    it('should handle transaction creation errors', async () => {
      const newTransaction = {
        symbol: 'INVALID',
        type: 'buy' as TransactionType,
        quantity: -10, // Invalid quantity
        price: 100,
        date: '2024-01-17T09:15:00Z'
      }

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => []
        } as Response) // Initial fetch
        .mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({ detail: 'Invalid transaction data' })
        } as Response) // Create transaction error

      const { result } = renderHook(() => useTransactions('portfolio-1'))

      await act(async () => {
        await result.current.createTransaction(newTransaction)
      })

      expect(result.current.error).toBe('Invalid transaction data')
    })
  })

  describe('Loading States', () => {
    it('should show loading state during initial fetch', async () => {
      let resolvePromise: (value: any) => void
      const fetchPromise = new Promise((resolve) => {
        resolvePromise = resolve
      })

      mockFetch.mockReturnValueOnce(fetchPromise as any)

      const { result } = renderHook(() => useTransactions('portfolio-1'))

      expect(result.current.loading).toBe(true)
      expect(result.current.transactions).toEqual([])

      // Resolve the promise
      await act(async () => {
        resolvePromise!({
          ok: true,
          json: async () => []
        })
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
    })

    it('should show loading state during transaction operations', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => []
      } as Response)

      const { result } = renderHook(() => useTransactions('portfolio-1'))

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // Mock slow create operation
      let resolveCreate: (value: any) => void
      const createPromise = new Promise((resolve) => {
        resolveCreate = resolve
      })

      mockFetch.mockReturnValueOnce(createPromise as any)

      act(() => {
        result.current.createTransaction({
          symbol: 'TEST',
          type: 'buy' as TransactionType,
          quantity: 10,
          price: 100,
          date: '2024-01-17T09:15:00Z'
        })
      })

      expect(result.current.loading).toBe(true)

      // Resolve create operation
      await act(async () => {
        resolveCreate!({
          ok: true,
          json: async () => ({ id: 'new-id' })
        })
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
    })
  })

  describe('Real-time Updates', () => {
    it('should refresh transactions after create/update/delete', async () => {
      const initialTransactions = [
        {
          id: '1',
          portfolio_id: 'portfolio-1',
          symbol: 'AAPL',
          type: 'buy' as TransactionType,
          quantity: 100,
          price: 150.00,
          total_amount: 15000.00,
          date: '2024-01-15T10:30:00Z',
          fees: 10.00
        }
      ]

      const updatedTransactions = [
        ...initialTransactions,
        {
          id: '2',
          portfolio_id: 'portfolio-1',
          symbol: 'GOOGL',
          type: 'buy' as TransactionType,
          quantity: 25,
          price: 2800.00,
          total_amount: 70000.00,
          date: '2024-01-18T14:45:00Z',
          fees: 15.00
        }
      ]

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => initialTransactions
        } as Response) // Initial fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ id: '2' })
        } as Response) // Create transaction
        .mockResolvedValueOnce({
          ok: true,
          json: async () => updatedTransactions
        } as Response) // Refresh after create

      const { result } = renderHook(() => useTransactions('portfolio-1'))

      await waitFor(() => {
        expect(result.current.transactions).toHaveLength(1)
      })

      await act(async () => {
        await result.current.createTransaction({
          symbol: 'GOOGL',
          type: 'buy' as TransactionType,
          quantity: 25,
          price: 2800.00,
          date: '2024-01-18T14:45:00Z',
          fees: 15.00
        })
      })

      await waitFor(() => {
        expect(result.current.transactions).toHaveLength(2)
      })
    })
  })
})
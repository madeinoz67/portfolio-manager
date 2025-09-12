'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'

interface Portfolio {
  id: string
  name: string
  description?: string
  total_value: string
  daily_change: string
  daily_change_percent: string
  created_at: string
  updated_at: string
}

interface Transaction {
  id: string
  stock: {
    id: string
    symbol: string
    company_name: string
    current_price?: string
  }
  transaction_type: 'BUY' | 'SELL'
  quantity: string
  price_per_share: string
  total_amount: string
  fees: string
  transaction_date: string
  notes?: string
  processed_date: string
}

interface TransactionListResponse {
  transactions: Transaction[]
  total: number
  limit: number
  offset: number
}

export default function PortfolioDetail() {
  const params = useParams()
  const router = useRouter()
  const portfolioId = params.id as string

  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showTransactionForm, setShowTransactionForm] = useState(false)
  const [newTransaction, setNewTransaction] = useState({
    stock_symbol: '',
    transaction_type: 'BUY' as 'BUY' | 'SELL',
    quantity: '',
    price_per_share: '',
    fees: '0.00',
    transaction_date: new Date().toISOString().split('T')[0],
    notes: ''
  })

  // Fetch portfolio details
  const fetchPortfolio = async () => {
    try {
      const response = await fetch(`http://localhost:8001/api/v1/portfolios/${portfolioId}`)
      if (response.ok) {
        const data = await response.json()
        setPortfolio(data)
      } else if (response.status === 404) {
        setError('Portfolio not found')
      } else {
        setError('Failed to fetch portfolio')
      }
    } catch (error) {
      setError('Connection error')
      console.error('Error fetching portfolio:', error)
    }
  }

  // Fetch transactions
  const fetchTransactions = async () => {
    try {
      const response = await fetch(`http://localhost:8001/api/v1/portfolios/${portfolioId}/transactions`)
      if (response.ok) {
        const data: TransactionListResponse = await response.json()
        setTransactions(data.transactions)
      } else {
        console.error('Failed to fetch transactions')
      }
    } catch (error) {
      console.error('Error fetching transactions:', error)
    }
  }

  // Create new transaction
  const createTransaction = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const response = await fetch(`http://localhost:8001/api/v1/portfolios/${portfolioId}/transactions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newTransaction),
      })
      
      if (response.ok) {
        setNewTransaction({
          stock_symbol: '',
          transaction_type: 'BUY',
          quantity: '',
          price_per_share: '',
          fees: '0.00',
          transaction_date: new Date().toISOString().split('T')[0],
          notes: ''
        })
        setShowTransactionForm(false)
        fetchTransactions() // Refresh the list
      } else {
        const errorData = await response.json()
        setError(errorData.detail || 'Failed to create transaction')
      }
    } catch (error) {
      setError('Connection error')
      console.error('Error creating transaction:', error)
    }
  }

  // Delete portfolio
  const deletePortfolio = async () => {
    if (!confirm('Are you sure you want to delete this portfolio? This action cannot be undone.')) {
      return
    }

    try {
      const response = await fetch(`http://localhost:8001/api/v1/portfolios/${portfolioId}`, {
        method: 'DELETE',
      })
      
      if (response.ok) {
        router.push('/') // Navigate back to dashboard
      } else {
        setError('Failed to delete portfolio')
      }
    } catch (error) {
      setError('Connection error')
      console.error('Error deleting portfolio:', error)
    }
  }

  useEffect(() => {
    if (portfolioId) {
      Promise.all([fetchPortfolio(), fetchTransactions()]).finally(() => {
        setLoading(false)
      })
    }
  }, [portfolioId])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 text-lg mb-4">{error}</p>
          <Link href="/" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
            Back to Dashboard
          </Link>
        </div>
      </div>
    )
  }

  if (!portfolio) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 text-lg mb-4">Portfolio not found</p>
          <Link href="/" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
            Back to Dashboard
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <Link href="/" className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
            ← Back to Dashboard
          </Link>
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{portfolio.name}</h1>
              {portfolio.description && (
                <p className="mt-2 text-gray-600">{portfolio.description}</p>
              )}
            </div>
            <button
              onClick={deletePortfolio}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
            >
              Delete Portfolio
            </button>
          </div>
        </div>

        {/* Portfolio Summary */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-xl font-semibold mb-4">Portfolio Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-gray-500 text-sm">Total Value</p>
              <p className="text-2xl font-bold">${portfolio.total_value}</p>
            </div>
            <div>
              <p className="text-gray-500 text-sm">Daily Change</p>
              <p className={`text-2xl font-bold ${
                parseFloat(portfolio.daily_change) >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                ${portfolio.daily_change} ({portfolio.daily_change_percent}%)
              </p>
            </div>
            <div>
              <p className="text-gray-500 text-sm">Created</p>
              <p className="text-lg">{new Date(portfolio.created_at).toLocaleDateString()}</p>
            </div>
          </div>
        </div>

        {/* Add Transaction Button */}
        <div className="mb-6">
          <button
            onClick={() => setShowTransactionForm(!showTransactionForm)}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
          >
            + Add Transaction
          </button>
        </div>

        {/* Transaction Form */}
        {showTransactionForm && (
          <div className="mb-6 bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4">Add New Transaction</h3>
            <form onSubmit={createTransaction} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Stock Symbol
                  </label>
                  <input
                    type="text"
                    required
                    value={newTransaction.stock_symbol}
                    onChange={(e) => setNewTransaction({...newTransaction, stock_symbol: e.target.value.toUpperCase()})}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., AAPL"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Transaction Type
                  </label>
                  <select
                    value={newTransaction.transaction_type}
                    onChange={(e) => setNewTransaction({...newTransaction, transaction_type: e.target.value as 'BUY' | 'SELL'})}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="BUY">Buy</option>
                    <option value="SELL">Sell</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Quantity
                  </label>
                  <input
                    type="number"
                    step="0.0001"
                    min="0"
                    required
                    value={newTransaction.quantity}
                    onChange={(e) => setNewTransaction({...newTransaction, quantity: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Price per Share
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    value={newTransaction.price_per_share}
                    onChange={(e) => setNewTransaction({...newTransaction, price_per_share: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="0.00"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Fees (optional)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={newTransaction.fees}
                    onChange={(e) => setNewTransaction({...newTransaction, fees: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="0.00"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Transaction Date
                  </label>
                  <input
                    type="date"
                    required
                    value={newTransaction.transaction_date}
                    onChange={(e) => setNewTransaction({...newTransaction, transaction_date: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes (optional)
                </label>
                <textarea
                  value={newTransaction.notes}
                  onChange={(e) => setNewTransaction({...newTransaction, notes: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Add any notes about this transaction"
                  rows={3}
                />
              </div>
              <div className="flex space-x-2">
                <button
                  type="submit"
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                >
                  Add Transaction
                </button>
                <button
                  type="button"
                  onClick={() => setShowTransactionForm(false)}
                  className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Transactions List */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b">
            <h2 className="text-xl font-semibold">Transactions</h2>
          </div>
          {transactions.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-gray-500 text-lg">No transactions found</p>
              <p className="text-gray-400 mt-2">Add your first transaction to get started</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stock</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fees</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {transactions.map((transaction) => (
                    <tr key={transaction.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(transaction.transaction_date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{transaction.stock.symbol}</div>
                          <div className="text-sm text-gray-500">{transaction.stock.company_name}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          transaction.transaction_type === 'BUY' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {transaction.transaction_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {parseFloat(transaction.quantity).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        ${parseFloat(transaction.price_per_share).toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        ${parseFloat(transaction.total_amount).toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        ${parseFloat(transaction.fees).toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
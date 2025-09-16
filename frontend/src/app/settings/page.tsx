'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Navigation from '@/components/layout/Navigation'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorMessage from '@/components/ui/ErrorMessage'
import Button from '@/components/ui/Button'
import DatePicker from '@/components/ui/DatePicker'
import { useToast } from '@/components/ui/Toast'
import { useAuth } from '@/contexts/AuthContext'
import { getCurrentDateInUserTimezone, formatDisplayDate, parseServerDate, convertLocalDateToUTC } from '@/utils/timezone'

interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  is_active: boolean
  created_at: string
}

interface ApiKey {
  id: string
  name: string
  permissions: Record<string, any> | null
  last_used_at: string | null
  expires_at: string | null
  is_active: boolean
  created_at: string
}

interface ApiKeyCreateResponse {
  id: string
  name: string
  key: string
  permissions: Record<string, any> | null
  expires_at: string | null
  created_at: string
}

export default function Settings() {
  const router = useRouter()
  const { addToast } = useToast()
  const { user: authUser, isAdmin } = useAuth()
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [updating, setUpdating] = useState(false)

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: ''
  })

  // API Keys state
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([])
  const [apiKeysLoading, setApiKeysLoading] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [newKeyExpiryDate, setNewKeyExpiryDate] = useState('')
  const [createdKey, setCreatedKey] = useState<ApiKeyCreateResponse | null>(null)

  useEffect(() => {
    fetchUserProfile()
    fetchApiKeys()
    // Set default expiry to 90 days from now
    const today = new Date()
    const defaultExpiry = new Date(today.getTime() + 90 * 24 * 60 * 60 * 1000)
    const year = defaultExpiry.getFullYear()
    const month = String(defaultExpiry.getMonth() + 1).padStart(2, '0')
    const day = String(defaultExpiry.getDate()).padStart(2, '0')
    setNewKeyExpiryDate(`${year}-${month}-${day}`)
  }, [])

  // Helper functions for date validation
  const getTodayDate = () => {
    return getCurrentDateInUserTimezone()
  }

  const getMaxExpiryDate = () => {
    const maxDate = new Date()
    maxDate.setDate(maxDate.getDate() + (365 * 2)) // 2 years max
    return maxDate.toISOString().split('T')[0]
  }

  const fetchUserProfile = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        router.push('/auth/login')
        return
      }

      const response = await fetch('http://localhost:8001/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem('auth_token')
          router.push('/auth/login')
          return
        }
        throw new Error('Failed to fetch user profile')
      }

      const userData = await response.json()
      setUser(userData)
      setFormData({
        first_name: userData.first_name || '',
        last_name: userData.last_name || ''
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setUpdating(true)
    setError(null)

    try {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        router.push('/auth/login')
        return
      }

      const response = await fetch('http://localhost:8001/api/v1/auth/me', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      })

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem('auth_token')
          router.push('/auth/login')
          return
        }
        throw new Error('Failed to update profile')
      }

      const updatedUser = await response.json()
      setUser(updatedUser)
      addToast('Profile updated successfully!', 'success')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setUpdating(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  // API Key functions
  const fetchApiKeys = async () => {
    try {
      setApiKeysLoading(true)
      const token = localStorage.getItem('auth_token')
      if (!token) return

      const response = await fetch('http://localhost:8001/api/v1/api-keys', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const keys = await response.json()
        setApiKeys(keys)
      }
    } catch (err) {
      console.error('Error fetching API keys:', err)
    } finally {
      setApiKeysLoading(false)
    }
  }

  const createApiKey = async () => {
    if (!newKeyName.trim() || !newKeyExpiryDate) {
      addToast('Please provide both name and expiry date', 'error')
      return
    }

    try {
      const token = localStorage.getItem('auth_token')
      if (!token) return

      // Convert date to ISO format with timezone
      const expiryDateTime = new Date(newKeyExpiryDate)
      expiryDateTime.setUTCHours(23, 59, 59, 999) // Set to end of day
      
      const requestBody = {
        name: newKeyName.trim(),
        expires_at: expiryDateTime.toISOString()
      }

      const response = await fetch('http://localhost:8001/api/v1/api-keys', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      })

      if (response.ok) {
        const newKey = await response.json()
        setCreatedKey(newKey)
        setNewKeyName('')
        setNewKeyExpiryDate('')
        setShowCreateModal(false)
        fetchApiKeys() // Refresh the list
        addToast('API key created successfully!', 'success')
      } else {
        const errorData = await response.json().catch(() => ({}))
        const errorMessage = errorData.detail || 'Failed to create API key'
        addToast(errorMessage, 'error')
      }
    } catch (err) {
      console.error('Error creating API key:', err)
      addToast('Error creating API key', 'error')
    }
  }

  const deleteApiKey = async (keyId: string) => {
    if (!confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
      return
    }

    try {
      const token = localStorage.getItem('auth_token')
      if (!token) return

      const response = await fetch(`http://localhost:8001/api/v1/api-keys/${keyId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        fetchApiKeys() // Refresh the list
        addToast('API key deleted successfully', 'success')
      } else {
        addToast('Failed to delete API key', 'error')
      }
    } catch (err) {
      console.error('Error deleting API key:', err)
      addToast('Error deleting API key', 'error')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navigation />
        <div className="container mx-auto px-4 py-8">
          <div className="flex justify-center">
            <LoadingSpinner />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navigation />
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Settings</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Manage your account settings and preferences
          </p>
        </div>

        {error && (
          <div className="mb-6">
            <ErrorMessage message={error} />
          </div>
        )}

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md">
          {/* Profile Section */}
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Profile Information
            </h2>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    First Name
                  </label>
                  <input
                    type="text"
                    id="first_name"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Last Name
                  </label>
                  <input
                    type="text"
                    id="last_name"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                    required
                  />
                </div>
              </div>
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  id="email"
                  value={user?.email || ''}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-gray-100 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed"
                />
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  Email address cannot be changed
                </p>
              </div>
              <div className="flex justify-end">
                <Button
                  type="submit"
                  disabled={updating}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md transition-colors duration-200 disabled:opacity-50"
                >
                  {updating ? 'Updating...' : 'Update Profile'}
                </Button>
              </div>
            </form>
          </div>

          {/* Account Information */}
          <div className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Account Information
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Account Created
                </label>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  {user ? new Date(user.created_at).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  }) : ''}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Account Status
                </label>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mt-1 ${
                  user?.is_active 
                    ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100' 
                    : 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100'
                }`}>
                  {user?.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Role
                </label>
                <div className="mt-1">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    authUser?.role === 'admin'
                      ? 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100'
                      : 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100'
                  }`}>
                    {authUser?.role === 'admin' ? 'Administrator' : 'User'}
                  </span>
                  {authUser?.role === 'admin' && (
                    <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                      You have administrative privileges. <a href="/admin" className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200">Access Admin Panel</a>
                    </p>
                  )}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  User ID
                </label>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400 font-mono">
                  {user?.id}
                </p>
              </div>
            </div>
          </div>

          {/* API Keys Section */}
          <div className="p-6 border-t border-gray-200 dark:border-gray-700">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                API Keys
              </h2>
              <Button
                onClick={() => setShowCreateModal(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md"
              >
                Create New Key
              </Button>
            </div>
            
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
              API keys allow you to authenticate with the Portfolio API. Keep your keys secure and don't share them publicly.
            </p>

            {apiKeysLoading ? (
              <div className="flex justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              </div>
            ) : apiKeys.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No API keys created yet. Create your first key to get started.
              </div>
            ) : (
              <div className="space-y-4">
                {apiKeys.map((apiKey) => (
                  <div key={apiKey.id} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900 dark:text-white">{apiKey.name}</h3>
                        <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                          <p>Created: {new Date(apiKey.created_at).toLocaleDateString()}</p>
                          {apiKey.expires_at && (
                            <p className={`${new Date(apiKey.expires_at) < new Date() ? 'text-red-600 font-semibold' : ''}`}>
                              Expires: {new Date(apiKey.expires_at).toLocaleDateString()}
                              {new Date(apiKey.expires_at) < new Date() && ' (EXPIRED)'}
                            </p>
                          )}
                          {apiKey.last_used_at && (
                            <p>Last used: {new Date(apiKey.last_used_at).toLocaleDateString()}</p>
                          )}
                        </div>
                        <div className="mt-2">
                          <code className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                            pk_••••••••••••••••••••••••••••••••
                          </code>
                        </div>
                      </div>
                      <Button
                        onClick={() => deleteApiKey(apiKey.id)}
                        className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 text-sm rounded"
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Create API Key Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Create New API Key
              </h3>
              <div className="mb-4">
                <label htmlFor="keyName" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Key Name
                </label>
                <input
                  type="text"
                  id="keyName"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="e.g., My App Integration"
                />
              </div>
              
              <div className="mb-4">
                <label htmlFor="expiryDate" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Expiry Date <span className="text-red-500">*</span>
                </label>
                <DatePicker
                  id="expiryDate"
                  value={newKeyExpiryDate}
                  onChange={setNewKeyExpiryDate}
                  min={getTodayDate()}
                  max={getMaxExpiryDate()}
                  required
                />
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  API key will expire at 11:59 PM on this date (max 2 years)
                </p>
              </div>
              <div className="flex justify-end space-x-3">
                <Button
                  onClick={() => {
                    setShowCreateModal(false)
                    setNewKeyName('')
                    // Reset expiry to default
                    const defaultExpiry = new Date()
                    defaultExpiry.setDate(defaultExpiry.getDate() + 90)
                    setNewKeyExpiryDate(defaultExpiry.toISOString().split('T')[0])
                  }}
                  className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded-md"
                >
                  Cancel
                </Button>
                <Button
                  onClick={createApiKey}
                  disabled={!newKeyName.trim() || !newKeyExpiryDate}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md disabled:opacity-50"
                >
                  Create Key
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Created Key Modal */}
        {createdKey && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-lg w-full">
              <div className="flex items-center mb-4">
                <div className="w-8 h-8 bg-green-100 dark:bg-green-800 rounded-full flex items-center justify-center mr-3">
                  <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  API Key Created Successfully
                </h3>
              </div>
              
              <div className="mb-4 p-3 bg-yellow-50 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-700 rounded-md">
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  <strong>Important:</strong> Copy your API key now. You won't be able to see it again!
                </p>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Your API Key
                </label>
                <div className="flex">
                  <input
                    type="text"
                    value={createdKey.key}
                    readOnly
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-l-md bg-gray-50 dark:bg-gray-700 text-sm font-mono dark:text-white"
                  />
                  <Button
                    onClick={() => {
                      navigator.clipboard.writeText(createdKey.key)
                      addToast('API key copied to clipboard!', 'success')
                    }}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-r-md border-l-0"
                  >
                    Copy
                  </Button>
                </div>
              </div>

              <div className="flex justify-end">
                <Button
                  onClick={() => setCreatedKey(null)}
                  className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md"
                >
                  Done
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

    </div>
  )
}
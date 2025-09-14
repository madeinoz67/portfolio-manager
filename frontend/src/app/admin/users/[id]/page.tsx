'use client'

import { use, useState, useEffect } from 'react'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
// import { useUserDetails } from '@/hooks/useAdmin'
// import LoadingSpinner from '@/components/ui/LoadingSpinner'
// import ErrorMessage from '@/components/ui/ErrorMessage'

interface UserDetailsPageProps {
  params: Promise<{ id: string }>
}

interface UserInfoCardProps {
  title: string
  children: React.ReactNode
  className?: string
}

function UserInfoCard({ title, children, className = '' }: UserInfoCardProps) {
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        {title}
      </h3>
      {children}
    </div>
  )
}

interface InfoRowProps {
  label: string
  value: React.ReactNode
  className?: string
}

function InfoRow({ label, value, className = '' }: InfoRowProps) {
  return (
    <div className={`flex justify-between py-3 border-b border-gray-200 dark:border-gray-600 last:border-b-0 ${className}`}>
      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
        {label}
      </dt>
      <dd className="text-sm text-gray-900 dark:text-white text-right">
        {value}
      </dd>
    </div>
  )
}

export default function UserDetailsPage({ params }: UserDetailsPageProps) {
  const { id } = use(params)
  const { user: currentUser, token } = useAuth()
  const [userDetails, setUserDetails] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchUserDetails = async () => {
      if (!currentUser || !token || !id) return

      try {
        const response = await fetch(`http://localhost:8001/api/v1/admin/users/${id}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        })

        if (response.ok) {
          const data = await response.json()
          setUserDetails(data)
        } else {
          setError(`API Error: ${response.status}`)
        }
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchUserDetails()
  }, [currentUser, token, id])

  const refetch = () => {
    window.location.reload()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            Loading user details...
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="py-12 text-center">
        <div className="text-red-600">Error: {error}</div>
        <button
          onClick={refetch}
          className="mt-4 bg-red-600 text-white px-4 py-2 rounded"
        >
          Retry
        </button>
      </div>
    )
  }

  if (!userDetails) {
    return null
  }

  const selectedUser = userDetails

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link
            href="/admin/users"
            className="text-red-600 hover:text-red-700 dark:hover:text-red-400 font-medium"
          >
            ← Back to Users
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              {selectedUser.firstName && selectedUser.lastName
                ? `${selectedUser.firstName} ${selectedUser.lastName}`
                : selectedUser.email
              }
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              User Details and Portfolio Information
            </p>
          </div>
        </div>
        <button
          onClick={refetch}
          className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* User Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0 h-12 w-12">
              <div className="h-12 w-12 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
                <span className="text-lg font-semibold text-red-600 dark:text-red-400">
                  {(selectedUser.firstName?.[0] || selectedUser.email[0]).toUpperCase()}
                </span>
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Account Status
              </h3>
              <div className="flex items-center space-x-2 mt-1">
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  selectedUser.isActive
                    ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300'
                    : 'bg-gray-100 dark:bg-gray-900/20 text-gray-800 dark:text-gray-300'
                }`}>
                  {selectedUser.isActive ? 'Active' : 'Inactive'}
                </span>
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  selectedUser.role === 'admin'
                    ? 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-300'
                    : 'bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300'
                }`}>
                  {selectedUser.role}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Portfolios
              </h3>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {selectedUser.portfolioCount}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Total Assets
              </h3>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                ${selectedUser.totalAssets.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* User Information */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <UserInfoCard title="Account Information">
          <dl className="divide-y divide-gray-200 dark:divide-gray-600">
            <InfoRow label="User ID" value={selectedUser.id} />
            <InfoRow label="Email" value={selectedUser.email} />
            <InfoRow label="First Name" value={selectedUser.firstName || 'Not provided'} />
            <InfoRow label="Last Name" value={selectedUser.lastName || 'Not provided'} />
            <InfoRow label="Role" value={
              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                selectedUser.role === 'admin'
                  ? 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-300'
                  : 'bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300'
              }`}>
                {selectedUser.role}
              </span>
            } />
            <InfoRow label="Status" value={
              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                selectedUser.isActive
                  ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300'
                  : 'bg-gray-100 dark:bg-gray-900/20 text-gray-800 dark:text-gray-300'
              }`}>
                {selectedUser.isActive ? 'Active' : 'Inactive'}
              </span>
            } />
            <InfoRow label="Created" value={new Date(selectedUser.createdAt).toLocaleString()} />
            <InfoRow label="Last Login" value={selectedUser.lastLoginAt ? new Date(selectedUser.lastLoginAt).toLocaleString() : 'Never'} />
          </dl>
        </UserInfoCard>

        <UserInfoCard title="Portfolio Summary">
          <dl className="divide-y divide-gray-200 dark:divide-gray-600">
            <InfoRow label="Total Portfolios" value={selectedUser.portfolioCount} />
            <InfoRow label="Total Asset Value" value={`$${selectedUser.totalAssets.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`} />
            <InfoRow label="Average Portfolio Value" value={
              selectedUser.portfolioCount > 0
                ? `$${(selectedUser.totalAssets / selectedUser.portfolioCount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                : '$0.00'
            } />
          </dl>
        </UserInfoCard>
      </div>

      {/* Portfolios Details */}
      {selectedUser.portfolios.length > 0 && (
        <UserInfoCard title={`User Portfolios (${selectedUser.portfolios.length})`}>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Portfolio Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Value
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Last Updated
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    % of Total
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {selectedUser.portfolios.map((portfolio) => (
                  <tr key={portfolio.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {portfolio.name}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        ID: {portfolio.id}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white font-medium">
                      ${portfolio.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {new Date(portfolio.lastUpdated).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {selectedUser.totalAssets > 0 ? ((portfolio.value / selectedUser.totalAssets) * 100).toFixed(1) + '%' : '0%'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </UserInfoCard>
      )}

      {/* Empty Portfolio State */}
      {selectedUser.portfolios.length === 0 && (
        <UserInfoCard title="User Portfolios">
          <div className="text-center py-8">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">No portfolios</h3>
            <p className="mt-2 text-gray-500 dark:text-gray-400">
              This user has not created any portfolios yet.
            </p>
          </div>
        </UserInfoCard>
      )}
    </div>
  )
}
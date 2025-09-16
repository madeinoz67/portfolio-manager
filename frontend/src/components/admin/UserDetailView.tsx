import React from 'react'
import { AdminUserDetails } from '@/types/admin'

interface UserDetailViewProps {
  user: AdminUserDetails
  loading?: boolean
  className?: string
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

export function UserDetailView({
  user,
  loading = false,
  className = ''
}: UserDetailViewProps) {
  if (loading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="animate-pulse">
          {/* Header skeleton */}
          <div className="flex items-center space-x-4 mb-6">
            <div className="h-12 w-12 bg-gray-300 dark:bg-gray-600 rounded-full"></div>
            <div className="space-y-2">
              <div className="h-6 bg-gray-300 dark:bg-gray-600 rounded w-48"></div>
              <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-32"></div>
            </div>
          </div>

          {/* Cards skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="bg-white dark:bg-gray-800 rounded-lg border p-6">
                <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-24 mb-4"></div>
                <div className="h-8 bg-gray-300 dark:bg-gray-600 rounded w-16"></div>
              </div>
            ))}
          </div>

          {/* Info cards skeleton */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[...Array(2)].map((_, i) => (
              <div key={i} className="bg-white dark:bg-gray-800 rounded-lg border p-6">
                <div className="h-5 bg-gray-300 dark:bg-gray-600 rounded w-32 mb-4"></div>
                <div className="space-y-3">
                  {[...Array(4)].map((_, j) => (
                    <div key={j} className="flex justify-between">
                      <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-20"></div>
                      <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-24"></div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* User Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0 h-12 w-12">
              <div className="h-12 w-12 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
                <span className="text-lg font-semibold text-red-600 dark:text-red-400">
                  {(user.firstName?.[0] || user.email[0]).toUpperCase()}
                </span>
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Account Status
              </h3>
              <div className="flex items-center space-x-2 mt-1">
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  user.isActive
                    ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300'
                    : 'bg-gray-100 dark:bg-gray-900/20 text-gray-800 dark:text-gray-300'
                }`}>
                  {user.isActive ? 'Active' : 'Inactive'}
                </span>
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  user.role === 'admin'
                    ? 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-300'
                    : 'bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300'
                }`}>
                  {user.role}
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
                {user.portfolioCount}
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
                ${user.totalAssets.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* User Information */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <UserInfoCard title="Account Information">
          <dl className="divide-y divide-gray-200 dark:divide-gray-600">
            <InfoRow label="User ID" value={user.id} />
            <InfoRow label="Email" value={user.email} />
            <InfoRow label="First Name" value={user.firstName || 'Not provided'} />
            <InfoRow label="Last Name" value={user.lastName || 'Not provided'} />
            <InfoRow label="Role" value={
              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                user.role === 'admin'
                  ? 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-300'
                  : 'bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300'
              }`}>
                {user.role}
              </span>
            } />
            <InfoRow label="Status" value={
              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                user.isActive
                  ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300'
                  : 'bg-gray-100 dark:bg-gray-900/20 text-gray-800 dark:text-gray-300'
              }`}>
                {user.isActive ? 'Active' : 'Inactive'}
              </span>
            } />
            <InfoRow label="Created" value={new Date(user.createdAt).toLocaleString()} />
            <InfoRow label="Last Login" value={user.lastLoginAt ? new Date(user.lastLoginAt).toLocaleString() : 'Never'} />
          </dl>
        </UserInfoCard>

        <UserInfoCard title="Portfolio Summary">
          <dl className="divide-y divide-gray-200 dark:divide-gray-600">
            <InfoRow label="Total Portfolios" value={user.portfolioCount} />
            <InfoRow label="Total Asset Value" value={`$${user.totalAssets.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`} />
            <InfoRow label="Average Portfolio Value" value={
              user.portfolioCount > 0
                ? `$${(user.totalAssets / user.portfolioCount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                : '$0.00'
            } />
          </dl>
        </UserInfoCard>
      </div>

      {/* Portfolios Details */}
      {user.portfolios.length > 0 && (
        <UserInfoCard title={`User Portfolios (${user.portfolios.length})`}>
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
                {user.portfolios.map((portfolio) => (
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
                      {user.totalAssets > 0 ? ((portfolio.value / user.totalAssets) * 100).toFixed(1) + '%' : '0%'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </UserInfoCard>
      )}

      {/* Empty Portfolio State */}
      {user.portfolios.length === 0 && (
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

export default UserDetailView
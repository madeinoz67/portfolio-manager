import React from 'react'
import Link from 'next/link'
import { AdminUserListItem } from '@/types/admin'

interface UserManagementTableProps {
  users: AdminUserListItem[]
  loading?: boolean
  className?: string
}

export function UserManagementTable({
  users,
  loading = false,
  className = ''
}: UserManagementTableProps) {
  if (loading) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 ${className}`}>
        <div className="animate-pulse p-6">
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center space-x-4">
                <div className="h-10 w-10 bg-gray-300 dark:bg-gray-600 rounded-full"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-1/4"></div>
                  <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-1/3"></div>
                </div>
                <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-16"></div>
                <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-20"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (users.length === 0) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 p-12 text-center ${className}`}>
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
        </svg>
        <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">No users found</h3>
        <p className="mt-2 text-gray-500 dark:text-gray-400">
          No users match the current filters.
        </p>
      </div>
    )
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 overflow-hidden ${className}`}>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                User
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Role
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Portfolios
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Created
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {users.map((user) => (
              <UserRow key={user.id} user={user} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

interface UserRowProps {
  user: AdminUserListItem
}

function UserRow({ user }: UserRowProps) {
  return (
    <tr className="hover:bg-gray-50 dark:hover:bg-gray-700">
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center">
          <div className="flex-shrink-0 h-10 w-10">
            <div className="h-10 w-10 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {(user.firstName?.[0] || user.email[0]).toUpperCase()}
              </span>
            </div>
          </div>
          <div className="ml-4">
            <div className="text-sm font-medium text-gray-900 dark:text-white">
              {user.firstName && user.lastName
                ? `${user.firstName} ${user.lastName}`
                : user.email
              }
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {user.email}
            </div>
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
          user.role === 'admin'
            ? 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-300'
            : 'bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300'
        }`}>
          {user.role}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
          user.isActive
            ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300'
            : 'bg-gray-100 dark:bg-gray-900/20 text-gray-800 dark:text-gray-300'
        }`}>
          {user.isActive ? 'Active' : 'Inactive'}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
        {user.portfolioCount}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
        {new Date(user.createdAt).toLocaleDateString()}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
        <Link
          href={`/admin/users/${user.id}`}
          className="text-red-600 hover:text-red-900 dark:hover:text-red-400"
        >
          View Details
        </Link>
      </td>
    </tr>
  )
}

export default UserManagementTable
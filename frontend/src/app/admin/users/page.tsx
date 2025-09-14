'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
// import { useAdminUsers } from '@/hooks/useAdmin'
// import { AdminUsersListParams } from '@/types/admin'
// import LoadingSpinner from '@/components/ui/LoadingSpinner'
// import ErrorMessage from '@/components/ui/ErrorMessage'

interface AdminUsersListParams {
  page?: number
  size?: number
  role?: 'admin' | 'user'
  active?: boolean
}

interface FilterBarProps {
  params: AdminUsersListParams
  onParamsChange: (params: AdminUsersListParams) => void
  totalUsers: number
}

function FilterBar({ params, onParamsChange, totalUsers }: FilterBarProps) {
  const handleRoleFilter = (role: 'admin' | 'user' | 'all') => {
    onParamsChange({
      ...params,
      role: role === 'all' ? undefined : role,
      page: 1, // Reset to first page when filtering
    })
  }

  const handleActiveFilter = (active: boolean | 'all') => {
    onParamsChange({
      ...params,
      active: active === 'all' ? undefined : active,
      page: 1, // Reset to first page when filtering
    })
  }

  const handlePageSizeChange = (size: number) => {
    onParamsChange({
      ...params,
      size,
      page: 1, // Reset to first page when changing page size
    })
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 p-6 space-y-4">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Role Filter */}
          <div className="flex flex-col">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Filter by Role
            </label>
            <div className="flex rounded-lg border dark:border-gray-600 overflow-hidden">
              {[
                { value: 'all', label: 'All' },
                { value: 'admin', label: 'Admin' },
                { value: 'user', label: 'User' },
              ].map((option) => (
                <button
                  key={option.value}
                  onClick={() => handleRoleFilter(option.value as 'admin' | 'user' | 'all')}
                  className={`px-4 py-2 text-sm font-medium transition-colors ${
                    (params.role === option.value) || (option.value === 'all' && !params.role)
                      ? 'bg-red-600 text-white'
                      : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Active Status Filter */}
          <div className="flex flex-col">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Filter by Status
            </label>
            <div className="flex rounded-lg border dark:border-gray-600 overflow-hidden">
              {[
                { value: 'all', label: 'All' },
                { value: true, label: 'Active' },
                { value: false, label: 'Inactive' },
              ].map((option) => (
                <button
                  key={String(option.value)}
                  onClick={() => handleActiveFilter(option.value as boolean | 'all')}
                  className={`px-4 py-2 text-sm font-medium transition-colors ${
                    (params.active === option.value) || (option.value === 'all' && params.active === undefined)
                      ? 'bg-red-600 text-white'
                      : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Results Info and Page Size */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Showing {totalUsers} user{totalUsers !== 1 ? 's' : ''}
          </div>

          <div className="flex flex-col">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Page Size
            </label>
            <select
              value={params.size || 20}
              onChange={(e) => handlePageSizeChange(Number(e.target.value))}
              className="border dark:border-gray-600 rounded-md px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  )
}

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null

  const pages = []
  const maxVisiblePages = 5

  let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2))
  const endPage = Math.min(totalPages, startPage + maxVisiblePages - 1)

  if (endPage - startPage < maxVisiblePages - 1) {
    startPage = Math.max(1, endPage - maxVisiblePages + 1)
  }

  for (let i = startPage; i <= endPage; i++) {
    pages.push(i)
  }

  return (
    <div className="flex items-center justify-center space-x-2">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-2 rounded-md border dark:border-gray-600 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600"
      >
        Previous
      </button>

      {startPage > 1 && (
        <>
          <button
            onClick={() => onPageChange(1)}
            className="px-3 py-2 rounded-md border dark:border-gray-600 text-sm font-medium transition-colors bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600"
          >
            1
          </button>
          {startPage > 2 && <span className="text-gray-500">...</span>}
        </>
      )}

      {pages.map((page) => (
        <button
          key={page}
          onClick={() => onPageChange(page)}
          className={`px-3 py-2 rounded-md border dark:border-gray-600 text-sm font-medium transition-colors ${
            page === currentPage
              ? 'bg-red-600 text-white border-red-600'
              : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
          }`}
        >
          {page}
        </button>
      ))}

      {endPage < totalPages && (
        <>
          {endPage < totalPages - 1 && <span className="text-gray-500">...</span>}
          <button
            onClick={() => onPageChange(totalPages)}
            className="px-3 py-2 rounded-md border dark:border-gray-600 text-sm font-medium transition-colors bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600"
          >
            {totalPages}
          </button>
        </>
      )}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-3 py-2 rounded-md border dark:border-gray-600 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600"
      >
        Next
      </button>
    </div>
  )
}

export default function AdminUsersPage() {
  const { user, token } = useAuth()
  const [params, setParams] = useState<AdminUsersListParams>({
    page: 1,
    size: 20,
  })
  const [users, setUsers] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchUsers = async (searchParams = params) => {
    if (!user || !token) return

    try {
      setLoading(true)
      setError(null)

      const urlParams = new URLSearchParams()
      if (searchParams.page !== undefined) urlParams.set('page', searchParams.page.toString())
      if (searchParams.size !== undefined) urlParams.set('size', searchParams.size.toString())
      if (searchParams.role) urlParams.set('role', searchParams.role)
      if (searchParams.active !== undefined) urlParams.set('active', searchParams.active.toString())

      const queryString = urlParams.toString()
      const endpoint = `http://localhost:8001/api/v1/admin/users${queryString ? `?${queryString}` : ''}`

      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const data = await response.json()
        setUsers(data)
      } else {
        setError(`API Error: ${response.status}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [user, token, params])

  const updateParams = (newParams) => {
    setParams(newParams)
  }

  const refetch = () => {
    fetchUsers(params)
  }

  const handleParamsChange = (newParams: AdminUsersListParams) => {
    setParams(newParams)
  }

  const handlePageChange = (page: number) => {
    handleParamsChange({ ...params, page })
  }

  if (loading && !users) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            Loading users...
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">User Management</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage user accounts and permissions
          </p>
        </div>
        <button
          onClick={refetch}
          className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Filters */}
      {users && (
        <FilterBar
          params={params}
          onParamsChange={handleParamsChange}
          totalUsers={users.total}
        />
      )}

      {/* Users Table */}
      {users && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 overflow-hidden">
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
                {users.users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
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
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {users.pages > 1 && (
            <div className="px-6 py-4 border-t dark:border-gray-700">
              <Pagination
                currentPage={users.page}
                totalPages={users.pages}
                onPageChange={handlePageChange}
              />
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {users && users.users.length === 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 p-12 text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">No users found</h3>
          <p className="mt-2 text-gray-500 dark:text-gray-400">
            {params.role || params.active !== undefined
              ? 'Try adjusting your filters to see more results.'
              : 'No users have been registered yet.'
            }
          </p>
        </div>
      )}
    </div>
  )
}
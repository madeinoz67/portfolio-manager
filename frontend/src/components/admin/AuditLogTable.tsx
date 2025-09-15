'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { AuditLogResponse, AuditLogEntry, AuditLogFilters, EVENT_TYPES, ENTITY_TYPES } from '@/types/audit'
import { fetchAuditLogs } from '@/services/audit'
import { formatDisplayDateTime } from '@/utils/timezone'

interface AuditLogTableProps {
  className?: string
}

export function AuditLogTable({ className = '' }: AuditLogTableProps) {
  const [data, setData] = useState<AuditLogResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<AuditLogFilters>({})
  const [currentPage, setCurrentPage] = useState(1)
  const [searchTerm, setSearchTerm] = useState('')
  const [searchTimeoutId, setSearchTimeoutId] = useState<NodeJS.Timeout | null>(null)

  const loadAuditLogs = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Get token from localStorage (this should match your auth implementation)
      const token = localStorage.getItem('token')

      const response = await fetchAuditLogs(filters, currentPage, 20, { token: token || undefined })
      setData(response)
    } catch (err) {
      console.error('Failed to load audit logs:', err)
      setError(err instanceof Error ? err.message : 'Error loading audit logs')
    } finally {
      setLoading(false)
    }
  }, [filters, currentPage])

  useEffect(() => {
    loadAuditLogs()
  }, [loadAuditLogs])

  const handleSearchChange = (value: string) => {
    setSearchTerm(value)

    // Clear existing timeout
    if (searchTimeoutId) {
      clearTimeout(searchTimeoutId)
    }

    // Set new timeout for debounced search
    const timeoutId = setTimeout(() => {
      setFilters(prev => ({
        ...prev,
        search: value || undefined
      }))
      setCurrentPage(1)
    }, 300)

    setSearchTimeoutId(timeoutId)
  }

  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      if (searchTimeoutId) {
        clearTimeout(searchTimeoutId)
      }
      setFilters(prev => ({
        ...prev,
        search: searchTerm || undefined
      }))
      setCurrentPage(1)
    }
  }

  const handleFilterChange = (key: keyof AuditLogFilters, value: string) => {
    setFilters(prev => ({
      ...prev,
      [key]: value || undefined
    }))
    setCurrentPage(1)
  }

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage)
  }

  const handleRetry = () => {
    loadAuditLogs()
  }

  if (loading && !data) {
    return (
      <div className={`p-4 ${className}`}>
        <div className="text-center py-8">Loading audit logs...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`p-4 ${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-red-800 font-semibold">Error loading audit logs</h3>
          <p className="text-red-600 mt-2">{error}</p>
          <button
            onClick={handleRetry}
            className="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className={`p-4 ${className}`}>
        <div className="text-center py-8">No audit log data available.</div>
      </div>
    )
  }

  return (
    <div className={`p-4 ${className}`}>
      {/* Header with stats */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Audit Logs</h2>
        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
          <span>{data.meta.total_events_in_system.toLocaleString()} total events in system</span>
          <span>Query processed in {data.meta.processing_time_ms}ms</span>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
              Search audit logs
            </label>
            <input
              id="search"
              type="text"
              placeholder="Search audit logs..."
              value={searchTerm}
              onChange={(e) => handleSearchChange(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="event-type" className="block text-sm font-medium text-gray-700 mb-1">
              Event Type
            </label>
            <select
              id="event-type"
              value={filters.event_type || ''}
              onChange={(e) => handleFilterChange('event_type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Event Types</option>
              {EVENT_TYPES.map(type => (
                <option key={type} value={type}>
                  {type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="entity-type" className="block text-sm font-medium text-gray-700 mb-1">
              Entity Type
            </label>
            <select
              id="entity-type"
              value={filters.entity_type || ''}
              onChange={(e) => handleFilterChange('entity_type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Entity Types</option>
              {ENTITY_TYPES.map(type => (
                <option key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="user-filter" className="block text-sm font-medium text-gray-700 mb-1">
              User
            </label>
            <input
              id="user-filter"
              type="text"
              placeholder="User ID or email..."
              value={filters.user_id || ''}
              onChange={(e) => handleFilterChange('user_id', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <div>
            <label htmlFor="from-date" className="block text-sm font-medium text-gray-700 mb-1">
              From Date
            </label>
            <input
              id="from-date"
              type="datetime-local"
              value={filters.date_from || ''}
              onChange={(e) => handleFilterChange('date_from', e.target.value ? `${e.target.value}:00Z` : '')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="to-date" className="block text-sm font-medium text-gray-700 mb-1">
              To Date
            </label>
            <input
              id="to-date"
              type="datetime-local"
              value={filters.date_to || ''}
              onChange={(e) => handleFilterChange('date_to', e.target.value ? `${e.target.value}:00Z` : '')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Pagination info */}
      <div className="flex justify-between items-center mb-4">
        <div className="text-sm text-gray-600">
          Page {data.pagination.current_page} of {data.pagination.total_pages} • {data.pagination.total_items} total items
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Previous
          </button>
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === data.pagination.total_pages}
            className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Event
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Entity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Details
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.data.map((entry: AuditLogEntry) => (
                <tr key={entry.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {entry.event_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </div>
                      <div className="text-sm text-gray-500">{entry.event_description}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {entry.user_email}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{entry.entity_type}</div>
                    <div className="text-sm text-gray-500">{entry.entity_id}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDisplayDateTime(entry.timestamp)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {entry.ip_address && (
                      <div>IP: {entry.ip_address}</div>
                    )}
                    {entry.event_metadata && Object.keys(entry.event_metadata).length > 0 && (
                      <div className="text-xs text-blue-600 cursor-pointer" title={JSON.stringify(entry.event_metadata, null, 2)}>
                        View metadata
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {data.data.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No audit log entries found for the current filters.
        </div>
      )}
    </div>
  )
}
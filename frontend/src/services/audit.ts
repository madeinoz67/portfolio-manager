/**
 * Service for making audit log API calls.
 */

import { AuditLogResponse, AuditLogFilters, AuditLogStatsResponse, AuditLogEntry } from '@/types/audit'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export class AuditLogApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message)
    this.name = 'AuditLogApiError'
  }
}

export interface AuditLogApiOptions {
  token?: string
}

export async function fetchAuditLogs(
  filters: AuditLogFilters = {},
  page: number = 1,
  limit: number = 50,
  options: AuditLogApiOptions = {}
): Promise<AuditLogResponse> {
  const params = new URLSearchParams()

  params.append('page', page.toString())
  params.append('limit', limit.toString())

  if (filters.user_id) params.append('user_id', filters.user_id)
  if (filters.event_type) params.append('event_type', filters.event_type)
  if (filters.entity_type) params.append('entity_type', filters.entity_type)
  if (filters.entity_id) params.append('entity_id', filters.entity_id)
  if (filters.date_from) params.append('date_from', filters.date_from)
  if (filters.date_to) params.append('date_to', filters.date_to)
  if (filters.search) params.append('search', filters.search)
  if (filters.sort_by) params.append('sort_by', filters.sort_by)
  if (filters.sort_order) params.append('sort_order', filters.sort_order)

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }

  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/admin/audit-logs?${params}`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    if (response.status === 401) {
      throw new AuditLogApiError('Unauthorized access to audit logs', 401)
    }
    if (response.status === 403) {
      throw new AuditLogApiError('Admin access required', 403)
    }
    throw new AuditLogApiError(`Failed to fetch audit logs: ${response.status}`, response.status)
  }

  return response.json()
}

export async function fetchAuditLogEntry(
  auditId: number,
  options: AuditLogApiOptions = {}
): Promise<AuditLogEntry> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }

  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/admin/audit-logs/${auditId}`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    if (response.status === 404) {
      throw new AuditLogApiError('Audit log entry not found', 404)
    }
    if (response.status === 401) {
      throw new AuditLogApiError('Unauthorized access', 401)
    }
    if (response.status === 403) {
      throw new AuditLogApiError('Admin access required', 403)
    }
    throw new AuditLogApiError(`Failed to fetch audit log entry: ${response.status}`, response.status)
  }

  return response.json()
}

export async function fetchAuditLogStats(
  options: AuditLogApiOptions = {}
): Promise<AuditLogStatsResponse> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }

  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/admin/audit-logs/stats`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    if (response.status === 401) {
      throw new AuditLogApiError('Unauthorized access', 401)
    }
    if (response.status === 403) {
      throw new AuditLogApiError('Admin access required', 403)
    }
    throw new AuditLogApiError(`Failed to fetch audit log stats: ${response.status}`, response.status)
  }

  return response.json()
}
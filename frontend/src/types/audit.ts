/**
 * TypeScript types for audit log functionality.
 */

export interface AuditLogEntry {
  id: number
  event_type: string
  event_description: string
  user_id: string
  user_email: string
  entity_type: string
  entity_id: string
  timestamp: string
  event_metadata?: Record<string, any>
  ip_address?: string
  user_agent?: string
  created_at: string
}

export interface AuditLogPagination {
  current_page: number
  total_pages: number
  total_items: number
  items_per_page: number
}

export interface AuditLogFilters {
  user_id?: string
  event_type?: string
  entity_type?: string
  entity_id?: string
  date_from?: string
  date_to?: string
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface AuditLogMetadata {
  request_timestamp: string
  processing_time_ms: number
  total_events_in_system: number
}

export interface AuditLogResponse {
  data: AuditLogEntry[]
  pagination: AuditLogPagination
  filters: AuditLogFilters
  meta: AuditLogMetadata
}

export interface AuditLogStats {
  total_events: number
  events_today: number
  events_this_week: number
  events_this_month: number
  event_types_breakdown: Record<string, number>
  user_activity_breakdown: Record<string, number>
  entity_types_breakdown: Record<string, number>
}

export interface AuditLogStatsResponse {
  stats: AuditLogStats
  generated_at: string
}

export const EVENT_TYPES = [
  'portfolio_created',
  'portfolio_updated',
  'portfolio_deleted',
  'portfolio_soft_deleted',
  'portfolio_hard_deleted',
  'transaction_created',
  'transaction_updated',
  'transaction_deleted',
  'holding_created',
  'holding_updated',
  'holding_deleted',
  'user_login',
  'user_logout',
  'user_created',
  'user_updated',
  'admin_action_performed'
] as const

export const ENTITY_TYPES = [
  'portfolio',
  'transaction',
  'holding',
  'user',
  'admin'
] as const
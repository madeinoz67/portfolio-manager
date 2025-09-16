// Admin API data models - matching backend Pydantic schemas

export interface SystemMetrics {
  totalUsers: number
  totalPortfolios: number
  activeUsers: number
  adminUsers: number
  systemStatus: 'healthy' | 'warning' | 'error'
  lastUpdated: string
}

export interface AdminUserListItem {
  id: string
  email: string
  firstName?: string
  lastName?: string
  role: 'admin' | 'user'
  isActive: boolean
  createdAt: string
  portfolioCount: number
  lastLoginAt?: string
}

export interface PaginatedUsersResponse {
  users: AdminUserListItem[]
  total: number
  page: number
  pages: number
}

export interface AdminPortfolioSummary {
  id: string
  name: string
  value: number
  lastUpdated: string
}

export interface AdminUserDetails extends AdminUserListItem {
  totalAssets: number
  portfolios: AdminPortfolioSummary[]
}

export interface MarketDataProvider {
  providerId: string
  providerName: string
  isEnabled: boolean
  lastUpdate: string
  apiCallsToday: number
  monthlyLimit: number
  monthlyUsage: number
  costPerCall: number
  status: 'active' | 'disabled' | 'error' | 'rate_limited'
  supportsBulkFetch?: boolean
  bulkFetchLimit?: number
}

export interface MarketDataStatus {
  providers: MarketDataProvider[]
}

export interface UsageStatsToday {
  totalRequests: number
  totalErrors: number
  totalCost: number
  avgResponseTime: number
  rateLimitHits: number
  successRate: number
}

export interface HistoricalData {
  date: string
  requests: number
  errors: number
}

export interface HistoricalStats {
  last7Days: HistoricalData[]
  last30Days: HistoricalData[]
}

export interface UsageStats {
  today: UsageStatsToday
  yesterday: UsageStatsToday
  historical: HistoricalStats
}

export interface PerformanceMetrics {
  successRate: number
  errorRate: number
  avgResponseTime: number
  uptimePercentage: number
}

export interface RateLimits {
  perMinute: number
  perDay: number
  perMonth: number
}

export interface ProviderConfiguration {
  apiEndpoint: string
  authentication: string
  rateLimits: RateLimits
  timeout: number
}

export interface RecentActivity {
  timestamp: string
  type: string
  description: string
  status: 'success' | 'error' | 'warning'
}

export interface CostBreakdownItem {
  type: string
  cost: number
  percentage: number
}

export interface CostAnalysis {
  totalCostToday: number
  totalCostThisMonth: number
  projectedMonthlyCost: number
  costPerRequest: number
  costBreakdown: CostBreakdownItem[]
}

export interface ProviderDetailResponse {
  providerId: string
  providerName: string
  isEnabled: boolean
  priority: number
  rateLimitPerMinute: number
  rateLimitPerDay: number
  lastUpdated: string
  usageStats: UsageStats
  performanceMetrics: PerformanceMetrics
  configuration: ProviderConfiguration
  recentActivity: RecentActivity[]
  costAnalysis: CostAnalysis
}

// API query parameters
export interface AdminUsersListParams {
  page?: number
  size?: number
  role?: 'admin' | 'user'
  active?: boolean
}

// Standard API error response
export interface ApiError {
  error: string
  message: string
}

// Dashboard Activities (matches backend DashboardActivity model)
export interface DashboardActivity {
  id: string
  provider_id: string
  provider_name: string
  activity_type: string
  description: string
  status: 'success' | 'warning' | 'error' | 'info'
  timestamp: string
  relative_time: string
  metadata?: Record<string, any>
}

export interface DashboardActivitiesResponse {
  activities: DashboardActivity[]
  summary: {
    total_activities: number
    by_status: {
      success: number
      warning: number
      error: number
      info: number
    }
    by_provider: Record<string, number>
    activity_types: Record<string, number>
    last_updated: string
  }
}

// Scheduler Status Types
export interface SchedulerStatus {
  status: 'running' | 'stopped' | 'error'
  uptime_seconds: number
  next_run_at: string | null
  last_run_at: string | null
  total_runs: number
  successful_runs: number
  failed_runs: number
}

export interface SchedulerRecentActivity {
  total_symbols_processed: number
  success_rate: number
  avg_response_time_ms: number | null
}

export interface ProviderStats {
  [providerName: string]: {
    calls_last_hour: number
    success_rate: number
    avg_response_time_ms: number | null
    last_successful_call: string | null
  }
}

export interface SchedulerStatusResponse {
  scheduler: SchedulerStatus
  recent_activity: SchedulerRecentActivity
  provider_stats: ProviderStats
}
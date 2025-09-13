/**
 * Performance-related TypeScript types
 */

export enum PerformancePeriod {
  ONE_DAY = "1D",
  ONE_WEEK = "1W",
  ONE_MONTH = "1M",
  THREE_MONTHS = "3M",
  SIX_MONTHS = "6M",
  ONE_YEAR = "1Y",
  YEAR_TO_DATE = "YTD",
  ALL = "ALL"
}

export interface PerformanceMetrics {
  total_return: string
  annualized_return: string
  max_drawdown: string
  dividend_yield: string
  period_start_value: string
  period_end_value: string
  total_dividends: string
  period: string
  calculated_at: string
}
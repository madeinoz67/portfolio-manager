import React from 'react'

interface SystemMetricsCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ReactNode
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  className?: string
}

export function SystemMetricsCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendValue,
  className = ''
}: SystemMetricsCardProps) {
  const getTrendColor = () => {
    if (!trend) return ''
    switch (trend) {
      case 'up': return 'text-green-600 dark:text-green-400'
      case 'down': return 'text-red-600 dark:text-red-400'
      default: return 'text-gray-600 dark:text-gray-400'
    }
  }

  const getTrendIcon = () => {
    if (!trend || trend === 'neutral') return null
    return (
      <svg
        className={`w-4 h-4 ${getTrendColor()}`}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        {trend === 'up' ? (
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 17l6-6 6 6" />
        ) : (
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 7l-6 6-6-6" />
        )}
      </svg>
    )
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-red-100 dark:bg-red-900/20 rounded-lg">
            {icon}
          </div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">{title}</h3>
        </div>
        {trend && trendValue && (
          <div className="flex items-center space-x-1">
            {getTrendIcon()}
            <span className={`text-sm font-medium ${getTrendColor()}`}>
              {trendValue}
            </span>
          </div>
        )}
      </div>

      <div>
        <div className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
          {value}
        </div>
        {subtitle && (
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {subtitle}
          </div>
        )}
      </div>
    </div>
  )
}

export default SystemMetricsCard
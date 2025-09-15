'use client'

import React from 'react'
import { TrendData } from '@/types/marketData'

interface TrendIndicatorProps {
  trend?: TrendData
  size?: 'sm' | 'md' | 'lg'
  showIcon?: boolean
  showChange?: boolean
  showPercentage?: boolean
  className?: string
}

export function TrendIndicator({
  trend,
  size = 'md',
  showIcon = true,
  showChange = true,
  showPercentage = true,
  className = ''
}: TrendIndicatorProps) {
  if (!trend) {
    return (
      <div className={`flex items-center space-x-1 text-gray-500 ${className}`}>
        <span className="text-sm">No trend data</span>
      </div>
    )
  }

  const getTrendColor = () => {
    switch (trend.trend) {
      case 'up':
        return 'text-green-600 dark:text-green-400'
      case 'down':
        return 'text-red-600 dark:text-red-400'
      case 'neutral':
        return 'text-gray-600 dark:text-gray-400'
      default:
        return 'text-gray-600 dark:text-gray-400'
    }
  }

  const getTrendIcon = () => {
    if (!showIcon) return null

    const iconSize = size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-5 h-5' : 'w-4 h-4'

    switch (trend.trend) {
      case 'up':
        return (
          <svg className={`${iconSize} fill-current`} viewBox="0 0 20 20">
            <path d="M10 3l6 7H4l6-7z" />
          </svg>
        )
      case 'down':
        return (
          <svg className={`${iconSize} fill-current`} viewBox="0 0 20 20">
            <path d="M10 17L4 10h12l-6 7z" />
          </svg>
        )
      case 'neutral':
        return (
          <svg className={`${iconSize} fill-current`} viewBox="0 0 20 20">
            <path d="M3 10h14v2H3z" />
          </svg>
        )
      default:
        return null
    }
  }

  const formatChange = (value: number) => {
    return value >= 0 ? `+${value.toFixed(2)}` : value.toFixed(2)
  }

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
  }

  const textSize = size === 'sm' ? 'text-xs' : size === 'lg' ? 'text-base' : 'text-sm'

  return (
    <div className={`flex items-center space-x-1 ${getTrendColor()} ${className}`}>
      {getTrendIcon()}
      <div className={`flex items-center space-x-1 ${textSize} font-medium`}>
        {showChange && (
          <span>{formatChange(trend.change)}</span>
        )}
        {showPercentage && (
          <span>({formatPercentage(trend.change_percent)})</span>
        )}
      </div>
    </div>
  )
}

interface PriceTrendDisplayProps {
  symbol: string
  currentPrice: number
  trend?: TrendData
  openingPrice?: number
  highPrice?: number
  lowPrice?: number
  previousClose?: number
  showDetails?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export function PriceTrendDisplay({
  symbol,
  currentPrice,
  trend,
  openingPrice,
  highPrice,
  lowPrice,
  previousClose,
  showDetails = false,
  size = 'md'
}: PriceTrendDisplayProps) {
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(price)
  }

  const headerSize = size === 'sm' ? 'text-sm' : size === 'lg' ? 'text-xl' : 'text-lg'
  const priceSize = size === 'sm' ? 'text-lg' : size === 'lg' ? 'text-3xl' : 'text-2xl'

  return (
    <div className="space-y-2">
      {/* Symbol and Current Price */}
      <div className="flex items-center justify-between">
        <h3 className={`font-bold text-gray-900 dark:text-gray-100 ${headerSize}`}>
          {symbol}
        </h3>
        <div className="text-right">
          <div className={`font-bold text-gray-900 dark:text-gray-100 ${priceSize}`}>
            {formatPrice(currentPrice)}
          </div>
          <TrendIndicator
            trend={trend}
            size={size}
            showIcon={true}
            showChange={true}
            showPercentage={true}
          />
        </div>
      </div>

      {/* Price Details */}
      {showDetails && (
        <div className="grid grid-cols-2 gap-4 text-sm text-gray-600 dark:text-gray-400">
          {openingPrice && (
            <div className="flex justify-between">
              <span>Open:</span>
              <span>{formatPrice(openingPrice)}</span>
            </div>
          )}
          {previousClose && (
            <div className="flex justify-between">
              <span>Prev Close:</span>
              <span>{formatPrice(previousClose)}</span>
            </div>
          )}
          {highPrice && (
            <div className="flex justify-between">
              <span>High:</span>
              <span>{formatPrice(highPrice)}</span>
            </div>
          )}
          {lowPrice && (
            <div className="flex justify-between">
              <span>Low:</span>
              <span>{formatPrice(lowPrice)}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
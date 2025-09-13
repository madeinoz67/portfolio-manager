'use client'

import React from 'react'
import { MarketPrice } from '@/types/marketData'

interface PriceDisplayProps {
  price: MarketPrice
  showVolume?: boolean
  showPercentage?: boolean
  compact?: boolean
}

export function PriceDisplay({ 
  price, 
  showVolume = false, 
  showPercentage = true, 
  compact = false 
}: PriceDisplayProps) {
  const isPositive = price.change >= 0
  const changeColor = isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
  
  const formatPrice = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value)
  }

  const formatVolume = (volume: number) => {
    if (volume >= 1e9) return `${(volume / 1e9).toFixed(1)}B`
    if (volume >= 1e6) return `${(volume / 1e6).toFixed(1)}M`
    if (volume >= 1e3) return `${(volume / 1e3).toFixed(1)}K`
    return volume.toString()
  }

  if (compact) {
    return (
      <div className="flex items-center space-x-2">
        <span className="font-semibold text-gray-900 dark:text-gray-100">
          {formatPrice(price.price)}
        </span>
        <span className={`text-sm ${changeColor}`}>
          {isPositive ? '+' : ''}{price.change.toFixed(2)}
          {showPercentage && ` (${isPositive ? '+' : ''}${price.change_percent.toFixed(2)}%)`}
        </span>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      <div className="flex items-baseline space-x-2">
        <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {formatPrice(price.price)}
        </span>
        <span className="text-lg font-medium text-gray-500 dark:text-gray-400">
          {price.symbol}
        </span>
      </div>
      
      <div className="flex items-center space-x-4">
        <div className={`flex items-center space-x-1 ${changeColor}`}>
          <span className="text-sm font-medium">
            {isPositive ? '+' : ''}{price.change.toFixed(2)}
          </span>
          {showPercentage && (
            <span className="text-sm">
              ({isPositive ? '+' : ''}{price.change_percent.toFixed(2)}%)
            </span>
          )}
        </div>
        
        {showVolume && price.volume && (
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Vol: {formatVolume(price.volume)}
          </div>
        )}
      </div>
      
      {price.timestamp && (
        <div className="text-xs text-gray-500 dark:text-gray-500">
          Last updated: {new Date(price.timestamp).toLocaleTimeString()}
        </div>
      )}
    </div>
  )
}
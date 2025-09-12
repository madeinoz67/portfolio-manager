'use client'

import { Doughnut } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend)

interface AssetAllocationChartProps {
  portfolios: any[]
}

export default function AssetAllocationChart({ portfolios }: AssetAllocationChartProps) {
  // Generate sample asset allocation data
  const generateAllocationData = () => {
    if (portfolios.length === 0) {
      return {
        labels: ['No Data'],
        values: [1],
        colors: ['#E5E7EB']
      }
    }

    // Simulate different asset types with portfolio values
    const assetTypes = ['Stocks', 'Bonds', 'ETFs', 'Crypto', 'Cash']
    const colors = [
      '#3B82F6', // Blue
      '#10B981', // Green  
      '#8B5CF6', // Purple
      '#F59E0B', // Yellow
      '#6B7280'  // Gray
    ]
    
    const values = assetTypes.map(() => Math.random() * 1000 + 500)
    
    return {
      labels: assetTypes,
      values,
      colors
    }
  }

  const allocationData = generateAllocationData()
  
  const chartData = {
    labels: allocationData.labels,
    datasets: [
      {
        data: allocationData.values,
        backgroundColor: allocationData.colors,
        borderColor: allocationData.colors,
        borderWidth: 0,
        hoverBorderWidth: 2,
        hoverBorderColor: '#ffffff',
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          padding: 20,
          usePointStyle: true,
          pointStyle: 'circle',
          font: {
            size: 12,
          },
          color: 'rgb(107, 114, 128)', // Gray-500
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: 'white',
        bodyColor: 'white',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 1,
        callbacks: {
          label: function(context: any) {
            const label = context.label || ''
            const value = context.parsed || 0
            const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0)
            const percentage = ((value / total) * 100).toFixed(1)
            return `${label}: $${value.toLocaleString()} (${percentage}%)`
          }
        }
      },
    },
    cutout: '60%',
    elements: {
      arc: {
        hoverBackgroundColor: function(ctx: any) {
          return ctx.element.options.backgroundColor
        }
      }
    }
  }

  const totalValue = allocationData.values.reduce((sum, value) => sum + value, 0)

  return (
    <div className="relative">
      <div className="h-64 w-full">
        <Doughnut data={chartData} options={options} />
      </div>
      
      {/* Center text showing total value */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            ${totalValue.toLocaleString()}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Total Value
          </div>
        </div>
      </div>
    </div>
  )
}
'use client'

import { Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
)

interface PortfolioComparisonProps {
  portfolios: any[]
}

export default function PortfolioComparison({ portfolios }: PortfolioComparisonProps) {
  if (portfolios.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center">
        <div className="text-center">
          <div className="text-gray-500 dark:text-gray-400 mb-2">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <p className="text-gray-500 dark:text-gray-400">No portfolios to compare</p>
        </div>
      </div>
    )
  }

  const portfolioNames = portfolios.map(p => p.name || 'Unnamed Portfolio')
  const portfolioValues = portfolios.map(p => parseFloat(p.total_value || '0'))
  const portfolioChanges = portfolios.map(p => parseFloat(p.daily_change || '0'))

  const chartData = {
    labels: portfolioNames,
    datasets: [
      {
        label: 'Portfolio Value',
        data: portfolioValues,
        backgroundColor: 'rgba(59, 130, 246, 0.8)', // Blue
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 1,
        borderRadius: 6,
        borderSkipped: false,
      },
      {
        label: 'Daily Change',
        data: portfolioChanges,
        backgroundColor: portfolioChanges.map(change => 
          change >= 0 ? 'rgba(34, 197, 94, 0.8)' : 'rgba(239, 68, 68, 0.8)'
        ), // Green for positive, Red for negative
        borderColor: portfolioChanges.map(change => 
          change >= 0 ? 'rgba(34, 197, 94, 1)' : 'rgba(239, 68, 68, 1)'
        ),
        borderWidth: 1,
        borderRadius: 6,
        borderSkipped: false,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          pointStyle: 'rect',
          padding: 20,
          color: 'rgb(107, 114, 128)', // Gray-500
        },
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: 'white',
        bodyColor: 'white',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 1,
        callbacks: {
          label: function(context: any) {
            const label = context.dataset.label || ''
            const value = context.parsed.y
            if (label === 'Portfolio Value') {
              return `${label}: $${value.toLocaleString()}`
            } else {
              const sign = value >= 0 ? '+' : ''
              return `${label}: ${sign}$${value.toLocaleString()}`
            }
          }
        }
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
        ticks: {
          color: 'rgb(156, 163, 175)', // Gray-400
          maxRotation: 45,
        },
      },
      y: {
        grid: {
          color: 'rgba(156, 163, 175, 0.2)',
        },
        ticks: {
          color: 'rgb(156, 163, 175)', // Gray-400
          callback: function(value: any) {
            return '$' + value.toLocaleString()
          }
        },
      },
    },
    elements: {
      bar: {
        borderWidth: 1,
      },
    },
  }

  return (
    <div>
      <div className="h-64 w-full mb-6">
        <Bar data={chartData} options={options} />
      </div>
      
      {/* Portfolio Performance Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-white">
                Portfolio
              </th>
              <th className="text-right py-3 px-4 font-medium text-gray-900 dark:text-white">
                Value
              </th>
              <th className="text-right py-3 px-4 font-medium text-gray-900 dark:text-white">
                Daily Change
              </th>
              <th className="text-right py-3 px-4 font-medium text-gray-900 dark:text-white">
                Change %
              </th>
            </tr>
          </thead>
          <tbody>
            {portfolios.map((portfolio, index) => {
              const dailyChange = parseFloat(portfolio.daily_change || '0')
              const changePercent = parseFloat(portfolio.daily_change_percent || '0')
              const isPositive = dailyChange >= 0
              
              return (
                <tr key={portfolio.id || index} className="border-b border-gray-100 dark:border-gray-800">
                  <td className="py-3 px-4 text-gray-900 dark:text-white font-medium">
                    {portfolio.name || 'Unnamed Portfolio'}
                  </td>
                  <td className="py-3 px-4 text-right text-gray-900 dark:text-white">
                    ${parseFloat(portfolio.total_value || '0').toLocaleString()}
                  </td>
                  <td className={`py-3 px-4 text-right font-medium ${
                    isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                  }`}>
                    {isPositive ? '+' : ''}${Math.abs(dailyChange).toLocaleString()}
                  </td>
                  <td className={`py-3 px-4 text-right font-medium ${
                    isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                  }`}>
                    {isPositive ? '+' : ''}{changePercent}%
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
'use client'

import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface PerformanceChartProps {
  portfolios: any[]
  timeRange: string
}

export default function PerformanceChart({ portfolios, timeRange }: PerformanceChartProps) {
  // Generate sample performance data based on time range
  const generatePerformanceData = () => {
    const periods: Record<string, number> = {
      '1D': 24,
      '1W': 7,
      '1M': 30,
      '3M': 90,
      '1Y': 365,
      'ALL': 365
    }
    
    const dataPoints = periods[timeRange] || 30
    const labels = []
    const data = []
    
    // Generate sample data points
    let baseValue = 10000
    for (let i = 0; i < dataPoints; i++) {
      const date = new Date()
      date.setDate(date.getDate() - (dataPoints - i))
      
      if (timeRange === '1D') {
        labels.push(date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))
      } else {
        labels.push(date.toLocaleDateString())
      }
      
      // Simulate portfolio performance with some volatility
      const change = (Math.random() - 0.5) * 200 // Random change between -100 and +100
      baseValue += change
      data.push(Math.max(0, baseValue))
    }
    
    return { labels, data }
  }

  const performanceData = generatePerformanceData()
  
  const chartData = {
    labels: performanceData.labels,
    datasets: [
      {
        label: 'Portfolio Value',
        data: performanceData.data,
        borderColor: 'rgb(59, 130, 246)', // Blue
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 6,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
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
            return `Value: $${context.parsed.y.toLocaleString()}`
          }
        }
      },
    },
    scales: {
      x: {
        display: true,
        grid: {
          display: false,
        },
        ticks: {
          maxTicksLimit: 6,
          color: 'rgb(156, 163, 175)', // Gray-400
        },
      },
      y: {
        display: true,
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
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false,
    },
    elements: {
      point: {
        hoverBackgroundColor: 'rgb(59, 130, 246)',
        hoverBorderColor: 'white',
        hoverBorderWidth: 2,
      },
    },
  }

  return (
    <div className="h-64 w-full">
      <Line data={chartData} options={options} />
    </div>
  )
}
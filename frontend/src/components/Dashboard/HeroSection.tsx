import { useAuth } from '@/contexts/AuthContext'

interface HeroSectionProps {
  totalValue: string
  totalGain: string
  gainPercent: string
  isPositive: boolean
}

export default function HeroSection({ totalValue, totalGain, gainPercent, isPositive }: HeroSectionProps) {
  const { user } = useAuth()
  return (
    <div className="relative bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-700 rounded-2xl p-8 mb-8 overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        }}></div>
      </div>

      <div className="relative z-10">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
          <div className="mb-6 lg:mb-0">
            <h1 className="text-white text-3xl lg:text-4xl font-bold mb-2">
              Welcome back, {user?.first_name || 'Friend'} 👋
            </h1>
            <p className="text-blue-100 text-lg">
              Here's what's happening with your investments today
            </p>
          </div>
          
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
            <div className="text-center">
              <p className="text-blue-100 text-sm uppercase tracking-wide font-medium">
                Total Portfolio Value
              </p>
              <p className="text-white text-3xl font-bold mt-1">
                ${totalValue}
              </p>
              <div className={`flex items-center justify-center space-x-1 mt-2 ${
                isPositive ? 'text-green-300' : 'text-red-300'
              }`}>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d={isPositive ? "M7 17l9.2-9.2M17 17V7H7" : "M17 7l-9.2 9.2M7 7v10h10"} 
                  />
                </svg>
                <span className="text-sm font-medium">
                  ${totalGain} ({gainPercent}%)
                </span>
              </div>
            </div>
          </div>
        </div>
        
        {/* Quick actions */}
        <div className="flex flex-wrap gap-3 mt-6">
          <button className="bg-white/20 hover:bg-white/30 backdrop-blur-sm text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors border border-white/20">
            📊 View Analytics
          </button>
          <button className="bg-white/20 hover:bg-white/30 backdrop-blur-sm text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors border border-white/20">
            💼 Add Transaction
          </button>
          <button className="bg-white/20 hover:bg-white/30 backdrop-blur-sm text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors border border-white/20">
            📈 Market Insights
          </button>
        </div>
      </div>
    </div>
  )
}
'use client'

import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import AdminNavigation from '@/components/admin/AdminNavigation'
import AdminErrorBoundary from '@/components/admin/AdminErrorBoundary'

interface AdminLayoutProps {
  children: React.ReactNode
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const { user, loading } = useAuth()
  const router = useRouter()

  console.log('AdminLayout Debug:', {
    user,
    loading,
    userRole: user?.role,
    isAdmin: user?.role === 'admin'
  })

  useEffect(() => {
    if (!loading && (!user || user.role !== 'admin')) {
      router.push('/')
    }
  }, [user, loading, router])

  // Show loading while checking auth
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner />
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            Checking admin access...
          </p>
        </div>
      </div>
    )
  }

  // Block access for non-admin users
  if (!user || user.role !== 'admin') {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto px-6">
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl border dark:border-gray-700">
            <div className="w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Access Denied
            </h2>
            <p className="text-gray-600 dark:text-gray-400 text-sm mb-6">
              You do not have administrator privileges to access this area.
            </p>
            <button
              onClick={() => router.push('/')}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Admin user authenticated - show admin layout
  return (
    <AdminErrorBoundary>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <AdminNavigation />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </div>
    </AdminErrorBoundary>
  )
}
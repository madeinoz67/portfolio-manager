'use client'

import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect, ReactNode } from 'react'

interface AdminRouteProps {
  children: ReactNode
  fallback?: ReactNode
  redirectTo?: string
}

export function AdminRoute({
  children,
  fallback,
  redirectTo = '/login'
}: AdminRouteProps) {
  const { user, loading, isAdmin, isAuthenticated } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !isAuthenticated()) {
      router.push(redirectTo)
    } else if (!loading && isAuthenticated() && !isAdmin()) {
      router.push('/dashboard')
    }
  }, [loading, isAuthenticated, isAdmin, router, redirectTo])

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  // Show fallback if not authenticated or not admin
  if (!isAuthenticated() || !isAdmin()) {
    if (fallback) {
      return <>{fallback}</>
    }

    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Access Denied
          </h1>
          <p className="text-gray-600 mb-8">
            You need administrator privileges to access this page.
          </p>
          <button
            onClick={() => router.push('/dashboard')}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    )
  }

  // User is authenticated and is admin, show children
  return <>{children}</>
}

export default AdminRoute
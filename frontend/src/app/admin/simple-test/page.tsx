'use client'

import { useAuth } from '@/contexts/AuthContext'

export default function SimpleTestPage() {
  console.log('SimpleTestPage is rendering!')

  const { user, isAdmin } = useAuth()

  console.log('SimpleTestPage auth data:', { user, isAdmin: isAdmin() })

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold">Simple Test Page</h1>
      <div className="mt-4 bg-white dark:bg-gray-800 p-4 rounded border">
        <p>User: {user?.email}</p>
        <p>Role: {user?.role}</p>
        <p>Is Admin: {isAdmin() ? 'Yes' : 'No'}</p>
      </div>
    </div>
  )
}
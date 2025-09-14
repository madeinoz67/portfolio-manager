'use client'

import { useAuth } from '@/contexts/AuthContext'

export default function DebugPage() {
  const { user, loading, token, isAdmin, isAuthenticated } = useAuth()

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Debug Information</h1>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-4">
        <div>
          <h3 className="font-semibold">Loading:</h3>
          <pre className="bg-gray-100 dark:bg-gray-700 p-2 rounded">{JSON.stringify(loading, null, 2)}</pre>
        </div>

        <div>
          <h3 className="font-semibold">Token:</h3>
          <pre className="bg-gray-100 dark:bg-gray-700 p-2 rounded">{token ? `${token.substring(0, 20)}...` : 'null'}</pre>
        </div>

        <div>
          <h3 className="font-semibold">User:</h3>
          <pre className="bg-gray-100 dark:bg-gray-700 p-2 rounded">{JSON.stringify(user, null, 2)}</pre>
        </div>

        <div>
          <h3 className="font-semibold">isAdmin():</h3>
          <pre className="bg-gray-100 dark:bg-gray-700 p-2 rounded">{JSON.stringify(isAdmin(), null, 2)}</pre>
        </div>

        <div>
          <h3 className="font-semibold">isAuthenticated():</h3>
          <pre className="bg-gray-100 dark:bg-gray-700 p-2 rounded">{JSON.stringify(isAuthenticated(), null, 2)}</pre>
        </div>
      </div>
    </div>
  )
}
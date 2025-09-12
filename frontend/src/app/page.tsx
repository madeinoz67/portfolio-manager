'use client'

import { useState, useEffect } from 'react'

export default function Home() {
  const [backendStatus, setBackendStatus] = useState('Connecting...')
  const [apiData, setApiData] = useState(null)

  useEffect(() => {
    const testBackendConnection = async () => {
      try {
        const response = await fetch('http://localhost:8001/health')
        if (response.ok) {
          const data = await response.json()
          setBackendStatus('✅ Backend: Connected')
          setApiData(data)
        } else {
          setBackendStatus('❌ Backend: Connection Failed')
        }
      } catch (error) {
        setBackendStatus('❌ Backend: Connection Error')
        console.error('Backend connection error:', error)
      }
    }

    testBackendConnection()
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Portfolio Management System
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Welcome to your intelligent portfolio dashboard
        </p>
        <div className="space-y-4">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-lg font-semibold text-gray-800 mb-2">Status</h2>
            <p className="text-green-600">✅ Frontend: Running</p>
            <p className={backendStatus.includes('✅') ? 'text-green-600' : 'text-red-600'}>
              {backendStatus}
            </p>
            {apiData && (
              <div className="mt-4 p-3 bg-gray-100 rounded text-sm text-left">
                <strong>API Response:</strong>
                <pre className="mt-1">{JSON.stringify(apiData, null, 2)}</pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
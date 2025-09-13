'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import Button from '@/components/ui/Button'
import { useToast } from '@/components/ui/Toast'
import { ErrorBanner } from '@/components/ui/ErrorBanner'

interface LoginFormProps {
  onSuccess?: () => void
  onSwitchToRegister?: () => void
}

export default function LoginForm({ onSuccess, onSwitchToRegister }: LoginFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [localError, setLocalError] = useState<any>(null)
  const { login, clearError } = useAuth()
  const { addToast } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (isSubmitting) return

    setIsSubmitting(true)
    setLocalError(null)
    clearError()

    try {
      const result = await login({ email, password })
      if (result.success) {
        addToast('Successfully logged in!', 'success')
        onSuccess?.()
      } else {
        setLocalError(result.error)
      }
    } catch (error) {
      addToast('Login failed. Please try again.', 'error')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 w-full max-w-md">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white">Sign In</h2>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Welcome back to your portfolio manager
        </p>
      </div>

      {/* Show local error banner if login failed */}
      {localError && (
        <ErrorBanner
          error={localError}
          onDismiss={() => setLocalError(null)}
          className="mb-6"
        />
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Email Address
          </label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter your email"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Password
          </label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter your password"
          />
        </div>

        <Button
          type="submit"
          className="w-full"
          disabled={isSubmitting}
          loading={isSubmitting}
        >
          {isSubmitting ? 'Signing In...' : 'Sign In'}
        </Button>
      </form>

      {onSwitchToRegister && (
        <div className="text-center mt-6">
          <p className="text-gray-600 dark:text-gray-400">
            Don't have an account?{' '}
            <button
              onClick={onSwitchToRegister}
              className="text-blue-600 hover:text-blue-500 font-medium"
            >
              Sign up
            </button>
          </p>
        </div>
      )}
    </div>
  )
}
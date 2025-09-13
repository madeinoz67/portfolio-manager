'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { User, LoginData, RegisterData, TokenResponse, AuthContextType, AuthError } from '@/types/auth'

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<AuthError | null>(null)

  const clearError = () => setError(null)

  const createError = (type: AuthError['type'], message: string, details?: string): AuthError => ({
    type,
    message,
    details,
    timestamp: new Date()
  })

  const handleFetchError = (error: unknown): AuthError => {
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        return createError('timeout', 'Request timed out', 'The server took too long to respond. Please check your connection and try again.')
      }
      if (error.message.includes('fetch')) {
        return createError('network', 'Network connection failed', 'Unable to connect to the server. Please check your internet connection.')
      }
      return createError('network', 'Connection error', error.message)
    }
    return createError('network', 'Unknown network error', 'An unexpected error occurred while connecting to the server.')
  }

  // Load token from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token')
    if (storedToken) {
      setToken(storedToken)
      // Verify token and get user profile
      fetchCurrentUser(storedToken)
    } else {
      setLoading(false)
    }
  }, [])

  const fetchCurrentUser = async (authToken: string) => {
    try {
      clearError()
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout

      let response: Response
      try {
        response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json',
          },
          signal: controller.signal,
        })
      } finally {
        clearTimeout(timeoutId)
      }

      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
        clearError()
      } else if (response.status === 401) {
        // Token invalid, remove it
        localStorage.removeItem('auth_token')
        setToken(null)
        setError(createError('auth', 'Session expired', 'Please log in again.'))
      } else {
        const errorText = await response.text().catch(() => 'Unknown server error')
        setError(createError('server', 'Authentication failed', `Server error: ${errorText}`))
        localStorage.removeItem('auth_token')
        setToken(null)
      }
    } catch (err) {
      console.error('Error fetching current user:', err)
      const authError = handleFetchError(err)
      setError(authError)
      localStorage.removeItem('auth_token')
      setToken(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (data: LoginData): Promise<{ success: boolean; error?: AuthError }> => {
    try {
      setLoading(true)
      clearError()

      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000)

      let response: Response
      try {
        response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
          signal: controller.signal,
        })
      } finally {
        clearTimeout(timeoutId)
      }

      if (response.ok) {
        const tokenData: TokenResponse = await response.json()
        const newToken = tokenData.access_token

        setToken(newToken)
        localStorage.setItem('auth_token', newToken)

        // Fetch user profile
        await fetchCurrentUser(newToken)
        return { success: true }
      } else {
        let errorMessage = 'Login failed'
        let errorDetails = 'Please check your credentials and try again.'

        try {
          const errorData = await response.json()
          errorMessage = errorData.message || errorData.detail || errorMessage
          errorDetails = `Server responded with status ${response.status}`
        } catch {
          errorDetails = `Server error (${response.status}): ${response.statusText}`
        }

        const authError = createError('auth', errorMessage, errorDetails)
        setError(authError)
        return { success: false, error: authError }
      }
    } catch (err) {
      console.error('Login error:', err)
      const authError = handleFetchError(err)
      setError(authError)
      return { success: false, error: authError }
    } finally {
      setLoading(false)
    }
  }

  const register = async (data: RegisterData): Promise<{ success: boolean; error?: AuthError }> => {
    try {
      setLoading(true)
      clearError()

      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000)

      let response: Response
      try {
        response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
          signal: controller.signal,
        })
      } finally {
        clearTimeout(timeoutId)
      }

      if (response.ok) {
        // After successful registration, automatically log in
        const loginResult = await login({ email: data.email, password: data.password })
        return loginResult
      } else {
        let errorMessage = 'Registration failed'
        let errorDetails = 'Unable to create account. Please try again.'

        try {
          const errorData = await response.json()
          errorMessage = errorData.message || errorData.detail || errorMessage
          if (response.status === 400) {
            errorDetails = 'Invalid registration data. Please check your input.'
          } else if (response.status === 409) {
            errorDetails = 'An account with this email already exists.'
          } else {
            errorDetails = `Server responded with status ${response.status}`
          }
        } catch {
          errorDetails = `Server error (${response.status}): ${response.statusText}`
        }

        const authError = createError('auth', errorMessage, errorDetails)
        setError(authError)
        return { success: false, error: authError }
      }
    } catch (err) {
      console.error('Registration error:', err)
      const authError = handleFetchError(err)
      setError(authError)
      return { success: false, error: authError }
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('auth_token')
    clearError()
  }

  const value: AuthContextType = {
    user,
    token,
    login,
    register,
    logout,
    loading,
    error,
    clearError,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
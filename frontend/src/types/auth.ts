export interface User {
  id: string
  email: string
  first_name?: string
  last_name?: string
  is_active: boolean
  created_at: string
}

export interface LoginData {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  first_name?: string
  last_name?: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface AuthContextType {
  user: User | null
  token: string | null
  login: (data: LoginData) => Promise<boolean>
  register: (data: RegisterData) => Promise<boolean>
  logout: () => void
  loading: boolean
}
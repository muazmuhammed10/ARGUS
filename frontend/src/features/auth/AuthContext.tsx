import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react'
import { useNavigate } from 'react-router-dom'
import { authService } from '../../services/auth.service'
import {
  clearTokens,
  loadTokensFromSession,
  setTokens,
  getAccessToken,
} from '../../services/api'
import type { User, UserRole } from '../../types'

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  hasRole: (...roles: UserRole[]) => boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()

  // Try to restore session on app load
  useEffect(() => {
    const restore = async () => {
      loadTokensFromSession()
      const rt = sessionStorage.getItem('argus_rt')
      if (!rt) {
        setIsLoading(false)
        return
      }
      try {
        const tokens = await authService.refresh(rt)
        setTokens(tokens)
        const me = await authService.getMe()
        setUser(me)
      } catch {
        clearTokens()
      } finally {
        setIsLoading(false)
      }
    }
    restore()
  }, [])

  // Listen for session expiry events fired by the API interceptor
  useEffect(() => {
    const handler = () => {
      setUser(null)
      navigate('/login', { replace: true })
    }
    window.addEventListener('argus:session-expired', handler)
    return () => window.removeEventListener('argus:session-expired', handler)
  }, [navigate])

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await authService.login({ email, password })
    setTokens(tokens)
    const me = await authService.getMe()
    setUser(me)
  }, [])

  const logout = useCallback(async () => {
    const rt = sessionStorage.getItem('argus_rt')
    try {
      if (rt) await authService.logout(rt)
    } catch {
      // Swallow — clear locally regardless
    }
    clearTokens()
    setUser(null)
    navigate('/login', { replace: true })
  }, [navigate])

  const hasRole = useCallback(
    (...roles: UserRole[]) => {
      if (!user) return false
      return roles.includes(user.role)
    },
    [user],
  )

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

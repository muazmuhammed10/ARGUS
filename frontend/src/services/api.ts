// ============================================================
// ARGUS — Axios API client with JWT token management
// Access tokens stored in memory only (not localStorage).
// Refresh tokens handled via Authorization header rotation.
// ============================================================

import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import type { AuthTokens } from '../types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

// In-memory token store — not persisted to localStorage for security
let accessToken: string | null = null
let refreshToken: string | null = null

export function setTokens(tokens: AuthTokens) {
  accessToken = tokens.access_token
  refreshToken = tokens.refresh_token
  // Store refresh token in sessionStorage so it survives page refresh
  // but is cleared when browser tab is closed
  sessionStorage.setItem('argus_rt', tokens.refresh_token)
}

export function clearTokens() {
  accessToken = null
  refreshToken = null
  sessionStorage.removeItem('argus_rt')
}

export function loadTokensFromSession() {
  const rt = sessionStorage.getItem('argus_rt')
  if (rt) refreshToken = rt
}

export function getAccessToken() {
  return accessToken
}

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000,
})

// ── Request interceptor: attach access token ──────────────────────────────
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

// ── Response interceptor: handle 401 → refresh token ─────────────────────
let isRefreshing = false
let failedQueue: Array<{
  resolve: (token: string) => void
  reject: (err: unknown) => void
}> = []

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error)
    else resolve(token!)
  })
  failedQueue = []
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry && refreshToken) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return apiClient(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const response = await axios.post<AuthTokens>(
          `${BASE_URL}/auth/refresh`,
          {},
          { headers: { Authorization: `Bearer ${refreshToken}` } }
        )
        setTokens(response.data)
        processQueue(null, response.data.access_token)
        originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`
        return apiClient(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        clearTokens()
        window.dispatchEvent(new CustomEvent('argus:session-expired'))
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient

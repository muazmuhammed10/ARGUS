import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import DashboardPage from '../pages/DashboardPage'

vi.mock('../features/auth/AuthContext', () => ({
  useAuth: () => ({
    user: { id: '1', email: 'admin@example.com', role: 'ADMIN', full_name: 'Admin', is_active: true, is_verified: true, created_at: new Date().toISOString(), username: 'admin' },
    isAuthenticated: true,
    isLoading: false,
    hasRole: () => true,
    login: vi.fn(),
    logout: vi.fn(),
  }),
  AuthProvider: ({ children }: any) => <>{children}</>,
}))

const mockSummary = {
  total_events: 42,
  critical_events: 3,
  high_events: 8,
  open_incidents: 2,
  resolved_incidents: 5,
  open_alerts: 1,
  unique_source_ips: 7,
  auth_failures: 12,
  active_investigations: 1,
  total_assets: 10,
  window_days: 7,
}

const mockTrends = {
  trend_data: [
    { day: '2024-01-01', critical: 1, high: 3, medium: 5, low: 8, info: 2 },
  ],
  event_type_distribution: [
    { type: 'AUTHENTICATION', count: 30 },
    { type: 'NETWORK', count: 12 },
  ],
  window_days: 7,
}

vi.mock('../services/dashboard.service', () => ({
  dashboardService: {
    getSummary: vi.fn().mockResolvedValue(mockSummary),
    getTrends: vi.fn().mockResolvedValue(mockTrends),
    getRecentAlerts: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  },
}))

function renderDashboard() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <MemoryRouter>
      <QueryClientProvider client={qc}>
        <DashboardPage />
      </QueryClientProvider>
    </MemoryRouter>
  )
}

describe('DashboardPage', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders the page title', async () => {
    renderDashboard()
    expect(screen.getByText('Security Overview')).toBeInTheDocument()
  })

  it('displays total events from API', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByText('42')).toBeInTheDocument()
    })
  })

  it('displays critical events from API', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument()
    })
  })

  it('shows open incidents count', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument()
    })
  })

  it('has a time range selector', () => {
    renderDashboard()
    expect(screen.getByRole('combobox', { name: /time range/i })).toBeInTheDocument()
  })
})

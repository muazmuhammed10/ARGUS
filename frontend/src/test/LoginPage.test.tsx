import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import LoginPage from '../pages/LoginPage'

// Mock auth context
const mockLogin = vi.fn()
vi.mock('../features/auth/AuthContext', () => ({
  useAuth: () => ({
    login: mockLogin,
    isAuthenticated: false,
    isLoading: false,
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

function renderLogin() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <MemoryRouter>
      <QueryClientProvider client={qc}>
        <LoginPage />
      </QueryClientProvider>
    </MemoryRouter>
  )
}

describe('LoginPage', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders the sign in form', () => {
    renderLogin()
    expect(screen.getByRole('heading', { name: /secure sign in/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('disables submit when fields are empty', () => {
    renderLogin()
    const btn = screen.getByRole('button', { name: /sign in/i })
    expect(btn).toBeDisabled()
  })

  it('enables submit when both fields are filled', async () => {
    renderLogin()
    const user = userEvent.setup()
    await user.type(screen.getByLabelText(/email/i), 'admin@argus.local')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    expect(screen.getByRole('button', { name: /sign in/i })).not.toBeDisabled()
  })

  it('calls login with email and password on submit', async () => {
    mockLogin.mockResolvedValue(undefined)
    renderLogin()
    const user = userEvent.setup()
    await user.type(screen.getByLabelText(/email/i), 'admin@argus.local')
    await user.type(screen.getByLabelText(/password/i), 'Admin@Argus2024!')
    await user.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('admin@argus.local', 'Admin@Argus2024!')
    })
  })

  it('shows an error message on login failure', async () => {
    const { AxiosError } = await import('axios')
    const err = new AxiosError('Invalid credentials')
    err.response = { data: { detail: 'Invalid credentials' }, status: 401 } as any
    mockLogin.mockRejectedValue(err)
    renderLogin()
    const user = userEvent.setup()
    await user.type(screen.getByLabelText(/email/i), 'bad@example.com')
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword1!')
    await user.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
    })
  })

  it('has a link to the register page', () => {
    renderLogin()
    expect(screen.getByRole('link', { name: /create an account/i })).toBeInTheDocument()
  })
})

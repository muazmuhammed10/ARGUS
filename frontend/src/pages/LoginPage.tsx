import { useState } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { Eye, EyeOff, ShieldCheck, AlertCircle } from 'lucide-react'
import { useAuth } from '../features/auth/AuthContext'
import { Logo } from '../components/Logo'
import { AxiosError } from 'axios'

export default function LoginPage() {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)

  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname ?? '/dashboard'

  if (isAuthenticated) {
    navigate(from, { replace: true })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email.trim(), password)
      navigate(from, { replace: true })
    } catch (err) {
      if (err instanceof AxiosError) {
        const msg = err.response?.data?.detail ?? 'Login failed. Please try again.'
        setError(msg)
      } else {
        setError('An unexpected error occurred.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-navy-950 flex items-center justify-center p-4">
      {/* Background grid effect */}
      <div
        className="fixed inset-0 opacity-5 pointer-events-none"
        style={{
          backgroundImage: 'linear-gradient(rgba(0,212,255,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(0,212,255,0.3) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
        aria-hidden="true"
      />

      <div className="w-full max-w-md relative z-10">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Logo size="lg" showText={false} />
          </div>
          <h1 className="text-3xl font-bold tracking-widest text-gray-100 font-mono mb-1">ARGUS</h1>
          <p className="text-sm text-gray-400">Cyber Defense Platform</p>
        </div>

        {/* Card */}
        <div className="card border-charcoal-500 shadow-2xl">
          <div className="flex items-center gap-2 mb-6">
            <ShieldCheck className="w-5 h-5 text-cyber-cyan" />
            <h2 className="text-lg font-semibold text-gray-200">Secure Sign In</h2>
          </div>

          {error && (
            <div className="flex items-center gap-2 p-3 mb-4 bg-red-500/10 border border-red-500/30 rounded-lg">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            <div>
              <label htmlFor="email" className="label">Email address</label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="input-field"
                placeholder="analyst@argus.local"
                disabled={loading}
              />
            </div>

            <div>
              <label htmlFor="password" className="label">Password</label>
              <div className="relative">
                <input
                  id="password"
                  type={showPass ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="input-field pr-10"
                  placeholder="••••••••••••"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPass(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                  aria-label={showPass ? 'Hide password' : 'Show password'}
                >
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !email || !password}
              className="btn-primary w-full justify-center py-2.5 mt-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-navy-950 border-t-transparent rounded-full animate-spin" />
                  Authenticating…
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <div className="mt-4 text-center">
            <Link
              to="/register"
              className="text-sm text-cyber-cyan hover:text-cyan-300 transition-colors"
            >
              Create an account
            </Link>
          </div>
        </div>

        {/* Demo credentials hint */}
        <div className="mt-4 p-3 bg-charcoal-700/50 border border-charcoal-500 rounded-lg">
          <p className="text-xs text-gray-500 text-center mb-2 font-semibold uppercase tracking-wider">Demo Credentials</p>
          <div className="space-y-1">
            {[
              { role: 'Admin',   email: 'admin@argus.local',   pass: 'Admin@Argus2024!' },
              { role: 'Analyst', email: 'analyst1@argus.local', pass: 'Analyst1Pass!23' },
              { role: 'Viewer',  email: 'viewer@argus.local',   pass: 'Viewer1Pass!23' },
            ].map(({ role, email: e, pass }) => (
              <button
                key={role}
                type="button"
                onClick={() => { setEmail(e); setPassword(pass) }}
                className="w-full text-left px-2 py-1 rounded text-xs text-gray-400 hover:bg-charcoal-600 hover:text-gray-200 transition-colors font-mono"
              >
                <span className="text-cyber-cyan">[{role}]</span> {e}
              </button>
            ))}
          </div>
        </div>

        <p className="text-center text-xs text-gray-600 mt-6">
          ARGUS v{import.meta.env.VITE_APP_VERSION ?? '1.0.0'} · Authorized access only
        </p>
      </div>
    </div>
  )
}

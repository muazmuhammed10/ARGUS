import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Eye, EyeOff, ShieldCheck, AlertCircle } from 'lucide-react'
import { authService } from '../services/auth.service'
import { Logo } from '../components/Logo'
import { AxiosError } from 'axios'

export default function RegisterPage() {
  const [form, setForm] = useState({ email: '', username: '', full_name: '', password: '', confirm: '' })
  const [showPass, setShowPass] = useState(false)
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const navigate = useNavigate()

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(v => ({ ...v, [k]: e.target.value }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirm) { setError('Passwords do not match.'); return }
    setLoading(true)
    try {
      await authService.register({
        email: form.email.trim(),
        username: form.username.trim(),
        full_name: form.full_name.trim(),
        password: form.password,
      })
      navigate('/login', { state: { registered: true } })
    } catch (err) {
      if (err instanceof AxiosError) {
        setError(err.response?.data?.detail ?? 'Registration failed.')
      } else {
        setError('An unexpected error occurred.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-navy-950 flex items-center justify-center p-4">
      <div
        className="fixed inset-0 opacity-5 pointer-events-none"
        style={{
          backgroundImage: 'linear-gradient(rgba(0,212,255,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(0,212,255,0.3) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
        aria-hidden="true"
      />
      <div className="w-full max-w-md relative z-10">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4"><Logo size="lg" showText={false} /></div>
          <h1 className="text-3xl font-bold tracking-widest text-gray-100 font-mono mb-1">ARGUS</h1>
          <p className="text-sm text-gray-400">Create your analyst account</p>
        </div>

        <div className="card border-charcoal-500 shadow-2xl">
          <div className="flex items-center gap-2 mb-6">
            <ShieldCheck className="w-5 h-5 text-cyber-cyan" />
            <h2 className="text-lg font-semibold text-gray-200">Register</h2>
          </div>

          {error && (
            <div className="flex items-center gap-2 p-3 mb-4 bg-red-500/10 border border-red-500/30 rounded-lg">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            <div>
              <label htmlFor="full_name" className="label">Full name</label>
              <input id="full_name" type="text" autoComplete="name" required value={form.full_name} onChange={set('full_name')} className="input-field" placeholder="Alex Chen" disabled={loading} />
            </div>
            <div>
              <label htmlFor="username" className="label">Username</label>
              <input id="username" type="text" autoComplete="username" required value={form.username} onChange={set('username')} className="input-field" placeholder="alexchen" disabled={loading} />
            </div>
            <div>
              <label htmlFor="email" className="label">Email address</label>
              <input id="email" type="email" autoComplete="email" required value={form.email} onChange={set('email')} className="input-field" placeholder="analyst@argus.local" disabled={loading} />
            </div>
            <div>
              <label htmlFor="password" className="label">Password</label>
              <div className="relative">
                <input id="password" type={showPass ? 'text' : 'password'} autoComplete="new-password" required value={form.password} onChange={set('password')} className="input-field pr-10" placeholder="Min 12 chars, upper, lower, digit, symbol" disabled={loading} />
                <button type="button" onClick={() => setShowPass(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300" aria-label={showPass ? 'Hide' : 'Show'}>
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <div>
              <label htmlFor="confirm" className="label">Confirm password</label>
              <input id="confirm" type="password" autoComplete="new-password" required value={form.confirm} onChange={set('confirm')} className="input-field" placeholder="Repeat password" disabled={loading} />
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full justify-center py-2.5 mt-2">
              {loading ? <><div className="w-4 h-4 border-2 border-navy-950 border-t-transparent rounded-full animate-spin" />Creating account…</> : 'Create Account'}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-gray-500">
            Already have an account?{' '}
            <Link to="/login" className="text-cyber-cyan hover:text-cyan-300 transition-colors">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}

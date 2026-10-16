import { useState } from 'react'
import { Bell, Search, ChevronDown, LogOut, User, Shield } from 'lucide-react'
import { useAuth } from '../features/auth/AuthContext'
import clsx from 'clsx'

const ROLE_LABELS: Record<string, string> = {
  ADMIN:            'Administrator',
  SECURITY_ANALYST: 'Security Analyst',
  VIEWER:           'Viewer',
}

const ROLE_COLORS: Record<string, string> = {
  ADMIN:            'text-red-400',
  SECURITY_ANALYST: 'text-cyber-cyan',
  VIEWER:           'text-gray-400',
}

export function TopBar() {
  const { user, logout } = useAuth()
  const [profileOpen, setProfileOpen] = useState(false)
  const [searchValue, setSearchValue] = useState('')

  return (
    <header className="h-16 bg-navy-900 border-b border-charcoal-600 flex items-center px-4 gap-4 shrink-0">
      {/* Global search */}
      <div className="flex-1 max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
          <input
            type="search"
            placeholder="Search events, incidents, IPs…"
            value={searchValue}
            onChange={e => setSearchValue(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-charcoal-700 border border-charcoal-500 text-gray-200 
                       text-sm rounded-lg placeholder-gray-500 focus:outline-none focus:ring-1 
                       focus:ring-cyber-cyan focus:border-cyber-cyan transition-colors"
            aria-label="Global search"
          />
        </div>
      </div>

      <div className="flex items-center gap-2 ml-auto">
        {/* Notifications */}
        <button
          className="relative p-2 text-gray-400 hover:text-gray-200 hover:bg-charcoal-700 
                     rounded-lg transition-colors"
          aria-label="Notifications"
        >
          <Bell className="w-5 h-5" />
          {/* Unread dot */}
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" aria-hidden="true" />
        </button>

        {/* Profile menu */}
        <div className="relative">
          <button
            onClick={() => setProfileOpen(v => !v)}
            className="flex items-center gap-2 pl-2 pr-3 py-1.5 rounded-lg hover:bg-charcoal-700
                       transition-colors"
            aria-expanded={profileOpen}
            aria-haspopup="true"
          >
            <div className="w-8 h-8 rounded-full bg-charcoal-500 border border-charcoal-400
                            flex items-center justify-center shrink-0">
              <span className="text-sm font-semibold text-cyber-cyan">
                {user?.full_name?.[0]?.toUpperCase() ?? 'U'}
              </span>
            </div>
            <div className="hidden sm:block text-left">
              <p className="text-sm font-medium text-gray-200 leading-tight">{user?.full_name}</p>
              <p className={clsx('text-xs leading-tight', user ? ROLE_COLORS[user.role] : 'text-gray-400')}>
                {user ? ROLE_LABELS[user.role] : ''}
              </p>
            </div>
            <ChevronDown className={clsx('w-4 h-4 text-gray-400 transition-transform', profileOpen && 'rotate-180')} />
          </button>

          {profileOpen && (
            <>
              {/* Backdrop */}
              <div
                className="fixed inset-0 z-10"
                onClick={() => setProfileOpen(false)}
                aria-hidden="true"
              />
              <div className="absolute right-0 mt-1 w-52 bg-navy-800 border border-charcoal-600 
                              rounded-xl shadow-xl z-20 py-1 animate-fade-in">
                <div className="px-4 py-2.5 border-b border-charcoal-600">
                  <p className="text-sm font-medium text-gray-200 truncate">{user?.full_name}</p>
                  <p className="text-xs text-gray-500 truncate">{user?.email}</p>
                </div>
                <button
                  className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-gray-300
                             hover:bg-charcoal-700 hover:text-gray-100 transition-colors"
                  onClick={() => { setProfileOpen(false) }}
                >
                  <User className="w-4 h-4" />
                  Profile
                </button>
                <button
                  className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-gray-300
                             hover:bg-charcoal-700 hover:text-gray-100 transition-colors"
                  onClick={() => { setProfileOpen(false) }}
                >
                  <Shield className="w-4 h-4" />
                  Security
                </button>
                <div className="border-t border-charcoal-600 mt-1 pt-1">
                  <button
                    className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-red-400
                               hover:bg-red-500/10 hover:text-red-300 transition-colors"
                    onClick={() => { setProfileOpen(false); logout() }}
                  >
                    <LogOut className="w-4 h-4" />
                    Sign out
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  )
}

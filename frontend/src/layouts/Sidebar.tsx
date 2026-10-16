import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, ShieldAlert, Brain, AlertOctagon,
  ScanSearch, Server, Microscope, FileText,
  Settings, ChevronLeft, ChevronRight, Activity,
} from 'lucide-react'
import { Logo } from '../components/Logo'
import { useAuth } from '../features/auth/AuthContext'
import clsx from 'clsx'

interface NavItem {
  label: string
  path: string
  icon: React.ElementType
  roles?: string[]
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Overview',          path: '/dashboard',        icon: LayoutDashboard },
  { label: 'Security Events',   path: '/events',           icon: ShieldAlert },
  { label: 'Threat Intel',      path: '/intelligence',     icon: Brain },
  { label: 'Incidents',         path: '/incidents',        icon: AlertOctagon },
  { label: 'Detection Rules',   path: '/rules',            icon: ScanSearch, roles: ['ADMIN', 'SECURITY_ANALYST'] },
  { label: 'Assets',            path: '/assets',           icon: Server },
  { label: 'Investigations',    path: '/investigations',   icon: Microscope },
  { label: 'Reports',           path: '/reports',          icon: FileText },
  { label: 'System Settings',   path: '/settings',         icon: Settings, roles: ['ADMIN'] },
]

interface Props {
  collapsed: boolean
  onToggle: () => void
}

export function Sidebar({ collapsed, onToggle }: Props) {
  const { user } = useAuth()

  const visibleItems = NAV_ITEMS.filter(item =>
    !item.roles || (user && item.roles.includes(user.role))
  )

  return (
    <aside
      className={clsx(
        'flex flex-col bg-navy-900 border-r border-charcoal-600 transition-all duration-300 shrink-0',
        collapsed ? 'w-16' : 'w-60',
      )}
      aria-label="Main navigation"
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b border-charcoal-600 shrink-0">
        {collapsed ? (
          <Logo size="sm" showText={false} />
        ) : (
          <Logo size="sm" showText />
        )}
      </div>

      {/* Nav links */}
      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-0.5">
        {visibleItems.map(({ label, path, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            title={collapsed ? label : undefined}
            className={({ isActive }) =>
              clsx(
                'sidebar-link',
                isActive && 'active',
                collapsed && 'justify-center px-0',
              )
            }
          >
            <Icon className="w-5 h-5 shrink-0" aria-hidden="true" />
            {!collapsed && <span className="truncate">{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* System status indicator */}
      {!collapsed && (
        <div className="px-3 pb-3">
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-charcoal-700/50 border border-charcoal-600">
            <Activity className="w-3.5 h-3.5 text-cyber-green shrink-0" />
            <span className="text-xs text-gray-400">Systems Nominal</span>
            <div className="ml-auto w-2 h-2 rounded-full bg-cyber-green animate-pulse-slow" />
          </div>
        </div>
      )}

      {/* Collapse toggle */}
      <button
        onClick={onToggle}
        className="flex items-center justify-center h-10 border-t border-charcoal-600 text-gray-500
                   hover:text-gray-300 hover:bg-charcoal-700/50 transition-colors"
        aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {collapsed ? (
          <ChevronRight className="w-4 h-4" />
        ) : (
          <ChevronLeft className="w-4 h-4" />
        )}
      </button>
    </aside>
  )
}

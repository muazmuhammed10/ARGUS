import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ShieldAlert, AlertOctagon, CheckCircle2, Activity,
  TrendingUp, Eye, Wifi, Clock, Server, Microscope,
} from 'lucide-react'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from 'recharts'
import { dashboardService } from '../services/dashboard.service'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorAlert } from '../components/ErrorAlert'
import { PageHeader } from '../components/PageHeader'
import { format } from 'date-fns'

const PIE_COLORS: Record<string, string> = {
  AUTHENTICATION: '#00d4ff',
  NETWORK: '#f97316',
  PRIVILEGE_ESCALATION: '#ef4444',
  POLICY_VIOLATION: '#eab308',
  SYSTEM: '#8b5cf6',
  ENDPOINT: '#22c55e',
  AUTHORIZATION: '#06b6d4',
  MALWARE: '#dc2626',
  OTHER: '#6b7280',
}

interface StatCardProps {
  label: string
  value: number | string
  icon: React.ElementType
  color: string
  subtext?: string
}

function StatCard({ label, value, icon: Icon, color, subtext }: StatCardProps) {
  return (
    <div className="card hover:border-charcoal-500 transition-colors">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">{label}</p>
          <p className={`text-3xl font-bold ${color}`}>{value}</p>
          {subtext && <p className="text-xs text-gray-500 mt-1">{subtext}</p>}
        </div>
        <div className="p-2.5 rounded-lg bg-charcoal-700">
          <Icon className={`w-5 h-5 ${color}`} />
        </div>
      </div>
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload) return null
  return (
    <div className="bg-navy-800 border border-charcoal-500 rounded-lg p-3 text-xs shadow-xl">
      <p className="text-gray-400 font-medium mb-2">{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.color }} className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full inline-block" style={{ background: p.color }} />
          {p.name}: <span className="font-semibold text-gray-200">{p.value}</span>
        </p>
      ))}
    </div>
  )
}

export default function DashboardPage() {
  const [days, setDays] = useState(7)

  const summaryQuery = useQuery({
    queryKey: ['dashboard-summary', days],
    queryFn: () => dashboardService.getSummary(days),
    refetchInterval: 30_000,
  })

  const trendsQuery = useQuery({
    queryKey: ['dashboard-trends', days],
    queryFn: () => dashboardService.getTrends(days),
    refetchInterval: 60_000,
  })

  const alertsQuery = useQuery({
    queryKey: ['dashboard-alerts'],
    queryFn: () => dashboardService.getRecentAlerts(8),
    refetchInterval: 30_000,
  })

  const summary = summaryQuery.data
  const trends = trendsQuery.data
  const recentAlerts = alertsQuery.data?.items ?? []

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        title="Security Overview"
        subtitle={`Live metrics · Updated ${format(new Date(), 'HH:mm:ss')}`}
        breadcrumbs={[{ label: 'Overview' }]}
        actions={
          <div className="flex items-center gap-3">
            <select
              value={days}
              onChange={e => setDays(Number(e.target.value))}
              className="input-field w-36 text-sm"
              aria-label="Time range"
            >
              <option value={1}>Last 24h</option>
              <option value={7}>Last 7 days</option>
              <option value={14}>Last 14 days</option>
              <option value={30}>Last 30 days</option>
            </select>
          </div>
        }
      />

      {summaryQuery.isLoading && <LoadingSpinner label="Loading dashboard…" />}
      {summaryQuery.isError && (
        <ErrorAlert title="Dashboard error" message={(summaryQuery.error as Error)?.message ?? 'Failed to load metrics.'} />
      )}

      {summary && (
        <>
          {/* Stat Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
            <StatCard label="Total Events"      value={summary.total_events}      icon={Activity}     color="text-cyber-cyan"   subtext="All time" />
            <StatCard label="Critical"          value={summary.critical_events}   icon={ShieldAlert}  color="text-red-400"      subtext={`Last ${days}d`} />
            <StatCard label="High"              value={summary.high_events}       icon={TrendingUp}   color="text-orange-400"   subtext={`Last ${days}d`} />
            <StatCard label="Open Incidents"    value={summary.open_incidents}    icon={AlertOctagon} color="text-yellow-400"   subtext="Needs triage" />
            <StatCard label="Resolved"          value={summary.resolved_incidents}icon={CheckCircle2} color="text-green-400"    subtext="Closed out" />
            <StatCard label="Open Alerts"       value={summary.open_alerts}       icon={Eye}          color="text-purple-400"   subtext="Unacknowledged" />
          </div>

          {/* Secondary metrics */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Unique Source IPs"      value={summary.unique_source_ips}      icon={Wifi}       color="text-cyan-400"   subtext={`Last ${days}d`} />
            <StatCard label="Auth Failures"          value={summary.auth_failures}          icon={ShieldAlert} color="text-red-300"   subtext={`Last ${days}d`} />
            <StatCard label="Active Investigations"  value={summary.active_investigations}  icon={Microscope} color="text-blue-400"   subtext="Open / In Progress" />
            <StatCard label="Total Assets"           value={summary.total_assets}           icon={Server}     color="text-green-300" subtext="Monitored" />
          </div>
        </>
      )}

      {/* Charts */}
      {trends && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          {/* Trend chart */}
          <div className="card xl:col-span-2">
            <div className="card-header">
              <h2 className="section-title">Event Trend — Last {days} Days</h2>
              <span className="text-xs text-gray-500">{trends.trend_data.length} days with data</span>
            </div>
            {trends.trend_data.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-12">No event data in this time range. Ingest events to see trends.</p>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={trends.trend_data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    {['crit','high','med'].map((k, i) => (
                      <linearGradient key={k} id={`grad${k}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={['#ef4444','#f97316','#eab308'][i]} stopOpacity={0.3} />
                        <stop offset="95%" stopColor={['#ef4444','#f97316','#eab308'][i]} stopOpacity={0} />
                      </linearGradient>
                    ))}
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2d374d" />
                  <XAxis dataKey="day" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false}
                    tickFormatter={v => v.slice(5)} />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="critical" name="Critical" stroke="#ef4444" fill="url(#gradcrit)" strokeWidth={2} />
                  <Area type="monotone" dataKey="high"     name="High"     stroke="#f97316" fill="url(#gradhigh)" strokeWidth={2} />
                  <Area type="monotone" dataKey="medium"   name="Medium"   stroke="#eab308" fill="url(#gradmed)"  strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Event type pie */}
          <div className="card">
            <div className="card-header">
              <h2 className="section-title">Events by Type</h2>
            </div>
            {trends.event_type_distribution.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-12">No data</p>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={trends.event_type_distribution.map(d => ({ name: d.type, value: d.count }))}
                    cx="50%" cy="45%" innerRadius={55} outerRadius={80} paddingAngle={3} dataKey="value">
                    {trends.event_type_distribution.map((d, i) => (
                      <Cell key={i} fill={PIE_COLORS[d.type] ?? '#6b7280'} stroke="transparent" />
                    ))}
                  </Pie>
                  <Legend formatter={v => <span style={{ color: '#9ca3af', fontSize: 10 }}>{v}</span>} iconSize={8} iconType="circle" />
                  <Tooltip
                    formatter={(v: number) => [v, 'Events']}
                    contentStyle={{ background: '#111c2d', border: '1px solid #2d374d', borderRadius: 8, fontSize: 12 }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      )}

      {/* Recent Alerts */}
      <div className="card">
        <div className="card-header">
          <h2 className="section-title">Recent Open Alerts</h2>
          <Clock className="w-4 h-4 text-gray-500" />
        </div>
        {recentAlerts.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-8">No open alerts. System is quiet.</p>
        ) : (
          <div className="space-y-3">
            {recentAlerts.map((alert: any) => (
              <div key={alert.id} className="flex items-start gap-3 text-sm">
                <div className={`w-2 h-2 rounded-full shrink-0 mt-1.5 ${
                  alert.severity === 'CRITICAL' ? 'bg-red-500' :
                  alert.severity === 'HIGH' ? 'bg-orange-500' :
                  alert.severity === 'MEDIUM' ? 'bg-yellow-500' : 'bg-blue-500'
                }`} />
                <div className="flex-1 min-w-0">
                  <p className="text-gray-300 truncate">{alert.title}</p>
                  <p className="text-xs text-gray-500">{alert.severity} · {alert.status}</p>
                </div>
                <span className="text-xs text-gray-500 shrink-0">
                  {format(new Date(alert.created_at), 'MMM d, HH:mm')}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

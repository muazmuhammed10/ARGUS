import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus, Search, RefreshCw, AlertOctagon } from 'lucide-react'
import { incidentsService } from '../services/incidents.service'
import { PageHeader } from '../components/PageHeader'
import { SeverityBadge } from '../components/SeverityBadge'
import { StatusBadge } from '../components/StatusBadge'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { EmptyState } from '../components/EmptyState'
import { ErrorAlert } from '../components/ErrorAlert'
import { useAuth } from '../features/auth/AuthContext'
import { format } from 'date-fns'
import type { Incident } from '../types'

const STATUS_OPTIONS = ['NEW', 'TRIAGED', 'INVESTIGATING', 'CONTAINED', 'RESOLVED', 'CLOSED']
const SEVERITY_OPTIONS = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']

export default function IncidentsPage() {
  const [search,   setSearch]   = useState('')
  const [status,   setStatus]   = useState('')
  const [severity, setSeverity] = useState('')
  const { hasRole } = useAuth()

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['incidents', { search, status, severity }],
    queryFn: () => incidentsService.getIncidents({ search, status, severity }),
  })

  const incidents: Incident[] = (data as any)?.items ?? []
  const total: number         = (data as any)?.total ?? 0

  return (
    <div className="space-y-5 animate-fade-in">
      <PageHeader
        title="Incidents"
        subtitle={`${total} total incident${total !== 1 ? 's' : ''}`}
        breadcrumbs={[{ label: 'Incidents' }]}
        actions={
          <div className="flex gap-2">
            <button onClick={() => refetch()} disabled={isFetching} className="btn-secondary">
              <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
            </button>
            {hasRole('ADMIN', 'SECURITY_ANALYST') && (
              <button className="btn-primary">
                <Plus className="w-4 h-4" />
                New Incident
              </button>
            )}
          </div>
        }
      />

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-48">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
            <input
              type="search"
              placeholder="Search incidents…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="input-field pl-9"
            />
          </div>
          <select value={status} onChange={e => setStatus(e.target.value)} className="input-field w-44">
            <option value="">All Statuses</option>
            {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
          </select>
          <select value={severity} onChange={e => setSeverity(e.target.value)} className="input-field w-40">
            <option value="">All Severities</option>
            {SEVERITY_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>

      {isError && (
        <ErrorAlert title="Failed to load incidents" message={(error as Error)?.message ?? 'Unknown error'} />
      )}

      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <LoadingSpinner label="Loading incidents…" />
        ) : incidents.length === 0 ? (
          <EmptyState
            icon={AlertOctagon}
            title="No incidents found"
            description="No incidents match the current filters."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="table-base">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Title</th>
                  <th>Severity</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Updated</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {incidents.map(inc => (
                  <tr key={inc.id}>
                    <td className="font-mono text-xs text-gray-500">{inc.id.slice(0, 8)}…</td>
                    <td className="max-w-sm">
                      <p className="text-sm font-medium text-gray-200 truncate">{inc.title}</p>
                      <p className="text-xs text-gray-500 truncate mt-0.5">{inc.description}</p>
                    </td>
                    <td><SeverityBadge severity={inc.severity} /></td>
                    <td><StatusBadge status={inc.status} /></td>
                    <td className="text-xs text-gray-400 whitespace-nowrap">
                      {format(new Date(inc.created_at), 'MMM d, HH:mm')}
                    </td>
                    <td className="text-xs text-gray-400 whitespace-nowrap">
                      {format(new Date(inc.updated_at), 'MMM d, HH:mm')}
                    </td>
                    <td>
                      <button className="text-xs text-cyber-cyan hover:text-cyan-300 transition-colors">
                        View →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

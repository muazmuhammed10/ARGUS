import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Filter, RefreshCw, Download } from 'lucide-react'
import { eventsService } from '../services/events.service'
import { PageHeader } from '../components/PageHeader'
import { SeverityBadge } from '../components/SeverityBadge'
import { StatusBadge } from '../components/StatusBadge'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { EmptyState } from '../components/EmptyState'
import { ErrorAlert } from '../components/ErrorAlert'
import { format } from 'date-fns'
import type { SecurityEvent, Severity, EventType } from '../types'
import { ShieldAlert } from 'lucide-react'

const SEVERITIES: Severity[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
const EVENT_TYPES: EventType[] = [
  'AUTHENTICATION', 'AUTHORIZATION', 'NETWORK', 'ENDPOINT',
  'MALWARE', 'POLICY_VIOLATION', 'PRIVILEGE_ESCALATION', 'SYSTEM', 'OTHER',
]

export default function EventsPage() {
  const [search,   setSearch]   = useState('')
  const [severity, setSeverity] = useState('')
  const [evType,   setEvType]   = useState('')
  const [page,     setPage]     = useState(1)

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['events', { search, severity, evType, page }],
    queryFn: () => eventsService.getEvents({
      page,
      page_size: 20,
      severity:   severity || undefined,
      event_type: evType   || undefined,
      search:     search   || undefined,
    }),
  })

  const events: SecurityEvent[] = (data as any)?.items ?? []
  const total: number           = (data as any)?.total ?? 0

  return (
    <div className="space-y-5 animate-fade-in">
      <PageHeader
        title="Security Events"
        subtitle="Normalized events from all monitored sources"
        breadcrumbs={[{ label: 'Security Events' }]}
        actions={
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="btn-secondary gap-2"
            aria-label="Refresh events"
          >
            <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        }
      />

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-48">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
            <input
              type="search"
              placeholder="Search IP, hostname, username, description…"
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1) }}
              className="input-field pl-9"
              aria-label="Search events"
            />
          </div>
          <select
            value={severity}
            onChange={e => { setSeverity(e.target.value); setPage(1) }}
            className="input-field w-40"
            aria-label="Filter by severity"
          >
            <option value="">All Severities</option>
            {SEVERITIES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <select
            value={evType}
            onChange={e => { setEvType(e.target.value); setPage(1) }}
            className="input-field w-48"
            aria-label="Filter by event type"
          >
            <option value="">All Event Types</option>
            {EVENT_TYPES.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
          </select>
          <div className="flex items-center gap-1.5 text-xs text-gray-400 px-2">
            <Filter className="w-3.5 h-3.5" />
            {total} result{total !== 1 ? 's' : ''}
          </div>
        </div>
      </div>

      {isError && (
        <ErrorAlert title="Failed to load events" message={(error as Error)?.message ?? 'Unknown error'} />
      )}

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <LoadingSpinner label="Loading events…" />
        ) : events.length === 0 ? (
          <EmptyState
            icon={ShieldAlert}
            title="No events found"
            description="Try adjusting your filters or run the seed script to generate synthetic data."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="table-base">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Severity</th>
                  <th>Type</th>
                  <th>Source</th>
                  <th>Source IP</th>
                  <th>Username</th>
                  <th>Description</th>
                  <th>Status</th>
                  <th>Synthetic</th>
                </tr>
              </thead>
              <tbody>
                {events.map(ev => (
                  <tr key={ev.id}>
                    <td className="font-mono text-xs text-gray-400 whitespace-nowrap">
                      {format(new Date(ev.timestamp), 'yyyy-MM-dd HH:mm:ss')}
                    </td>
                    <td><SeverityBadge severity={ev.severity} /></td>
                    <td className="text-xs text-gray-400 whitespace-nowrap">
                      {ev.event_type.replace(/_/g, ' ')}
                    </td>
                    <td className="text-xs text-gray-400 max-w-32 truncate">{ev.source_system}</td>
                    <td className="font-mono text-xs text-cyan-400">{ev.source_ip ?? '—'}</td>
                    <td className="text-xs">{ev.username ?? '—'}</td>
                    <td className="max-w-xs">
                      <p className="text-xs text-gray-300 truncate" title={ev.description}>
                        {ev.description}
                      </p>
                    </td>
                    <td><StatusBadge status={ev.detection_status} /></td>
                    <td>
                      {ev.is_synthetic && (
                        <span className="text-xs text-yellow-500 font-mono">[SYN]</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {total > 20 && (
        <div className="flex items-center justify-between text-sm text-gray-400">
          <span>Page {page} · {total} total events</span>
          <div className="flex gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(p => p - 1)}
              className="btn-secondary px-3 py-1.5 text-xs disabled:opacity-40"
            >
              ← Prev
            </button>
            <button
              disabled={page * 20 >= total}
              onClick={() => setPage(p => p + 1)}
              className="btn-secondary px-3 py-1.5 text-xs disabled:opacity-40"
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

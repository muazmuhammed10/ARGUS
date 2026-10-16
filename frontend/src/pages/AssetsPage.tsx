import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Server, Plus, Search, RefreshCw } from 'lucide-react'
import apiClient from '../services/api'
import { PageHeader } from '../components/PageHeader'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { EmptyState } from '../components/EmptyState'
import { ErrorAlert } from '../components/ErrorAlert'
import { StatusBadge } from '../components/StatusBadge'
import { SeverityBadge } from '../components/SeverityBadge'
import { useAuth } from '../features/auth/AuthContext'
import type { Asset } from '../types'
import { format } from 'date-fns'

export default function AssetsPage() {
  const [search, setSearch] = useState('')
  const [env,    setEnv]    = useState('')
  const { hasRole } = useAuth()

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['assets', { search, env }],
    queryFn: async () => {
      const { data } = await apiClient.get('/assets', { params: { search, environment: env } })
      return data
    },
  })

  const assets: Asset[] = (data as any)?.items ?? []

  return (
    <div className="space-y-5 animate-fade-in">
      <PageHeader
        title="Asset Inventory"
        subtitle="Monitored systems and their security status"
        breadcrumbs={[{ label: 'Assets' }]}
        actions={
          <div className="flex gap-2">
            <button onClick={() => refetch()} disabled={isFetching} className="btn-secondary">
              <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
            </button>
            {hasRole('ADMIN', 'SECURITY_ANALYST') && (
              <button className="btn-primary"><Plus className="w-4 h-4" />Add Asset</button>
            )}
          </div>
        }
      />

      <div className="card p-4">
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-48">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
            <input type="search" placeholder="Search assets by name, IP, hostname…" value={search} onChange={e => setSearch(e.target.value)} className="input-field pl-9" />
          </div>
          <select value={env} onChange={e => setEnv(e.target.value)} className="input-field w-44">
            <option value="">All Environments</option>
            {['PRODUCTION','STAGING','DEVELOPMENT','CORPORATE','DMZ'].map(e => (
              <option key={e} value={e}>{e}</option>
            ))}
          </select>
        </div>
      </div>

      {isError && <ErrorAlert title="Failed to load assets" message={(error as Error)?.message ?? 'Unknown error'} />}

      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <LoadingSpinner label="Loading assets…" />
        ) : assets.length === 0 ? (
          <EmptyState icon={Server} title="No assets found" description="Add assets manually or run the seed script." />
        ) : (
          <div className="overflow-x-auto">
            <table className="table-base">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Hostname</th>
                  <th>IP Address</th>
                  <th>OS</th>
                  <th>Environment</th>
                  <th>Criticality</th>
                  <th>Owner</th>
                  <th>Last Seen</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {assets.map(a => (
                  <tr key={a.id}>
                    <td className="font-medium text-gray-200">{a.name}</td>
                    <td className="font-mono text-xs text-gray-400">{a.hostname ?? '—'}</td>
                    <td className="font-mono text-xs text-cyan-400">{a.ip_address ?? '—'}</td>
                    <td className="text-xs text-gray-400">{a.operating_system ?? '—'}</td>
                    <td><span className="text-xs text-gray-300 font-mono">{a.environment}</span></td>
                    <td><SeverityBadge severity={a.criticality as any} /></td>
                    <td className="text-xs text-gray-400">{a.owner ?? '—'}</td>
                    <td className="text-xs text-gray-400 whitespace-nowrap">
                      {a.last_seen_at ? format(new Date(a.last_seen_at), 'MMM d, HH:mm') : '—'}
                    </td>
                    <td><StatusBadge status={a.monitoring_status} /></td>
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

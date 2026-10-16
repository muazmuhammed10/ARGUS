import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Brain, Search, Plus, ExternalLink, CheckCircle, XCircle, HelpCircle } from 'lucide-react'
import apiClient from '../services/api'
import { PageHeader } from '../components/PageHeader'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { EmptyState } from '../components/EmptyState'
import { ErrorAlert } from '../components/ErrorAlert'
import { StatusBadge } from '../components/StatusBadge'
import type { Indicator } from '../types'
import { format } from 'date-fns'

const TYPE_COLORS: Record<string, string> = {
  IPV4: 'text-cyan-400', IPV6: 'text-cyan-400',
  DOMAIN: 'text-purple-400', URL: 'text-blue-400',
  MD5: 'text-yellow-400', SHA1: 'text-yellow-400', SHA256: 'text-yellow-400',
  EMAIL: 'text-green-400', CVE: 'text-red-400',
}

function ReputationIcon({ isM }: { isM: boolean | null }) {
  if (isM === true)  return <XCircle className="w-4 h-4 text-red-400" />
  if (isM === false) return <CheckCircle className="w-4 h-4 text-green-400" />
  return <HelpCircle className="w-4 h-4 text-gray-500" />
}

export default function ThreatIntelPage() {
  const [search, setSearch]     = useState('')
  const [lookupVal, setLookup]  = useState('')
  const [lookupType, setLType]  = useState('IPV4')
  const [lookupErr, setLErr]    = useState('')
  const qc = useQueryClient()

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['indicators', search],
    queryFn: async () => {
      const { data } = await apiClient.get('/intelligence', { params: { search } })
      return data
    },
  })

  const lookup = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post('/intelligence/lookup', {
        value: lookupVal.trim(), indicator_type: lookupType,
      })
      return data
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['indicators'] }); setLookup(''); setLErr('') },
    onError: (e: any) => setLErr(e?.response?.data?.detail ?? 'Lookup failed'),
  })

  const indicators: Indicator[] = (data as any)?.items ?? []

  return (
    <div className="space-y-5 animate-fade-in">
      <PageHeader
        title="Threat Intelligence"
        subtitle="IOC lookup, reputation analysis, and indicator management"
        breadcrumbs={[{ label: 'Threat Intel' }]}
      />

      {/* IOC Lookup panel */}
      <div className="card">
        <h2 className="section-title mb-4">IOC Lookup</h2>
        <div className="flex flex-wrap gap-3">
          <select value={lookupType} onChange={e => setLType(e.target.value)} className="input-field w-36">
            {['IPV4','IPV6','DOMAIN','URL','MD5','SHA1','SHA256','EMAIL','CVE'].map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Enter IP, domain, hash, URL…"
            value={lookupVal}
            onChange={e => setLookup(e.target.value)}
            className="input-field flex-1 min-w-48"
            onKeyDown={e => e.key === 'Enter' && lookupVal && lookup.mutate()}
          />
          <button
            onClick={() => lookup.mutate()}
            disabled={!lookupVal.trim() || lookup.isPending}
            className="btn-primary"
          >
            {lookup.isPending ? (
              <><div className="w-4 h-4 border-2 border-navy-950 border-t-transparent rounded-full animate-spin" />Looking up…</>
            ) : (
              <><Search className="w-4 h-4" />Look Up</>
            )}
          </button>
        </div>
        {lookupErr && <p className="text-sm text-red-400 mt-2">{lookupErr}</p>}

        {/* Provider status */}
        <div className="mt-3 p-3 bg-charcoal-700/50 border border-charcoal-500 rounded-lg">
          <p className="text-xs text-gray-500">
            <span className="text-yellow-400 font-semibold">External enrichment:</span>{' '}
            Not configured. Set <code className="font-mono text-cyan-400">VIRUSTOTAL_API_KEY</code> in{' '}
            <code className="font-mono text-cyan-400">.env</code> to enable live reputation lookups.
            Internal IOC matching is always active.
          </p>
        </div>
      </div>

      {/* IOC table */}
      <div className="card p-4">
        <div className="flex items-center gap-3 mb-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
            <input type="search" placeholder="Filter indicators…" value={search}
              onChange={e => setSearch(e.target.value)} className="input-field pl-9" />
          </div>
        </div>

        {isError && <ErrorAlert title="Failed to load indicators" message={(error as Error)?.message ?? 'Unknown'} />}

        {isLoading ? (
          <LoadingSpinner label="Loading indicators…" />
        ) : indicators.length === 0 ? (
          <EmptyState icon={Brain} title="No indicators" description="Use the lookup above to add IOCs, or run the seed script." />
        ) : (
          <div className="overflow-x-auto">
            <table className="table-base">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Value</th>
                  <th>Malicious</th>
                  <th>Confidence</th>
                  <th>Source</th>
                  <th>Tags</th>
                  <th>Last Seen</th>
                </tr>
              </thead>
              <tbody>
                {indicators.map((ind: Indicator) => (
                  <tr key={ind.id}>
                    <td><span className={`font-mono text-xs font-bold ${TYPE_COLORS[ind.indicator_type] ?? 'text-gray-400'}`}>{ind.indicator_type}</span></td>
                    <td className="font-mono text-xs text-gray-200 max-w-xs truncate" title={ind.value}>{ind.value}</td>
                    <td><ReputationIcon isM={ind.is_malicious} /></td>
                    <td className="text-xs text-gray-400">
                      {ind.confidence != null ? `${(ind.confidence * 100).toFixed(0)}%` : '—'}
                    </td>
                    <td className="text-xs text-gray-400">{ind.source ?? '—'}</td>
                    <td className="text-xs text-gray-400">{ind.tags ?? '—'}</td>
                    <td className="text-xs text-gray-400 whitespace-nowrap">
                      {ind.last_seen_at ? format(new Date(ind.last_seen_at), 'MMM d, HH:mm') : '—'}
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

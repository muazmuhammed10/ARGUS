import { useQuery } from '@tanstack/react-query'
import { ScanSearch, ToggleLeft, ToggleRight, RefreshCw } from 'lucide-react'
import apiClient from '../services/api'
import { PageHeader } from '../components/PageHeader'
import { SeverityBadge } from '../components/SeverityBadge'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { EmptyState } from '../components/EmptyState'
import { ErrorAlert } from '../components/ErrorAlert'
import { useAuth } from '../features/auth/AuthContext'
import type { DetectionRule } from '../types'
import { format } from 'date-fns'

export default function DetectionRulesPage() {
  const { hasRole } = useAuth()

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['detection-rules'],
    queryFn: async () => {
      const { data } = await apiClient.get('/rules')
      return data
    },
  })

  const rules: DetectionRule[] = (data as any)?.items ?? []

  return (
    <div className="space-y-5 animate-fade-in">
      <PageHeader
        title="Detection Rules"
        subtitle="Configure and manage the threat detection engine"
        breadcrumbs={[{ label: 'Detection Rules' }]}
        actions={
          <button onClick={() => refetch()} disabled={isFetching} className="btn-secondary">
            <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        }
      />

      {/* Info banner */}
      <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl text-sm text-blue-300">
        <p className="font-semibold mb-1">Detection Engine — Rule-based, Explainable</p>
        <p className="text-blue-400 text-xs">
          Rules evaluate normalized events against configurable thresholds. Each alert references the
          rule that triggered it and the supporting evidence. Full detection engine wired in Phase 3.
        </p>
      </div>

      {isError && <ErrorAlert title="Failed to load rules" message={(error as Error)?.message ?? 'Unknown error'} />}

      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <LoadingSpinner label="Loading detection rules…" />
        ) : rules.length === 0 ? (
          <EmptyState
            icon={ScanSearch}
            title="No detection rules"
            description="Run the seed script to create the default rule set."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="table-base">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Rule Name</th>
                  <th>Category</th>
                  <th>Severity</th>
                  <th>Threshold</th>
                  <th>Window</th>
                  <th>Rule Key</th>
                  <th>Updated</th>
                  {hasRole('ADMIN') && <th>Actions</th>}
                </tr>
              </thead>
              <tbody>
                {rules.map((rule: DetectionRule) => (
                  <tr key={rule.id}>
                    <td>
                      {rule.is_enabled ? (
                        <span className="flex items-center gap-1.5 text-green-400 text-xs">
                          <ToggleRight className="w-4 h-4" /> Enabled
                        </span>
                      ) : (
                        <span className="flex items-center gap-1.5 text-gray-500 text-xs">
                          <ToggleLeft className="w-4 h-4" /> Disabled
                        </span>
                      )}
                    </td>
                    <td>
                      <p className="text-sm font-medium text-gray-200">{rule.name}</p>
                      <p className="text-xs text-gray-500 max-w-xs truncate mt-0.5">{rule.description}</p>
                    </td>
                    <td className="text-xs text-gray-400">{rule.category.replace(/_/g, ' ')}</td>
                    <td><SeverityBadge severity={rule.severity} /></td>
                    <td className="text-xs font-mono text-cyan-400">{rule.threshold_count} events</td>
                    <td className="text-xs font-mono text-gray-400">{rule.threshold_window_seconds}s</td>
                    <td className="font-mono text-xs text-purple-400">{rule.rule_key}</td>
                    <td className="text-xs text-gray-400 whitespace-nowrap">
                      {format(new Date(rule.updated_at), 'MMM d, HH:mm')}
                    </td>
                    {hasRole('ADMIN') && (
                      <td>
                        <button className="text-xs text-cyber-cyan hover:text-cyan-300 transition-colors">
                          Edit
                        </button>
                      </td>
                    )}
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

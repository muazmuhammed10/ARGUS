import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Microscope, Plus, Search, RefreshCw, X } from 'lucide-react'
import { investigationsService } from '../services/investigations.service'
import { PageHeader } from '../components/PageHeader'
import { StatusBadge } from '../components/StatusBadge'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { EmptyState } from '../components/EmptyState'
import { ErrorAlert } from '../components/ErrorAlert'
import { useAuth } from '../features/auth/AuthContext'
import type { Investigation } from '../types'
import { format } from 'date-fns'

export default function InvestigationsPage() {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ title: '', description: '', hypothesis: '' })
  const [formError, setFormError] = useState('')
  const { hasRole } = useAuth()
  const qc = useQueryClient()

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['investigations', { search, status }],
    queryFn: () => investigationsService.getInvestigations({ search: search || undefined, status: status || undefined }),
  })

  const createMutation = useMutation({
    mutationFn: () => investigationsService.createInvestigation({
      title: form.title,
      description: form.description || undefined,
      hypothesis: form.hypothesis || undefined,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['investigations'] })
      setShowCreate(false)
      setForm({ title: '', description: '', hypothesis: '' })
      setFormError('')
    },
    onError: (e: any) => setFormError(e?.response?.data?.detail ?? 'Failed to create investigation'),
  })

  const investigations: Investigation[] = (data as any)?.items ?? []
  const total = (data as any)?.total ?? 0

  return (
    <div className="space-y-5 animate-fade-in">
      <PageHeader
        title="Investigations"
        subtitle={`${total} investigation${total !== 1 ? 's' : ''}`}
        breadcrumbs={[{ label: 'Investigations' }]}
        actions={
          <div className="flex gap-2">
            <button onClick={() => refetch()} disabled={isFetching} className="btn-secondary">
              <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
            </button>
            {hasRole('ADMIN', 'SECURITY_ANALYST') && (
              <button onClick={() => setShowCreate(true)} className="btn-primary">
                <Plus className="w-4 h-4" />Start Investigation
              </button>
            )}
          </div>
        }
      />

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="bg-navy-800 border border-charcoal-500 rounded-xl w-full max-w-lg shadow-2xl">
            <div className="flex items-center justify-between p-5 border-b border-charcoal-600">
              <h2 className="text-lg font-semibold text-gray-200">Start New Investigation</h2>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-200"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-5 space-y-4">
              {formError && <ErrorAlert message={formError} onDismiss={() => setFormError('')} />}
              <div>
                <label className="label">Title *</label>
                <input className="input-field" value={form.title}
                  onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
                  placeholder="Investigation title…" />
              </div>
              <div>
                <label className="label">Description</label>
                <textarea className="input-field min-h-20 resize-none" value={form.description}
                  onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                  placeholder="Initial context and scope…" />
              </div>
              <div>
                <label className="label">Initial Hypothesis</label>
                <textarea className="input-field min-h-16 resize-none" value={form.hypothesis}
                  onChange={e => setForm(f => ({ ...f, hypothesis: e.target.value }))}
                  placeholder="What do you think happened?" />
              </div>
            </div>
            <div className="flex justify-end gap-3 p-5 border-t border-charcoal-600">
              <button onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
              <button
                onClick={() => createMutation.mutate()}
                disabled={!form.title.trim() || createMutation.isPending}
                className="btn-primary"
              >
                {createMutation.isPending ? 'Creating…' : 'Start Investigation'}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="card p-4">
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-48">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
            <input type="search" placeholder="Search investigations…" value={search}
              onChange={e => setSearch(e.target.value)} className="input-field pl-9" />
          </div>
          <select value={status} onChange={e => setStatus(e.target.value)} className="input-field w-44">
            <option value="">All Statuses</option>
            {['OPEN', 'IN_PROGRESS', 'ON_HOLD', 'CLOSED'].map(s => (
              <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
            ))}
          </select>
        </div>
      </div>

      {isError && <ErrorAlert title="Failed to load investigations" message={(error as Error)?.message ?? 'Unknown'} />}

      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <LoadingSpinner label="Loading investigations…" />
        ) : investigations.length === 0 ? (
          <EmptyState icon={Microscope} title="No investigations"
            description="Start an investigation to track threat analysis and findings."
            action={hasRole('ADMIN', 'SECURITY_ANALYST') ? (
              <button onClick={() => setShowCreate(true)} className="btn-primary text-sm">
                <Plus className="w-4 h-4" />Start Investigation
              </button>
            ) : undefined}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="table-base">
              <thead>
                <tr><th>Title</th><th>Status</th><th>Assigned</th><th>Created</th><th>Updated</th></tr>
              </thead>
              <tbody>
                {investigations.map((inv: Investigation) => (
                  <tr key={inv.id}>
                    <td>
                      <p className="text-sm font-medium text-gray-200">{inv.title}</p>
                      {inv.description && <p className="text-xs text-gray-500 truncate max-w-xs mt-0.5">{inv.description}</p>}
                    </td>
                    <td><StatusBadge status={inv.status} /></td>
                    <td className="text-xs text-gray-400">{inv.assigned_to_id ? 'Assigned' : 'Unassigned'}</td>
                    <td className="text-xs text-gray-400 whitespace-nowrap">{format(new Date(inv.created_at), 'MMM d, HH:mm')}</td>
                    <td className="text-xs text-gray-400 whitespace-nowrap">{format(new Date(inv.updated_at), 'MMM d, HH:mm')}</td>
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

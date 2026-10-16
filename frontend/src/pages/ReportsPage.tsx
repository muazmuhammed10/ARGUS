import { FileText, Download, BarChart2, ShieldAlert, Microscope, Server, ScanSearch } from 'lucide-react'
import { PageHeader } from '../components/PageHeader'
import { useAuth } from '../features/auth/AuthContext'

const REPORT_TYPES = [
  {
    id: 'security_event_summary',
    title: 'Security Event Summary',
    description: 'Aggregated view of all security events with severity breakdown and trend analysis.',
    icon: ShieldAlert,
    color: 'text-cyan-400',
    formats: ['CSV', 'JSON', 'HTML'],
  },
  {
    id: 'incident_investigation',
    title: 'Incident Investigation Report',
    description: 'Full incident timeline, evidence, investigation notes, and remediation actions.',
    icon: Microscope,
    color: 'text-purple-400',
    formats: ['JSON', 'HTML'],
  },
  {
    id: 'threat_intelligence',
    title: 'Threat Intelligence Report',
    description: 'IOC catalogue, reputation results, and analyst assessments.',
    icon: BarChart2,
    color: 'text-yellow-400',
    formats: ['CSV', 'JSON'],
  },
  {
    id: 'detection_activity',
    title: 'Detection Rule Activity',
    description: 'Rule trigger frequency, false positive rates, and threshold recommendations.',
    icon: ScanSearch,
    color: 'text-orange-400',
    formats: ['CSV', 'HTML'],
  },
  {
    id: 'asset_overview',
    title: 'Asset Security Overview',
    description: 'Asset inventory with associated events, incidents, and criticality status.',
    icon: Server,
    color: 'text-green-400',
    formats: ['CSV', 'JSON', 'HTML'],
  },
]

export default function ReportsPage() {
  const { hasRole } = useAuth()

  const handleExport = (reportId: string, fmt: string) => {
    // Phase 6 will wire this to the backend export endpoint
    alert(`Report export: ${reportId} as ${fmt}\n\nFull export implementation in Phase 6.`)
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <PageHeader
        title="Reports"
        subtitle="Generate and export security intelligence reports"
        breadcrumbs={[{ label: 'Reports' }]}
      />

      <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-xl text-sm text-yellow-300">
        <p className="font-semibold">Phase 6 Feature</p>
        <p className="text-yellow-400 text-xs mt-0.5">
          Full CSV, JSON, and HTML export with CSV injection protection and permission enforcement
          will be implemented in Phase 6. Report types are defined and ready.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {REPORT_TYPES.map(report => (
          <div key={report.id} className="card hover:border-charcoal-500 transition-colors group">
            <div className="flex items-start gap-4">
              <div className="p-2.5 rounded-lg bg-charcoal-700 shrink-0">
                <report.icon className={`w-5 h-5 ${report.color}`} />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold text-gray-200 mb-1">{report.title}</h3>
                <p className="text-xs text-gray-500 leading-relaxed">{report.description}</p>
              </div>
            </div>

            <div className="mt-4 flex items-center justify-between">
              <div className="flex gap-1.5">
                {report.formats.map(fmt => (
                  <span
                    key={fmt}
                    className="text-xs font-mono px-1.5 py-0.5 bg-charcoal-700 text-gray-400 rounded border border-charcoal-500"
                  >
                    {fmt}
                  </span>
                ))}
              </div>
              {hasRole('ADMIN', 'SECURITY_ANALYST') && (
                <div className="flex gap-1.5">
                  {report.formats.map(fmt => (
                    <button
                      key={fmt}
                      onClick={() => handleExport(report.id, fmt)}
                      className="flex items-center gap-1 text-xs text-cyber-cyan hover:text-cyan-300 
                                 transition-colors px-2 py-1 rounded hover:bg-charcoal-700"
                      title={`Export as ${fmt}`}
                    >
                      <Download className="w-3 h-3" />
                      {fmt}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Export history placeholder */}
      <div className="card">
        <div className="card-header">
          <h2 className="section-title">Recent Exports</h2>
          <FileText className="w-4 h-4 text-gray-500" />
        </div>
        <p className="text-sm text-gray-500 text-center py-8">
          Export history will appear here once Phase 6 is complete.
        </p>
      </div>
    </div>
  )
}

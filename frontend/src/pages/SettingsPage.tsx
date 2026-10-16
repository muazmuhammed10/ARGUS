import { Settings, Bot, Shield, Database, Bell, Key } from 'lucide-react'
import { PageHeader } from '../components/PageHeader'
import { useAuth } from '../features/auth/AuthContext'

export default function SettingsPage() {
  const { user } = useAuth()

  return (
    <div className="space-y-5 animate-fade-in">
      <PageHeader
        title="System Settings"
        subtitle="Platform configuration and integrations"
        breadcrumbs={[{ label: 'Settings' }]}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* AI Configuration */}
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-charcoal-700"><Bot className="w-5 h-5 text-purple-400" /></div>
            <div>
              <h2 className="section-title text-base">AI Analysis</h2>
              <p className="text-xs text-gray-500">OpenAI or Anthropic integration</p>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-charcoal-700/50 rounded-lg border border-charcoal-500">
              <span className="text-sm text-gray-300">Provider</span>
              <span className="text-sm font-mono text-gray-400">Not configured</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-charcoal-700/50 rounded-lg border border-charcoal-500">
              <span className="text-sm text-gray-300">Status</span>
              <span className="text-xs px-2 py-0.5 bg-gray-700 text-gray-400 rounded border border-gray-600">Unavailable</span>
            </div>
            <p className="text-xs text-gray-500">
              Set <code className="font-mono text-cyan-400">AI_PROVIDER</code> and the API key in{' '}
              <code className="font-mono text-cyan-400">.env</code> to enable AI-assisted analysis.
            </p>
          </div>
        </div>

        {/* Threat Intel */}
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-charcoal-700"><Shield className="w-5 h-5 text-cyan-400" /></div>
            <div>
              <h2 className="section-title text-base">Threat Intelligence</h2>
              <p className="text-xs text-gray-500">External enrichment providers</p>
            </div>
          </div>
          <div className="space-y-3">
            {[
              { name: 'VirusTotal', key: 'VIRUSTOTAL_API_KEY' },
              { name: 'AbuseIPDB',  key: 'ABUSEIPDB_API_KEY' },
            ].map(p => (
              <div key={p.name} className="flex items-center justify-between p-3 bg-charcoal-700/50 rounded-lg border border-charcoal-500">
                <span className="text-sm text-gray-300">{p.name}</span>
                <span className="text-xs px-2 py-0.5 bg-gray-700 text-gray-400 rounded border border-gray-600">Not configured</span>
              </div>
            ))}
            <p className="text-xs text-gray-500">
              Add API keys to <code className="font-mono text-cyan-400">.env</code> to enable live lookups.
            </p>
          </div>
        </div>

        {/* Database */}
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-charcoal-700"><Database className="w-5 h-5 text-green-400" /></div>
            <div>
              <h2 className="section-title text-base">Database</h2>
              <p className="text-xs text-gray-500">PostgreSQL connection</p>
            </div>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2 text-green-400">
              <div className="w-2 h-2 rounded-full bg-green-400" />
              Connected
            </div>
            <p className="text-xs text-gray-500">
              Database: <code className="font-mono text-cyan-400">argus_db</code>
            </p>
          </div>
        </div>

        {/* Security */}
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-charcoal-700"><Key className="w-5 h-5 text-yellow-400" /></div>
            <div>
              <h2 className="section-title text-base">Security</h2>
              <p className="text-xs text-gray-500">Auth and token configuration</p>
            </div>
          </div>
          <div className="space-y-3">
            {[
              { label: 'Password Hashing', value: 'Argon2id' },
              { label: 'Token Algorithm', value: 'HS256' },
              { label: 'Access Token TTL', value: '30 minutes' },
              { label: 'Refresh Token TTL', value: '7 days' },
              { label: 'Rate Limiting', value: '5 attempts / 5 min' },
            ].map(row => (
              <div key={row.label} className="flex items-center justify-between text-sm">
                <span className="text-gray-400">{row.label}</span>
                <span className="font-mono text-xs text-cyan-400">{row.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

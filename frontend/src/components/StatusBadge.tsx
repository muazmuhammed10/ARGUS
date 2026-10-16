interface Props {
  status: string
}

const map: Record<string, string> = {
  // Incident statuses
  NEW:           'bg-blue-500/20 text-blue-400 border-blue-500/30',
  TRIAGED:       'bg-purple-500/20 text-purple-400 border-purple-500/30',
  INVESTIGATING: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  CONTAINED:     'bg-orange-500/20 text-orange-400 border-orange-500/30',
  RESOLVED:      'bg-green-500/20 text-green-400 border-green-500/30',
  CLOSED:        'bg-gray-500/20 text-gray-400 border-gray-500/30',
  // Alert statuses
  OPEN:          'bg-red-500/20 text-red-400 border-red-500/30',
  ACKNOWLEDGED:  'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  FALSE_POSITIVE:'bg-gray-500/20 text-gray-400 border-gray-500/30',
  // Investigation
  IN_PROGRESS:   'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  ON_HOLD:       'bg-orange-500/20 text-orange-400 border-orange-500/30',
  // Detection
  UNREVIEWED:    'bg-red-500/20 text-red-400 border-red-500/30',
  REVIEWED:      'bg-green-500/20 text-green-400 border-green-500/30',
  ESCALATED:     'bg-orange-500/20 text-orange-400 border-orange-500/30',
}

export function StatusBadge({ status }: Props) {
  const cls = map[status] ?? 'bg-gray-500/20 text-gray-400 border-gray-500/30'
  return (
    <span className={`badge border ${cls}`}>
      {status.replace(/_/g, ' ')}
    </span>
  )
}

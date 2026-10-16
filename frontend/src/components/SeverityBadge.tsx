import type { Severity } from '../types'

interface Props {
  severity: Severity | string
  size?: 'sm' | 'md'
}

const map: Record<string, string> = {
  CRITICAL: 'badge-critical',
  HIGH:     'badge-high',
  MEDIUM:   'badge-medium',
  LOW:      'badge-low',
  INFO:     'badge-info',
}

export function SeverityBadge({ severity, size = 'md' }: Props) {
  const cls = map[severity] ?? 'badge bg-gray-700 text-gray-300'
  return (
    <span className={`${cls} ${size === 'sm' ? 'text-[10px] px-1.5 py-0' : ''}`}>
      {severity}
    </span>
  )
}

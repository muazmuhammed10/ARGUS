// ============================================================
// ARGUS — Shared TypeScript types
// ============================================================

export type UserRole = 'ADMIN' | 'SECURITY_ANALYST' | 'VIEWER'

export interface User {
  id: string
  email: string
  username: string
  full_name: string
  role: UserRole
  is_active: boolean
  is_verified: boolean
  created_at: string
  last_login_at: string | null
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO'
export type EventType =
  | 'AUTHENTICATION' | 'AUTHORIZATION' | 'NETWORK' | 'ENDPOINT'
  | 'MALWARE' | 'POLICY_VIOLATION' | 'PRIVILEGE_ESCALATION'
  | 'RECONNAISSANCE' | 'DATA_EXFILTRATION' | 'SYSTEM' | 'OTHER'

export type DetectionStatus = 'UNREVIEWED' | 'REVIEWED' | 'FALSE_POSITIVE' | 'ESCALATED'

export interface SecurityEvent {
  id: string
  timestamp: string
  source_system: string
  event_type: EventType
  severity: Severity
  source_ip: string | null
  destination_ip: string | null
  source_port: number | null
  destination_port: number | null
  username: string | null
  hostname: string | null
  description: string
  metadata_json: Record<string, unknown> | null
  detection_status: DetectionStatus
  is_synthetic: boolean
  incident_id: string | null
  created_at: string
}

export type IncidentSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
export type IncidentStatus =
  | 'NEW' | 'TRIAGED' | 'INVESTIGATING' | 'CONTAINED' | 'RESOLVED' | 'CLOSED'

export interface Incident {
  id: string
  title: string
  description: string
  severity: IncidentSeverity
  status: IncidentStatus
  assigned_to_id: string | null
  created_by_id: string
  remediation_summary: string | null
  resolution_summary: string | null
  resolved_at: string | null
  closed_at: string | null
  created_at: string
  updated_at: string
}

export type AssetEnvironment = 'PRODUCTION' | 'STAGING' | 'DEVELOPMENT' | 'CORPORATE' | 'DMZ' | 'UNKNOWN'
export type AssetCriticality = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'

export interface Asset {
  id: string
  name: string
  hostname: string | null
  ip_address: string | null
  operating_system: string | null
  environment: AssetEnvironment
  owner: string | null
  criticality: AssetCriticality
  monitoring_status: string
  notes: string | null
  last_seen_at: string | null
  created_at: string
  updated_at: string
}

export interface DetectionRule {
  id: string
  name: string
  description: string
  category: string
  severity: Severity
  is_enabled: boolean
  threshold_count: number
  threshold_window_seconds: number
  rule_key: string
  created_at: string
  updated_at: string
}

export type AlertStatus = 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED' | 'FALSE_POSITIVE'

export interface Alert {
  id: string
  title: string
  description: string
  severity: Severity
  status: AlertStatus
  rule_id: string | null
  event_id: string | null
  incident_id: string | null
  evidence: Record<string, unknown> | null
  dedup_key: string | null
  occurrence_count: number
  created_at: string
  updated_at: string
}

export type IndicatorType = 'IPV4' | 'IPV6' | 'DOMAIN' | 'URL' | 'MD5' | 'SHA1' | 'SHA256' | 'EMAIL' | 'CVE'

export interface Indicator {
  id: string
  value: string
  indicator_type: IndicatorType
  confidence: number | null
  is_malicious: boolean | null
  reputation_score: number | null
  analyst_notes: string | null
  tags: string | null
  source: string | null
  first_seen_at: string | null
  last_seen_at: string | null
  created_at: string
  updated_at: string
}

export type InvestigationStatus = 'OPEN' | 'IN_PROGRESS' | 'ON_HOLD' | 'CLOSED'

export interface Investigation {
  id: string
  title: string
  description: string | null
  status: InvestigationStatus
  hypothesis: string | null
  final_conclusion: string | null
  ai_summary: string | null
  incident_id: string | null
  assigned_to_id: string | null
  created_by_id: string
  created_at: string
  updated_at: string
  closed_at: string | null
}

export interface DashboardSummary {
  total_events: number
  critical_events: number
  high_events: number
  open_incidents: number
  resolved_incidents: number
  open_alerts: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface ApiError {
  detail: string
  status?: number
}

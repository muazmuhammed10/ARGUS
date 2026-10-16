# ARGUS — Architecture Document

## Overview

ARGUS is a modular, defence-oriented cybersecurity platform built as a
monorepo. The frontend and backend are independently deployable and communicate
exclusively through a versioned REST API.

```
┌─────────────────────────────────────────────────────────────┐
│                        ARGUS Platform                        │
│                                                             │
│  ┌──────────────┐    REST/JSON    ┌───────────────────────┐ │
│  │   Frontend   │◄──────────────►│      Backend API      │ │
│  │  React/Vite  │                │  FastAPI + SQLAlchemy │ │
│  │  TypeScript  │                │       Python 3.12     │ │
│  │  Tailwind    │                └──────────┬────────────┘ │
│  └──────────────┘                           │              │
│                                    ┌────────┴────────┐     │
│                              ┌─────┴──────┐  ┌───────┴──┐ │
│                              │ PostgreSQL │  │  Redis   │ │
│                              │   (data)   │  │ (cache/  │ │
│                              └────────────┘  │  queue)  │ │
│                                              └──────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Frontend Architecture

- **Framework**: React 18 with TypeScript, built with Vite
- **Routing**: React Router v6 with lazy-loaded pages
- **State**: TanStack Query for server state; React Context for auth
- **Styling**: Tailwind CSS with a custom dark cybersecurity design system
- **Charts**: Recharts for all data visualisations
- **Auth tokens**: Access tokens stored in memory only. Refresh tokens stored
  in `sessionStorage` (cleared on tab close). Never `localStorage`.

### Component hierarchy
```
App
├── AuthProvider (context)
│   ├── /login         → LoginPage
│   ├── /register      → RegisterPage
│   └── ProtectedRoute → AppLayout
│       ├── Sidebar (collapsible nav)
│       ├── TopBar  (search, notifications, profile)
│       └── <Outlet> → page components
│           ├── DashboardPage
│           ├── EventsPage
│           ├── IncidentsPage
│           ├── ThreatIntelPage
│           ├── DetectionRulesPage
│           ├── AssetsPage
│           ├── InvestigationsPage
│           ├── ReportsPage
│           └── SettingsPage
```

## Backend Architecture

- **Framework**: FastAPI with async SQLAlchemy 2.0
- **Database**: PostgreSQL 16 via `asyncpg`
- **Migrations**: Alembic (versioned, reviewed before apply)
- **Auth**: JWT (HS256) — short-lived access tokens + revocable refresh tokens
- **Password hashing**: Argon2id (64 MiB memory, 3 iterations, 4 parallelism)
- **Background tasks**: Celery + Redis (Phase 3+)
- **Logging**: structlog — JSON in production, pretty-print in development

### API structure
```
/api/v1/
├── auth/         register, login, refresh, logout, me
├── dashboard/    summary, trends
├── events/       list, get, ingest, import
├── incidents/    CRUD + status transitions
├── intelligence/ IOC lookup, list, get
├── assets/       CRUD
├── rules/        list, create, update
├── investigations/ CRUD + notes + evidence
├── reports/      list, export
└── ai/           analyze-event, summarize-incident
```

## Database Design

All tables use UUID primary keys and UTC timestamps.

```
users ──< refresh_tokens
users ──< audit_logs
users ──< incidents (created_by, assigned_to)
users ──< investigations (created_by, assigned_to)

security_events ──< alerts
security_events >── incidents (via incident_id FK)
security_events ──< incident_events (join table)

detection_rules ──< alerts

incidents ──< incident_events
incidents ──< alerts
incidents ──< investigations

indicators_of_compromise ──< threat_intelligence_results

investigations ──< investigation_notes
investigations ──< investigation_evidence
```

## Security Design Decisions

| Concern | Decision |
|---------|----------|
| Password hashing | Argon2id — PHC winner, memory-hard |
| Token storage (client) | Access: memory only. Refresh: sessionStorage |
| Token storage (server) | Refresh token SHA-256 hash stored in DB, not raw |
| Role enforcement | Backend RBAC on every protected endpoint |
| SQL injection | SQLAlchemy ORM parameterised queries only |
| CORS | Restrictive — explicit origin allowlist |
| Rate limiting | slowapi — 5 login attempts per 5 minutes per IP |
| Audit logging | Every auth event, role change, and rule modification |
| Imported data | Validated, normalised, never executed |
| AI input | Log content sanitised before sending to AI provider |
| Secrets | Environment variables only — never committed |

## Detection Engine Design (Phase 3)

The detection engine is rule-based and fully explainable. Each rule maps to a
`rule_key` that corresponds to a deterministic Python handler. Rules evaluate
normalised events and produce alerts with supporting evidence.

No arbitrary code execution is permitted through user-configured rules.
Thresholds and windows are configurable, but rule logic is fixed in code.

## AI Integration Design (Phase 5)

AI providers are optional and isolated in `app/ai/`. The platform functions
fully without any AI key configured. When enabled:

- Only required event fields are sent to the provider
- Log content (untrusted) is clearly delimited to prevent prompt injection
- AI output is labelled as "AI-assisted analysis" — never presented as fact
- AI cannot execute commands, modify users, or take remediation actions
- Human approval is required for all operational decisions

## Phase Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Foundation, structure, auth, DB | ✅ Complete |
| 2 | Full auth tests, migrations, seed | 🔄 Next |
| 3 | Event ingestion, detection engine | Pending |
| 4 | Dashboard data, incidents, investigations | Pending |
| 5 | Threat intel, AI analysis | Pending |
| 6 | Reports, hardening, testing | Pending |
| 7 | Polish, docs, portfolio prep | Pending |

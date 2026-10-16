<img src="https://img.shields.io/badge/Python-3.14-blue?logo=python" alt="Python 3.14"/> <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI"/> <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react" alt="React 18"/> <img src="https://img.shields.io/badge/PostgreSQL-14+-336791?logo=postgresql" alt="PostgreSQL"/> <img src="https://img.shields.io/badge/License-Portfolio-lightgrey" alt="License"/>

# ARGUS — AI-Powered Cyber Defense Platform

> A full-stack Security Operations Center (SOC) / SIEM platform with real-time threat detection, AI-assisted triage, incident management, and threat intelligence — built for security operations teams.

---

## ✨ Features

| Capability | Details |
|---|---|
| 🔐 **Authentication** | Argon2id passwords, JWT access tokens, refresh token rotation, RBAC (Admin / Analyst / Viewer) |
| 🔍 **Event Ingestion** | Single events or bulk JSON Lines import, deduplication, UTC normalisation, IP validation |
| ⚡ **Detection Engine** | 7 rules: brute force, credential stuffing, port scan, privilege escalation, IOC match, and more |
| 🚨 **Incident Management** | Full lifecycle (NEW → CLOSED), event linking, audit logs, RBAC enforcement |
| 🌐 **Threat Intelligence** | IOC lookup with optional VirusTotal + AbuseIPDB enrichment |
| 🤖 **AI Analysis** | OpenAI / Anthropic event & incident summaries with deterministic fallback |
| 📊 **Dashboard** | Real-time event trends, severity breakdowns, open alerts, asset overview |
| 📁 **Reports** | CSV / JSON / HTML exports for events, incidents, assets, rules, and IOCs |
| 🛡️ **Landing Page** | Animated cyberpunk landing with hacker figure, particle canvas, and feature showcase |

---

## 🖥️ Screenshots

> Landing page → http://localhost:5173 &nbsp;|&nbsp; Dashboard → http://localhost:5173/dashboard &nbsp;|&nbsp; API Docs → http://localhost:8000/api/docs

---

## 🚀 Quick Start — VS Code (Windows)

### Prerequisites

| Tool | Min Version | Install |
|---|---|---|
| Python | 3.12+ | https://python.org/downloads |
| Node.js | 20 LTS | https://nodejs.org |
| PostgreSQL | 14+ | https://postgresql.org/download |
| Git | any | https://git-scm.com |

> Redis is listed in requirements but **not required** to run the platform locally.
> The detection engine runs synchronously without it.

---

### Step 1 — Clone

```powershell
git clone https://github.com/<your-username>/ARGUS.git
cd ARGUS
```

---

### Step 2 — Environment file

```powershell
Copy-Item .env.example .env
```

Open `.env` and set **at minimum**:

```env
POSTGRES_PASSWORD=your_postgres_password
DATABASE_URL=postgresql+asyncpg://postgres:your_postgres_password@localhost:5432/argus_db
SECRET_KEY=<run: python -c "import secrets; print(secrets.token_hex(64))">
```

> The rest of the defaults work out of the box for local development.

---

### Step 3 — Create the database

Open pgAdmin (or psql) and run:

```sql
CREATE DATABASE argus_db;
```

Or via psql:

```powershell
psql -U postgres -c "CREATE DATABASE argus_db;"
```

---

### Step 4 — Backend setup

```powershell
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install all dependencies
pip install -r requirements.txt

# Apply database migrations
.venv\Scripts\python.exe -m scripts.migrate_safe

# Seed demo data (users, assets, events, incidents, IOCs)
.venv\Scripts\python.exe -m scripts.seed
```

Expected seed output:
```
🌱 Seeding ARGUS development database...
  Creating users...
  Creating assets...
  Creating detection rules...
  Creating synthetic security events...
  Creating incidents...
  Creating sample IOC indicators...
✅ Seed completed successfully.
   Admin:   admin@argus.local / Admin@Argus2024!
   Analyst: analyst1@argus.local / Analyst1Pass!23
   Viewer:  viewer@argus.local / Viewer1Pass!23
```

---

### Step 5 — Start the backend

```powershell
# From backend/ directory (venv active)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ API live at: http://localhost:8000  
✅ Swagger docs: http://localhost:8000/api/docs

---

### Step 6 — Start the frontend

Open a **new PowerShell terminal**:

```powershell
cd frontend
npm install     # only needed first time
npm run dev
```

✅ Frontend live at: http://localhost:5173

---

### Step 7 — Open in browser

Navigate to **http://localhost:5173** — you will see the landing page.

Click **Sign In** (top-right) or use the demo credentials:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@argus.local` | `Admin@Argus2024!` |
| Analyst | `analyst1@argus.local` | `Analyst1Pass!23` |
| Viewer | `viewer@argus.local` | `Viewer1Pass!23` |

---

## 🔧 Running in VS Code

This repo includes a full VS Code workspace configuration.

### One-click launch (F5)

Open the **Run and Debug** panel (`Ctrl+Shift+D`) and choose:

| Configuration | What it does |
|---|---|
| `🚀 Backend (uvicorn)` | Starts FastAPI with hot-reload on port 8000 |
| `🌐 Frontend (Vite)` | Starts Vite dev server on port 5173 |
| `🧪 Backend Tests` | Runs the full pytest suite |
| `🔗 Full Stack` | Launches backend + frontend together |

### Recommended VS Code extensions

The workspace suggests these automatically (`.vscode/extensions.json`):

- **Python** — `ms-python.python`
- **Pylance** — `ms-python.vscode-pylance`
- **Ruff** — `charliermarsh.ruff` (linting)
- **ESLint** — `dbaeumer.vscode-eslint`
- **Prettier** — `esbenp.prettier-vscode`
- **Tailwind CSS IntelliSense** — `bradlc.vscode-tailwindcss`
- **Thunder Client** — `rangav.vscode-thunder-client` (API testing)
- **GitLens** — `eamodio.gitlens`

---

## 🧪 Running Tests

### Backend (pytest)

```powershell
cd backend
.venv\Scripts\Activate.ps1

# All tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov=app --cov-report=term-missing

# Single file
pytest tests/test_auth.py -v
```

**Test suite: 80 tests across 9 files**

| File | Tests | Coverage |
|---|---|---|
| `test_auth.py` | 16 | Auth, register, RBAC, tokens |
| `test_security.py` | 9 | Argon2id, JWT signing |
| `test_health.py` | 5 | Health endpoint, 401s |
| `test_events.py` | 8 | Ingestion, dedup, validation |
| `test_incidents.py` | 8 | Lifecycle, status transitions |
| `test_assets.py` | 6 | CRUD, RBAC |
| `test_dashboard.py` | 6 | Real DB counts |
| `test_rbac.py` | 10 | Role enforcement |
| `test_detection.py` | 12 | All 7 detection rules |

### Frontend (Vitest)

```powershell
cd frontend
npm run test          # run once
npm run test:watch    # watch mode
npm run test:coverage # with coverage
```

---

## 🐳 Docker (Full Stack)

```powershell
# From project root
Copy-Item .env.example .env
# Edit .env — set POSTGRES_PASSWORD and SECRET_KEY

docker compose up --build

# In a second terminal
docker compose exec backend python -m scripts.migrate_safe
docker compose exec backend python -m scripts.seed

# Stop
docker compose down

# Stop + wipe database
docker compose down -v
```

Services exposed:

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/api/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

---

## 📁 Project Structure

```
ARGUS/
├── .env.example               ← Environment template (safe to commit)
├── .gitignore
├── docker-compose.yml
├── run.ps1                    ← One-command Windows startup script
├── README.md
│
├── frontend/                  ← React 18 + TypeScript + Vite + Tailwind
│   ├── src/
│   │   ├── pages/             ← LandingPage, DashboardPage, LoginPage, …
│   │   ├── components/        ← Shared UI (Logo, LoadingSpinner, …)
│   │   ├── features/auth/     ← AuthContext, ProtectedRoute
│   │   ├── layouts/           ← AppLayout, Sidebar, TopBar
│   │   ├── services/          ← Axios API service modules
│   │   ├── types/             ← Shared TypeScript interfaces
│   │   └── test/              ← Vitest + React Testing Library
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   └── Dockerfile
│
├── backend/                   ← Python 3.14 + FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── api/v1/endpoints/  ← auth, events, incidents, alerts, …
│   │   ├── core/              ← config, database, security, logging
│   │   ├── models/            ← 14 SQLAlchemy ORM models
│   │   ├── schemas/           ← Pydantic v2 request/response models
│   │   └── services/          ← detection engine, AI integration
│   ├── alembic/               ← Database migrations
│   │   └── versions/          ← 0001_initial_schema.py
│   ├── scripts/
│   │   ├── seed.py            ← Demo data seeder
│   │   └── migrate_safe.py    ← Smart migration helper
│   ├── tests/                 ← 80 pytest tests
│   ├── requirements.txt
│   └── Dockerfile
│
├── docs/
│   └── architecture.md        ← System design and data flow
└── sample_data/               ← Synthetic JSON event samples
```

---

## 🔌 API Reference

All endpoints are documented interactively at **http://localhost:8000/api/docs** (Swagger UI).

| Group | Base Path | Auth Required |
|---|---|---|
| Auth | `/api/v1/auth` | Partial (login/register public) |
| Events | `/api/v1/events` | Yes |
| Incidents | `/api/v1/incidents` | Yes |
| Alerts | `/api/v1/alerts` | Yes |
| Assets | `/api/v1/assets` | Yes |
| Investigations | `/api/v1/investigations` | Yes |
| Detection Rules | `/api/v1/rules` | Yes |
| Threat Intel | `/api/v1/intelligence` | Yes |
| AI Analysis | `/api/v1/ai` | Analyst+ |
| Reports | `/api/v1/reports` | Analyst+ |
| Dashboard | `/api/v1/dashboard` | Yes |
| Users | `/api/v1/users` | Admin only |

---

## 🔐 Security Design

| Control | Implementation |
|---|---|
| Password hashing | Argon2id (64 MiB, 3 iterations, 4 parallelism) |
| Access tokens | JWT HS256, 30-minute expiry, in-memory client storage |
| Refresh tokens | 7-day expiry, SHA-256 hashed in DB, rotation on each use |
| RBAC | Enforced on every backend endpoint — not just frontend guards |
| Rate limiting | 5 login attempts / 5 min per IP (slowapi) |
| Input validation | Pydantic v2 on all request bodies |
| SQL injection | SQLAlchemy ORM — no raw SQL |
| CORS | Restricted to `ALLOWED_ORIGINS` in `.env` |
| Secrets | `.env` in `.gitignore`, never committed |
| AI prompt injection | Log content sanitised before AI submission |
| CSV injection | `'` prefix on dangerous characters in exports |
| HTML reports | All values HTML-escaped |
| Audit trail | Every auth event, user change, rule change, incident change logged |

---

## ⚙️ Environment Variables

Full reference — copy from `.env.example`:

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ | — | JWT signing key (generate 64-byte hex) |
| `DATABASE_URL` | ✅ | — | PostgreSQL async connection string |
| `POSTGRES_PASSWORD` | ✅ | — | DB password |
| `APP_ENV` | | `development` | `development` / `production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | | `30` | JWT access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | | `7` | Refresh token lifetime |
| `REDIS_URL` | | `redis://localhost:6379/0` | Redis (optional locally) |
| `AI_PROVIDER` | | `none` | `openai` / `anthropic` / `none` |
| `OPENAI_API_KEY` | | — | OpenAI key for AI features |
| `ANTHROPIC_API_KEY` | | — | Anthropic key for AI features |
| `VIRUSTOTAL_API_KEY` | | — | VirusTotal IOC enrichment |
| `ABUSEIPDB_API_KEY` | | — | AbuseIPDB enrichment |
| `ALLOWED_ORIGINS` | | `http://localhost:5173` | CORS allowed origins (comma-separated) |

---

## 🛣️ Roadmap

| Phase | Status |
|---|---|
| Phase 1 — Foundation, models, auth skeleton | ✅ Complete |
| Phase 2 — Full auth, migrations, RBAC, tests | ✅ Complete |
| Phase 3 — Event ingestion, detection engine (7 rules) | ✅ Complete |
| Phase 4 — Dashboard, incidents, alerts, assets, investigations | ✅ Complete |
| Phase 5 — Threat intelligence, AI analysis | ✅ Complete |
| Phase 6 — Reports, exports, hardening | ✅ Complete |
| Phase 7 — Landing page, polish, GitHub-ready | ✅ Complete |
| Phase 8 — Async task queue (Celery/Redis), webhooks | 🔜 Planned |
| Phase 9 — Browser E2E tests (Playwright) | 🔜 Planned |

---

## 📄 License

ARGUS is a portfolio / demonstration project.

All synthetic data is for demonstration purposes only.  
Do not use this platform against systems you do not own or have explicit written permission to test.

---

<p align="center">
  Built with FastAPI · React · PostgreSQL · SQLAlchemy · Pydantic · Tailwind CSS
</p>

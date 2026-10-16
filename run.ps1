#!/usr/bin/env pwsh
# ============================================================
# ARGUS — Complete Local Startup Script (Windows PowerShell)
# Usage: .\run.ps1 [backend|frontend|migrate|seed|test|all]
# ============================================================

param(
    [string]$Action = "all"
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$Venv = Join-Path $Backend ".venv\Scripts"

function Write-Step([string]$msg) {
    Write-Host "`n► $msg" -ForegroundColor Cyan
}

function Write-OK([string]$msg) {
    Write-Host "  ✓ $msg" -ForegroundColor Green
}

function Write-Warn([string]$msg) {
    Write-Host "  ⚠ $msg" -ForegroundColor Yellow
}

function Write-Fail([string]$msg) {
    Write-Host "  ✗ $msg" -ForegroundColor Red
}

# ── Pre-flight checks ──────────────────────────────────────────────────────────

function Test-Prerequisites {
    Write-Step "Checking prerequisites…"

    # Python
    $pyOk = Test-Path (Join-Path $Venv "python.exe")
    if ($pyOk) { Write-OK "Python venv found" }
    else { Write-Fail "Python venv missing. Run: cd backend && py -m venv .venv && .venv\Scripts\pip install -r requirements.txt" }

    # Node
    try {
        $null = node --version 2>&1
        Write-OK "Node.js available"
    } catch {
        Write-Fail "Node.js not found"
    }

    # node_modules
    $nmOk = Test-Path (Join-Path $Frontend "node_modules")
    if ($nmOk) { Write-OK "Frontend node_modules present" }
    else { Write-Warn "node_modules missing — run: cd frontend && npm install" }

    # .env
    $envOk = Test-Path (Join-Path $Root ".env")
    if ($envOk) { Write-OK ".env file found" }
    else { Write-Fail ".env missing — copy .env.example to .env and configure" }
}

# ── Database migration ─────────────────────────────────────────────────────────

function Invoke-Migration {
    Write-Step "Running Alembic migrations…"
    Push-Location $Backend
    try {
        # Check if tables already exist (Phase 1 used create_all)
        $head = & "$Venv\python.exe" -m alembic current 2>&1
        if ($head -match "0001_initial_schema") {
            Write-OK "Database already at head (0001_initial_schema)"
            return
        }

        # If tables exist from create_all but no migration history, stamp current state
        Write-Warn "Checking if database already has tables from create_all…"
        $stamp = & "$Venv\python.exe" -c @"
import asyncio, asyncpg
from app.core.config import settings
async def check():
    url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    try:
        conn = await asyncpg.connect(url)
        tables = await conn.fetch("""SELECT tablename FROM pg_tables WHERE schemaname = 'public'""")
        await conn.close()
        return len(tables)
    except:
        return -1
print(asyncio.run(check()))
"@ 2>&1

        $tableCount = [int]($stamp.Trim())
        if ($tableCount -gt 5) {
            Write-Warn "Found $tableCount existing tables. Stamping as head to avoid re-migration…"
            & "$Venv\alembic.exe" stamp head
            Write-OK "Stamped existing schema as migration head"
        } else {
            Write-Step "Applying initial migration…"
            & "$Venv\alembic.exe" upgrade head
            Write-OK "Migration applied successfully"
        }
    } finally {
        Pop-Location
    }
}

# ── Seed data ─────────────────────────────────────────────────────────────────

function Invoke-Seed {
    Write-Step "Seeding development database…"
    Push-Location $Backend
    try {
        & "$Venv\python.exe" -m scripts.seed
        Write-OK "Seed completed"
    } catch {
        Write-Warn "Seed failed or already seeded: $_"
    } finally {
        Pop-Location
    }
}

# ── Run tests ─────────────────────────────────────────────────────────────────

function Invoke-Tests {
    Write-Step "Running backend tests…"
    Push-Location $Backend
    try {
        & "$Venv\pytest.exe" tests/ -v --tb=short -q
        if ($LASTEXITCODE -eq 0) {
            Write-OK "All backend tests passed"
        } else {
            Write-Warn "Some backend tests failed — see output above"
        }
    } finally {
        Pop-Location
    }

    Write-Step "Running frontend tests…"
    Push-Location $Frontend
    try {
        & npm run test -- --run 2>&1
        Write-OK "Frontend tests completed"
    } catch {
        Write-Warn "Frontend tests encountered issues: $_"
    } finally {
        Pop-Location
    }
}

# ── Start backend ─────────────────────────────────────────────────────────────

function Start-Backend {
    Write-Step "Starting FastAPI backend on port 8000…"
    Push-Location $Backend
    $env:APP_ENV = "development"
    Start-Process -FilePath "$Venv\uvicorn.exe" `
        -ArgumentList "app.main:app --reload --host 0.0.0.0 --port 8000" `
        -WorkingDirectory $Backend `
        -NoNewWindow
    Write-OK "Backend started — http://localhost:8000"
    Write-OK "API docs — http://localhost:8000/api/docs"
    Pop-Location
}

# ── Start frontend ────────────────────────────────────────────────────────────

function Start-Frontend {
    Write-Step "Starting Vite frontend on port 5173…"
    Push-Location $Frontend
    Start-Process -FilePath "npm" `
        -ArgumentList "run dev" `
        -WorkingDirectory $Frontend `
        -NoNewWindow
    Write-OK "Frontend started — http://localhost:5173"
    Pop-Location
}

# ── Main ──────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "═══════════════════════════════════════════" -ForegroundColor DarkCyan
Write-Host "  ARGUS — Cyber Defense Platform           " -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════" -ForegroundColor DarkCyan

Test-Prerequisites

switch ($Action.ToLower()) {
    "migrate" { Invoke-Migration }
    "seed"    { Invoke-Seed }
    "test"    { Invoke-Tests }
    "backend" { Invoke-Migration; Start-Backend }
    "frontend"{ Start-Frontend }
    "all" {
        Invoke-Migration
        Invoke-Seed
        Write-Host ""
        Write-Host "Starting servers in separate windows…" -ForegroundColor Yellow
        Write-Host "  Backend: http://localhost:8000" -ForegroundColor White
        Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
        Write-Host "  API Docs: http://localhost:8000/api/docs" -ForegroundColor White
        Write-Host ""
        Write-Host "Demo credentials:" -ForegroundColor Yellow
        Write-Host "  Admin:   admin@argus.local / Admin@Argus2024!" -ForegroundColor White
        Write-Host "  Analyst: analyst1@argus.local / Analyst1Pass!23" -ForegroundColor White
        Write-Host "  Viewer:  viewer@argus.local / Viewer1Pass!23" -ForegroundColor White
        Write-Host ""
        Start-Backend
        Start-Sleep -Seconds 2
        Start-Frontend
    }
    default {
        Write-Host "Usage: .\run.ps1 [all|backend|frontend|migrate|seed|test]"
    }
}

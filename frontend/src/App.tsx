import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './features/auth/AuthContext'
import { ProtectedRoute } from './features/auth/ProtectedRoute'
import { AppLayout } from './layouts/AppLayout'
import { LoadingSpinner } from './components/LoadingSpinner'

// Lazy-loaded pages for code splitting
const LandingPage      = lazy(() => import('./pages/LandingPage'))
const LoginPage        = lazy(() => import('./pages/LoginPage'))
const RegisterPage     = lazy(() => import('./pages/RegisterPage'))
const DashboardPage    = lazy(() => import('./pages/DashboardPage'))
const EventsPage       = lazy(() => import('./pages/EventsPage'))
const IncidentsPage    = lazy(() => import('./pages/IncidentsPage'))
const ThreatIntelPage  = lazy(() => import('./pages/ThreatIntelPage'))
const DetectionRules   = lazy(() => import('./pages/DetectionRulesPage'))
const AssetsPage       = lazy(() => import('./pages/AssetsPage'))
const InvestigationsPage = lazy(() => import('./pages/InvestigationsPage'))
const ReportsPage      = lazy(() => import('./pages/ReportsPage'))
const SettingsPage     = lazy(() => import('./pages/SettingsPage'))
const NotFoundPage     = lazy(() => import('./pages/NotFoundPage'))
const ForbiddenPage    = lazy(() => import('./pages/ForbiddenPage'))

const PageFallback = () => <LoadingSpinner fullPage label="Loading…" />

export default function App() {
  return (
    <AuthProvider>
      <Suspense fallback={<PageFallback />}>
        <Routes>
          {/* Public landing page */}
          <Route path="/" element={<LandingPage />} />

          {/* Auth routes */}
          <Route path="/login"    element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/403"      element={<ForbiddenPage />} />

          {/* Protected routes — any authenticated role */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/dashboard"      element={<DashboardPage />} />
              <Route path="/events"         element={<EventsPage />} />
              <Route path="/incidents"      element={<IncidentsPage />} />
              <Route path="/intelligence"   element={<ThreatIntelPage />} />
              <Route path="/assets"         element={<AssetsPage />} />
              <Route path="/investigations" element={<InvestigationsPage />} />
              <Route path="/reports"        element={<ReportsPage />} />

              {/* Analyst + Admin only */}
              <Route element={<ProtectedRoute allowedRoles={['ADMIN', 'SECURITY_ANALYST']} />}>
                <Route path="/rules" element={<DetectionRules />} />
              </Route>

              {/* Admin only */}
              <Route element={<ProtectedRoute allowedRoles={['ADMIN']} />}>
                <Route path="/settings" element={<SettingsPage />} />
              </Route>
            </Route>
          </Route>

          {/* 404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </AuthProvider>
  )
}

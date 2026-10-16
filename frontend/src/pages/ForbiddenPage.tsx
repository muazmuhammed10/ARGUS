import { Link } from 'react-router-dom'
import { ShieldOff, Home } from 'lucide-react'

export default function ForbiddenPage() {
  return (
    <div className="min-h-screen bg-navy-950 flex items-center justify-center p-4">
      <div className="text-center space-y-6">
        <div className="flex justify-center">
          <div className="w-20 h-20 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center">
            <ShieldOff className="w-10 h-10 text-red-400" />
          </div>
        </div>
        <div>
          <h1 className="text-6xl font-bold font-mono text-red-900">403</h1>
          <h2 className="text-xl font-semibold text-gray-300 mt-2">Access Denied</h2>
          <p className="text-gray-500 mt-2 text-sm">
            You don't have permission to access this resource.
          </p>
        </div>
        <Link to="/dashboard" className="btn-secondary inline-flex">
          <Home className="w-4 h-4" />
          Return to Dashboard
        </Link>
      </div>
    </div>
  )
}

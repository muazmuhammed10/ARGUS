import { Link } from 'react-router-dom'
import { Home, AlertTriangle } from 'lucide-react'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-navy-950 flex items-center justify-center p-4">
      <div className="text-center space-y-6">
        <div className="flex justify-center">
          <div className="w-20 h-20 rounded-full bg-charcoal-700 flex items-center justify-center">
            <AlertTriangle className="w-10 h-10 text-yellow-400" />
          </div>
        </div>
        <div>
          <h1 className="text-6xl font-bold font-mono text-charcoal-500">404</h1>
          <h2 className="text-xl font-semibold text-gray-300 mt-2">Page Not Found</h2>
          <p className="text-gray-500 mt-2 text-sm">The route you're looking for doesn't exist.</p>
        </div>
        <Link to="/dashboard" className="btn-primary inline-flex">
          <Home className="w-4 h-4" />
          Return to Dashboard
        </Link>
      </div>
    </div>
  )
}

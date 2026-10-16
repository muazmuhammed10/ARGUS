import { type LucideIcon, Inbox } from 'lucide-react'

interface Props {
  icon?: LucideIcon
  title: string
  description?: string
  action?: React.ReactNode
}

export function EmptyState({ icon: Icon = Inbox, title, description, action }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center gap-4">
      <div className="w-16 h-16 rounded-full bg-charcoal-700 flex items-center justify-center">
        <Icon className="w-7 h-7 text-gray-500" />
      </div>
      <div>
        <p className="text-gray-300 font-medium">{title}</p>
        {description && <p className="text-sm text-gray-500 mt-1 max-w-sm">{description}</p>}
      </div>
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}

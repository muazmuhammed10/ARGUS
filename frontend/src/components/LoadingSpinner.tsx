interface Props {
  size?: 'sm' | 'md' | 'lg'
  label?: string
  fullPage?: boolean
}

const sizes = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-10 h-10' }

export function LoadingSpinner({ size = 'md', label, fullPage }: Props) {
  const spinner = (
    <div className="flex flex-col items-center gap-3">
      <div className={`${sizes[size]} border-2 border-cyber-cyan border-t-transparent rounded-full animate-spin`} />
      {label && <p className="text-sm text-gray-400">{label}</p>}
    </div>
  )

  if (fullPage) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-navy-950">
        {spinner}
      </div>
    )
  }

  return <div className="flex items-center justify-center p-8">{spinner}</div>
}

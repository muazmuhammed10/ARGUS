interface Props {
  size?: 'sm' | 'md' | 'lg'
  showText?: boolean
}

const sizes = {
  sm: { icon: 28, text: 'text-lg' },
  md: { icon: 36, text: 'text-xl' },
  lg: { icon: 48, text: 'text-3xl' },
}

export function Logo({ size = 'md', showText = true }: Props) {
  const { icon, text } = sizes[size]
  return (
    <div className="flex items-center gap-2.5 select-none">
      <svg
        width={icon}
        height={icon}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <rect width="32" height="32" rx="8" fill="#111c2d" />
        <path
          d="M16 4L28 10V18C28 23.5 22.6 28.4 16 30C9.4 28.4 4 23.5 4 18V10L16 4Z"
          fill="#162338"
          stroke="#00d4ff"
          strokeWidth="1.5"
        />
        <ellipse cx="16" cy="17" rx="7" ry="5" stroke="#00d4ff" strokeWidth="1.5" fill="none" />
        <circle cx="16" cy="17" r="2.5" fill="#00ff88" />
        <circle cx="16" cy="17" r="1" fill="#111c2d" />
      </svg>
      {showText && (
        <span className={`${text} font-bold tracking-widest text-gray-100 font-mono`}>
          ARGUS
        </span>
      )}
    </div>
  )
}

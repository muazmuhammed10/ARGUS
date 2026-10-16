/**
 * ARGUS — Landing Page
 * Full-screen cyberpunk landing with animated hacker figure,
 * particle matrix, scan lines, and feature sections.
 */

import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, Eye, Zap, Lock, Activity, Globe,
  ChevronDown, Terminal, AlertTriangle, BarChart3,
  ArrowRight, CheckCircle,
} from 'lucide-react'

// ─── Particle canvas background ────────────────────────────────────────────

function ParticleCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animId: number
    let w = (canvas.width = window.innerWidth)
    let h = (canvas.height = window.innerHeight)

    const resize = () => {
      w = canvas.width = window.innerWidth
      h = canvas.height = window.innerHeight
    }
    window.addEventListener('resize', resize)

    // Particles
    const PARTICLE_COUNT = 90
    type Particle = {
      x: number; y: number; vx: number; vy: number
      r: number; alpha: number; color: string
    }
    const colors = ['#00d4ff', '#00ff88', '#0088ff', '#7c3aed']
    const particles: Particle[] = Array.from({ length: PARTICLE_COUNT }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      r: Math.random() * 2 + 0.5,
      alpha: Math.random() * 0.6 + 0.2,
      color: colors[Math.floor(Math.random() * colors.length)],
    }))

    // Matrix rain columns
    const COLS = Math.floor(w / 18)
    const drops = Array.from({ length: COLS }, () => Math.random() * -50)
    const chars = '01アイウエオカキクケコサシスセソタチツテトナニヌネノ'

    let frame = 0

    const draw = () => {
      frame++
      // Dark overlay
      ctx.fillStyle = 'rgba(8,13,20,0.92)'
      ctx.fillRect(0, 0, w, h)

      // Matrix rain (sparse)
      ctx.font = '12px monospace'
      for (let i = 0; i < drops.length; i++) {
        if (Math.random() > 0.985) {
          const ch = chars[Math.floor(Math.random() * chars.length)]
          const y = drops[i] * 18
          const bright = drops[i] < 2
          ctx.fillStyle = bright
            ? `rgba(0,255,136,0.9)`
            : `rgba(0,212,255,${0.08 + Math.random() * 0.12})`
          ctx.fillText(ch, i * 18, y)
          if (y > h && Math.random() > 0.975) drops[i] = 0
          drops[i] += 0.4
        }
      }

      // Particles + connections
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i]
        p.x += p.vx
        p.y += p.vy
        if (p.x < 0) p.x = w
        if (p.x > w) p.x = 0
        if (p.y < 0) p.y = h
        if (p.y > h) p.y = 0

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
        ctx.fillStyle = p.color.replace(')', `,${p.alpha})`)
          .replace('rgb(', 'rgba(')
          .replace('#00d4ff', `rgba(0,212,255,${p.alpha})`)
          .replace('#00ff88', `rgba(0,255,136,${p.alpha})`)
          .replace('#0088ff', `rgba(0,136,255,${p.alpha})`)
          .replace('#7c3aed', `rgba(124,58,237,${p.alpha})`)
        ctx.fill()

        // Draw edges to nearby particles
        for (let j = i + 1; j < particles.length; j++) {
          const q = particles[j]
          const dx = p.x - q.x
          const dy = p.y - q.y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < 120) {
            ctx.beginPath()
            ctx.moveTo(p.x, p.y)
            ctx.lineTo(q.x, q.y)
            ctx.strokeStyle = `rgba(0,212,255,${0.12 * (1 - dist / 120)})`
            ctx.lineWidth = 0.5
            ctx.stroke()
          }
        }
      }

      // Scan line
      const scanY = ((frame * 1.2) % (h + 100)) - 50
      const scanGrad = ctx.createLinearGradient(0, scanY, 0, scanY + 2)
      scanGrad.addColorStop(0, 'rgba(0,212,255,0)')
      scanGrad.addColorStop(0.5, 'rgba(0,212,255,0.15)')
      scanGrad.addColorStop(1, 'rgba(0,212,255,0)')
      ctx.fillStyle = scanGrad
      ctx.fillRect(0, scanY, w, 2)

      animId = requestAnimationFrame(draw)
    }

    draw()
    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('resize', resize)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 w-full h-full pointer-events-none"
      style={{ zIndex: 0 }}
      aria-hidden="true"
    />
  )
}

// ─── SVG Hacker Figure ──────────────────────────────────────────────────────

function HackerFigure() {
  return (
    <div className="relative flex items-center justify-center select-none" aria-hidden="true">
      {/* Outer glow rings */}
      <div className="absolute w-[420px] h-[420px] rounded-full border border-cyan-500/10 animate-spin-slow" />
      <div className="absolute w-[360px] h-[360px] rounded-full border border-cyan-500/15" style={{ animationDuration: '15s' }} />
      <div
        className="absolute w-[300px] h-[300px] rounded-full border border-cyan-400/20"
        style={{ animation: 'spin 12s linear infinite reverse' }}
      />

      {/* Rotating hex ring */}
      <svg
        className="absolute w-[350px] h-[350px] animate-spin-slow opacity-20"
        viewBox="0 0 200 200"
      >
        {[0, 60, 120, 180, 240, 300].map((angle, i) => {
          const rad = (angle * Math.PI) / 180
          const x = 100 + 88 * Math.cos(rad)
          const y = 100 + 88 * Math.sin(rad)
          return (
            <g key={i}>
              <circle cx={x} cy={y} r="4" fill="#00d4ff" opacity="0.8" />
              <line x1="100" y1="100" x2={x} y2={y} stroke="#00d4ff" strokeWidth="0.5" opacity="0.4" />
            </g>
          )
        })}
        <circle cx="100" cy="100" r="88" fill="none" stroke="#00d4ff" strokeWidth="0.5" strokeDasharray="8 4" />
      </svg>

      {/* Floating glow behind figure */}
      <div className="absolute w-64 h-64 rounded-full bg-cyan-500/5 blur-3xl animate-pulse-slow" />
      <div className="absolute w-48 h-48 rounded-full bg-blue-500/8 blur-2xl animate-float" />

      {/* Main hacker SVG */}
      <svg
        viewBox="0 0 280 400"
        className="relative w-72 h-96 animate-float drop-shadow-[0_0_40px_rgba(0,212,255,0.4)]"
        style={{ filter: 'drop-shadow(0 0 20px rgba(0,212,255,0.5))' }}
      >
        {/* Hoodie body */}
        <defs>
          <linearGradient id="bodyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#0d1420" />
            <stop offset="50%" stopColor="#111c2d" />
            <stop offset="100%" stopColor="#080d14" />
          </linearGradient>
          <linearGradient id="cyanGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#00d4ff" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#0088ff" stopOpacity="0.8" />
          </linearGradient>
          <linearGradient id="maskGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#1a2a3a" />
            <stop offset="100%" stopColor="#0d1520" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="glowStrong">
            <feGaussianBlur stdDeviation="5" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Hood shadow */}
        <ellipse cx="140" cy="155" rx="78" ry="90" fill="url(#bodyGrad)" opacity="0.6" />

        {/* Body / torso */}
        <path
          d="M 60 200 Q 40 280 45 370 L 235 370 Q 240 280 220 200 Q 200 185 140 185 Q 80 185 60 200 Z"
          fill="url(#bodyGrad)"
          stroke="#00d4ff"
          strokeWidth="0.8"
          strokeOpacity="0.3"
        />

        {/* Left arm */}
        <path
          d="M 68 210 Q 30 250 20 310 Q 35 315 45 310 Q 55 265 80 230 Z"
          fill="url(#bodyGrad)"
          stroke="#00d4ff"
          strokeWidth="0.6"
          strokeOpacity="0.25"
        />

        {/* Right arm */}
        <path
          d="M 212 210 Q 250 250 260 310 Q 245 315 235 310 Q 225 265 200 230 Z"
          fill="url(#bodyGrad)"
          stroke="#00d4ff"
          strokeWidth="0.6"
          strokeOpacity="0.25"
        />

        {/* Laptop in hands */}
        <rect x="60" y="310" width="160" height="8" rx="2" fill="#1a2a3a" stroke="#00d4ff" strokeWidth="0.8" strokeOpacity="0.6" />
        <rect x="55" y="316" width="170" height="4" rx="1" fill="#0d1f2d" />
        {/* Screen glow */}
        <rect x="65" y="270" width="150" height="42" rx="3" fill="#0a1a28" stroke="#00d4ff" strokeWidth="1" strokeOpacity="0.5" />
        <rect x="68" y="273" width="144" height="36" rx="2" fill="#051015" />
        {/* Code on screen */}
        {[0, 1, 2, 3, 4].map(i => (
          <rect
            key={i}
            x={72 + (i % 2) * 8}
            y={277 + i * 6}
            width={20 + Math.sin(i * 2.1) * 30 + 30}
            height="2"
            rx="1"
            fill={i === 1 ? '#00ff88' : i === 3 ? '#00d4ff' : '#1e4060'}
            opacity={i === 1 || i === 3 ? 0.9 : 0.5}
          />
        ))}

        {/* Hood */}
        <path
          d="M 62 180 Q 55 120 95 90 Q 120 70 140 68 Q 160 70 185 90 Q 225 120 218 180 Q 200 170 180 168 Q 160 166 140 166 Q 120 166 100 168 Z"
          fill="#0d1520"
          stroke="#00d4ff"
          strokeWidth="0.8"
          strokeOpacity="0.4"
        />

        {/* Hood inner shadow */}
        <path
          d="M 70 175 Q 65 130 100 100 Q 120 80 140 78 Q 160 80 180 100 Q 215 130 210 175"
          fill="none"
          stroke="#00d4ff"
          strokeWidth="0.4"
          strokeOpacity="0.2"
        />

        {/* Face area — dark */}
        <ellipse cx="140" cy="152" rx="52" ry="60" fill="#060c14" />

        {/* GUY FAWKES / HACKER MASK */}
        {/* Mask base */}
        <ellipse cx="140" cy="152" rx="46" ry="54" fill="url(#maskGrad)" stroke="#00d4ff" strokeWidth="1" strokeOpacity="0.5" />

        {/* Mask forehead detail */}
        <path
          d="M 100 120 Q 115 108 140 106 Q 165 108 180 120"
          fill="none"
          stroke="#00d4ff"
          strokeWidth="0.8"
          strokeOpacity="0.6"
        />

        {/* Eyebrows — angled menacing */}
        <path d="M 106 130 L 128 136" stroke="#00d4ff" strokeWidth="2" strokeLinecap="round" filter="url(#glow)" />
        <path d="M 174 130 L 152 136" stroke="#00d4ff" strokeWidth="2" strokeLinecap="round" filter="url(#glow)" />

        {/* Eyes — glowing cyan visor style */}
        <ellipse cx="122" cy="144" rx="14" ry="8" fill="#001a25" stroke="#00d4ff" strokeWidth="1.2" filter="url(#glow)" />
        <ellipse cx="158" cy="144" rx="14" ry="8" fill="#001a25" stroke="#00d4ff" strokeWidth="1.2" filter="url(#glow)" />

        {/* Eye glow fill */}
        <ellipse cx="122" cy="144" rx="10" ry="5" fill="#00d4ff" opacity="0.25" />
        <ellipse cx="158" cy="144" rx="10" ry="5" fill="#00d4ff" opacity="0.25" />

        {/* Eye pupils / lens reflections */}
        <ellipse cx="119" cy="142" rx="3" ry="2" fill="#00d4ff" opacity="0.7" filter="url(#glowStrong)" />
        <ellipse cx="155" cy="142" rx="3" ry="2" fill="#00d4ff" opacity="0.7" filter="url(#glowStrong)" />

        {/* Nose ridge */}
        <path d="M 135 152 Q 132 163 138 168 Q 142 170 145 168 Q 151 163 148 152" fill="#0a1520" stroke="#1a3040" strokeWidth="0.8" />

        {/* Mask cheek ornaments */}
        <path d="M 96 148 Q 100 155 96 163" stroke="#00d4ff" strokeWidth="0.8" strokeOpacity="0.4" strokeLinecap="round" />
        <path d="M 184 148 Q 180 155 184 163" stroke="#00d4ff" strokeWidth="0.8" strokeOpacity="0.4" strokeLinecap="round" />

        {/* Mask smile — pointed Joker/Guy Fawkes style */}
        <path
          d="M 108 172 Q 120 165 140 168 Q 160 165 172 172 Q 162 185 155 188 Q 148 191 140 190 Q 132 191 125 188 Q 118 185 108 172 Z"
          fill="#0a1824"
          stroke="#00d4ff"
          strokeWidth="1"
          strokeOpacity="0.6"
        />
        {/* Smile teeth / line */}
        <path
          d="M 112 174 Q 126 168 140 171 Q 154 168 168 174"
          fill="none"
          stroke="#00d4ff"
          strokeWidth="0.8"
          strokeOpacity="0.8"
          filter="url(#glow)"
        />
        {/* Upturned smile corners */}
        <path d="M 108 172 Q 105 176 110 180" fill="none" stroke="#00d4ff" strokeWidth="1" strokeOpacity="0.5" />
        <path d="M 172 172 Q 175 176 170 180" fill="none" stroke="#00d4ff" strokeWidth="1" strokeOpacity="0.5" />

        {/* Mask chin */}
        <path d="M 116 190 Q 128 200 140 202 Q 152 200 164 190" fill="none" stroke="#00d4ff" strokeWidth="0.6" strokeOpacity="0.3" />

        {/* Vertical center line on mask */}
        <line x1="140" y1="106" x2="140" y2="202" stroke="#00d4ff" strokeWidth="0.4" strokeOpacity="0.15" strokeDasharray="3 4" />

        {/* Hoodie pocket detail */}
        <path
          d="M 95 300 Q 95 285 140 282 Q 185 285 185 300 Q 185 315 140 316 Q 95 315 95 300 Z"
          fill="none"
          stroke="#00d4ff"
          strokeWidth="0.6"
          strokeOpacity="0.25"
        />

        {/* Data stream lines on body */}
        {[245, 258, 271, 284, 297].map((y, i) => (
          <line
            key={i}
            x1={100 + i * 5}
            y1={y}
            x2={180 - i * 5}
            y2={y}
            stroke="#00d4ff"
            strokeWidth="0.4"
            strokeOpacity={0.08 + i * 0.02}
          />
        ))}
      </svg>

      {/* Floating data badges */}
      <div className="absolute top-8 -left-4 text-xs font-mono text-cyber-cyan bg-navy-900/90 border border-cyan-500/30 rounded px-2 py-1 animate-float" style={{ animationDelay: '1s' }}>
        <span className="text-green-400">●</span> SYSTEM BREACH DETECTED
      </div>
      <div className="absolute top-24 -right-6 text-xs font-mono text-cyber-cyan bg-navy-900/90 border border-cyan-500/30 rounded px-2 py-1 animate-float" style={{ animationDelay: '2.5s' }}>
        <span className="text-red-400">▲</span> THREAT LEVEL: CRITICAL
      </div>
      <div className="absolute bottom-20 -left-8 text-xs font-mono text-green-400 bg-navy-900/90 border border-green-500/30 rounded px-2 py-1 animate-float" style={{ animationDelay: '0.5s' }}>
        <span className="text-cyan-400">■</span> ARGUS NEUTRALIZING…
      </div>
      <div className="absolute bottom-36 -right-4 text-xs font-mono text-purple-400 bg-navy-900/90 border border-purple-500/30 rounded px-2 py-1 animate-float" style={{ animationDelay: '3s' }}>
        <span className="text-yellow-400">◆</span> 847 IOCs BLOCKED
      </div>
    </div>
  )
}

// ─── Glitch text ────────────────────────────────────────────────────────────

function GlitchText({ text, className = '' }: { text: string; className?: string }) {
  return (
    <span className={`relative inline-block ${className}`} style={{ animationName: 'glitch' }}>
      <span className="relative z-10">{text}</span>
      <span
        className="absolute inset-0 text-red-400 opacity-0"
        style={{
          animation: 'glitch 3s infinite',
          clipPath: 'polygon(0 30%, 100% 30%, 100% 50%, 0 50%)',
          transform: 'translateX(-2px)',
        }}
        aria-hidden="true"
      >
        {text}
      </span>
      <span
        className="absolute inset-0 text-blue-400 opacity-0"
        style={{
          animation: 'glitch 3s infinite 0.1s',
          clipPath: 'polygon(0 60%, 100% 60%, 100% 80%, 0 80%)',
          transform: 'translateX(2px)',
        }}
        aria-hidden="true"
      >
        {text}
      </span>
    </span>
  )
}

// ─── Counter animation ──────────────────────────────────────────────────────

function AnimatedCounter({ target, suffix = '', duration = 2000 }: { target: number; suffix?: string; duration?: number }) {
  const [count, setCount] = useState(0)
  const ref = useRef<HTMLSpanElement>(null)
  const started = useRef(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !started.current) {
          started.current = true
          const start = Date.now()
          const tick = () => {
            const elapsed = Date.now() - start
            const progress = Math.min(elapsed / duration, 1)
            const eased = 1 - Math.pow(1 - progress, 3)
            setCount(Math.floor(eased * target))
            if (progress < 1) requestAnimationFrame(tick)
          }
          requestAnimationFrame(tick)
        }
      },
      { threshold: 0.5 }
    )
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [target, duration])

  return <span ref={ref}>{count.toLocaleString()}{suffix}</span>
}

// ─── Feature card ───────────────────────────────────────────────────────────

function FeatureCard({
  icon: Icon, title, desc, delay = 0,
}: { icon: React.ElementType; title: string; desc: string; delay?: number }) {
  const [visible, setVisible] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) setVisible(true) },
      { threshold: 0.2 }
    )
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [])

  return (
    <div
      ref={ref}
      className="group relative bg-navy-800/60 border border-charcoal-600 rounded-2xl p-6 hover:border-cyan-500/40 transition-all duration-500 hover:bg-navy-800/80 cursor-default backdrop-blur-sm"
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(30px)',
        transition: `opacity 0.6s ease ${delay}ms, transform 0.6s ease ${delay}ms, border-color 0.3s, background 0.3s`,
      }}
    >
      {/* Hover glow */}
      <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
        style={{ boxShadow: 'inset 0 0 30px rgba(0,212,255,0.05)' }} />

      <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mb-4 group-hover:bg-cyan-500/20 group-hover:border-cyan-500/40 transition-all duration-300">
        <Icon className="w-6 h-6 text-cyber-cyan" />
      </div>
      <h3 className="text-lg font-semibold text-gray-100 mb-2 group-hover:text-cyber-cyan transition-colors duration-300">{title}</h3>
      <p className="text-sm text-gray-400 leading-relaxed">{desc}</p>

      {/* Bottom accent line */}
      <div className="absolute bottom-0 left-6 right-6 h-px bg-gradient-to-r from-transparent via-cyan-500/0 to-transparent group-hover:via-cyan-500/40 transition-all duration-500" />
    </div>
  )
}

// ─── Typewriter ─────────────────────────────────────────────────────────────

function Typewriter({ lines, speed = 60 }: { lines: string[]; speed?: number }) {
  const [lineIdx, setLineIdx] = useState(0)
  const [charIdx, setCharIdx] = useState(0)
  const [displayed, setDisplayed] = useState<string[]>([])

  useEffect(() => {
    if (lineIdx >= lines.length) return
    const current = lines[lineIdx]
    if (charIdx < current.length) {
      const t = setTimeout(() => setCharIdx(c => c + 1), speed)
      return () => clearTimeout(t)
    } else {
      const t = setTimeout(() => {
        setDisplayed(d => [...d, current])
        setLineIdx(l => l + 1)
        setCharIdx(0)
      }, 500)
      return () => clearTimeout(t)
    }
  }, [charIdx, lineIdx, lines, speed])

  const currentLine = lineIdx < lines.length ? lines[lineIdx].slice(0, charIdx) : ''

  return (
    <div className="font-mono text-sm text-left bg-navy-900/80 border border-charcoal-600 rounded-xl p-5 min-h-[140px]">
      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-charcoal-700">
        <div className="w-3 h-3 rounded-full bg-red-500/80" />
        <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
        <div className="w-3 h-3 rounded-full bg-green-500/80" />
        <span className="text-xs text-gray-500 ml-2">argus@defense:~$</span>
      </div>
      {displayed.map((line, i) => (
        <div key={i} className="text-green-400 mb-1">
          <span className="text-gray-500">» </span>{line}
        </div>
      ))}
      {lineIdx < lines.length && (
        <div className="text-cyber-cyan">
          <span className="text-gray-500">» </span>{currentLine}
          <span className="animate-pulse">█</span>
        </div>
      )}
    </div>
  )
}

// ─── Main Landing Page ──────────────────────────────────────────────────────

const FEATURES = [
  {
    icon: Eye,
    title: 'Real-Time Threat Visibility',
    desc: 'Monitor every security event across your infrastructure with millisecond precision. Full-spectrum visibility from endpoint to cloud.',
  },
  {
    icon: Zap,
    title: 'AI-Powered Detection',
    desc: 'Machine learning models that evolve with your threat landscape. Detect zero-days, APTs, and insider threats before damage is done.',
  },
  {
    icon: Shield,
    title: 'Automated Incident Response',
    desc: 'Automatically triage, correlate, and respond to threats. Cut your mean time to respond from hours to seconds.',
  },
  {
    icon: Activity,
    title: 'Behavioral Analytics',
    desc: 'UEBA engine profiles normal behavior baselines and instantly flags anomalies — credential stuffing, lateral movement, data exfil.',
  },
  {
    icon: Globe,
    title: 'Global Threat Intelligence',
    desc: 'Live IOC feeds from VirusTotal, AbuseIPDB, and proprietary sources. Every event cross-referenced against 850M+ known threats.',
  },
  {
    icon: Lock,
    title: 'Enterprise-Grade RBAC',
    desc: 'Granular role-based access control. Analysts see what they need. Admins control everything. Auditors get read-only logs.',
  },
]

const TERMINAL_LINES = [
  'Initializing ARGUS threat detection engine…',
  'Loading 12 active detection rules…',
  'Connected to threat intelligence feeds…',
  'Monitoring 54 security events in real-time…',
  'Status: ALL SYSTEMS OPERATIONAL ✓',
]

export default function LandingPage() {
  const [scrolled, setScrolled] = useState(false)
  const heroRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const scrollToFeatures = () => {
    document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="min-h-screen bg-navy-950 text-gray-100 overflow-x-hidden">
      <ParticleCanvas />

      {/* ── NAVBAR ── */}
      <nav
        className="fixed top-0 left-0 right-0 z-50 transition-all duration-300"
        style={{
          background: scrolled
            ? 'rgba(8,13,20,0.95)'
            : 'rgba(8,13,20,0.6)',
          backdropFilter: 'blur(12px)',
          borderBottom: scrolled ? '1px solid rgba(0,212,255,0.15)' : '1px solid transparent',
        }}
      >
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="relative w-9 h-9">
              <div className="absolute inset-0 bg-cyan-500/20 rounded-lg rotate-45 animate-pulse-slow" />
              <div className="absolute inset-0 flex items-center justify-center">
                <Eye className="w-5 h-5 text-cyber-cyan" />
              </div>
            </div>
            <span className="text-xl font-bold tracking-[0.2em] font-mono text-gray-100">
              ARG<span className="text-cyber-cyan">US</span>
            </span>
          </div>

          {/* Center nav links */}
          <div className="hidden md:flex items-center gap-8">
            {['Features', 'Platform', 'Intelligence'].map(item => (
              <button
                key={item}
                onClick={() => document.getElementById(item.toLowerCase())?.scrollIntoView({ behavior: 'smooth' })}
                className="text-sm text-gray-400 hover:text-cyber-cyan transition-colors duration-200 font-medium tracking-wide"
              >
                {item}
              </button>
            ))}
          </div>

          {/* Auth buttons */}
          <div className="flex items-center gap-3">
            <Link
              to="/login"
              className="px-4 py-2 text-sm font-semibold text-cyber-cyan border border-cyan-500/40 rounded-lg hover:bg-cyan-500/10 hover:border-cyan-500/70 transition-all duration-200 tracking-wide"
            >
              Sign In
            </Link>
            <Link
              to="/register"
              className="px-4 py-2 text-sm font-semibold bg-cyber-cyan text-navy-950 rounded-lg hover:bg-cyan-400 active:scale-95 transition-all duration-200 tracking-wide shadow-lg"
              style={{ boxShadow: '0 0 20px rgba(0,212,255,0.3)' }}
            >
              Get Access
            </Link>
          </div>
        </div>
      </nav>

      {/* ── HERO SECTION ── */}
      <section
        ref={heroRef}
        className="relative min-h-screen flex items-center pt-16"
        style={{ zIndex: 1 }}
      >
        <div className="max-w-7xl mx-auto px-6 w-full">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left — copy */}
            <div className="relative z-10">
              {/* Badge */}
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-cyan-500/30 bg-cyan-500/5 text-xs font-mono text-cyber-cyan mb-6 animate-fade-in">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                AI-POWERED SOC PLATFORM · LIVE THREAT DETECTION
              </div>

              {/* Headline */}
              <h1 className="text-5xl xl:text-7xl font-black tracking-tight leading-none mb-6 opacity-0 animate-slide-up" style={{ animationFillMode: 'forwards' }}>
                <span className="block text-gray-100">DEFEND.</span>
                <span className="block text-gray-100">DETECT.</span>
                <span className="block">
                  <GlitchText
                    text="DESTROY."
                    className="text-transparent bg-clip-text"
                    // inline gradient
                  />
                  <span
                    className="text-transparent bg-clip-text ml-0"
                    style={{ backgroundImage: 'linear-gradient(90deg, #00d4ff, #00ff88)' }}
                  >
                    {' '}THREATS.
                  </span>
                </span>
              </h1>

              <p className="text-lg text-gray-400 leading-relaxed mb-8 max-w-xl opacity-0 animate-slide-up-delay" style={{ animationFillMode: 'forwards' }}>
                ARGUS gives your security team an all-seeing eye over your infrastructure.
                Real-time event correlation, AI-assisted triage, and automated response
                — built for security operations teams that can't afford to miss a thing.
              </p>

              {/* CTA buttons */}
              <div className="flex flex-wrap gap-4 mb-10 opacity-0 animate-slide-up-delay2" style={{ animationFillMode: 'forwards' }}>
                <Link
                  to="/register"
                  className="group inline-flex items-center gap-2 px-6 py-3 bg-cyber-cyan text-navy-950 font-bold rounded-xl text-sm hover:bg-cyan-400 transition-all duration-200 shadow-xl"
                  style={{ boxShadow: '0 0 30px rgba(0,212,255,0.4)' }}
                >
                  Start Free Trial
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </Link>
                <Link
                  to="/login"
                  className="inline-flex items-center gap-2 px-6 py-3 border border-charcoal-500 text-gray-300 rounded-xl text-sm hover:border-cyan-500/50 hover:text-cyber-cyan transition-all duration-200"
                >
                  <Terminal className="w-4 h-4" />
                  Live Demo
                </Link>
              </div>

              {/* Trust indicators */}
              <div className="flex flex-wrap items-center gap-5 text-xs text-gray-500">
                {[
                  { icon: CheckCircle, text: 'No credit card required' },
                  { icon: Lock, text: 'SOC 2 compliant' },
                  { icon: Shield, text: 'End-to-end encrypted' },
                ].map(({ icon: Icon, text }) => (
                  <div key={text} className="flex items-center gap-1.5">
                    <Icon className="w-3.5 h-3.5 text-green-400" />
                    <span>{text}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Right — hacker figure */}
            <div className="relative flex justify-center lg:justify-end items-center">
              <HackerFigure />
            </div>
          </div>
        </div>

        {/* Scroll hint */}
        <button
          onClick={scrollToFeatures}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-gray-500 hover:text-cyber-cyan transition-colors"
          aria-label="Scroll to features"
        >
          <span className="text-xs font-mono tracking-widest">SCROLL</span>
          <ChevronDown className="w-5 h-5 animate-bounce" />
        </button>
      </section>

      {/* ── STATS BAR ── */}
      <section className="relative z-10 border-y border-charcoal-700/50 bg-navy-900/40 backdrop-blur-sm py-10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { value: 99, suffix: '.9%', label: 'Platform Uptime' },
              { value: 850, suffix: 'M+', label: 'Threats in DB' },
              { value: 12, suffix: 'ms', label: 'Avg Detection Time' },
              { value: 7, suffix: ' rules', label: 'Detection Engines' },
            ].map(({ value, suffix, label }) => (
              <div key={label} className="text-center">
                <div className="text-3xl md:text-4xl font-black font-mono text-cyber-cyan mb-1">
                  <AnimatedCounter target={value} suffix={suffix} />
                </div>
                <div className="text-xs text-gray-500 uppercase tracking-widest font-semibold">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section id="features" className="relative z-10 py-24 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Section header */}
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-purple-500/30 bg-purple-500/5 text-xs font-mono text-purple-400 mb-4">
              <Zap className="w-3 h-3" />
              CORE CAPABILITIES
            </div>
            <h2 className="text-4xl md:text-5xl font-black text-gray-100 mb-4">
              Everything your SOC
              <span className="text-transparent bg-clip-text ml-3" style={{ backgroundImage: 'linear-gradient(90deg, #00d4ff, #00ff88)' }}>
                needs.
              </span>
            </h2>
            <p className="text-gray-400 max-w-2xl mx-auto text-lg">
              A complete security operations platform — from raw event ingestion to AI-assisted forensics.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((f, i) => (
              <FeatureCard key={f.title} {...f} delay={i * 80} />
            ))}
          </div>
        </div>
      </section>

      {/* ── PLATFORM PREVIEW ── */}
      <section id="platform" className="relative z-10 py-24 px-6 bg-navy-900/30">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Terminal demo */}
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-cyan-500/30 bg-cyan-500/5 text-xs font-mono text-cyber-cyan mb-6">
                <Terminal className="w-3 h-3" />
                LIVE PLATFORM DEMO
              </div>
              <h2 className="text-4xl font-black text-gray-100 mb-4">
                See threats
                <span className="text-cyber-cyan"> before they strike.</span>
              </h2>
              <p className="text-gray-400 mb-8 leading-relaxed">
                ARGUS monitors every packet, every login, every file access.
                The detection engine runs 7 parallel rule sets, from brute-force
                detection to AI-powered anomaly scoring — all in real-time.
              </p>
              <Typewriter lines={TERMINAL_LINES} />
            </div>

            {/* Threat metrics panel */}
            <div className="space-y-4" id="intelligence">
              <div className="bg-navy-800/60 border border-charcoal-600 rounded-2xl p-6 backdrop-blur-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-gray-200 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-orange-400" />
                    Active Threat Indicators
                  </h3>
                  <span className="text-xs font-mono text-green-400 bg-green-400/10 px-2 py-1 rounded">LIVE</span>
                </div>
                {[
                  { type: 'Brute Force', count: 847, severity: 'CRITICAL', color: 'bg-red-500' },
                  { type: 'Port Scan', count: 234, severity: 'HIGH', color: 'bg-orange-500' },
                  { type: 'IOC Match', count: 112, severity: 'HIGH', color: 'bg-orange-400' },
                  { type: 'Credential Stuffing', count: 67, severity: 'MEDIUM', color: 'bg-yellow-500' },
                  { type: 'Privilege Escalation', count: 12, severity: 'CRITICAL', color: 'bg-red-600' },
                ].map(({ type, count, severity, color }) => (
                  <div key={type} className="flex items-center gap-3 py-2 border-b border-charcoal-700/50 last:border-0">
                    <div className={`w-2 h-2 rounded-full ${color} animate-pulse`} />
                    <span className="text-sm text-gray-300 flex-1">{type}</span>
                    <span className="text-sm font-mono text-gray-400">{count.toLocaleString()}</span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                      severity === 'CRITICAL' ? 'text-red-400 bg-red-400/10' :
                      severity === 'HIGH' ? 'text-orange-400 bg-orange-400/10' :
                      'text-yellow-400 bg-yellow-400/10'
                    }`}>{severity}</span>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-navy-800/60 border border-charcoal-600 rounded-2xl p-5 text-center backdrop-blur-sm">
                  <BarChart3 className="w-8 h-8 text-cyber-cyan mx-auto mb-2" />
                  <div className="text-2xl font-black font-mono text-cyber-cyan">98.7%</div>
                  <div className="text-xs text-gray-500 mt-1">Detection Accuracy</div>
                </div>
                <div className="bg-navy-800/60 border border-charcoal-600 rounded-2xl p-5 text-center backdrop-blur-sm">
                  <Zap className="w-8 h-8 text-green-400 mx-auto mb-2" />
                  <div className="text-2xl font-black font-mono text-green-400">&lt;30s</div>
                  <div className="text-xs text-gray-500 mt-1">Alert Response Time</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA SECTION ── */}
      <section className="relative z-10 py-32 px-6 overflow-hidden">
        {/* Background glow */}
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] rounded-full bg-cyan-500/5 blur-3xl" />
          <div className="absolute left-1/3 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[300px] rounded-full bg-blue-500/5 blur-3xl" />
        </div>

        <div className="max-w-4xl mx-auto text-center relative">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-cyan-500/30 bg-cyan-500/5 text-xs font-mono text-cyber-cyan mb-6">
            <Shield className="w-3 h-3" />
            READY TO SECURE YOUR INFRASTRUCTURE?
          </div>

          <h2 className="text-5xl md:text-6xl font-black text-gray-100 mb-6 leading-tight">
            Your threats are{' '}
            <span
              className="text-transparent bg-clip-text"
              style={{ backgroundImage: 'linear-gradient(90deg, #00d4ff, #00ff88, #00d4ff)', backgroundSize: '200%' }}
            >
              watching.
            </span>
            <br />
            So is ARGUS.
          </h2>

          <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto leading-relaxed">
            Join security teams that trust ARGUS to protect their infrastructure
            around the clock. Deploy in minutes, monitor everything, fear nothing.
          </p>

          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/register"
              className="group inline-flex items-center gap-2 px-8 py-4 bg-cyber-cyan text-navy-950 font-black rounded-xl text-base hover:bg-cyan-400 transition-all duration-200 shadow-2xl"
              style={{ boxShadow: '0 0 40px rgba(0,212,255,0.5)' }}
            >
              Create Free Account
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              to="/login"
              className="inline-flex items-center gap-2 px-8 py-4 border border-charcoal-500 text-gray-300 rounded-xl text-base hover:border-cyan-500/50 hover:text-cyber-cyan transition-all duration-200"
            >
              Sign In to Dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="relative z-10 border-t border-charcoal-700/50 py-8 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Eye className="w-4 h-4 text-cyber-cyan" />
            <span className="font-mono text-sm tracking-widest text-gray-400">
              ARG<span className="text-cyber-cyan">US</span> v1.0.0
            </span>
          </div>
          <p className="text-xs text-gray-600">
            AI-Powered Threat Intelligence & Cyber Defense Platform · Authorized access only
          </p>
          <div className="flex gap-4">
            <Link to="/login" className="text-xs text-gray-500 hover:text-cyber-cyan transition-colors">Sign In</Link>
            <Link to="/register" className="text-xs text-gray-500 hover:text-cyber-cyan transition-colors">Register</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}

// Design-system primitives

// ─── Icons ────────────────────────────────────────────────────────────────────
const IC = ({ d, size = 16, fill = false, ...p }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill={fill ? 'currentColor' : 'none'}
    stroke={fill ? 'none' : 'currentColor'}
    strokeWidth="1.75"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...p}
  >
    {d}
  </svg>
)

export const Icons = {
  Sparkle: (p) => (
    <IC size={p.size} {...p}>
      <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z" />
    </IC>
  ),
  File: (p) => (
    <IC size={p.size} {...p}>
      <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" />
      <path d="M14 2v4a2 2 0 0 0 2 2h4" />
      <path d="M10 9H8" /><path d="M16 13H8" /><path d="M16 17H8" />
    </IC>
  ),
  Zap: (p) => (
    <IC size={p.size} {...p}>
      <path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z" />
    </IC>
  ),
  CheckCircle: (p) => (
    <IC size={p.size} {...p}>
      <circle cx="12" cy="12" r="10" />
      <path d="m9 12 2 2 4-4" />
    </IC>
  ),
  Clock: (p) => (
    <IC size={p.size} {...p}>
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </IC>
  ),
  Lock: (p) => (
    <IC size={p.size} {...p}>
      <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </IC>
  ),
  Search: (p) => (
    <IC size={p.size} {...p}>
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.3-4.3" />
    </IC>
  ),
  BarChart: (p) => (
    <IC size={p.size} {...p}>
      <line x1="12" x2="12" y1="20" y2="10" />
      <line x1="18" x2="18" y1="20" y2="4" />
      <line x1="6" x2="6" y1="20" y2="16" />
    </IC>
  ),
  Send: (p) => (
    <IC size={p.size} {...p}>
      <path d="m22 2-7 20-4-9-9-4Z" />
      <path d="M22 2 11 13" />
    </IC>
  ),
  Mic: (p) => (
    <IC size={p.size} {...p}>
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" x2="12" y1="19" y2="22" />
    </IC>
  ),
  ArrowLeft: (p) => (
    <IC size={p.size} {...p}>
      <path d="m12 19-7-7 7-7" />
      <path d="M19 12H5" />
    </IC>
  ),
  Plus: (p) => (
    <IC size={p.size} {...p}>
      <path d="M5 12h14" /><path d="M12 5v14" />
    </IC>
  ),
  RefreshCw: (p) => (
    <IC size={p.size} {...p}>
      <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
      <path d="M21 3v5h-5" />
      <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
      <path d="M8 16H3v5" />
    </IC>
  ),
  Check: (p) => (
    <IC size={p.size} {...p}>
      <path d="M20 6 9 17l-5-5" />
    </IC>
  ),
  AlertTriangle: (p) => (
    <IC size={p.size} {...p}>
      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
      <path d="M12 9v4" /><path d="M12 17h.01" />
    </IC>
  ),
  Shield: (p) => (
    <IC size={p.size} {...p}>
      <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" />
    </IC>
  ),
  Compass: (p) => (
    <IC size={p.size} {...p}>
      <circle cx="12" cy="12" r="10" />
      <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
    </IC>
  ),
  ChevronRight: (p) => (
    <IC size={p.size} {...p}>
      <path d="m9 18 6-6-6-6" />
    </IC>
  ),
}

// ─── Platform icons ────────────────────────────────────────────────────────────
export const PlatformIcon = ({ platform, size = 18 }) => {
  const s = size
  switch (platform?.toLowerCase()) {
    case 'linkedin':
      return (
        <svg width={s} height={s} viewBox="0 0 24 24" fill="#0A66C2">
          <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
          <rect width="4" height="12" x="2" y="9" />
          <circle cx="4" cy="4" r="2" />
        </svg>
      )
    case 'instagram':
      return (
        <svg width={s} height={s} viewBox="0 0 24 24" fill="none">
          <defs>
            <linearGradient id="ig-grad" x1="0" y1="1" x2="1" y2="0">
              <stop offset="0%" stopColor="#FCAF45" />
              <stop offset="40%" stopColor="#E1306C" />
              <stop offset="100%" stopColor="#833AB4" />
            </linearGradient>
          </defs>
          <rect x="2" y="2" width="20" height="20" rx="5" ry="5" stroke="url(#ig-grad)" strokeWidth="2" />
          <circle cx="12" cy="12" r="4" stroke="url(#ig-grad)" strokeWidth="2" />
          <circle cx="17.5" cy="6.5" r="1.5" fill="url(#ig-grad)" />
        </svg>
      )
    case 'twitter':
      return (
        <svg width={s} height={s} viewBox="0 0 24 24" fill="currentColor" className="text-ink-1">
          <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
        </svg>
      )
    case 'facebook':
      return (
        <svg width={s} height={s} viewBox="0 0 24 24" fill="#1877F2">
          <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z" />
        </svg>
      )
    case 'tiktok':
      return (
        <svg width={s} height={s} viewBox="0 0 24 24" fill="currentColor" className="text-ink-1">
          <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1-2.89-2.89 2.89 2.89 0 0 1 2.89-2.89c.28 0 .54.04.79.1V9.01a6.34 6.34 0 0 0-.79-.05 6.34 6.34 0 0 0-6.34 6.34 6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.33-6.34l-.01-9.33a8.25 8.25 0 0 0 4.83 1.54V4.07a4.85 4.85 0 0 1-1.05-.38z" />
        </svg>
      )
    default:
      return (
        <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
          <rect width="20" height="20" x="2" y="2" rx="5" />
          <path d="M12 8v8M8 12h8" />
        </svg>
      )
  }
}

// ─── Button ───────────────────────────────────────────────────────────────────
export function Button({ variant = 'primary', size = 'md', className = '', children, ...props }) {
  const base =
    'inline-flex items-center justify-center gap-2 font-medium transition-all duration-150 disabled:cursor-not-allowed disabled:opacity-40 select-none'

  const variants = {
    primary:
      'rounded-lg bg-violet-600 text-white hover:bg-violet-500 active:bg-violet-700 shadow-sm ' +
      'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500',
    secondary:
      'rounded-lg border border-border bg-surface-2 text-ink-1 hover:bg-surface-3 hover:border-border-strong active:bg-surface-1 ' +
      'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500',
    ghost:
      'rounded-lg text-ink-2 hover:text-ink-1 hover:bg-surface-2 active:bg-surface-3 ' +
      'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500',
    success:
      'rounded-lg bg-emerald-600 text-white hover:bg-emerald-500 active:bg-emerald-700 shadow-sm',
    danger:
      'rounded-lg bg-rose-600/15 text-rose-400 border border-rose-500/30 hover:bg-rose-600/25',
  }

  const sizes = {
    sm: 'px-2.5 py-1.5 text-xs',
    md: 'px-3.5 py-2 text-sm',
    lg: 'px-5 py-2.5 text-sm',
  }

  return (
    <button className={`${base} ${variants[variant]} ${sizes[size]} ${className}`} {...props}>
      {children}
    </button>
  )
}

// ─── Badge ────────────────────────────────────────────────────────────────────
export function Badge({ tone = 'default', className = '', children }) {
  const tones = {
    default: 'bg-surface-3 text-ink-2 border border-border',
    violet: 'bg-violet-500/15 text-violet-300 border border-violet-500/25',
    green: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25',
    amber: 'bg-amber-500/15 text-amber-400 border border-amber-500/25',
    red: 'bg-rose-500/15 text-rose-400 border border-rose-500/25',
    cyan: 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/25',
    soon: 'bg-surface-3 text-ink-3 border border-border text-[10px] tracking-wide uppercase',
  }
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${tones[tone]} ${className}`}
    >
      {children}
    </span>
  )
}

// ─── Spinner ──────────────────────────────────────────────────────────────────
export function Spinner({ size = 16, className = '' }) {
  return (
    <svg
      className={`animate-spin ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle
        className="opacity-20"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="3"
      />
      <path
        className="opacity-80"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  )
}

// ─── Field ────────────────────────────────────────────────────────────────────
export function Field({ label, hint, required, children, className = '' }) {
  return (
    <div className={`space-y-1.5 ${className}`}>
      <label className="flex items-center gap-1">
        <span className="text-sm font-medium text-ink-1">{label}</span>
        {required && <span className="text-violet-400">*</span>}
      </label>
      {children}
      {hint && <p className="text-xs text-ink-3">{hint}</p>}
    </div>
  )
}

// ─── Input / Textarea ─────────────────────────────────────────────────────────
export function Input({ className = '', ...props }) {
  return (
    <input
      className={`input-base ${className}`}
      {...props}
    />
  )
}

export function Textarea({ className = '', ...props }) {
  return (
    <textarea
      className={`input-base resize-none ${className}`}
      {...props}
    />
  )
}

// ─── ScoreBar ─────────────────────────────────────────────────────────────────
export function ScoreBar({ label, value, maxValue = 5 }) {
  const pct = (value / maxValue) * 100
  const color =
    value >= 4 ? 'bg-emerald-500' : value >= 3 ? 'bg-amber-500' : 'bg-rose-500'
  const textColor =
    value >= 4 ? 'text-emerald-400' : value >= 3 ? 'text-amber-400' : 'text-rose-400'

  return (
    <div className="flex items-center gap-3">
      <span className="w-24 shrink-0 text-xs text-ink-3">{label}</span>
      <div className="flex-1 h-1.5 rounded-full bg-surface-3 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`w-5 text-right text-xs font-semibold tabular-nums ${textColor}`}>
        {value}
      </span>
    </div>
  )
}

// ─── ScoreRing ────────────────────────────────────────────────────────────────
export function ScoreRing({ value, maxValue = 5, size = 56 }) {
  const pct = value / maxValue
  const r = 22
  const circ = 2 * Math.PI * r
  const dash = pct * circ
  const gap = circ - dash

  const color =
    value >= 4 ? '#10B981' : value >= 3 ? '#F59E0B' : '#F43F5E'
  const trackColor = '#1D1F2A'

  return (
    <svg width={size} height={size} viewBox="0 0 50 50">
      <circle cx="25" cy="25" r={r} fill="none" stroke={trackColor} strokeWidth="4" />
      <circle
        cx="25"
        cy="25"
        r={r}
        fill="none"
        stroke={color}
        strokeWidth="4"
        strokeLinecap="round"
        strokeDasharray={`${dash} ${gap}`}
        strokeDashoffset={circ * 0.25}
        style={{ transition: 'stroke-dasharray 0.7s ease-out' }}
      />
      <text
        x="25"
        y="25"
        textAnchor="middle"
        dominantBaseline="central"
        fill={color}
        fontSize="12"
        fontWeight="600"
        fontFamily="Inter, sans-serif"
      >
        {value}
      </text>
    </svg>
  )
}

// ─── Divider ──────────────────────────────────────────────────────────────────
export function Divider({ className = '' }) {
  return <div className={`h-px bg-border ${className}`} />
}

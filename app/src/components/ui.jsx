// Small shared UI primitives.

export function Badge({ tone = 'slate', children }) {
  const tones = {
    slate: 'bg-slate-700/60 text-slate-200',
    green: 'bg-emerald-600/20 text-emerald-300 ring-1 ring-emerald-500/30',
    red: 'bg-rose-600/20 text-rose-300 ring-1 ring-rose-500/30',
    amber: 'bg-amber-600/20 text-amber-300 ring-1 ring-amber-500/30',
    indigo: 'bg-indigo-600/20 text-indigo-300 ring-1 ring-indigo-500/30',
  }
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${tones[tone]}`}>
      {children}
    </span>
  )
}

export function Spinner({ className = '' }) {
  return (
    <svg className={`animate-spin h-4 w-4 ${className}`} viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
  )
}

// A labeled 1-5 rubric dimension bar.
export function ScoreBar({ label, value }) {
  const pct = (value / 5) * 100
  const color = value >= 4 ? 'bg-emerald-500' : value >= 3 ? 'bg-amber-500' : 'bg-rose-500'
  return (
    <div className="flex items-center gap-3">
      <span className="w-28 shrink-0 text-xs text-slate-400">{label}</span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-800">
        <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-6 text-right text-xs tabular-nums text-slate-300">{value}</span>
    </div>
  )
}

export function Field({ label, hint, children }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-slate-300">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-slate-500">{hint}</span>}
    </label>
  )
}

export const inputClass =
  'w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 ' +
  'placeholder-slate-500 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500'

import { useState } from 'react'
import { Button, Spinner } from './ui'

const PLATFORM_LABELS = {
  linkedin: 'LinkedIn',
  instagram: 'Instagram',
  twitter: 'Twitter / X',
  facebook: 'Facebook',
  tiktok: 'TikTok',
}

function toLocalDatetimeValue(d) {
  // Returns a string compatible with <input type="datetime-local">
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function minDatetimeValue() {
  const d = new Date(Date.now() + 5 * 60 * 1000) // 5 min from now
  return toLocalDatetimeValue(d)
}

export default function PublishModal({ platform, onClose, onPublish }) {
  const [tab, setTab] = useState('now') // 'now' | 'schedule'
  const [scheduledAt, setScheduledAt] = useState(() => {
    const d = new Date(Date.now() + 60 * 60 * 1000) // 1 hour from now
    return toLocalDatetimeValue(d)
  })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const label = PLATFORM_LABELS[platform] ?? platform

  const handleAction = async () => {
    setError(null)
    setBusy(true)
    try {
      const opts = tab === 'schedule'
        ? { scheduledAt: new Date(scheduledAt).toISOString() }
        : {}
      const res = await onPublish(opts)
      setResult(res)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    // Backdrop
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-md rounded-2xl border border-border bg-surface-1 shadow-2xl animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <div>
            <h2 className="text-sm font-semibold text-ink-1">Publish to {label}</h2>
            <p className="text-xs text-ink-3">Choose when this post goes live</p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-ink-4 transition hover:bg-surface-2 hover:text-ink-1"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-5">
          {result ? (
            // Success state
            <div className="space-y-4">
              <div className={`flex items-start gap-3 rounded-xl border px-4 py-3 ${
                result.status === 'published'
                  ? 'border-emerald-500/25 bg-emerald-500/10'
                  : 'border-violet-500/25 bg-violet-500/10'
              }`}>
                <svg
                  width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                  className={`mt-0.5 shrink-0 ${result.status === 'published' ? 'text-emerald-400' : 'text-violet-400'}`}
                >
                  <path d="M20 6 9 17l-5-5"/>
                </svg>
                <div>
                  <p className={`text-sm font-medium ${result.status === 'published' ? 'text-emerald-300' : 'text-violet-300'}`}>
                    {result.status === 'published' ? 'Published!' : 'Scheduled'}
                  </p>
                  <p className="mt-0.5 text-xs text-ink-3">
                    {result.status === 'published'
                      ? `Live on ${label}`
                      : `Queued for ${new Date(result.scheduled_at).toLocaleString()}`}
                  </p>
                  {result.url && result.status === 'published' && (
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-1 inline-flex items-center gap-1 text-xs text-emerald-400 hover:underline"
                    >
                      View post
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                        <polyline points="15 3 21 3 21 9"/><line x1="10" x2="21" y1="14" y2="3"/>
                      </svg>
                    </a>
                  )}
                </div>
              </div>
              <Button variant="secondary" size="md" onClick={onClose} className="w-full">
                Done
              </Button>
            </div>
          ) : (
            <>
              {/* Tab switcher */}
              <div className="flex rounded-lg border border-border bg-surface-2 p-1 gap-1">
                {[
                  { key: 'now', label: 'Publish now' },
                  { key: 'schedule', label: 'Schedule' },
                ].map(({ key, label: tabLabel }) => (
                  <button
                    key={key}
                    onClick={() => setTab(key)}
                    className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition ${
                      tab === key
                        ? 'bg-surface-1 text-ink-1 shadow-sm'
                        : 'text-ink-3 hover:text-ink-2'
                    }`}
                  >
                    {tabLabel}
                  </button>
                ))}
              </div>

              {tab === 'now' && (
                <div className="rounded-lg border border-border bg-surface-2 px-4 py-3 text-xs text-ink-2 leading-relaxed">
                  This asset will be posted to <strong className="text-ink-1">{label}</strong> immediately using the configured publisher.
                </div>
              )}

              {tab === 'schedule' && (
                <div className="space-y-2">
                  <label className="block text-xs font-medium text-ink-2">Publish at</label>
                  <input
                    type="datetime-local"
                    value={scheduledAt}
                    min={minDatetimeValue()}
                    onChange={(e) => setScheduledAt(e.target.value)}
                    className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-xs text-ink-1 focus:outline-none focus:ring-1 focus:ring-violet-500/50"
                  />
                  <p className="text-[10px] text-ink-4">
                    The post will be queued. A background worker executes scheduled posts.
                  </p>
                </div>
              )}

              {error && (
                <p className="rounded-lg border border-rose-500/25 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">
                  {error}
                </p>
              )}

              <div className="flex gap-2">
                <Button variant="secondary" size="md" onClick={onClose} disabled={busy}>
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="md"
                  onClick={handleAction}
                  disabled={busy}
                  className="flex-1"
                >
                  {busy ? (
                    <><Spinner size={13} /> {tab === 'now' ? 'Publishing…' : 'Scheduling…'}</>
                  ) : (
                    tab === 'now' ? 'Publish now' : 'Schedule post'
                  )}
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

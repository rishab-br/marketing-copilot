import { useEffect, useRef, useState } from 'react'
import { streamCampaign } from '../api'
import { Badge, PlatformIcon, Spinner } from './ui'

const NODE_META = {
  strategist: {
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>
      </svg>
    ),
    label: 'Strategist',
    desc: 'Planning angle & key messages',
    color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
    dot: 'bg-cyan-500',
  },
  copywriter: {
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
        <path d="m15 5 4 4"/>
      </svg>
    ),
    label: 'Copywriter',
    desc: 'Drafting platform-specific copy',
    color: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
    dot: 'bg-violet-500',
  },
  critic: {
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>
      </svg>
    ),
    label: 'Critic',
    desc: 'Guardrails + rubric scoring',
    color: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    dot: 'bg-amber-500',
  },
  finalize: {
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <path d="m9 12 2 2 4-4"/>
      </svg>
    ),
    label: 'Finalize',
    desc: 'Run complete',
    color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    dot: 'bg-emerald-500',
  },
}

function ScoreChip({ platform, overall, guardrail_passed }) {
  const pass = guardrail_passed && overall >= 4
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium ${
        pass
          ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-400'
          : 'border-amber-500/20 bg-amber-500/10 text-amber-400'
      }`}
    >
      <PlatformIcon platform={platform} size={11} />
      {platform}
      <span className="font-semibold">{overall}</span>
      {!guardrail_passed && (
        <span className="opacity-70">⚠</span>
      )}
    </span>
  )
}

function StepPayload({ node, payload }) {
  if (node === 'strategist')
    return (
      <p className="text-xs text-ink-2">
        Angle:{' '}
        <span className="text-ink-1">"{payload.angle}"</span>
      </p>
    )

  if (node === 'copywriter')
    return (
      <p className="text-xs text-ink-2">
        Iteration {payload.iteration} · drafting{' '}
        <span className="text-ink-1">{payload.platforms?.join(', ')}</span>
      </p>
    )

  if (node === 'critic')
    return (
      <div className="flex flex-wrap gap-1.5 pt-0.5">
        {payload.assets?.map((a) => (
          <ScoreChip key={a.platform} {...a} />
        ))}
      </div>
    )

  if (node === 'finalize')
    return payload.needs_human_attention ? (
      <Badge tone="amber">Max iterations reached — needs review</Badge>
    ) : (
      <Badge tone="green">All assets passed the quality gate</Badge>
    )

  return null
}

export default function RunProgress({ campaignId, onComplete, onError }) {
  const [steps, setSteps] = useState([])
  const [done, setDone] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    setSteps([])
    setDone(false)

    const es = streamCampaign(campaignId, {
      onNode: (ev) => setSteps((s) => [...s, ev]),
      onComplete: (ev) => {
        setDone(true)
        onComplete?.(ev)
      },
      onError: (err) => onError?.(err?.message ?? 'stream error'),
    })

    return () => es.close()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId])

  // Auto-scroll to bottom as steps come in
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [steps])

  return (
    <div className="animate-fade-in space-y-6">
      {/* Status banner */}
      <div
        className={`flex items-center gap-3 rounded-xl border px-4 py-3 ${
          done
            ? 'border-emerald-500/25 bg-emerald-500/8'
            : 'border-violet-500/25 bg-violet-500/8'
        }`}
      >
        {done ? (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10B981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>
          </svg>
        ) : (
          <Spinner size={16} className="text-violet-400" />
        )}
        <div>
          <p className={`text-sm font-medium ${done ? 'text-emerald-400' : 'text-violet-300'}`}>
            {done ? 'Run complete — loading results…' : 'Agents running'}
          </p>
          <p className="text-xs text-ink-3">
            {done
              ? 'Switching to review screen.'
              : 'Watch the strategist → copywriter ↔ critic loop in real time.'}
          </p>
        </div>
      </div>

      {/* Timeline */}
      <div className="relative">
        {/* Connecting line */}
        {steps.length > 1 && (
          <div className="absolute left-[19px] top-8 bottom-8 w-px bg-border" />
        )}

        <ol className="space-y-3">
          {steps.length === 0 && (
            <li className="flex items-center gap-3 rounded-xl border border-dashed border-border px-5 py-6 text-center">
              <div className="flex-1 text-center text-sm text-ink-3">
                Connecting to agent stream…
              </div>
            </li>
          )}

          {steps.map((step, i) => {
            const meta = NODE_META[step.node] ?? {
              icon: <span className="text-xs">●</span>,
              label: step.node,
              desc: '',
              color: 'bg-surface-3 text-ink-2 border-border',
              dot: 'bg-ink-3',
            }

            const isLast = i === steps.length - 1 && !done

            return (
              <li
                key={i}
                className="relative flex items-start gap-4 animate-slide-up"
              >
                {/* Node icon */}
                <div
                  className={`relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border ${meta.color} ${
                    isLast ? 'ring-2 ring-violet-500/20' : ''
                  }`}
                >
                  {meta.icon}
                  {isLast && (
                    <span
                      className={`absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full border-2 border-canvas ${meta.dot} animate-pulse-dot`}
                    />
                  )}
                </div>

                {/* Content */}
                <div className="min-w-0 flex-1 rounded-xl border border-border bg-surface-1 px-4 py-3 shadow-card">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-ink-1">{meta.label}</span>
                    <span className="text-xs text-ink-3">{meta.desc}</span>
                    {isLast && (
                      <span className="ml-auto flex items-center gap-1 text-xs text-ink-3">
                        <Spinner size={11} className="text-violet-400" />
                        working
                      </span>
                    )}
                  </div>
                  {step.payload && (
                    <div className="mt-1.5">
                      <StepPayload node={step.node} payload={step.payload} />
                    </div>
                  )}
                </div>
              </li>
            )
          })}
        </ol>
        <div ref={bottomRef} />
      </div>
    </div>
  )
}

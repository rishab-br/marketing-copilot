import { useEffect, useRef, useState } from 'react'
import { streamCampaign } from '../api'
import { Badge, Spinner } from './ui'

const NODE_META = {
  strategist: { icon: '🧭', label: 'Strategist', desc: 'Planning the angle & key messages' },
  copywriter: { icon: '✍️', label: 'Copywriter', desc: 'Drafting platform-specific copy' },
  critic: { icon: '🛡️', label: 'Critic', desc: 'Guardrails + rubric scoring' },
  finalize: { icon: '🏁', label: 'Finalize', desc: 'Wrapping up the run' },
}

function renderPayload(node, payload) {
  if (node === 'strategist') return <span>angle: “{payload.angle}”</span>
  if (node === 'copywriter')
    return (
      <span>
        iteration {payload.iteration} — drafting {payload.platforms?.join(', ')}
      </span>
    )
  if (node === 'critic')
    return (
      <span className="flex flex-wrap gap-2">
        {payload.assets?.map((a) => (
          <Badge key={a.platform} tone={a.guardrail_passed && a.overall >= 4 ? 'green' : 'amber'}>
            {a.platform}: {a.overall} {a.guardrail_passed ? '' : '⚠ guardrail'}
          </Badge>
        ))}
      </span>
    )
  if (node === 'finalize')
    return payload.needs_human_attention ? (
      <Badge tone="amber">needs human attention</Badge>
    ) : (
      <Badge tone="green">all assets passed</Badge>
    )
  return null
}

export default function RunProgress({ campaignId, onComplete, onError }) {
  const [steps, setSteps] = useState([])
  const esRef = useRef(null)

  useEffect(() => {
    setSteps([])
    const es = streamCampaign(campaignId, {
      onNode: (ev) => setSteps((s) => [...s, ev]),
      onComplete: (ev) => onComplete?.(ev),
      onError: (err) => onError?.(err?.message ?? 'stream error'),
    })
    esRef.current = es
    return () => es.close()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId])

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 text-slate-300">
        <Spinner className="text-indigo-400" />
        <span className="text-sm">Agents are working… watch the revision loop in real time.</span>
      </div>

      <ol className="space-y-2">
        {steps.map((step, i) => {
          const meta = NODE_META[step.node] ?? { icon: '•', label: step.node, desc: '' }
          return (
            <li
              key={i}
              className="flex items-start gap-3 rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3"
            >
              <span className="text-lg leading-none">{meta.icon}</span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-200">{meta.label}</span>
                  <span className="text-xs text-slate-500">{meta.desc}</span>
                </div>
                <div className="mt-1 text-sm text-slate-400">{renderPayload(step.node, step.payload)}</div>
              </div>
            </li>
          )
        })}
        {steps.length === 0 && (
          <li className="rounded-lg border border-dashed border-slate-800 px-4 py-6 text-center text-sm text-slate-500">
            Connecting to the agent stream…
          </li>
        )}
      </ol>
    </div>
  )
}

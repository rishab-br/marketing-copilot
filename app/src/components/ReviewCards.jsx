import { useState } from 'react'
import { Badge, ScoreBar, Spinner } from './ui'

// Mirrors the backend default EVAL_THRESHOLD.
const THRESHOLD = 4.0

function GateBadge({ guardrail, overall }) {
  if (!guardrail.passed) return <Badge tone="red">Guardrail blocked</Badge>
  if (overall >= THRESHOLD) return <Badge tone="green">Passed gate · {overall}</Badge>
  return <Badge tone="amber">Below threshold · {overall}</Badge>
}

function AssetCard({ item, busy, onApprove, onRegenerate }) {
  const { asset, guardrail, score, iterations, approved } = item
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <h3 className="text-base font-semibold capitalize text-slate-100">{asset.platform}</h3>
          <Badge tone="slate">iter {iterations}</Badge>
          {approved && <Badge tone="green">✓ Approved</Badge>}
        </div>
        <GateBadge guardrail={guardrail} overall={score.overall} />
      </div>

      <blockquote className="rounded-lg border-l-2 border-indigo-500/50 bg-slate-950/50 px-4 py-3 text-sm leading-relaxed text-slate-200">
        {asset.body}
      </blockquote>

      <div className="mt-3 text-sm">
        <span className="text-slate-500">CTA:</span>{' '}
        <span className="font-medium text-slate-200">{asset.cta}</span>
      </div>

      {asset.hashtags?.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {asset.hashtags.map((h) => (
            <span key={h} className="text-xs text-indigo-300">
              #{h}
            </span>
          ))}
        </div>
      )}

      <div className="mt-4 space-y-1.5">
        <ScoreBar label="Clarity" value={score.clarity} />
        <ScoreBar label="CTA strength" value={score.cta_strength} />
        <ScoreBar label="Brand fit" value={score.brand_fit} />
        <ScoreBar label="Platform fit" value={score.platform_fit} />
      </div>

      <p className="mt-3 text-sm italic text-slate-400">“{score.rationale}”</p>

      {!guardrail.passed && guardrail.violations.length > 0 && (
        <ul className="mt-3 space-y-1 rounded-lg border border-rose-500/30 bg-rose-600/10 px-3 py-2 text-xs text-rose-300">
          {guardrail.violations.map((v, i) => (
            <li key={i}>⚠ {v}</li>
          ))}
        </ul>
      )}

      <div className="mt-4 flex items-center gap-2">
        <button
          onClick={() => onApprove(asset.platform)}
          disabled={approved || !!busy}
          className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {busy === 'approve' && <Spinner />}
          {approved ? 'Approved' : 'Approve'}
        </button>
        <button
          onClick={() => onRegenerate(asset.platform)}
          disabled={!!busy}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {busy === 'regenerate' && <Spinner />}
          Regenerate
        </button>
      </div>
    </div>
  )
}

export default function ReviewCards({ campaign, onApprove, onRegenerate, onStartOver }) {
  const [busy, setBusy] = useState({}) // { platform: 'approve' | 'regenerate' }

  const wrap = (action, fn) => async (platform) => {
    setBusy((b) => ({ ...b, [platform]: action }))
    try {
      await fn(platform)
    } finally {
      setBusy((b) => ({ ...b, [platform]: undefined }))
    }
  }

  const assets = campaign?.assets ?? []

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold text-slate-100">Review</h2>
          {campaign?.needs_human_attention && (
            <Badge tone="amber">Some assets need attention</Badge>
          )}
        </div>
        <button
          onClick={onStartOver}
          className="text-sm text-slate-400 underline-offset-2 hover:text-slate-200 hover:underline"
        >
          ← New brief
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {assets.map((item) => (
          <AssetCard
            key={item.platform}
            item={item}
            busy={busy[item.platform]}
            onApprove={wrap('approve', onApprove)}
            onRegenerate={wrap('regenerate', onRegenerate)}
          />
        ))}
      </div>

      {assets.length === 0 && (
        <p className="rounded-lg border border-dashed border-slate-800 px-4 py-6 text-center text-sm text-slate-500">
          No assets were produced.
        </p>
      )}
    </div>
  )
}

import { useState } from 'react'
import { Field, Spinner, inputClass } from './ui'

const PLATFORMS = ['instagram', 'linkedin', 'twitter', 'facebook', 'tiktok']

const SAMPLE = {
  brand: 'TaskFlow',
  product: 'TaskFlow',
  goal: 'drive signups for the free trial',
  audience: 'busy startup founders and small teams',
  tone: 'confident, friendly, no fluff',
  brand_guidelines: 'No absolute or unverifiable claims (e.g. "guaranteed", "best in the world"). Warm, human tone.',
}

export default function BriefForm({ onSubmit, busy, error }) {
  const [form, setForm] = useState({
    brand: '',
    product: '',
    goal: '',
    audience: '',
    tone: '',
    brand_guidelines: '',
  })
  const [platforms, setPlatforms] = useState(['linkedin', 'instagram'])

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const togglePlatform = (p) =>
    setPlatforms((ps) => (ps.includes(p) ? ps.filter((x) => x !== p) : [...ps, p]))

  const canSubmit =
    form.brand && form.product && form.goal && form.audience && form.tone && platforms.length > 0

  const submit = (e) => {
    e.preventDefault()
    if (!canSubmit || busy) return
    onSubmit({ ...form, platforms, brand_guidelines: form.brand_guidelines || null })
  }

  return (
    <form onSubmit={submit} className="space-y-5">
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <Field label="Brand">
          <input className={inputClass} value={form.brand} onChange={set('brand')} placeholder="TaskFlow" />
        </Field>
        <Field label="Product">
          <input className={inputClass} value={form.product} onChange={set('product')} placeholder="TaskFlow" />
        </Field>
      </div>

      <Field label="Goal" hint="What should this campaign achieve?">
        <input className={inputClass} value={form.goal} onChange={set('goal')} placeholder="drive signups" />
      </Field>

      <Field label="Audience">
        <input className={inputClass} value={form.audience} onChange={set('audience')} placeholder="busy founders" />
      </Field>

      <Field label="Tone">
        <input className={inputClass} value={form.tone} onChange={set('tone')} placeholder="confident, friendly" />
      </Field>

      <Field label="Target platforms">
        <div className="flex flex-wrap gap-2">
          {PLATFORMS.map((p) => {
            const on = platforms.includes(p)
            return (
              <button
                type="button"
                key={p}
                onClick={() => togglePlatform(p)}
                className={`rounded-full px-3 py-1 text-sm capitalize transition ${
                  on
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                {p}
              </button>
            )
          })}
        </div>
      </Field>

      <Field label="Brand guidelines" hint="Optional — banned claims / tone rules the critic enforces.">
        <textarea
          className={`${inputClass} min-h-[80px] resize-y`}
          value={form.brand_guidelines}
          onChange={set('brand_guidelines')}
          placeholder='e.g. No "guaranteed" or absolute claims.'
        />
      </Field>

      {error && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-600/10 px-3 py-2 text-sm text-rose-300">
          {error}
        </div>
      )}

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={!canSubmit || busy}
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busy && <Spinner />}
          {busy ? 'Starting run…' : 'Generate campaign'}
        </button>
        <button
          type="button"
          onClick={() => setForm(SAMPLE)}
          className="text-sm text-slate-400 underline-offset-2 hover:text-slate-200 hover:underline"
        >
          Fill sample brief
        </button>
      </div>
    </form>
  )
}

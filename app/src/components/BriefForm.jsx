import { useState } from 'react'
import { Button, Field, Input, PlatformIcon, Spinner, Textarea } from './ui'

const PLATFORMS = ['linkedin', 'instagram', 'twitter', 'facebook', 'tiktok']

const PLATFORM_LABELS = {
  linkedin: 'LinkedIn',
  instagram: 'Instagram',
  twitter: 'Twitter / X',
  facebook: 'Facebook',
  tiktok: 'TikTok',
}

const SAMPLE = {
  brand: 'TaskFlow',
  product: 'TaskFlow Pro',
  goal: 'drive signups for the free trial',
  audience: 'busy startup founders and small teams',
  tone: 'confident, friendly, no fluff',
  brand_guidelines:
    'No absolute or unverifiable claims (e.g. "guaranteed", "best in the world"). Warm, human tone. Always include a clear CTA.',
}

function SectionLabel({ label, description }) {
  return (
    <div className="mb-4">
      <p className="text-sm font-semibold text-ink-1">{label}</p>
      {description && <p className="mt-0.5 text-xs text-ink-3">{description}</p>}
    </div>
  )
}

export default function BriefForm({ onSubmit, busy }) {
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

  const fillSample = () => {
    setForm(SAMPLE)
    setPlatforms(['linkedin', 'instagram'])
  }

  return (
    <form onSubmit={submit} className="space-y-6 animate-fade-in">
      {/* Identity section */}
      <div className="card p-6">
        <SectionLabel
          label="Campaign identity"
          description="Who is this for and what are we promoting?"
        />
        <div className="grid grid-cols-2 gap-4">
          <Field label="Brand name" required>
            <Input
              value={form.brand}
              onChange={set('brand')}
              placeholder="e.g. TaskFlow"
              autoFocus
            />
          </Field>
          <Field label="Product / service" required>
            <Input
              value={form.product}
              onChange={set('product')}
              placeholder="e.g. TaskFlow Pro"
            />
          </Field>
        </div>
      </div>

      {/* Goals section */}
      <div className="card p-6">
        <SectionLabel
          label="Goals & audience"
          description="What outcome does this campaign drive and who sees it?"
        />
        <div className="space-y-4">
          <Field
            label="Campaign goal"
            required
            hint="What action should users take?"
          >
            <Input
              value={form.goal}
              onChange={set('goal')}
              placeholder="e.g. drive signups for the free trial"
            />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Target audience" required>
              <Input
                value={form.audience}
                onChange={set('audience')}
                placeholder="e.g. busy startup founders"
              />
            </Field>
            <Field
              label="Brand tone"
              required
              hint="Adjectives the copy should feel like"
            >
              <Input
                value={form.tone}
                onChange={set('tone')}
                placeholder="e.g. confident, friendly, no fluff"
              />
            </Field>
          </div>
        </div>
      </div>

      {/* Platforms section */}
      <div className="card p-6">
        <SectionLabel
          label="Target platforms"
          description="The agents produce one tailored asset per platform."
        />
        <div className="flex flex-wrap gap-2">
          {PLATFORMS.map((p) => {
            const on = platforms.includes(p)
            return (
              <button
                type="button"
                key={p}
                onClick={() => togglePlatform(p)}
                className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-all duration-150 ${
                  on
                    ? 'border-violet-500/50 bg-violet-500/10 text-violet-300 shadow-glow-sm'
                    : 'border-border bg-surface-2 text-ink-2 hover:border-border-strong hover:text-ink-1'
                }`}
              >
                <PlatformIcon platform={p} size={15} />
                {PLATFORM_LABELS[p]}
                {on && (
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="text-violet-400"
                  >
                    <path d="M20 6 9 17l-5-5" />
                  </svg>
                )}
              </button>
            )
          })}
        </div>
        {platforms.length === 0 && (
          <p className="mt-2 text-xs text-rose-400">Select at least one platform.</p>
        )}
      </div>

      {/* Brand guidelines */}
      <div className="card p-6">
        <SectionLabel
          label="Brand guidelines"
          description="Optional — the critic enforces these on every asset."
        />
        <Textarea
          rows={3}
          value={form.brand_guidelines}
          onChange={set('brand_guidelines')}
          placeholder='e.g. No "guaranteed" or absolute claims. Always end with a question.'
        />
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <Button
          type="submit"
          variant="primary"
          size="lg"
          disabled={!canSubmit || busy}
          className="gap-2"
        >
          {busy ? (
            <>
              <Spinner size={14} />
              Starting run…
            </>
          ) : (
            <>
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z" />
              </svg>
              Generate campaign
            </>
          )}
        </Button>

        <button
          type="button"
          onClick={fillSample}
          className="text-sm text-ink-3 transition hover:text-ink-1"
        >
          Fill sample brief →
        </button>
      </div>
    </form>
  )
}

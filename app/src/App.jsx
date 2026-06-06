import { useState } from 'react'
import { approveAsset, createCampaign, getCampaign, regenerateAsset } from './api'
import BriefForm from './components/BriefForm'
import RunProgress from './components/RunProgress'
import ReviewCards from './components/ReviewCards'

const STEPS = [
  { key: 'brief', label: 'Brief' },
  { key: 'run', label: 'Run' },
  { key: 'review', label: 'Review' },
]

function Stepper({ screen }) {
  const idx = STEPS.findIndex((s) => s.key === screen)
  return (
    <div className="flex items-center gap-2 text-xs">
      {STEPS.map((s, i) => (
        <div key={s.key} className="flex items-center gap-2">
          <span
            className={`flex h-6 w-6 items-center justify-center rounded-full font-semibold ${
              i <= idx ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-500'
            }`}
          >
            {i + 1}
          </span>
          <span className={i <= idx ? 'text-slate-200' : 'text-slate-500'}>{s.label}</span>
          {i < STEPS.length - 1 && <span className="mx-1 text-slate-700">→</span>}
        </div>
      ))}
    </div>
  )
}

export default function App() {
  const [screen, setScreen] = useState('brief')
  const [campaignId, setCampaignId] = useState(null)
  const [campaign, setCampaign] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (brief) => {
    setError(null)
    setBusy(true)
    try {
      const { id } = await createCampaign(brief)
      setCampaignId(id)
      setScreen('run')
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const handleRunComplete = async () => {
    try {
      const data = await getCampaign(campaignId)
      setCampaign(data)
      setScreen('review')
    } catch (e) {
      setError(e.message)
      setScreen('brief')
    }
  }

  const handleRunError = (msg) => {
    setError(`Run failed: ${msg}`)
    setScreen('brief')
  }

  const replaceAsset = (updated) =>
    setCampaign((c) => ({
      ...c,
      assets: c.assets.map((a) => (a.platform === updated.platform ? updated : a)),
    }))

  const handleApprove = async (platform) => {
    const updated = await approveAsset(campaignId, platform)
    replaceAsset(updated)
  }

  const handleRegenerate = async (platform) => {
    const updated = await regenerateAsset(campaignId, platform)
    replaceAsset(updated)
  }

  const startOver = () => {
    setScreen('brief')
    setCampaignId(null)
    setCampaign(null)
    setError(null)
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800/80">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-5 py-4">
          <div>
            <h1 className="text-lg font-bold text-slate-100">Agentic Marketing Copilot</h1>
            <p className="text-xs text-slate-500">
              Strategist → Copywriter ↔ Critic · guardrails · eval gate · human approval
            </p>
          </div>
          <Stepper screen={screen} />
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-5 py-8">
        {screen === 'brief' && <BriefForm onSubmit={handleSubmit} busy={busy} error={error} />}

        {screen === 'run' && campaignId && (
          <RunProgress
            campaignId={campaignId}
            onComplete={handleRunComplete}
            onError={handleRunError}
          />
        )}

        {screen === 'review' && campaign && (
          <ReviewCards
            campaign={campaign}
            onApprove={handleApprove}
            onRegenerate={handleRegenerate}
            onStartOver={startOver}
          />
        )}
      </main>
    </div>
  )
}

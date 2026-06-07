import { useState } from 'react'
import { approveAsset, createCampaign, getCampaign, regenerateAsset } from './api'
import BriefForm from './components/BriefForm'
import RunProgress from './components/RunProgress'
import ReviewCards from './components/ReviewCards'
import Sidebar from './components/Sidebar'

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

  const screenTitles = {
    brief: {
      title: 'New Campaign',
      subtitle: 'Describe your brand and goals — the agents handle the rest.',
    },
    run: {
      title: 'Agents Running',
      subtitle: 'Strategist → Copywriter ↔ Critic · watch the revision loop live.',
    },
    review: {
      title: 'Review & Approve',
      subtitle: 'Scored, guardrail-checked assets — approve or regenerate each one.',
    },
  }

  const { title, subtitle } = screenTitles[screen]

  return (
    <div className="flex h-screen overflow-hidden bg-canvas">
      {/* Sidebar */}
      <Sidebar screen={screen} onLogoClick={startOver} />

      {/* Main */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex shrink-0 items-center justify-between border-b border-border bg-surface-1/60 px-8 py-4 backdrop-blur">
          <div>
            <h1 className="text-base font-semibold text-ink-1">{title}</h1>
            <p className="text-xs text-ink-3">{subtitle}</p>
          </div>
          {screen !== 'brief' && (
            <button
              onClick={startOver}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-ink-3 transition hover:bg-surface-2 hover:text-ink-1"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>
              </svg>
              New brief
            </button>
          )}
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-3xl px-8 py-8">
            {error && (
              <div className="mb-6 flex items-start gap-3 rounded-xl border border-rose-500/25 bg-rose-500/10 px-4 py-3 text-sm text-rose-300 animate-fade-in">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="mt-0.5 shrink-0">
                  <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
                  <path d="M12 9v4"/><path d="M12 17h.01"/>
                </svg>
                <span>{error}</span>
              </div>
            )}

            {screen === 'brief' && (
              <BriefForm onSubmit={handleSubmit} busy={busy} />
            )}

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
          </div>
        </main>
      </div>
    </div>
  )
}

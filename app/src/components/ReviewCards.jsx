import { useEffect, useState } from 'react'
import { getPosts, publishAsset } from '../api'
import PublishModal from './PublishModal'
import { Badge, Button, PlatformIcon, ScoreBar, ScoreRing, Spinner } from './ui'

const THRESHOLD = 4.0

const PLATFORM_COLORS = {
  linkedin: { bg: '#0A66C2', light: 'rgba(10, 102, 194, 0.12)', border: 'rgba(10, 102, 194, 0.25)' },
  instagram: { bg: '#E1306C', light: 'rgba(225, 48, 108, 0.1)', border: 'rgba(225, 48, 108, 0.2)' },
  twitter: { bg: '#FFFFFF', light: 'rgba(255, 255, 255, 0.05)', border: 'rgba(255, 255, 255, 0.1)' },
  facebook: { bg: '#1877F2', light: 'rgba(24, 119, 242, 0.1)', border: 'rgba(24, 119, 242, 0.2)' },
  tiktok: { bg: '#FF0050', light: 'rgba(255, 0, 80, 0.1)', border: 'rgba(255, 0, 80, 0.2)' },
}

const PLATFORM_LABELS = {
  linkedin: 'LinkedIn',
  instagram: 'Instagram',
  twitter: 'Twitter / X',
  facebook: 'Facebook',
  tiktok: 'TikTok',
}

function GateStatus({ guardrail, overall }) {
  if (!guardrail.passed)
    return (
      <Badge tone="red">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
          <path d="M12 9v4"/><path d="M12 17h.01"/>
        </svg>
        Guardrail blocked
      </Badge>
    )
  if (overall >= THRESHOLD)
    return (
      <Badge tone="green">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20 6 9 17l-5-5"/>
        </svg>
        Passed · {overall}
      </Badge>
    )
  return (
    <Badge tone="amber">
      Below threshold · {overall}
    </Badge>
  )
}

// Platform-specific post mockup
function PostMockup({ platform, asset }) {
  const colors = PLATFORM_COLORS[platform] ?? PLATFORM_COLORS.twitter

  if (platform === 'linkedin') {
    return (
      <div
        className="rounded-xl border p-4 text-sm"
        style={{ background: colors.light, borderColor: colors.border }}
      >
        <div className="mb-3 flex items-center gap-2.5">
          <div
            className="flex h-9 w-9 items-center justify-center rounded-full text-xs font-bold text-white"
            style={{ background: colors.bg }}
          >
            <PlatformIcon platform="linkedin" size={16} />
          </div>
          <div>
            <p className="text-xs font-semibold text-ink-1">Your Company</p>
            <p className="text-[10px] text-ink-3">Company · Now</p>
          </div>
        </div>
        <p className="text-xs leading-relaxed text-ink-1 whitespace-pre-wrap">{asset.body}</p>
        {asset.cta && (
          <p className="mt-2 text-xs font-semibold text-[#0A66C2]">{asset.cta}</p>
        )}
        {asset.hashtags?.length > 0 && (
          <p className="mt-2 text-[11px] text-[#0A66C2]">
            {asset.hashtags.map((h) => `#${h}`).join(' ')}
          </p>
        )}
      </div>
    )
  }

  if (platform === 'instagram') {
    return (
      <div
        className="rounded-xl border p-4 text-sm"
        style={{ background: colors.light, borderColor: colors.border }}
      >
        <div className="mb-3 flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-yellow-400 via-pink-500 to-purple-600 p-0.5">
            <div className="h-full w-full rounded-full bg-surface-2 flex items-center justify-center">
              <PlatformIcon platform="instagram" size={13} />
            </div>
          </div>
          <p className="text-xs font-semibold text-ink-1">yourbrand</p>
        </div>
        <div className="mb-3 h-36 w-full rounded-lg bg-gradient-to-br from-surface-3 to-surface-4 flex items-center justify-center">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-ink-4">
            <rect width="18" height="18" x="3" y="3" rx="2" ry="2"/>
            <circle cx="9" cy="9" r="2"/>
            <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>
          </svg>
        </div>
        <p className="text-xs leading-relaxed text-ink-1 whitespace-pre-wrap">
          <span className="font-semibold">yourbrand</span> {asset.body}
        </p>
        {asset.cta && (
          <p className="mt-1 text-xs font-medium text-ink-2">{asset.cta}</p>
        )}
        {asset.hashtags?.length > 0 && (
          <p className="mt-1.5 text-[11px] text-[#833AB4]">
            {asset.hashtags.map((h) => `#${h}`).join(' ')}
          </p>
        )}
      </div>
    )
  }

  if (platform === 'twitter') {
    return (
      <div
        className="rounded-xl border p-4 text-sm"
        style={{ background: colors.light, borderColor: colors.border }}
      >
        <div className="mb-3 flex items-start gap-2.5">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-surface-3 text-xs font-bold text-ink-1">
            Y
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-semibold text-ink-1">Your Brand</span>
              <span className="text-[10px] text-ink-3">@yourbrand · now</span>
            </div>
            <p className="mt-1 text-xs leading-relaxed text-ink-1 whitespace-pre-wrap">{asset.body}</p>
            {asset.cta && (
              <p className="mt-1 text-xs font-medium text-[#1d9bf0]">{asset.cta}</p>
            )}
            {asset.hashtags?.length > 0 && (
              <p className="mt-1.5 text-[11px] text-[#1d9bf0]">
                {asset.hashtags.map((h) => `#${h}`).join(' ')}
              </p>
            )}
          </div>
        </div>
      </div>
    )
  }

  // Generic fallback for facebook, tiktok, others
  return (
    <div
      className="rounded-xl border p-4 text-sm"
      style={{ background: colors.light, borderColor: colors.border }}
    >
      <p className="text-xs leading-relaxed text-ink-1 whitespace-pre-wrap">{asset.body}</p>
      {asset.cta && (
        <p className="mt-2 text-xs font-semibold text-ink-2">{asset.cta}</p>
      )}
      {asset.hashtags?.length > 0 && (
        <p className="mt-2 text-[11px] text-ink-3">
          {asset.hashtags.map((h) => `#${h}`).join(' ')}
        </p>
      )}
    </div>
  )
}

function PostStatusBadge({ post }) {
  if (!post) return null
  if (post.status === 'published') {
    return (
      <Badge tone="cyan">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>
        </svg>
        Published
      </Badge>
    )
  }
  if (post.status === 'pending') {
    return (
      <Badge tone="amber">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
        </svg>
        Scheduled
      </Badge>
    )
  }
  if (post.status === 'failed') {
    return <Badge tone="red">Failed</Badge>
  }
  return null
}

function AssetCard({ item, post, busy, onApprove, onRegenerate, onPublish }) {
  const { asset, guardrail, score, iterations, approved } = item
  const platform = asset.platform
  const platformLabel = PLATFORM_LABELS[platform] ?? platform

  return (
    <div className="card overflow-hidden animate-slide-up">
      {/* Card header */}
      <div className="flex items-center justify-between border-b border-border px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-2 border border-border">
            <PlatformIcon platform={platform} size={16} />
          </div>
          <div>
            <p className="text-sm font-semibold text-ink-1 capitalize">{platformLabel}</p>
            <p className="text-xs text-ink-3">
              {iterations} iteration{iterations !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <PostStatusBadge post={post} />
          {approved && (
            <Badge tone="green">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 6 9 17l-5-5"/>
              </svg>
              Approved
            </Badge>
          )}
          <GateStatus guardrail={guardrail} overall={score.overall} />
        </div>
      </div>

      <div className="p-5 space-y-5">
        {/* Platform post mockup */}
        <PostMockup platform={platform} asset={asset} />

        {/* Guardrail violations */}
        {!guardrail.passed && guardrail.violations.length > 0 && (
          <div className="rounded-lg border border-rose-500/20 bg-rose-500/8 px-4 py-3 space-y-1">
            <p className="flex items-center gap-1.5 text-xs font-semibold text-rose-400">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
                <path d="M12 9v4"/><path d="M12 17h.01"/>
              </svg>
              Guardrail violations
            </p>
            <ul className="space-y-0.5">
              {guardrail.violations.map((v, i) => (
                <li key={i} className="text-xs text-rose-300">
                  · {v}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Score section */}
        <div className="flex items-start gap-5">
          {/* Score ring */}
          <div className="flex shrink-0 flex-col items-center gap-1">
            <ScoreRing value={score.overall} size={60} />
            <p className="text-[10px] text-ink-3">overall</p>
          </div>

          {/* Rubric bars */}
          <div className="flex-1 space-y-2 pt-1">
            <ScoreBar label="Clarity" value={score.clarity} />
            <ScoreBar label="CTA strength" value={score.cta_strength} />
            <ScoreBar label="Brand fit" value={score.brand_fit} />
            <ScoreBar label="Platform fit" value={score.platform_fit} />
          </div>
        </div>

        {/* Critic rationale */}
        <div className="rounded-lg border border-border bg-surface-2 px-4 py-3">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-widest text-ink-4">
            Critic's notes
          </p>
          <p className="text-xs leading-relaxed text-ink-2 italic">"{score.rationale}"</p>
        </div>

        {/* Published post link */}
        {post?.status === 'published' && post.url && (
          <a
            href={post.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 rounded-lg border border-cyan-500/25 bg-cyan-500/8 px-3 py-2 text-xs text-cyan-400 hover:bg-cyan-500/15 transition"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
              <polyline points="15 3 21 3 21 9"/><line x1="10" x2="21" y1="14" y2="3"/>
            </svg>
            View live post
          </a>
        )}
        {post?.status === 'pending' && post.scheduled_at && (
          <p className="text-xs text-amber-400">
            Scheduled for {new Date(post.scheduled_at).toLocaleString()}
          </p>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 pt-1">
          <Button
            variant="success"
            size="md"
            onClick={() => onApprove(platform)}
            disabled={approved || !!busy}
          >
            {busy === 'approve' ? (
              <><Spinner size={13} /> Approving…</>
            ) : approved ? (
              <>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 6 9 17l-5-5"/>
                </svg>
                Approved
              </>
            ) : (
              <>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 6 9 17l-5-5"/>
                </svg>
                Approve
              </>
            )}
          </Button>
          <Button
            variant="secondary"
            size="md"
            onClick={() => onRegenerate(platform)}
            disabled={!!busy}
          >
            {busy === 'regenerate' ? (
              <><Spinner size={13} /> Regenerating…</>
            ) : (
              <>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
                  <path d="M21 3v5h-5"/>
                  <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
                  <path d="M8 16H3v5"/>
                </svg>
                Regenerate
              </>
            )}
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={() => onPublish(platform)}
            disabled={!approved || !!busy}
            title={!approved ? 'Approve first to unlock publishing' : undefined}
          >
            {busy === 'publish' ? (
              <><Spinner size={13} /> Publishing…</>
            ) : (
              <>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                  <path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>
                </svg>
                Publish
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}

export default function ReviewCards({ campaign, onApprove, onRegenerate, onStartOver }) {
  const [busy, setBusy] = useState({})
  const [posts, setPosts] = useState({}) // keyed by platform, latest post per platform
  const [publishModal, setPublishModal] = useState(null) // platform string or null

  // Load existing posts for this campaign on mount.
  useEffect(() => {
    if (!campaign?.id) return
    getPosts(campaign.id)
      .then((list) => {
        const byPlatform = {}
        for (const p of list) byPlatform[p.platform] = p // last-write wins
        setPosts(byPlatform)
      })
      .catch(() => {}) // non-fatal
  }, [campaign?.id])

  const wrap = (action, fn) => async (platform) => {
    setBusy((b) => ({ ...b, [platform]: action }))
    try {
      await fn(platform)
    } finally {
      setBusy((b) => ({ ...b, [platform]: undefined }))
    }
  }

  const handlePublish = (platform) => (opts) =>
    publishAsset(campaign.id, platform, opts).then((result) => {
      setPosts((p) => ({ ...p, [platform]: result }))
      return result
    })

  const assets = campaign?.assets ?? []
  const approvedCount = assets.filter((a) => a.approved).length
  const passedCount = assets.filter(
    (a) => a.guardrail?.passed && a.score?.overall >= THRESHOLD,
  ).length
  const publishedCount = Object.values(posts).filter((p) => p.status === 'published').length

  return (
    <>
      {/* Publish modal (portal-style, rendered above everything) */}
      {publishModal && (
        <PublishModal
          platform={publishModal}
          onClose={() => setPublishModal(null)}
          onPublish={handlePublish(publishModal)}
        />
      )}

      <div className="animate-fade-in space-y-6">
        {/* Summary bar */}
        <div className="flex items-center justify-between rounded-xl border border-border bg-surface-1 px-5 py-4">
          <div className="flex items-center gap-4">
            <div className="text-center">
              <p className="text-lg font-bold text-ink-1">{assets.length}</p>
              <p className="text-[10px] text-ink-3 uppercase tracking-wide">assets</p>
            </div>
            <div className="h-8 w-px bg-border" />
            <div className="text-center">
              <p className="text-lg font-bold text-emerald-400">{passedCount}</p>
              <p className="text-[10px] text-ink-3 uppercase tracking-wide">passed gate</p>
            </div>
            <div className="h-8 w-px bg-border" />
            <div className="text-center">
              <p className="text-lg font-bold text-violet-400">{approvedCount}</p>
              <p className="text-[10px] text-ink-3 uppercase tracking-wide">approved</p>
            </div>
            <div className="h-8 w-px bg-border" />
            <div className="text-center">
              <p className="text-lg font-bold text-cyan-400">{publishedCount}</p>
              <p className="text-[10px] text-ink-3 uppercase tracking-wide">published</p>
            </div>
            {campaign?.needs_human_attention && (
              <>
                <div className="h-8 w-px bg-border" />
                <Badge tone="amber">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
                    <path d="M12 9v4"/><path d="M12 17h.01"/>
                  </svg>
                  Needs attention
                </Badge>
              </>
            )}
          </div>

          <button
            onClick={onStartOver}
            className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-ink-3 transition hover:bg-surface-2 hover:text-ink-1"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>
            </svg>
            New campaign
          </button>
        </div>

        {/* Asset cards */}
        <div className="space-y-5">
          {assets.map((item) => (
            <AssetCard
              key={item.platform}
              item={item}
              post={posts[item.asset.platform]}
              busy={busy[item.platform]}
              onApprove={wrap('approve', onApprove)}
              onRegenerate={wrap('regenerate', onRegenerate)}
              onPublish={(platform) => setPublishModal(platform)}
            />
          ))}
        </div>

        {assets.length === 0 && (
          <div className="rounded-xl border border-dashed border-border px-6 py-12 text-center text-sm text-ink-3">
            No assets were produced.
          </div>
        )}
      </div>
    </>
  )
}

import { Badge, Divider, Icons } from './ui'

const WORKFLOW_STEPS = [
  { key: 'brief', icon: Icons.File, label: 'Campaign Brief' },
  { key: 'run', icon: Icons.Zap, label: 'Agent Run' },
  { key: 'review', icon: Icons.CheckCircle, label: 'Review & Approve' },
]

const V2_FEATURES = [
  {
    icon: Icons.Search,
    label: 'Research Agent',
    desc: 'Live web context for strategy',
    tag: 'v2',
  },
  {
    icon: Icons.BarChart,
    label: 'Analytics',
    desc: 'Performance & cost tracking',
    tag: 'v2',
  },
  {
    icon: Icons.Send,
    label: 'Publishing',
    desc: 'Post to platforms on approval',
    tag: 'v2',
  },
  {
    icon: Icons.Mic,
    label: 'Brand Voice RAG',
    desc: 'Write in your brand\'s voice',
    tag: 'v3',
  },
]

export default function Sidebar({ screen, onLogoClick }) {
  const activeIdx = WORKFLOW_STEPS.findIndex((s) => s.key === screen)

  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-border bg-surface-1">
      {/* Logo */}
      <div
        className="flex cursor-pointer items-center gap-3 px-5 py-5 select-none"
        onClick={onLogoClick}
      >
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-600 shadow-glow-sm">
          <Icons.Sparkle size={15} className="text-white" />
        </div>
        <div>
          <p className="text-sm font-semibold text-ink-1 leading-tight">CopyCraft</p>
          <p className="text-[10px] text-ink-3 leading-tight">Agentic Marketing</p>
        </div>
      </div>

      <Divider />

      {/* Workflow steps */}
      <div className="px-3 pt-4">
        <p className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest text-ink-4">
          Workflow
        </p>
        <nav className="space-y-0.5">
          {WORKFLOW_STEPS.map((step, i) => {
            const Icon = step.icon
            const isDone = i < activeIdx
            const isActive = i === activeIdx
            const isFuture = i > activeIdx

            return (
              <div
                key={step.key}
                className={`flex items-center gap-3 rounded-lg px-2.5 py-2 transition-colors ${
                  isActive
                    ? 'bg-violet-600/15 text-violet-300'
                    : isDone
                    ? 'text-ink-2 hover:bg-surface-2'
                    : 'text-ink-4'
                }`}
              >
                <div
                  className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                    isActive
                      ? 'bg-violet-600 text-white'
                      : isDone
                      ? 'bg-emerald-600/20 text-emerald-400'
                      : 'bg-surface-3 text-ink-4'
                  }`}
                >
                  {isDone ? (
                    <Icons.Check size={11} />
                  ) : (
                    <span>{i + 1}</span>
                  )}
                </div>
                <span className="text-sm font-medium">{step.label}</span>
                {isActive && (
                  <span className="ml-auto h-1.5 w-1.5 rounded-full bg-violet-400 animate-pulse-dot" />
                )}
              </div>
            )
          })}
        </nav>
      </div>

      <Divider className="mt-4" />

      {/* v2 / v3 features — locked */}
      <div className="px-3 pt-4">
        <p className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest text-ink-4">
          Coming soon
        </p>
        <nav className="space-y-0.5">
          {V2_FEATURES.map((feat) => {
            const Icon = feat.icon
            const isV3 = feat.tag === 'v3'
            return (
              <div
                key={feat.label}
                className="group flex cursor-default items-center gap-3 rounded-lg px-2.5 py-2 opacity-40"
                title={`${feat.desc} — planned for ${feat.tag}`}
              >
                <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-md bg-surface-3">
                  <Icons.Lock size={10} className="text-ink-3" />
                </div>
                <span className="flex-1 text-sm text-ink-2">{feat.label}</span>
                <Badge tone="soon">{feat.tag}</Badge>
              </div>
            )
          })}
        </nav>
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Footer */}
      <Divider />
      <div className="px-5 py-4 space-y-1">
        <p className="text-[11px] text-ink-4">
          Strategist · Copywriter · Critic
        </p>
        <p className="text-[11px] text-ink-4">
          LangGraph · Groq · Pydantic
        </p>
        <p className="text-[11px] text-ink-4 font-medium text-violet-600/70">v1.0</p>
      </div>
    </aside>
  )
}

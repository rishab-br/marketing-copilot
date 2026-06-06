# Frontend — Agentic Marketing Copilot

React + Vite + TailwindCSS UI for the copilot. Three screens:

1. **Brief** — campaign form (brand, product, goal, audience, tone, platforms, guidelines)
2. **Run** — live agent progress streamed over SSE (watch the copywriter ↔ critic loop)
3. **Review** — per-asset cards with the rubric score breakdown, critic rationale,
   guardrail status, and **Approve / Regenerate** actions

## Develop

```bash
npm install
npm run dev          # http://localhost:5173
```

The dev server proxies `/api/*` → `http://localhost:8000` (the backend), so run the
backend alongside it:

```bash
cd ../backend && uvicorn app.main:app --reload
```

Set `GEMINI_API_KEY` in the repo-root `.env` for real generation (without it, a run
surfaces a clear "GEMINI_API_KEY is not set" error in the UI — the wiring still works).

## Build

```bash
npm run build        # -> dist/
npm run preview      # serve the production build locally
```

For a deployed backend on a different origin, set `VITE_API_BASE` (e.g.
`VITE_API_BASE=https://your-backend.fly.dev`) at build time instead of using the proxy.

## Structure

```
src/
  api.js                 fetch + SSE client (EventSource)
  App.jsx                screen state machine (brief → run → review)
  components/
    BriefForm.jsx        the campaign form
    RunProgress.jsx      live SSE agent steps
    ReviewCards.jsx      scored asset cards + approve/regenerate
    ui.jsx               Badge, ScoreBar, Spinner, Field primitives
```

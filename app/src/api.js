// Thin API client for the backend. In dev, Vite proxies /api -> http://localhost:8000
// (see vite.config.js). Override with VITE_API_BASE for a deployed backend.
const BASE = import.meta.env.VITE_API_BASE ?? '/api'

async function asJson(res) {
  if (!res.ok) {
    let detail = ''
    try {
      detail = (await res.json())?.detail ?? ''
    } catch {
      /* ignore */
    }
    throw new Error(`${res.status} ${res.statusText}${detail ? ` — ${detail}` : ''}`)
  }
  return res.json()
}

export function createCampaign(brief) {
  return fetch(`${BASE}/campaigns`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(brief),
  }).then(asJson)
}

export function getCampaign(id) {
  return fetch(`${BASE}/campaigns/${id}`).then(asJson)
}

export function approveAsset(id, platform) {
  return fetch(`${BASE}/campaigns/${id}/assets/${platform}/approve`, {
    method: 'POST',
  }).then(asJson)
}

export function regenerateAsset(id, platform) {
  return fetch(`${BASE}/campaigns/${id}/assets/${platform}/regenerate`, {
    method: 'POST',
  }).then(asJson)
}

// Open an SSE stream of agent progress. Returns the EventSource so callers can
// close it on unmount. The backend tags each event with its type as the SSE
// event name ("node" | "complete" | "error").
export function streamCampaign(id, { onNode, onComplete, onError } = {}) {
  const es = new EventSource(`${BASE}/campaigns/${id}/stream`)
  let done = false

  es.addEventListener('node', (e) => {
    try {
      onNode?.(JSON.parse(e.data))
    } catch {
      /* ignore malformed frame */
    }
  })

  es.addEventListener('complete', (e) => {
    done = true
    try {
      onComplete?.(JSON.parse(e.data))
    } finally {
      es.close()
    }
  })

  // EventSource fires 'error' for BOTH our server-sent error frames (which carry
  // data) and plain connection drops (which don't). Disambiguate via e.data.
  es.addEventListener('error', (e) => {
    if (e.data) {
      done = true
      try {
        onError?.(JSON.parse(e.data))
      } catch {
        onError?.({ message: 'stream error' })
      }
      es.close()
    } else if (!done) {
      onError?.({ message: 'connection lost' })
      es.close()
    }
  })

  return es
}

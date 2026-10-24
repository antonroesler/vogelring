/** Live mirror: SSE client with reconnect; dispatches engine events to the stores and the router. */
import type { Router } from 'vue-router'
import { useLiveStore, type LiveEvent } from '@/stores/live'

let source: EventSource | null = null
let lastSeq = 0
let retry = 0
let connectedAt = 0

const TYPES = [
  'visual.created', 'visual.updated', 'view.created', 'view.updated', 'view.deleted', 'workbook.created', 'workbook.updated', 'workbook.deleted', 'workbook.rendered',
  'pipeline.created', 'pipeline.updated', 'pipeline.deleted', 'pipeline.started', 'pipeline.step', 'pipeline.finished', 'report.created', 'deck.created',
  'note.created', 'note.updated', 'note.deleted', 'group.created', 'group.updated', 'group.deleted', 'definition.saved', 'definition.deleted', 'navigate', 'log', 'run.deleted', 'dataset.created',
]

const ROUTES: Record<string, (id?: string) => string> = {
  group: (id) => (id ? `/gruppen/${id}` : '/gruppen'),
  view: (id) => (id ? `/erkunden/${id}` : '/ansichten'),
  workbook: (id) => (id ? `/mappen/${id}` : '/mappen'),
  pipeline: (id) => (id ? `/auswertungen/${id}` : '/auswertungen'),
  run: (id) => (id ? `/live?run=${id}` : '/live'),
  report: () => '/berichte',
  deck: () => '/berichte',
  visual: (id) => (id ? `/live?visual=${id}` : '/live'),
  dataset: (id) => (id ? `/daten/${id}` : '/start'),
  page: (id) => `/${id || 'start'}`,
}

export function connectEvents(router: Router) {
  const live = useLiveStore()
  if (source) return
  const open = () => {
    const url = lastSeq ? `/api/live?since=${lastSeq}` : '/api/live'
    source = new EventSource(url)
    live.connected = false
    source.onopen = () => {
      live.connected = true
      retry = 0
      connectedAt = Date.now()
    }
    source.onerror = () => {
      live.connected = false
      source?.close()
      source = null
      const delay = Math.min(30000, 1000 * 2 ** retry++)
      setTimeout(open, delay)
    }
    const handler = (e: MessageEvent) => {
      let data: LiveEvent
      try {
        data = JSON.parse(e.data)
      } catch {
        return
      }
      if (data.seq && data.seq > lastSeq) lastSeq = data.seq
      live.push(data)
      if (data.type === 'navigate') {
        // only follow fresh steering events, never ones replayed from history after a reconnect
        const at = Date.parse(String(data.at || ''))
        if (Number.isFinite(at) && at < connectedAt - 5000) return
        const to = ROUTES[data.target as string]?.(data.id as string | undefined)
        if (to) router.push(to)
      }
    }
    TYPES.forEach((t) => source!.addEventListener(t, handler as EventListener))
  }
  open()
}

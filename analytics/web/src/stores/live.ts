import { defineStore } from 'pinia'

export interface LiveEvent {
  seq: number
  type: string
  title: string
  at: string
  [k: string]: any
}

export interface Artefact {
  kind: 'visual' | 'report' | 'deck' | 'view' | 'workbook' | 'run' | 'note' | 'dataset'
  id: string
  title: string
  at: string
  urls?: Record<string, string>
  event: LiveEvent
}

export interface PipelineProgress {
  run_id: string
  pipeline: string
  index: number
  total: number
  status: 'running' | 'ok' | 'error'
  steps: { index: number; title: string; status: string; artifact?: any }[]
  error?: string | null
}

/** Which list pages must refetch when an event of this type arrives. */
export const REFRESH: Record<string, string[]> = {
  view: ['views'],
  visual: ['visuals'],
  workbook: ['workbooks'],
  pipeline: ['pipelines', 'runs'],
  report: ['reports'],
  deck: ['decks'],
  note: ['notes'],
  definition: ['definitions'],
  run: ['runs'],
  dataset: ['datasets'],
  group: ['groups'],
}

export const useLiveStore = defineStore('live', {
  state: () => ({
    connected: false,
    events: [] as LiveEvent[],
    latest: null as Artefact | null,
    progress: {} as Record<string, PipelineProgress>,
    version: {} as Record<string, number>, // bumps per list key → pages watch and refetch
  }),
  getters: {
    lastTitle: (s) => (s.events.length ? s.events[s.events.length - 1].title : ''),
    activeRun: (s) => Object.values(s.progress).find((p) => p.status === 'running') || null,
  },
  actions: {
    push(ev: LiveEvent) {
      this.events.push(ev)
      if (this.events.length > 300) this.events.splice(0, this.events.length - 300)
      const [group] = ev.type.split('.')
      for (const key of REFRESH[group] || []) this.version[key] = (this.version[key] || 0) + 1
      if (ev.type === 'visual.created' || ev.type === 'visual.updated') {
        this.latest = { kind: 'visual', id: ev.visual_id, title: ev.title, at: ev.at, urls: ev.urls, event: ev }
      } else if (ev.type === 'report.created') {
        this.latest = { kind: 'report', id: ev.report_id || ev.id, title: ev.title, at: ev.at, urls: { html: ev.html, pdf: ev.pdf, docx: ev.docx }, event: ev }
      } else if (ev.type === 'deck.created') {
        this.latest = { kind: 'deck', id: ev.deck_id, title: ev.title, at: ev.at, urls: { pptx: ev.pptx_url }, event: ev }
      } else if (ev.type === 'workbook.rendered' || ev.type === 'workbook.created') {
        this.latest = { kind: 'workbook', id: ev.workbook_id || ev.id, title: ev.title, at: ev.at, event: ev }
      } else if (ev.type === 'pipeline.started') {
        this.progress[ev.run_id] = { run_id: ev.run_id, pipeline: ev.pipeline, index: 0, total: ev.total || 0, status: 'running', steps: [] }
        this.latest = { kind: 'run', id: ev.run_id, title: ev.title, at: ev.at, event: ev }
      } else if (ev.type === 'pipeline.step') {
        const p = this.progress[ev.run_id] || (this.progress[ev.run_id] = { run_id: ev.run_id, pipeline: ev.pipeline, index: 0, total: ev.total || 0, status: 'running', steps: [] })
        p.index = ev.index || p.steps.length + 1
        p.total = ev.total || p.total
        p.steps.push({ index: p.index, title: ev.title, status: ev.status || 'ok', artifact: ev.artifact })
      } else if (ev.type === 'pipeline.finished') {
        const p = this.progress[ev.run_id]
        if (p) {
          p.status = ev.status === 'error' ? 'error' : 'ok'
          p.error = ev.error
        }
        this.latest = { kind: 'run', id: ev.run_id, title: ev.title, at: ev.at, event: ev }
      }
    },
  },
})

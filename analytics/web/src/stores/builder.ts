/** Form state of „Daten erkunden“ (mirrors the server's ViewSpec; only non-default fields are sent). */
import { defineStore } from 'pinia'
import { api, type Preview } from '@/api/client'
import { friendlyError } from '@/lib/format'

export interface Filters {
  species: string[]
  places: string[]
  place_groups: string[]
  exclude_places: string[]
  ringing_places: string[]
  rings: string[]
  ring_groups: string[]
  ring_contains: string[]
  groups: string[]
  exclude_ids: string[]
  date_from: string | null
  date_to: string | null
  months: number[]
  seasons: string[]
  periods: string[]
  years: number[]
  status: string[]
  age: number[]
  sex: number[]
  melder: string[]
  ringing_age: number[]
  around_place: string | null
  around_place_km: number
  only_with_coords: boolean
  only_exact_location: boolean
}

export const emptyFilters = (): Filters => ({
  species: [], places: [], place_groups: [], exclude_places: [], ringing_places: [], rings: [], ring_groups: [], ring_contains: [], groups: [], exclude_ids: [],
  date_from: null, date_to: null, months: [], seasons: [], periods: [], years: [], status: [], age: [], sex: [], melder: [], ringing_age: [],
  around_place: null, around_place_km: 5, only_with_coords: false, only_exact_location: false,
})

export interface BuilderForm {
  kind: 'chart' | 'map' | 'table'
  source: string
  filters: Filters
  title: string
  subtitle: string
  chart_kind: string
  metric_kind: string
  metric_column: string | null
  dimension: string
  color: string | null
  facet: string | null
  sort: 'none' | 'asc' | 'desc' | 'x'
  limit: number | null
  show_values: boolean
  show_totals: boolean
  annotate_moult: boolean
  x_column: string | null
  series_column: string | null
  y_column: string | null
  color_column: string | null
  source_column: string | null
  target_column: string | null
  map: { color_mode: string; color_column: string | null; show_ringing_sites: boolean; tracks: boolean; bubbles_by_place: boolean; labels: boolean; basemap: string }
  columns: string[]
  group_by: string[]
  sort_by: string | null
  sort_desc: boolean
  totals_row: boolean
}

export const defaultForm = (): BuilderForm => ({
  kind: 'chart', source: 'sightings', filters: emptyFilters(), title: '', subtitle: '', chart_kind: 'bar', metric_kind: 'birds', metric_column: null,
  dimension: 'month', color: null, facet: null, sort: 'none', limit: null, show_values: false, show_totals: false, annotate_moult: false,
  x_column: 'date', series_column: 'ring', y_column: null, color_column: null, source_column: 'ringing_place', target_column: 'place',
  map: { color_mode: 'season', color_column: null, show_ringing_sites: true, tracks: false, bubbles_by_place: false, labels: true, basemap: 'light' },
  columns: [], group_by: [], sort_by: null, sort_desc: true, totals_row: false,
})

const RAW = new Set(['timeline', 'calendar', 'scatter', 'boxplot', 'sankey', 'graph', 'histogram'])

/** Strip defaults/empties so the spec stays small and valid (extra=forbid on the server). */
export function toSpec(f: BuilderForm): any {
  const filters: Record<string, any> = {}
  for (const [k, v] of Object.entries(f.filters)) {
    if (Array.isArray(v) ? v.length : v !== null && v !== false && v !== '' && !(k === 'around_place_km' && !f.filters.around_place)) filters[k] = v
  }
  const spec: any = { kind: f.kind, source: f.source, filters }
  if (f.title) spec.title = f.title
  if (f.subtitle) spec.subtitle = f.subtitle
  if (f.kind === 'chart') {
    spec.chart_kind = f.chart_kind
    if (RAW.has(f.chart_kind)) {
      if (['timeline', 'calendar', 'histogram', 'scatter', 'boxplot'].includes(f.chart_kind)) spec.x_column = f.x_column
      if (f.chart_kind === 'timeline') {
        spec.series_column = f.series_column
        if (f.color_column) spec.color_column = f.color_column
      }
      if (['scatter', 'boxplot'].includes(f.chart_kind)) spec.y_column = f.y_column
      if (['sankey', 'graph'].includes(f.chart_kind)) {
        spec.source_column = f.source_column
        spec.target_column = f.target_column
        if (f.y_column) spec.y_column = f.y_column
      }
      if (f.chart_kind === 'calendar') spec.metric = { kind: f.metric_kind, column: f.metric_column }
    } else {
      spec.metric = { kind: f.metric_kind, column: f.metric_column }
      spec.dimension = f.dimension
      if (f.color) spec.color = f.color
      if (f.facet) spec.facet = f.facet
    }
    if (f.sort !== 'none') spec.sort = f.sort
    if (f.limit) spec.limit = f.limit
    if (f.show_values) spec.show_values = true
    if (f.show_totals) spec.show_totals = true
    if (f.annotate_moult) spec.annotate_moult = true
  } else if (f.kind === 'map') {
    spec.map = { ...f.map }
    if (!spec.map.color_column) delete spec.map.color_column
  } else {
    if (f.columns.length) spec.columns = f.columns
    if (f.group_by.length) {
      spec.group_by = f.group_by
      spec.metric = { kind: f.metric_kind, column: f.metric_column }
    }
    if (f.sort_by) spec.sort_by = f.sort_by
    spec.sort_desc = f.sort_desc
    if (f.totals_row) spec.totals_row = true
  }
  return spec
}

/** Inverse: fill the form from a saved ViewSpec (unknown keys ignored). */
export function fromSpec(spec: any): BuilderForm {
  const f = defaultForm()
  f.kind = spec.kind || 'chart'
  f.source = spec.source || 'sightings'
  f.filters = { ...emptyFilters(), ...(spec.filters || {}) }
  f.title = spec.title || ''
  f.subtitle = spec.subtitle || ''
  f.chart_kind = spec.chart_kind || 'bar'
  if (spec.metric) {
    f.metric_kind = spec.metric.kind || 'sightings'
    f.metric_column = spec.metric.column || null
  }
  f.dimension = spec.dimension || 'month'
  f.color = spec.color || null
  f.facet = spec.facet || null
  f.sort = spec.sort || 'none'
  f.limit = spec.limit || null
  f.show_values = !!spec.show_values
  f.show_totals = !!spec.show_totals
  f.annotate_moult = !!spec.annotate_moult
  for (const k of ['x_column', 'series_column', 'y_column', 'color_column', 'source_column', 'target_column'] as const) if (spec[k]) (f as any)[k] = spec[k]
  if (spec.map) f.map = { ...f.map, ...spec.map }
  f.columns = spec.columns || []
  f.group_by = spec.group_by || []
  f.sort_by = spec.sort_by || null
  f.sort_desc = spec.sort_desc !== false
  f.totals_row = !!spec.totals_row
  return f
}

export const useBuilderStore = defineStore('builder', {
  state: () => ({
    form: defaultForm(),
    viewId: null as string | null,
    viewTitle: '' as string,
    preview: null as Preview | null,
    loading: false,
    error: '' as string,
    dirty: false,
    timer: 0 as any,
    seq: 0,
  }),
  getters: {
    spec: (s) => toSpec(s.form),
  },
  actions: {
    reset() {
      this.form = defaultForm()
      this.viewId = null
      this.viewTitle = ''
      this.preview = null
      this.error = ''
      this.dirty = false
    },
    loadSpec(spec: any, id: string | null, title = '') {
      this.form = fromSpec(spec)
      this.viewId = id
      this.viewTitle = title
      this.dirty = false
      this.refresh(true)
    },
    refresh(immediate = false) {
      clearTimeout(this.timer)
      this.timer = setTimeout(() => this.runPreview(), immediate ? 0 : 400)
    },
    async runPreview() {
      const my = ++this.seq
      this.loading = true
      this.error = ''
      try {
        const p = await api.previewView(this.spec)
        if (my === this.seq) this.preview = p
      } catch (e) {
        if (my === this.seq) this.error = friendlyError(e)
      } finally {
        if (my === this.seq) this.loading = false
      }
    },
    async save(title: string) {
      const res = this.viewId ? await api.updateView(this.viewId, this.spec, title) : await api.createView(this.spec, title)
      this.viewId = res.id
      this.viewTitle = res.title
      this.dirty = false
      return res
    },
  },
})

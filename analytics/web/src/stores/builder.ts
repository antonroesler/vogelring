/** Form state of „Daten erkunden“ (mirrors the server's ViewSpec; only non-default fields are sent). */
import { defineStore } from 'pinia'
import { api, type Preview } from '@/api/client'
import { friendlyError } from '@/lib/format'

/** One AND-combination of simple filters (what the server calls FilterFields). */
export interface FilterFields {
  species: string[]
  places: string[]
  place_groups: string[]
  exclude_places: string[]
  ringing_places: string[]
  rings: string[]
  ring_groups: string[]
  ring_contains: string[]
  groups: string[]
  all_groups: string[]
  exclude_groups: string[]
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

/** FilterFields plus one level of OR / NOT blocks (server: FilterBlock). */
export interface FilterBlock extends FilterFields {
  any_of: FilterFields[]
  none_of: FilterFields[]
}

/** The full filter language (server: FilterSpec): a block plus bird-level selection. */
export interface Filters extends FilterBlock {
  birds_of: FilterBlock | null
  birds_not_of: FilterBlock | null
}

export const emptyFields = (): FilterFields => ({
  species: [], places: [], place_groups: [], exclude_places: [], ringing_places: [], rings: [], ring_groups: [], ring_contains: [], groups: [], all_groups: [], exclude_groups: [], exclude_ids: [],
  date_from: null, date_to: null, months: [], seasons: [], periods: [], years: [], status: [], age: [], sex: [], melder: [], ringing_age: [],
  around_place: null, around_place_km: 5, only_with_coords: false, only_exact_location: false,
})
export const emptyBlock = (): FilterBlock => ({ ...emptyFields(), any_of: [], none_of: [] })
export const emptyFilters = (): Filters => ({ ...emptyBlock(), birds_of: null, birds_not_of: null })

/** Fill a saved filter spec (any depth) with form defaults so every v-model has a value. */
export function toFilterForm(spec: any): Filters {
  const fields = (x: any): FilterFields => ({ ...emptyFields(), ...(x || {}) })
  const block = (x: any): FilterBlock => ({ ...fields(x), any_of: ((x && x.any_of) || []).map(fields), none_of: ((x && x.none_of) || []).map(fields) })
  const f = { ...block(spec), birds_of: null as FilterBlock | null, birds_not_of: null as FilterBlock | null }
  if (spec?.birds_of) f.birds_of = block(spec.birds_of)
  if (spec?.birds_not_of) f.birds_not_of = block(spec.birds_not_of)
  return f
}

/** Classes for a numeric/date column used as a category (server: BinSpec). */
export interface BinForm {
  mode: 'auto' | 'width' | 'edges' | 'date'
  width: number | null
  edges: string
  date_part: 'year' | 'month' | 'year_month' | 'season'
  unit: string
}

export const DEFAULT_UNITS: Record<string, string> = { km_from_ringing: 'km', max_km: 'km', days_known: 'Tage' }

export const emptyBin = (column = '', type = 'number'): BinForm => ({ mode: type === 'date' ? 'date' : 'auto', width: null, edges: '', date_part: 'year', unit: DEFAULT_UNITS[column] || '' })

/** A column can be put into classes when it holds free numbers, numeric measures or dates (coded ints like age have labels). */
export function binnable(c: { type: string; role: string } | undefined | null): boolean {
  return !!c && (c.type === 'date' || c.type === 'number' || (c.type === 'int' && c.role === 'measure'))
}

/** Columns that act as categories in the current chart/table and therefore may need classes. */
export function categoryColumns(f: BuilderForm): string[] {
  let cols: (string | null)[] = []
  if (f.kind === 'chart') {
    if (RAW.has(f.chart_kind)) {
      if (['sankey', 'graph'].includes(f.chart_kind)) cols = [f.source_column, f.target_column]
      else if (f.chart_kind === 'boxplot' || f.chart_kind === 'histogram') cols = [f.x_column]
      else if (f.chart_kind === 'timeline') cols = [f.series_column, f.color_column]
      else if (f.chart_kind === 'scatter') cols = [f.color_column]
    } else cols = [f.dimension, f.color, f.facet]
  } else if (f.kind === 'table') cols = f.group_by
  return [...new Set(cols.filter((c): c is string => !!c))]
}

function binToSpec(column: string, b: BinForm | undefined): any | null {
  if (!b || b.mode === 'auto') return null
  if (b.mode === 'date') return { column, date_part: b.date_part }
  const out: any = { column }
  if (b.mode === 'width') {
    if (!b.width || b.width <= 0) return null
    out.width = b.width
  } else {
    const edges = b.edges.split(/[,;\s]+/).map((x) => x.replace(',', '.')).filter(Boolean).map(Number).filter((x) => Number.isFinite(x))
    if (!edges.length || edges.some((x, i) => i && x <= edges[i - 1])) return null
    out.edges = edges
  }
  if (b.unit.trim()) out.unit = b.unit.trim()
  return out
}

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
  map: { color_mode: string; color_column: string | null; show_ringing_sites: boolean; tracks: boolean; bubbles_by_place: boolean; labels: boolean; basemap: string; bounds: [[number, number], [number, number]] | null; fit: 'auto' | 'all' }
  columns: string[]
  group_by: string[]
  sort_by: string | null
  sort_desc: boolean
  totals_row: boolean
  bins: Record<string, BinForm>
}

export const defaultForm = (): BuilderForm => ({
  kind: 'chart', source: 'sightings', filters: emptyFilters(), title: '', subtitle: '', chart_kind: 'bar', metric_kind: 'birds', metric_column: null,
  dimension: 'month', color: null, facet: null, sort: 'none', limit: null, show_values: false, show_totals: false, annotate_moult: false,
  x_column: 'date', series_column: 'ring', y_column: null, color_column: null, source_column: 'ringing_place', target_column: 'place',
  map: { color_mode: 'season', color_column: null, show_ringing_sites: true, tracks: false, bubbles_by_place: false, labels: false, basemap: 'light', bounds: null, fit: 'auto' },
  columns: [], group_by: [], sort_by: null, sort_desc: true, totals_row: false, bins: {},
})

const RAW = new Set(['timeline', 'calendar', 'scatter', 'boxplot', 'sankey', 'graph', 'histogram'])

/** Strip defaults/empties so the spec stays small and valid (extra=forbid on the server). */
/** Only the filters that are actually set (what the engine receives). */
export function cleanFilters(src: Partial<Filters> | FilterFields | FilterBlock): Record<string, any> {
  const filters: Record<string, any> = {}
  const s = src as any
  for (const [k, v] of Object.entries(s)) {
    if (k === 'any_of' || k === 'none_of') {
      const blocks = ((v as any[]) || []).map((b) => cleanFilters(b)).filter((b) => Object.keys(b).length)
      if (blocks.length) filters[k] = blocks
    } else if (k === 'birds_of' || k === 'birds_not_of') {
      if (v) {
        const b = cleanFilters(v as FilterBlock)
        if (Object.keys(b).length) filters[k] = b
      }
    } else if (Array.isArray(v) ? v.length : v !== null && v !== false && v !== '' && !(k === 'around_place_km' && !s.around_place)) filters[k] = v
  }
  return filters
}

export function toSpec(f: BuilderForm): any {
  const filters = cleanFilters(f.filters)
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
    if (!spec.map.bounds) delete spec.map.bounds
    if (spec.map.fit === 'auto') delete spec.map.fit
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
  const bins = categoryColumns(f).map((c) => binToSpec(c, f.bins[c])).filter(Boolean)
  if (bins.length) spec.bins = bins
  return spec
}

/** Inverse: fill the form from a saved ViewSpec (unknown keys ignored). */
export function fromSpec(spec: any): BuilderForm {
  const f = defaultForm()
  f.kind = spec.kind || 'chart'
  f.source = spec.source || 'sightings'
  f.filters = toFilterForm(spec.filters)
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
  for (const b of spec.bins || []) {
    const form = emptyBin(b.column, b.date_part ? 'date' : 'number')
    if (b.width) Object.assign(form, { mode: 'width', width: b.width })
    else if (b.edges?.length) Object.assign(form, { mode: 'edges', edges: b.edges.join(', ') })
    else if (b.date_part) Object.assign(form, { mode: 'date', date_part: b.date_part })
    if (b.unit !== undefined) form.unit = b.unit || ''
    f.bins[b.column] = form
  }
  return f
}

export const useBuilderStore = defineStore('builder', {
  state: () => ({
    form: defaultForm(),
    viewId: null as string | null,
    viewTitle: '' as string,
    visualId: null as string | null, // rendered image of the saved view (PNG/PDF links)
    preview: null as Preview | null,
    loading: false,
    error: '' as string,
    dirty: false,
    savedJson: '' as string, // spec as last loaded/saved – dirty = form differs from it (not: any watcher tick)
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
      this.visualId = null
      this.preview = null
      this.error = ''
      this.markSaved()
    },
    markSaved() {
      this.savedJson = JSON.stringify(this.spec)
      this.dirty = false
    },
    checkDirty() {
      this.dirty = JSON.stringify(this.spec) !== this.savedJson
    },
    loadSpec(spec: any, id: string | null, title = '', visualId: string | null = null) {
      this.form = fromSpec(spec)
      this.viewId = id
      this.viewTitle = title
      this.visualId = visualId
      this.markSaved()
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
      this.visualId = res.visual?.visual_id || this.visualId
      this.markSaved()
      return res
    },
  },
})

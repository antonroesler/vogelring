/** REST client for the analytics engine (same origin). */

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method,
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    credentials: 'same-origin',
  })
  const text = await res.text()
  let data: any = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = { error: text }
  }
  if (!res.ok) throw new ApiError(data?.error || `Fehler ${res.status}`, res.status)
  return data as T
}

export const get = <T>(path: string) => request<T>('GET', path)
export const post = <T>(path: string, body?: unknown) => request<T>('POST', path, body ?? {})
export const put = <T>(path: string, body?: unknown) => request<T>('PUT', path, body ?? {})
export const del = <T>(path: string) => request<T>('DELETE', path)

export function qs(params: Record<string, string | number | boolean | undefined | null>): string {
  const p = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== null && v !== '') p.set(k, String(v))
  const s = p.toString()
  return s ? `?${s}` : ''
}

// ---------------------------------------------------------------- types

export interface Meta {
  app: string
  version: string
  user: string
  public_base_url: string
  chat_url: string
  chat_agent_id: string
  counts: Record<string, number>
}

export interface Choice {
  value: string | number
  label: string
  count: number
}

export interface FilterField {
  name: string
  label: string
  widget: string
  choices?: string
  options?: { value: any; label: string }[]
  free_text?: boolean
  km_field?: string
}

export interface SourcesInfo {
  sources: { key: string; label: string; description: string; date_column: string | null; columns: { name: string; label: string; type: string; role: string; filterable: boolean }[]; filters: string[]; dimensions: string[]; metrics: string[] }[]
  metrics: { key: string; label: string; needs_column: boolean }[]
  dimensions: { key: string; label: string; sources: string[]; is_month: boolean; is_time: boolean }[]
  filters: FilterField[]
  seasons: { key: string; label: string; months: number[] }[]
}

export interface VisualUrls {
  interactive_url: string
  embed_url: string
  png_url: string
  pdf_url: string
  xlsx_url: string
}

export interface CatalogItem<T = any> {
  kind: string
  id: string
  title: string
  description: string
  owner: string
  project: string
  tags: string[]
  pinned: boolean
  created_at: string
  updated_at: string
  doc: T
  extra?: Record<string, any>
}

export interface ViewSummary extends Partial<VisualUrls> {
  id: string
  title: string
  description: string
  kind: 'chart' | 'map' | 'table'
  source: string
  visual_id?: string | null
  pinned: boolean
  updated_at: string
  tags: string[]
}

export interface Preview {
  kind: 'chart' | 'map' | 'table'
  model: any
  summary: any
  dataset_id: string
  description: string
  row_count: number
  sql: string
  notes: string[]
  visual_spec: any
  describe: string
}

export interface VisualInfo extends VisualUrls {
  visual_id: string
  kind: 'chart' | 'map' | 'table'
  title: string | null
  updated_at: string
  dataset_ids: string[]
  width: number
  height: number
  summary: any
  model?: any
  spec?: any
}

export interface PipelineSummary {
  id: string
  title: string
  description: string
  describe: string
  parameters: { name: string; label: string; type: string; required: boolean; default: any; choices?: string[] | null; help?: string | null }[]
  icon?: string | null
  tags: string[]
  steps: number
  pinned: boolean
  updated_at: string
}

export interface RunArtifact {
  step_id: string
  kind: string
  title?: string
  dataset_id?: string
  visual_id?: string
  report_id?: string
  deck_id?: string
  urls?: Record<string, string>
  summary?: any
  description?: string
  url?: string
  rows?: number
}

export interface RunResult {
  run_id: string
  pipeline: string
  pipeline_id?: string
  status: 'ok' | 'error'
  started_at: string
  finished_at: string
  params: Record<string, any>
  artifacts: RunArtifact[]
  log: string[]
  error: string | null
}

export interface ReportItem {
  report_id: string
  title: string
  created_at: string
  sections?: number
  html: string
  pdf: string
  docx: string
}

export interface DeckItem {
  deck_id: string
  title: string
  created_at: string
  slides: number
  pptx_url: string
}

export interface Definition {
  name: string
  kind: 'place_group' | 'ring_group' | 'period' | 'filter' | 'note'
  description: string
  values: string[]
  sql: string | null
  date_from: string | null
  date_to: string | null
  default_column: string | null
  updated_at?: string
}

export interface GroupStats {
  sightings: number
  birds: number
  places: number
  first: string | null
  last: string | null
  species: { label: string; sightings: number; birds: number }[]
  status: { label: string; sightings: number }[]
  years: { year: number; sightings: number }[]
  computed_at: string
}

export interface GroupSummary {
  id: string
  name: string
  title: string
  description: string
  describe: string
  color: string | null
  tags: string[]
  pinned: boolean
  owner: string
  updated_at: string
  created_at: string
  ring_count: number
  excluded_count: number
  filter_count: number
  stats: GroupStats | null
  extra?: Record<string, any>
  doc?: any
}

export interface GroupPreview {
  group_id: string
  name: string
  columns: string[]
  rows: Record<string, any>[]
  total: number
  offset: number
  limit: number
  with_excluded: boolean
}

export interface ActivityItem {
  seq: number
  at: string
  type: string
  title: string
  [k: string]: any
}

// ---------------------------------------------------------------- endpoints

export const api = {
  meta: () => get<Meta>('/api/meta'),
  activity: (limit = 50) => get<{ items: ActivityItem[] }>(`/api/activity${qs({ limit })}`),
  navigate: (target: string, id?: string) => post('/api/navigate', { target, id }),
  sources: () => get<SourcesInfo>('/api/sources'),
  dimensions: (source: string) => get<{ items: { key: string; label: string }[] }>(`/api/sources/${source}/dimensions`),
  choices: (source: string, column: string, q = '', limit = 50) => get<{ items: Choice[] }>(`/api/sources/${source}/choices/${column}${qs({ q, limit })}`),
  previewView: (spec: any) => post<Preview>('/api/views/preview', { spec }),
  createView: (spec: any, title?: string, render = true) => post<any>('/api/views', { spec, title, render }),
  updateView: (id: string, spec: any, title?: string, render = true) => put<any>(`/api/views/${id}`, { spec, title, render }),
  views: (q = '') => get<{ items: ViewSummary[] }>(`/api/views${qs({ q, limit: 200 })}`),
  item: <T = any>(kind: string, id: string) => get<CatalogItem<T>>(`/api/${kind}/${id}`),
  list: <T = any>(kind: string, params: Record<string, any> = {}) => get<{ items: CatalogItem<T>[] }>(`/api/${kind}${qs({ limit: 100, ...params })}`),
  remove: (kind: string, id: string) => del(`/api/${kind}/${id}`),
  pin: (kind: string, id: string, pinned: boolean) => post(`/api/${kind}/${id}/pin`, { pinned }),
  saveWorkbook: (spec: any, id?: string) => (id ? put<CatalogItem>(`/api/workbooks/${id}`, { spec }) : post<CatalogItem>('/api/workbooks', { spec })),
  renderWorkbook: (id: string, render = true) => post<any>(`/api/workbooks/${id}/render${qs({ render: render ? 1 : 0 })}`),
  workbookReport: (id: string) => post<any>(`/api/workbooks/${id}/report`),
  workbookDeck: (id: string) => post<any>(`/api/workbooks/${id}/deck`),
  pipelines: (q = '') => get<{ items: PipelineSummary[] }>(`/api/pipelines${qs({ q })}`),
  runPipeline: (id: string, params: Record<string, any>) => post<RunResult>(`/api/pipelines/${id}/run`, { params }),
  runs: (pipeline?: string) => get<{ items: CatalogItem<RunResult>[] }>(`/api/runs${qs({ pipeline, limit: 50 })}`),
  reports: () => get<{ items: ReportItem[] }>('/api/reports'),
  decks: () => get<{ items: DeckItem[] }>('/api/decks'),
  deckFromReport: (report_id: string) => post<DeckItem & { pptx_url: string }>('/api/decks', { report_id }),
  datasets: () => get<{ items: any[] }>('/api/datasets'),
  dataset: (id: string, limit = 100, offset = 0) => get<any>(`/api/datasets/${id}${qs({ limit, offset })}`),
  visuals: (limit = 30) => get<{ items: VisualInfo[] }>(`/api/visuals${qs({ limit })}`),
  visual: (id: string) => get<VisualInfo>(`/api/visuals/${id}`),
  definitions: () => get<{ items: Definition[] }>('/api/definitions'),
  saveDefinition: (d: Partial<Definition>) => post('/api/definitions', d),
  deleteDefinition: (name: string) => del(`/api/definitions/${encodeURIComponent(name)}`),
  groups: (q = '') => get<{ items: GroupSummary[] }>(`/api/groups${qs({ q, limit: 500 })}`),
  group: (id: string) => get<GroupSummary & { doc: any }>(`/api/groups/${id}`),
  createGroup: (spec: any) => post<GroupSummary & { doc: any }>('/api/groups', { spec }),
  updateGroup: (id: string, spec: any) => put<GroupSummary & { doc: any }>(`/api/groups/${id}`, { spec }),
  patchGroup: (id: string, patch: any) => put<GroupSummary & { doc: any }>(`/api/groups/${id}`, { patch }),
  groupSummary: (id: string) => get<GroupStats & { group_id: string; name: string; describe: string }>(`/api/groups/${id}/summary`),
  groupPreview: (id: string, limit = 50, offset = 0, withExcluded = false) => get<GroupPreview>(`/api/groups/${id}/preview${qs({ limit, offset, with_excluded: withExcluded ? 1 : 0 })}`),
  groupExclude: (id: string, ids: string[], excluded: boolean) => post<GroupSummary & { doc: any }>(`/api/groups/${id}/exclude`, { ids, excluded }),
  compareGroups: (group_ids: string[], metric: string, dimension: string, chart_kind: string, save = false, title?: string) => post<any>('/api/groups/compare', { group_ids, metric, dimension, chart_kind, save, title }),
  importLegacyGroups: (dir?: string) => post<any>('/api/groups/import-legacy', dir ? { dir } : {}),
  saveNote: (note: { id?: string; text: string; title?: string; project?: string; tags?: string[] }) => (note.id ? put<CatalogItem>(`/api/notes/${note.id}`, note) : post<CatalogItem>('/api/notes', note)),
}

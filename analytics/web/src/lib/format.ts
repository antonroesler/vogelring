export const fmtNum = new Intl.NumberFormat('de-DE', { maximumFractionDigits: 2 })
export const fmtInt = new Intl.NumberFormat('de-DE', { maximumFractionDigits: 0 })

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return String(iso)
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

export function fmtDateTime(iso: string | null | undefined): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return String(iso)
  return d.toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export function fmtTime(iso: string | null | undefined): string {
  if (!iso) return ''
  const d = new Date(iso)
  return isNaN(d.getTime()) ? '' : d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
}

export function relTime(iso: string): string {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000
  if (diff < 60) return 'gerade eben'
  if (diff < 3600) return `vor ${Math.round(diff / 60)} Min.`
  if (diff < 86400) return `vor ${Math.round(diff / 3600)} Std.`
  if (diff < 86400 * 7) return `vor ${Math.round(diff / 86400)} Tagen`
  return fmtDate(iso)
}

export const KIND_LABEL: Record<string, string> = { chart: 'Diagramm', map: 'Karte', table: 'Tabelle', report: 'Bericht', deck: 'Präsentation', export: 'Datei', view: 'Ansicht', workbook: 'Mappe', pipeline: 'Auswertung', group: 'Gruppe' }
export const KIND_ICON: Record<string, string> = { chart: 'mdi-chart-bar', map: 'mdi-map', table: 'mdi-table', report: 'mdi-file-document', deck: 'mdi-presentation', export: 'mdi-file-excel', view: 'mdi-eye', workbook: 'mdi-view-dashboard', pipeline: 'mdi-play-box-multiple', note: 'mdi-note-text', dataset: 'mdi-database', group: 'mdi-folder-multiple-outline' }

export const CHART_KINDS: { value: string; label: string; icon: string; raw?: boolean }[] = [
  { value: 'bar', label: 'Balken', icon: 'mdi-chart-bar' },
  { value: 'stacked_bar', label: 'Gestapelte Balken', icon: 'mdi-chart-bar-stacked' },
  { value: 'line', label: 'Linie', icon: 'mdi-chart-line' },
  { value: 'area', label: 'Fläche', icon: 'mdi-chart-areaspline' },
  { value: 'pie', label: 'Kreis', icon: 'mdi-chart-pie' },
  { value: 'heatmap', label: 'Heatmap', icon: 'mdi-grid' },
  { value: 'calendar', label: 'Kalender', icon: 'mdi-calendar-month', raw: true },
  { value: 'timeline', label: 'Zeitstrahl', icon: 'mdi-chart-timeline', raw: true },
  { value: 'boxplot', label: 'Boxplot', icon: 'mdi-chart-box-outline', raw: true },
  { value: 'histogram', label: 'Histogramm', icon: 'mdi-chart-histogram', raw: true },
  { value: 'scatter', label: 'Streudiagramm', icon: 'mdi-chart-scatter-plot', raw: true },
  { value: 'sankey', label: 'Fluss', icon: 'mdi-chart-sankey', raw: true },
  { value: 'graph', label: 'Netz', icon: 'mdi-graph', raw: true },
]

export const MONTHS_DE = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
export const MONTHS_DE_LONG = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']

export function friendlyError(e: unknown): string {
  const msg = (e as any)?.message || String(e)
  if (/Failed to fetch|NetworkError/.test(msg)) return 'Keine Verbindung zum Server. Bitte später noch einmal versuchen.'
  return msg
}

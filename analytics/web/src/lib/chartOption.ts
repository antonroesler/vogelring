/** ECharts option builder – faithful port of the server's render/static/chart.js (house theme). */

import { token } from './theme'

export const FONT = '"Inter Variable", Inter, system-ui, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
// Theme colours come from the CSS tokens (light/dark) and are refreshed at the start of every build.
let TEXT = '#212121'
let MUTED = '#595959'
let PRIMARY = '#00436C'
let GRID = 'rgba(0,0,0,0.08)'
let AXIS = '#424242'
let PAPER = '#ffffff'
let CELL = '#f7f7f8'
let CELL_LINE = '#e3e3e3'
function refreshTheme() {
  TEXT = token('--text-primary', '#212121')
  MUTED = token('--text-tertiary', '#595959')
  AXIS = token('--text-secondary', '#424242')
  PRIMARY = token('--brand', '#00436C')
  GRID = token('--border-light', '#e3e3e3')
  PAPER = token('--surface-primary', '#ffffff')
  CELL = token('--surface-primary-alt', '#f7f7f8')
  CELL_LINE = token('--border-medium', '#cdcdcd')
}

const fmt = new Intl.NumberFormat('de-DE', { maximumFractionDigits: 2 })
const fmtPct = new Intl.NumberFormat('de-DE', { style: 'percent', maximumFractionDigits: 1 })

export interface AxisModel {
  title?: string | null
  min?: number | null
  max?: number | null
  format?: 'number' | 'percent' | 'integer'
}

export interface ChartModel {
  kind: string
  title?: string | null
  subtitle?: string | null
  footnote?: string | null
  legend_title?: string | null
  width: number
  height: number
  horizontal?: boolean
  show_values?: boolean
  show_totals?: boolean
  x_axis: AxisModel
  y_axis: AxisModel
  annotations?: { kind: 'band' | 'line'; from: any; to?: any; label?: string | null; color: string }[]
  categories?: string[] | null
  rows?: string[]
  series: { name: string; data: any[]; color: string; stack?: string | null }[]
  stack?: boolean
  totals?: number[]
  pie?: { name: string; value: number; color: string }[]
  heat?: { values: [number, number, number][]; min: number; max: number }
  timeline?: { points: { row: number; t: string; end?: string; cls: string; color: string; tip: string }[]; classes: { name: string; color: string }[]; min: string; max: string }
  calendar?: { years: number[]; values: [string, number][]; max: number; value_label: string }
  sankey?: { nodes: { name: string; label: string; color: string }[]; links: { source: string; target: string; value: number }[] }
  box?: { data: number[][]; outliers: [number, number][]; color: string; name: string }
  graph?: { nodes: { name: string; value: number; category: number; symbolSize: number }[]; links: { source: string; target: string; value: number; label?: string | null; color?: string | null }[]; categories: { name: string; color: string }[]; edge_types: { name: string; color: string }[]; directed: boolean }
  facets?: { name: string; categories: string[]; series: { name: string; data: any[]; color: string }[] }[]
  facet_columns?: number
}

function fmtVal(v: any, axis?: AxisModel | null): string {
  if (v === null || v === undefined) return ''
  if (axis && axis.format === 'percent') return fmtPct.format(v / 100)
  if (axis && axis.format === 'integer') return fmt.format(Math.round(v))
  return fmt.format(v)
}

function longestLabel(arr: any[] | null | undefined): number {
  return (arr || []).reduce((m: number, s: any) => Math.max(m, String(s).length), 0)
}

function axisBase(axis: AxisModel, isCategory: boolean, data?: any[] | null): any {
  const a: any = {
    name: axis.title || '',
    nameLocation: 'middle',
    nameGap: isCategory ? 34 : 44,
    nameTextStyle: { color: MUTED, fontSize: 12.5, fontFamily: FONT },
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: AXIS, fontSize: 12, fontFamily: FONT },
    splitLine: { show: !isCategory, lineStyle: { type: 'dashed', color: GRID } },
  }
  if (isCategory) {
    a.type = 'category'
    a.data = data
    a.axisLabel.interval = 0
    a.axisLabel.hideOverlap = true
    if (data && data.length > 12) {
      a.axisLabel.rotate = 35
      a.nameGap = 60
    }
  } else {
    a.type = 'value'
    a.axisLabel.formatter = (v: number) => fmtVal(v, axis)
    if (axis.min !== null && axis.min !== undefined) a.min = axis.min
    if (axis.max !== null && axis.max !== undefined) a.max = axis.max
  }
  return a
}

const fmtDate = (iso: string) => {
  const p = String(iso).split('-')
  return p.length === 3 ? `${p[2]}.${p[1]}.${p[0]}` : iso
}

export function buildChartOption(M: ChartModel, interactive = true): any {
  refreshTheme()
  const kind = M.kind
  const horizontal = !!M.horizontal
  const legendNames = (M.series || []).map((s) => s.name)
  const showLegend = legendNames.length > 1 || kind === 'pie' || !!M.legend_title
  const legendBottom = legendNames.length <= 8
  const opt: any = {
    animation: false,
    textStyle: { fontFamily: FONT, color: TEXT },
    color: (M.series || []).map((s) => s.color),
    tooltip: {
      trigger: kind === 'pie' || kind === 'scatter' || kind === 'heatmap' ? 'item' : 'axis',
      confine: true,
      axisPointer: { type: kind === 'line' || kind === 'area' ? 'line' : 'shadow' },
      valueFormatter: (v: any) => fmtVal(v, M.y_axis),
      backgroundColor: token('--surface-dialog', '#ffffff'),
      borderColor: token('--border-light', '#e3e3e3'),
      textStyle: { color: TEXT, fontFamily: FONT, fontSize: 12 },
    },
    grid: { left: 30 + (M.y_axis.title ? 14 : 0), right: 28, top: 20, bottom: 20 + (M.x_axis.title ? 10 : 0), containLabel: true },
    legend: showLegend
      ? {
          type: 'scroll',
          orient: legendBottom ? 'horizontal' : 'vertical',
          bottom: legendBottom ? 4 : undefined,
          right: legendBottom ? undefined : 8,
          top: legendBottom ? undefined : 24,
          itemWidth: 14,
          itemHeight: 12,
          textStyle: { fontSize: 12, color: TEXT, fontFamily: FONT },
          data: legendNames.length ? legendNames : undefined,
        }
      : { show: false },
    series: [],
  }
  if (showLegend) {
    if (legendBottom) opt.grid.bottom = 44
    else opt.grid.right = 24 + Math.min(260, 8 * longestLabel(legendNames) + 40)
  }
  if (M.legend_title && showLegend) {
    opt.title = [{ text: M.legend_title, right: legendBottom ? undefined : 8, top: legendBottom ? undefined : 4, bottom: legendBottom ? 24 : undefined, left: legendBottom ? 'center' : undefined, textStyle: { fontSize: 12, color: MUTED, fontWeight: 600 } }]
  }

  if (kind === 'timeline') return buildTimeline(M, opt)
  if (kind === 'calendar') return buildCalendar(M, opt)
  if (kind === 'sankey') return buildSankey(M, opt)
  if (kind === 'boxplot') return buildBoxplot(M, opt)
  if (kind === 'graph') return buildGraph(M, opt, interactive)
  if (M.facets) return buildFacets(M, opt)

  if (kind === 'pie') {
    opt.series = [
      {
        type: 'pie',
        radius: ['38%', '68%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: { borderColor: PAPER, borderWidth: 2, borderRadius: 4 },
        label: { formatter: (p: any) => `${p.name}\n${fmtVal(p.value)} (${fmt.format(p.percent)} %)`, fontSize: 12, color: TEXT },
        data: (M.pie || []).map((d) => ({ name: d.name, value: d.value, itemStyle: { color: d.color } })),
      },
    ]
    opt.legend.data = (M.pie || []).map((d) => d.name)
    opt.tooltip.formatter = (p: any) => `${p.name}: ${fmtVal(p.value)} (${fmt.format(p.percent)} %)`
    return opt
  }

  if (kind === 'heatmap' && M.heat) {
    opt.grid = { left: 24, right: 90, top: 20, bottom: 20, containLabel: true }
    opt.xAxis = axisBase(M.x_axis, true, M.categories)
    opt.xAxis.position = 'top'
    opt.xAxis.splitArea = { show: true }
    opt.yAxis = axisBase(M.y_axis, true, M.rows)
    opt.yAxis.inverse = true
    opt.yAxis.splitArea = { show: true }
    opt.visualMap = { min: M.heat.min, max: M.heat.max, calculable: true, orient: 'vertical', right: 10, top: 'center', inRange: { color: [CELL, '#9BC8B6', '#228096', '#00436C'] }, textStyle: { color: MUTED, fontSize: 11 } }
    const mid = (M.heat.min + M.heat.max) / 2
    const heatData = M.heat.values.map((v) => ({ value: v, label: { color: v[2] > mid ? '#fff' : TEXT } }))
    opt.series = [{ type: 'heatmap', data: heatData, label: { show: M.show_values, fontSize: 10.5 }, itemStyle: { borderColor: PAPER, borderWidth: 1 }, emphasis: { itemStyle: { shadowBlur: 6, shadowColor: 'rgba(0,0,0,.3)' } } }]
    opt.tooltip.formatter = (p: any) => `${M.rows![p.value[1]]} · ${M.categories![p.value[0]]}: ${fmtVal(p.value[2])}`
    return opt
  }

  if (kind === 'scatter') {
    opt.xAxis = axisBase(M.x_axis, false)
    opt.xAxis.splitLine.show = true
    opt.yAxis = axisBase(M.y_axis, false)
    opt.series = M.series.map((s) => ({ name: s.name, type: 'scatter', symbolSize: 9, data: s.data, itemStyle: { color: s.color, opacity: 0.85 } }))
    opt.tooltip.formatter = (p: any) => `${p.seriesName}<br>${fmtVal(p.value[0], M.x_axis)} / ${fmtVal(p.value[1], M.y_axis)}`
    return opt
  }

  const catAxis = axisBase(M.x_axis, true, M.categories)
  const valAxis = axisBase(M.y_axis, false)
  if (horizontal) {
    opt.xAxis = valAxis
    opt.yAxis = catAxis
    opt.yAxis.inverse = true
    opt.yAxis.axisLabel.rotate = 0
    opt.yAxis.nameGap = 8 * longestLabel(M.categories) + 16
  } else {
    opt.xAxis = catAxis
    opt.yAxis = valAxis
  }
  const isBar = kind === 'bar' || kind === 'stacked_bar'
  const stacked = !!M.stack
  const nSeries = M.series.length

  opt.series = M.series.map((s, i) => {
    const base: any = { name: s.name, data: s.data, itemStyle: { color: s.color }, emphasis: { focus: 'series' } }
    if (isBar) {
      base.type = 'bar'
      base.barMaxWidth = 48
      base.barGap = '15%'
      base.barCategoryGap = '35%'
      if (stacked) base.stack = 'total'
      if (!stacked || i === nSeries - 1) base.itemStyle.borderRadius = horizontal ? [0, 3, 3, 0] : [3, 3, 0, 0]
      if (M.show_values) base.label = { show: true, position: stacked ? 'inside' : horizontal ? 'right' : 'top', fontSize: 11, color: stacked ? '#fff' : TEXT, formatter: (p: any) => (p.value ? fmtVal(p.value, M.y_axis) : '') }
    } else {
      base.type = 'line'
      base.smooth = 0.25
      base.symbol = 'circle'
      base.symbolSize = 7
      base.lineStyle = { width: 2.5, color: s.color }
      if (kind === 'area') {
        base.areaStyle = { opacity: 0.18 }
        if (stacked) base.stack = 'total'
      }
      if (M.show_values) base.label = { show: true, position: 'top', fontSize: 11, color: TEXT, formatter: (p: any) => fmtVal(p.value, M.y_axis) }
    }
    return base
  })

  if (M.show_totals && M.totals && stacked && isBar) {
    opt.series.push({
      name: '__totals',
      type: 'bar',
      stack: 'total',
      data: M.totals.map(() => 0),
      itemStyle: { color: 'transparent' },
      tooltip: { show: false },
      silent: true,
      label: { show: true, position: horizontal ? 'right' : 'top', fontSize: 11.5, fontWeight: 600, color: TEXT, formatter: (p: any) => fmtVal(M.totals![p.dataIndex], M.y_axis) },
    })
    if (opt.legend && opt.legend.data) opt.legend.data = legendNames
  }

  if (M.annotations && M.annotations.length && opt.series.length) {
    const areas: any[] = []
    const lines: any[] = []
    M.annotations.forEach((a) => {
      const key = horizontal ? 'yAxis' : 'xAxis'
      if (a.kind === 'band') {
        const from: any = {}
        const to: any = {}
        from[key] = a.from
        to[key] = a.to === null || a.to === undefined ? a.from : a.to
        from.name = a.label || ''
        from.itemStyle = { color: a.color, opacity: 0.13 }
        areas.push([from, to])
      } else {
        const l: any = {}
        l[key] = a.from
        l.name = a.label || ''
        l.lineStyle = { color: a.color, type: 'dashed', width: 1.5 }
        lines.push(l)
      }
    })
    const host = opt.series[0]
    if (areas.length) host.markArea = { silent: true, data: areas, label: { show: true, position: 'insideTop', color: PRIMARY, fontSize: 11.5, fontWeight: 600 } }
    if (lines.length) host.markLine = { silent: true, symbol: 'none', data: lines, label: { color: PRIMARY, fontSize: 11 } }
  }
  return opt
}

function buildTimeline(M: ChartModel, opt: any) {
  const T = M.timeline!
  const rows = M.rows || []
  opt.grid = { left: 24, right: 28, top: 16, bottom: T.classes.length > 1 ? 48 : 28, containLabel: true }
  opt.xAxis = { type: 'time', min: T.min, max: T.max, axisLabel: { color: AXIS, fontSize: 12, fontFamily: FONT, hideOverlap: true }, axisLine: { show: false }, axisTick: { show: false }, splitLine: { show: true, lineStyle: { type: 'dashed', color: GRID } }, name: M.x_axis.title || '', nameLocation: 'middle', nameGap: 30, nameTextStyle: { color: MUTED, fontSize: 12.5 } }
  opt.yAxis = { type: 'category', data: rows, inverse: true, axisLabel: { color: AXIS, fontSize: 12, fontFamily: FONT }, axisLine: { show: false }, axisTick: { show: false }, splitLine: { show: true, lineStyle: { color: GRID } }, name: M.y_axis.title || '', nameLocation: 'middle', nameGap: 8 * longestLabel(rows) + 16, nameTextStyle: { color: MUTED, fontSize: 12.5 } }
  opt.tooltip = { trigger: 'item', confine: true, formatter: (p: any) => p.data.tip || '' }
  const sym = Math.max(5, Math.min(12, 420 / Math.max(rows.length, 1)))
  const series: any[] = T.classes.map((c) => {
    const dots = T.points.filter((pt) => pt.cls === c.name && !pt.end).map((pt) => ({ value: [pt.t, pt.row], tip: pt.tip, itemStyle: { color: pt.color } }))
    return { name: c.name, type: 'scatter', symbolSize: sym, data: dots, itemStyle: { color: c.color, opacity: 0.9 } }
  })
  const ranges = T.points.filter((pt) => pt.end)
  if (ranges.length) {
    series.push({
      name: 'Zeitraum',
      type: 'custom',
      renderItem: (_params: any, api: any) => {
        const y = api.coord([api.value(0), api.value(2)])[1]
        const x1 = api.coord([api.value(0), 0])[0]
        const x2 = api.coord([api.value(1), 0])[0]
        const h = Math.max(4, Math.min(18, api.size([0, 1])[1] * 0.55))
        return { type: 'rect', shape: { x: x1, y: y - h / 2, width: Math.max(2, x2 - x1), height: h }, style: { fill: api.visual('color'), opacity: 0.75 } }
      },
      encode: { x: [0, 1], y: 2 },
      data: ranges.map((pt) => ({ value: [pt.t, pt.end, pt.row], tip: pt.tip, itemStyle: { color: pt.color } })),
    })
  }
  opt.series = series
  opt.legend = T.classes.length > 1 ? { bottom: 4, itemWidth: 12, itemHeight: 12, textStyle: { fontSize: 12, color: TEXT }, data: T.classes.map((c) => c.name) } : { show: false }
  opt.color = T.classes.map((c) => c.color)
  return opt
}

function buildCalendar(M: ChartModel, opt: any) {
  const C = M.calendar!
  const years = C.years
  const n = years.length
  const usable = M.height - 90
  const cellH = Math.max(90, Math.min(150, (usable - 30 * n) / n))
  opt.tooltip = { trigger: 'item', confine: true, formatter: (p: any) => `${fmtDate(p.value[0])}: ${fmtVal(p.value[1])} ${C.value_label}` }
  opt.visualMap = { min: 0, max: C.max, calculable: true, orient: 'horizontal', left: 'center', bottom: 0, inRange: { color: [CELL, '#9BC8B6', '#228096', '#00436C'] }, textStyle: { color: MUTED, fontSize: 11 } }
  opt.calendar = years.map((y, i) => ({
    top: 28 + i * (cellH + 30),
    left: 56,
    right: 24,
    cellSize: ['auto', Math.max(9, Math.min(20, cellH / 7))],
    range: String(y),
    orient: 'horizontal',
    dayLabel: { firstDay: 1, nameMap: ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'], color: MUTED, fontSize: 10.5 },
    monthLabel: { nameMap: ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'], color: TEXT, fontSize: 11.5 },
    yearLabel: { show: true, position: 'left', margin: 36, color: PRIMARY, fontSize: 14, fontWeight: 700 },
    itemStyle: { borderWidth: 1.5, borderColor: PAPER, color: CELL },
    splitLine: { lineStyle: { color: CELL_LINE, width: 1 } },
  }))
  opt.series = years.map((y, i) => ({ type: 'heatmap', coordinateSystem: 'calendar', calendarIndex: i, data: C.values.filter((v) => v[0].slice(0, 4) === String(y)) }))
  opt.grid = undefined
  opt.legend = { show: false }
  return opt
}

function buildSankey(M: ChartModel, opt: any) {
  const S = M.sankey!
  const strip = (s: string) => s.replace(/​/g, '')
  opt.tooltip = { trigger: 'item', confine: true, formatter: (p: any) => (p.dataType === 'edge' ? `${strip(p.data.source)} → ${strip(p.data.target)}: ${fmtVal(p.value)}` : `${strip(p.name)}: ${fmtVal(p.value)}`) }
  const targets = S.nodes.filter((n) => !S.links.some((l) => l.source === n.name)).map((n) => n.label + '  000')
  const rightPad = Math.min(360, 7.2 * longestLabel(targets) + 24)
  opt.series = [
    {
      type: 'sankey',
      left: 24,
      right: rightPad,
      top: 16,
      bottom: 16,
      nodeWidth: 16,
      nodeGap: 10,
      nodeAlign: 'justify',
      layoutIterations: 64,
      emphasis: { focus: 'adjacency' },
      data: S.nodes.map((n) => ({ name: n.name, itemStyle: { color: n.color, borderColor: n.color } })),
      links: S.links.map((l) => ({ source: l.source, target: l.target, value: l.value })),
      lineStyle: { color: 'gradient', opacity: 0.35, curveness: 0.5 },
      label: { fontFamily: FONT, fontSize: 12, color: TEXT, formatter: (p: any) => `${strip(p.name)}  ${fmtVal(p.value)}` },
    },
  ]
  opt.grid = undefined
  opt.legend = { show: false }
  return opt
}

function buildBoxplot(M: ChartModel, opt: any) {
  const B = M.box!
  const cat = axisBase(M.x_axis, true, M.categories)
  const val = axisBase(M.y_axis, false)
  if (M.horizontal) {
    opt.xAxis = val
    opt.yAxis = cat
    opt.yAxis.inverse = true
  } else {
    opt.xAxis = cat
    opt.yAxis = val
  }
  opt.tooltip = {
    trigger: 'item',
    confine: true,
    formatter: (p: any) => {
      if (p.seriesType === 'scatter') return `${M.categories![p.value[0]]}: Ausreißer ${fmtVal(p.value[1], M.y_axis)}`
      const v = p.value
      return `<b>${p.name}</b><br>Min ${fmtVal(v[1])} · Q1 ${fmtVal(v[2])} · <b>Median ${fmtVal(v[3])}</b> · Q3 ${fmtVal(v[4])} · Max ${fmtVal(v[5])}`
    },
  }
  opt.series = [
    { name: B.name, type: 'boxplot', data: B.data, itemStyle: { color: B.color + '33', borderColor: B.color, borderWidth: 1.8 }, boxWidth: ['35%', '55%'] },
    { name: 'Ausreißer', type: 'scatter', data: B.outliers, symbolSize: 6, itemStyle: { color: B.color, opacity: 0.6 } },
  ]
  opt.legend = { show: false }
  return opt
}

function buildGraph(M: ChartModel, opt: any, interactive: boolean) {
  const G = M.graph!
  opt.tooltip = { trigger: 'item', confine: true, formatter: (p: any) => (p.dataType === 'edge' ? `${p.data.label ? `<b>${p.data.label}</b><br>` : ''}${p.data.source} – ${p.data.target}${p.data.value > 1 ? ` (${fmtVal(p.data.value)})` : ''}` : `<b>${p.name}</b><br>Verbindungen: ${fmtVal(p.value)}`) }
  opt.series = [
    {
      type: 'graph',
      layout: 'force',
      roam: interactive,
      draggable: interactive,
      animation: false,
      force: { repulsion: 180, edgeLength: [50, 130], gravity: 0.12, layoutAnimation: false, initLayout: 'circular' },
      categories: G.categories.map((c) => ({ name: c.name, itemStyle: { color: c.color } })),
      data: G.nodes.map((n) => ({ name: n.name, value: n.value, category: n.category, symbolSize: n.symbolSize, label: { show: true, position: 'right', fontSize: 11.5, fontFamily: FONT, color: TEXT } })),
      links: G.links.map((l) => ({ source: l.source, target: l.target, value: l.value, label: l.label, lineStyle: { color: l.color || '#8a949c', width: 1 + Math.min(4, Math.sqrt(l.value || 1)), curveness: 0.1 } })),
      edgeSymbol: G.directed ? ['none', 'arrow'] : ['none', 'none'],
      edgeSymbolSize: 7,
      itemStyle: { borderColor: PAPER, borderWidth: 1.5 },
      lineStyle: { opacity: 0.7 },
      emphasis: { focus: 'adjacency', lineStyle: { width: 3 } },
    },
  ]
  opt.legend = { show: false }
  opt.grid = undefined
  opt.xAxis = undefined
  opt.yAxis = undefined
  if (G.edge_types.length) {
    const items = G.edge_types.map((t, i) => [
      { type: 'rect', left: 14, bottom: 12 + i * 20 + 4, shape: { width: 18, height: 4 }, style: { fill: t.color } },
      { type: 'text', left: 40, bottom: 12 + i * 20, style: { text: t.name, fill: TEXT, fontSize: 12, fontFamily: FONT } },
    ])
    opt.graphic = [{ type: 'rect', left: 6, bottom: 6, shape: { width: 24 + 8 * longestLabel(G.edge_types.map((t) => t.name)) + 40, height: 20 * G.edge_types.length + 10 }, style: { fill: 'rgba(255,255,255,0.9)', stroke: '#e3e8ec' } }, ...items.reverse().flat()]
  }
  return opt
}

function buildFacets(M: ChartModel, opt: any) {
  const F = M.facets!
  const cols = M.facet_columns || 3
  const n = F.length
  const rows = Math.ceil(n / cols)
  const legendNames = M.series.map((s) => s.name)
  const showLegend = legendNames.length > 1
  const top = 10
  const bottom = showLegend ? 44 : 8
  const left = 16
  const right = 10
  const gapX = 34
  const gapY = 44
  const W = M.width - 44
  const H = M.height - 40 - (M.title || M.subtitle ? 40 : 0)
  const cw = (W - left - right - gapX * (cols - 1)) / cols
  const ch = (H - top - bottom - gapY * (rows - 1)) / rows
  opt.grid = []
  opt.xAxis = []
  opt.yAxis = []
  opt.title = []
  opt.series = []
  const isBar = M.kind === 'bar' || M.kind === 'stacked_bar'
  const stacked = !!M.stack
  const longest = longestLabel(M.categories)
  F.forEach((f, i) => {
    const r = Math.floor(i / cols)
    const c = i % cols
    const gx = left + c * (cw + gapX)
    const gy = top + 24 + r * (ch + gapY)
    opt.grid.push({ left: gx, top: gy, width: cw, height: ch - 24, containLabel: true })
    opt.title.push({ text: f.name, left: gx + 4, top: gy - 22, textStyle: { fontSize: 13, fontWeight: 600, color: PRIMARY, fontFamily: FONT } })
    const ax = axisBase(M.x_axis, true, f.categories)
    ax.gridIndex = i
    ax.name = ''
    if ((M.categories || []).length > 8 || longest > 6) ax.axisLabel.rotate = 35
    ax.axisLabel.fontSize = 10.5
    const ay = axisBase(M.y_axis, false)
    ay.gridIndex = i
    ay.name = c === 0 ? M.y_axis.title || '' : ''
    ay.axisLabel.fontSize = 10.5
    opt.xAxis.push(ax)
    opt.yAxis.push(ay)
    f.series.forEach((s) => {
      const base: any = { name: s.name, data: s.data, xAxisIndex: i, yAxisIndex: i, itemStyle: { color: s.color }, emphasis: { focus: 'series' } }
      if (isBar) {
        base.type = 'bar'
        base.barMaxWidth = 32
        if (stacked) base.stack = 'total'
      } else {
        base.type = 'line'
        base.smooth = 0.25
        base.symbol = 'circle'
        base.symbolSize = 5
        base.lineStyle = { width: 2, color: s.color }
        if (M.kind === 'area') {
          base.areaStyle = { opacity: 0.18 }
          if (stacked) base.stack = 'total'
        }
      }
      opt.series.push(base)
    })
  })
  opt.legend = showLegend ? { bottom: 4, itemWidth: 14, itemHeight: 12, textStyle: { fontSize: 12, color: TEXT }, data: legendNames } : { show: false }
  opt.color = M.series.map((s) => s.color)
  opt.tooltip = { trigger: 'axis', confine: true, axisPointer: { type: isBar ? 'shadow' : 'line' }, valueFormatter: (v: any) => fmtVal(v, M.y_axis) }
  return opt
}

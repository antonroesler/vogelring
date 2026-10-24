/** Leaflet renderer – faithful port of the server's render/static/map.js (shapes, tracks, flows, labels, legend). */
import L from 'leaflet'
import 'leaflet.markercluster'

export const FONT_FAMILY = '"Inter", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans", sans-serif'

export interface PointFeature {
  lat: number
  lon: number
  color: string
  size: number
  shape: string
  opacity: number
  cls: string
  tooltip?: string
  label?: string
  label_size?: number
  label_placement?: string
}

export interface MapModel {
  title?: string | null
  subtitle?: string | null
  footnote?: string | null
  width: number
  height: number
  basemap: { url: string; attribution: string; subdomains: string; retina: boolean }
  basemap_name: string
  zoom?: number | null
  center?: [number, number] | null
  bounds?: [[number, number], [number, number]] | null
  fit_padding: number
  scale_bar: boolean
  legend: { title?: string | null; show: boolean; position: string; entries: { label: string; color: string; shape?: string; count?: number }[] }
  layers: any[]
}

export function shapeSvg(shape: string, size: number, color: string, opacity: number, stroke?: number): string {
  const s = size
  const h = s / 2
  const sw = stroke === undefined ? Math.max(1.2, s * 0.09) : stroke
  let body: string
  switch (shape) {
    case 'triangle':
      body = `<polygon points="${h},${s * 0.06} ${s * 0.96},${s * 0.92} ${s * 0.04},${s * 0.92}"/>`
      break
    case 'square':
      body = `<rect x="${s * 0.1}" y="${s * 0.1}" width="${s * 0.8}" height="${s * 0.8}" rx="${s * 0.08}"/>`
      break
    case 'diamond':
      body = `<polygon points="${h},${s * 0.04} ${s * 0.96},${h} ${h},${s * 0.96} ${s * 0.04},${h}"/>`
      break
    case 'star': {
      const pts: string[] = []
      for (let i = 0; i < 10; i++) {
        const r = i % 2 === 0 ? h * 0.95 : h * 0.42
        const a = -Math.PI / 2 + (i * Math.PI) / 5
        pts.push(`${(h + r * Math.cos(a)).toFixed(2)},${(h + r * Math.sin(a)).toFixed(2)}`)
      }
      body = `<polygon points="${pts.join(' ')}"/>`
      break
    }
    default:
      body = `<circle cx="${h}" cy="${h}" r="${h - sw / 2}"/>`
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${s}" height="${s}" viewBox="0 0 ${s} ${s}" style="fill:${color};fill-opacity:${opacity};stroke:#fff;stroke-width:${sw}">${body}</svg>`
}

function escapeHtml(s: any): string {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] as string)
}

export interface MapHandle {
  map: L.Map
  setBasemap: (name: string) => void
  relayout: () => void
  destroy: () => void
}

export function renderMap(mapEl: HTMLElement, M: MapModel, opts: { interactive?: boolean } = {}): MapHandle {
  const interactive = opts.interactive !== false
  const RENDER = !interactive
  const icon = (f: PointFeature) => {
    const size = Math.round(f.size)
    return L.divIcon({ className: 'vr-marker', html: shapeSvg(f.shape, size, f.color, f.opacity), iconSize: [size, size], iconAnchor: [size / 2, size / 2] })
  }

  const map = L.map(mapEl, { zoomControl: interactive, attributionControl: true, preferCanvas: false, zoomSnap: RENDER ? 0.25 : 0.5, zoomDelta: 0.5, wheelPxPerZoomLevel: 240, wheelDebounceTime: 60, fadeAnimation: false, zoomAnimation: false, markerZoomAnimation: false })
  let tile: L.TileLayer | null = null
  function basemapFor(name: string) {
    if (!name || name === M.basemap_name) return M.basemap
    return { url: `/tiles/${name}/{z}/{x}/{y}{r}.png`, attribution: name === 'osm' ? '© OpenStreetMap contributors' : '© OpenStreetMap contributors, © CARTO', subdomains: '', retina: name !== 'osm' }
  }
  function setBasemap(name: string) {
    const cfg = basemapFor(name)
    if (tile) map.removeLayer(tile)
    tile = L.tileLayer(cfg.url, { attribution: cfg.attribution, detectRetina: cfg.retina, maxZoom: 19, keepBuffer: 2, updateWhenIdle: false })
    tile.addTo(map)
  }
  setBasemap(M.basemap_name)
  if (M.scale_bar) L.control.scale({ imperial: false, position: 'bottomleft', maxWidth: 160 }).addTo(map)

  const labelFeatures: { latlng: L.LatLng; text: string; size: number; placement: string; radius: number }[] = []
  const arrowMarkers: { a: L.LatLng; b: L.LatLng; color: string; group: L.FeatureGroup; size: number; atEnd?: boolean; marker?: L.Marker }[] = []

  function addPoints(layer: any) {
    const group: L.FeatureGroup = layer.cluster
      ? (L as any).markerClusterGroup({ maxClusterRadius: 34, spiderfyOnMaxZoom: interactive, showCoverageOnHover: false, zoomToBoundsOnClick: interactive, disableClusteringAtZoom: 16, animate: false })
      : L.featureGroup()
    layer.features.forEach((f: PointFeature) => {
      const m = L.marker([f.lat, f.lon], { icon: icon(f), riseOnHover: true, keyboard: false })
      if (f.tooltip) m.bindTooltip(f.tooltip, { className: 'vr-tooltip', direction: 'top', offset: [0, -f.size / 2], opacity: 0.97 })
      group.addLayer(m)
      if (f.label) labelFeatures.push({ latlng: L.latLng(f.lat, f.lon), text: f.label, size: f.label_size || 12, placement: f.label_placement || 'auto', radius: f.size / 2 })
    })
    group.addTo(map)
  }
  function bearing(a: L.LatLng, b: L.LatLng) {
    const pa = map.latLngToLayerPoint(a)
    const pb = map.latLngToLayerPoint(b)
    return (Math.atan2(pb.y - pa.y, pb.x - pa.x) * 180) / Math.PI
  }
  function arrowAt(latlng: L.LatLng, angle: number, color: string, size: number) {
    const s = size || 14
    const html = `<svg xmlns="http://www.w3.org/2000/svg" width="${s}" height="${s}" viewBox="0 0 10 10" style="transform:rotate(${angle}deg);transform-origin:50% 50%"><polygon points="1,1 9,5 1,9 3,5" fill="${color}" stroke="#fff" stroke-width="0.8"/></svg>`
    return L.marker(latlng, { icon: L.divIcon({ className: 'vr-arrow', html, iconSize: [s, s], iconAnchor: [s / 2, s / 2] }), interactive: false, keyboard: false })
  }
  const midpoint = (a: L.LatLng, b: L.LatLng) => L.latLng((a.lat + b.lat) / 2, (a.lng + b.lng) / 2)
  function addTracks(layer: any) {
    const group = L.featureGroup()
    layer.lines.forEach((ln: any) => {
      const latlngs = ln.coords.map((c: number[]) => L.latLng(c[0], c[1]))
      const casing = L.polyline(latlngs, { color: '#fff', weight: ln.width + 2.5, opacity: 0.9, lineJoin: 'round', interactive: false })
      const pl = L.polyline(latlngs, { color: ln.color, weight: ln.width, opacity: ln.opacity, lineJoin: 'round' })
      if (ln.tooltip) pl.bindTooltip(ln.tooltip, { className: 'vr-tooltip', sticky: true })
      group.addLayer(casing)
      group.addLayer(pl)
      if (ln.arrows) for (let i = 1; i < latlngs.length; i++) arrowMarkers.push({ a: latlngs[i - 1], b: latlngs[i], color: ln.color, group, size: 12 + ln.width })
    })
    group.addTo(map)
  }
  function addFlows(layer: any) {
    const group = L.featureGroup()
    layer.lines.forEach((ln: any) => {
      const a = L.latLng(ln.from[0], ln.from[1])
      const b = L.latLng(ln.to[0], ln.to[1])
      const casing = L.polyline([a, b], { color: '#fff', weight: ln.width + 2.5, opacity: 0.85, interactive: false })
      const pl = L.polyline([a, b], { color: ln.color, weight: ln.width, opacity: ln.opacity })
      if (ln.tooltip) pl.bindTooltip(ln.tooltip, { className: 'vr-tooltip', sticky: true })
      group.addLayer(casing)
      group.addLayer(pl)
      if (ln.arrows) arrowMarkers.push({ a, b, color: ln.color, group, size: 10 + ln.width * 1.5, atEnd: true })
      if (ln.label) group.addLayer(L.marker(midpoint(a, b), { icon: L.divIcon({ className: 'vr-flow-label', html: ln.label, iconSize: undefined as any }), interactive: false }))
    })
    group.addTo(map)
  }
  function addMarkers(layer: any) {
    const group = L.featureGroup()
    layer.features.forEach((f: PointFeature) => {
      const m = L.marker([f.lat, f.lon], { icon: icon(f), zIndexOffset: 1000, keyboard: false })
      if (f.tooltip) m.bindTooltip(f.tooltip, { className: 'vr-tooltip', direction: 'top' })
      group.addLayer(m)
      if (f.label) labelFeatures.push({ latlng: L.latLng(f.lat, f.lon), text: f.label, size: f.label_size || 13, placement: f.label_placement || 'right', radius: f.size / 2 })
    })
    group.addTo(map)
  }
  function placeArrows() {
    arrowMarkers.forEach((ar) => {
      if (ar.marker) ar.group.removeLayer(ar.marker)
      const pa = map.latLngToLayerPoint(ar.a)
      const pb = map.latLngToLayerPoint(ar.b)
      const len = pa.distanceTo(pb)
      if (len < 18) return
      const pos = ar.atEnd ? map.layerPointToLatLng(pb.subtract(pb.subtract(pa).multiplyBy(Math.min(14, len * 0.2) / len))) : midpoint(ar.a, ar.b)
      ar.marker = arrowAt(pos, bearing(ar.a, ar.b), ar.color, ar.size)
      ar.group.addLayer(ar.marker)
    })
  }

  // labels with collision avoidance
  const labelLayer = L.layerGroup().addTo(map)
  const measureCtx = document.createElement('canvas').getContext('2d')!
  const textWidth = (text: string, size: number) => {
    measureCtx.font = `600 ${size}px ${FONT_FAMILY}`
    return measureCtx.measureText(text).width + 2
  }
  type Box = { x: number; y: number; w: number; h: number; dir?: string; off?: [number, number]; obstacle?: boolean }
  function placeLabels() {
    labelLayer.clearLayers()
    const placed: Box[] = []
    const size = map.getSize()
    const gap = 4
    function cand(p: L.Point, w: number, h: number, dir: string, r: number): Box {
      switch (dir) {
        case 'left': return { x: p.x - r - gap - w, y: p.y - h / 2, w, h, dir: 'left', off: [-(r + gap), 0] }
        case 'top': return { x: p.x - w / 2, y: p.y - r - gap - h, w, h, dir: 'top', off: [0, -(r + gap)] }
        case 'bottom': return { x: p.x - w / 2, y: p.y + r + gap, w, h, dir: 'bottom', off: [0, r + gap] }
        case 'topright': return { x: p.x + r * 0.7 + gap, y: p.y - r * 0.7 - gap - h, w, h, dir: 'right', off: [r * 0.7 + gap, -(r * 0.7 + gap + h / 2)] }
        case 'bottomright': return { x: p.x + r * 0.7 + gap, y: p.y + r * 0.7 + gap, w, h, dir: 'right', off: [r * 0.7 + gap, r * 0.7 + gap + h / 2] }
        case 'topleft': return { x: p.x - r * 0.7 - gap - w, y: p.y - r * 0.7 - gap - h, w, h, dir: 'left', off: [-(r * 0.7 + gap), -(r * 0.7 + gap + h / 2)] }
        case 'bottomleft': return { x: p.x - r * 0.7 - gap - w, y: p.y + r * 0.7 + gap, w, h, dir: 'left', off: [-(r * 0.7 + gap), r * 0.7 + gap + h / 2] }
        default: return { x: p.x + r + gap, y: p.y - h / 2, w, h, dir: 'right', off: [r + gap, 0] }
      }
    }
    function cost(b: Box) {
      let c = 0
      if (b.x < 2) c += (2 - b.x) * 50
      if (b.y < 2) c += (2 - b.y) * 50
      if (b.x + b.w > size.x - 2) c += (b.x + b.w - size.x + 2) * 50
      if (b.y + b.h > size.y - 2) c += (b.y + b.h - size.y + 2) * 50
      placed.forEach((o) => {
        const ix = Math.min(b.x + b.w, o.x + o.w) - Math.max(b.x, o.x)
        const iy = Math.min(b.y + b.h, o.y + o.h) - Math.max(b.y, o.y)
        if (ix > 0 && iy > 0) c += ix * iy
      })
      return c
    }
    const mapRect = mapEl.getBoundingClientRect()
    mapEl.querySelectorAll('.vr-legend, .leaflet-control-scale').forEach((el) => {
      const r = el.getBoundingClientRect()
      placed.push({ x: r.left - mapRect.left - 4, y: r.top - mapRect.top - 4, w: r.width + 8, h: r.height + 8, obstacle: true })
    })
    labelFeatures.forEach((lf) => {
      const p = map.latLngToContainerPoint(lf.latlng)
      placed.push({ x: p.x - lf.radius, y: p.y - lf.radius, w: lf.radius * 2, h: lf.radius * 2, obstacle: true })
    })
    const ALL = ['right', 'left', 'top', 'bottom', 'topright', 'bottomright', 'topleft', 'bottomleft']
    labelFeatures.forEach((lf) => {
      const p = map.latLngToContainerPoint(lf.latlng)
      const w = textWidth(lf.text, lf.size)
      const h = lf.size * 1.25
      const order = lf.placement === 'auto' ? ALL : [lf.placement].concat(ALL.filter((d) => d !== lf.placement))
      let best: Box | null = null
      let bestCost = Infinity
      for (let i = 0; i < order.length; i++) {
        const b = cand(p, w, h, order[i], lf.radius)
        const c = cost(b) + i * 0.5
        if (c < bestCost) {
          bestCost = c
          best = b
        }
        if (c < 1) break
      }
      if (!best) return
      placed.push(best)
      const tt = L.tooltip({ permanent: true, direction: best.dir as any, className: 'vr-label', offset: best.off as any, interactive: false, opacity: 1 })
        .setLatLng(lf.latlng)
        .setContent(`<span style="font-size:${lf.size}px">${escapeHtml(lf.text)}</span>`)
      labelLayer.addLayer(tt)
    })
  }

  function legendControl() {
    const ctl = new L.Control({ position: (M.legend.position || 'topright') as any })
    ctl.onAdd = () => {
      const div = L.DomUtil.create('div', 'vr-legend')
      let html = M.legend.title ? `<h4>${escapeHtml(M.legend.title)}</h4>` : ''
      M.legend.entries.forEach((e) => {
        const sw = e.shape === 'line' ? `<span style="display:inline-block;width:16px;height:3px;background:${e.color};border-radius:2px"></span>` : shapeSvg(e.shape || 'circle', 14, e.color, 1, 1)
        html += `<div class="row"><span class="sw">${sw}</span><span>${escapeHtml(e.label)}</span>${e.count !== undefined ? `<span class="n">${e.count}</span>` : ''}</div>`
      })
      div.innerHTML = html
      L.DomEvent.disableClickPropagation(div)
      return div
    }
    return ctl
  }

  M.layers.forEach((layer) => {
    if (layer.type === 'points') addPoints(layer)
    else if (layer.type === 'tracks') addTracks(layer)
    else if (layer.type === 'flows') addFlows(layer)
    else if (layer.type === 'markers') addMarkers(layer)
  })
  if (M.legend.show && M.legend.entries.length) legendControl().addTo(map)

  if (M.zoom && M.center) map.setView(M.center, M.zoom)
  else if (M.zoom && M.bounds) {
    map.fitBounds(M.bounds, { padding: [M.fit_padding, M.fit_padding] })
    map.setZoom(M.zoom)
  } else if (M.bounds) map.fitBounds(M.bounds, { padding: [M.fit_padding, M.fit_padding], maxZoom: 16 })
  else map.setView([50.11, 8.68], 11)

  const relayout = () => {
    placeArrows()
    placeLabels()
  }
  relayout()
  map.on('zoomend moveend', relayout)
  const onResize = () => {
    map.invalidateSize()
    relayout()
  }
  const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(onResize) : null
  ro?.observe(mapEl)

  return {
    map,
    setBasemap,
    relayout,
    destroy: () => {
      ro?.disconnect()
      map.off()
      map.remove()
    },
  }
}

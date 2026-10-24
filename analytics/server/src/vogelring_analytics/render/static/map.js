/* Leaflet map built from window.__MODEL__: points/tracks/flows/markers, legend, labels, scale bar. */
(function () {
  var M = window.__MODEL__;
  var RENDER = window.__RENDER__;
  var mapEl = document.getElementById('map');

  // ---------- symbols
  function shapeSvg(shape, size, color, opacity, stroke) {
    var s = size, h = s / 2, sw = stroke === undefined ? Math.max(1.2, s * 0.09) : stroke;
    var body;
    switch (shape) {
      case 'triangle': body = '<polygon points="' + h + ',' + (s * 0.06) + ' ' + (s * 0.96) + ',' + (s * 0.92) + ' ' + (s * 0.04) + ',' + (s * 0.92) + '"/>'; break;
      case 'square': body = '<rect x="' + (s * 0.1) + '" y="' + (s * 0.1) + '" width="' + (s * 0.8) + '" height="' + (s * 0.8) + '" rx="' + (s * 0.08) + '"/>'; break;
      case 'diamond': body = '<polygon points="' + h + ',' + (s * 0.04) + ' ' + (s * 0.96) + ',' + h + ' ' + h + ',' + (s * 0.96) + ' ' + (s * 0.04) + ',' + h + '"/>'; break;
      case 'star': {
        var pts = [];
        for (var i = 0; i < 10; i++) { var r = i % 2 === 0 ? h * 0.95 : h * 0.42; var a = -Math.PI / 2 + i * Math.PI / 5; pts.push((h + r * Math.cos(a)).toFixed(2) + ',' + (h + r * Math.sin(a)).toFixed(2)); }
        body = '<polygon points="' + pts.join(' ') + '"/>'; break;
      }
      default: body = '<circle cx="' + h + '" cy="' + h + '" r="' + (h - sw / 2) + '"/>';
    }
    return '<svg xmlns="http://www.w3.org/2000/svg" width="' + s + '" height="' + s + '" viewBox="0 0 ' + s + ' ' + s + '" style="fill:' + color + ';fill-opacity:' + opacity + ';stroke:#fff;stroke-width:' + sw + '">' + body + '</svg>';
  }
  function icon(f) {
    var size = Math.round(f.size);
    return L.divIcon({ className: 'vr-marker', html: shapeSvg(f.shape, size, f.color, f.opacity), iconSize: [size, size], iconAnchor: [size / 2, size / 2] });
  }

  // ---------- map
  var map = L.map(mapEl, { zoomControl: !RENDER, attributionControl: true, preferCanvas: false, zoomSnap: RENDER ? 0.25 : 1, fadeAnimation: false, zoomAnimation: false, markerZoomAnimation: false });
  var tile = null;
  function basemapFor(name) {
    if (!name || name === M.basemap_name) return M.basemap;
    return { url: '/tiles/' + name + '/{z}/{x}/{y}{r}.png', attribution: name === 'osm' ? '© OpenStreetMap contributors' : '© OpenStreetMap contributors, © CARTO', subdomains: '', retina: name !== 'osm' };
  }
  function setBasemap(name) {
    var cfg = basemapFor(name);
    if (tile) map.removeLayer(tile);
    tile = L.tileLayer(cfg.url, { attribution: cfg.attribution, detectRetina: cfg.retina, maxZoom: 19, keepBuffer: 2, updateWhenIdle: false });
    tile.addTo(map);
    return tile;
  }
  var tileLayer = setBasemap(M.basemap_name);
  var sel = document.getElementById('basemap-select');
  if (sel) { sel.value = M.basemap_name; sel.addEventListener('change', function () { setBasemap(sel.value); }); }
  if (M.scale_bar) L.control.scale({ imperial: false, position: 'bottomleft', maxWidth: 160 }).addTo(map);

  // ---------- layers
  var allLayers = [];
  var labelFeatures = []; // {latlng, text, size, placement, marker}
  function addPoints(layer) {
    var group = layer.cluster ? L.markerClusterGroup({ maxClusterRadius: 34, spiderfyOnMaxZoom: !RENDER, showCoverageOnHover: false, zoomToBoundsOnClick: !RENDER, disableClusteringAtZoom: 16, animate: false })
                              : L.featureGroup();
    layer.features.forEach(function (f) {
      var m = L.marker([f.lat, f.lon], { icon: icon(f), riseOnHover: true, keyboard: false });
      if (f.tooltip) m.bindTooltip(f.tooltip, { className: 'vr-tooltip', direction: 'top', offset: [0, -f.size / 2], opacity: 0.97 });
      group.addLayer(m);
      if (f.label) labelFeatures.push({ latlng: L.latLng(f.lat, f.lon), text: f.label, size: f.label_size || 12, placement: f.label_placement || 'auto', radius: f.size / 2 });
    });
    group.addTo(map); allLayers.push(group);
  }
  function bearing(a, b) { // pixel-space angle for arrow rotation
    var pa = map.latLngToLayerPoint(a), pb = map.latLngToLayerPoint(b);
    return Math.atan2(pb.y - pa.y, pb.x - pa.x) * 180 / Math.PI;
  }
  var arrowMarkers = [];
  function arrowAt(latlng, angle, color, size) {
    var s = size || 14;
    var html = '<svg xmlns="http://www.w3.org/2000/svg" width="' + s + '" height="' + s + '" viewBox="0 0 10 10" style="transform:rotate(' + angle + 'deg);transform-origin:50% 50%"><polygon points="1,1 9,5 1,9 3,5" fill="' + color + '" stroke="#fff" stroke-width="0.8"/></svg>';
    var m = L.marker(latlng, { icon: L.divIcon({ className: 'vr-arrow', html: html, iconSize: [s, s], iconAnchor: [s / 2, s / 2] }), interactive: false, keyboard: false });
    return m;
  }
  function midpoint(a, b) { return L.latLng((a.lat + b.lat) / 2, (a.lng + b.lng) / 2); }
  function addTracks(layer) {
    var group = L.featureGroup();
    layer.lines.forEach(function (ln) {
      var latlngs = ln.coords.map(function (c) { return L.latLng(c[0], c[1]); });
      var casing = L.polyline(latlngs, { color: '#fff', weight: ln.width + 2.5, opacity: 0.9, lineJoin: 'round', interactive: false });
      var pl = L.polyline(latlngs, { color: ln.color, weight: ln.width, opacity: ln.opacity, lineJoin: 'round' });
      if (ln.tooltip) pl.bindTooltip(ln.tooltip, { className: 'vr-tooltip', sticky: true });
      group.addLayer(casing); group.addLayer(pl);
      if (ln.arrows) for (var i = 1; i < latlngs.length; i++) arrowMarkers.push({ a: latlngs[i - 1], b: latlngs[i], color: ln.color, group: group, size: 12 + ln.width });
    });
    group.addTo(map); allLayers.push(group);
  }
  function addFlows(layer) {
    var group = L.featureGroup();
    layer.lines.forEach(function (ln) {
      var a = L.latLng(ln.from[0], ln.from[1]), b = L.latLng(ln.to[0], ln.to[1]);
      var casing = L.polyline([a, b], { color: '#fff', weight: ln.width + 2.5, opacity: 0.85, interactive: false });
      var pl = L.polyline([a, b], { color: ln.color, weight: ln.width, opacity: ln.opacity });
      if (ln.tooltip) pl.bindTooltip(ln.tooltip, { className: 'vr-tooltip', sticky: true });
      group.addLayer(casing); group.addLayer(pl);
      if (ln.arrows) arrowMarkers.push({ a: a, b: b, color: ln.color, group: group, size: 10 + ln.width * 1.5, atEnd: true });
      if (ln.label) group.addLayer(L.marker(midpoint(a, b), { icon: L.divIcon({ className: 'vr-flow-label', html: ln.label, iconSize: null }), interactive: false }));
    });
    group.addTo(map); allLayers.push(group);
  }
  function addMarkers(layer) {
    var group = L.featureGroup();
    layer.features.forEach(function (f) {
      var m = L.marker([f.lat, f.lon], { icon: icon(f), zIndexOffset: 1000, keyboard: false });
      if (f.tooltip) m.bindTooltip(f.tooltip, { className: 'vr-tooltip', direction: 'top' });
      group.addLayer(m);
      if (f.label) labelFeatures.push({ latlng: L.latLng(f.lat, f.lon), text: f.label, size: f.label_size || 13, placement: f.label_placement || 'right', radius: f.size / 2 });
    });
    group.addTo(map); allLayers.push(group);
  }
  function placeArrows() {
    arrowMarkers.forEach(function (ar) {
      if (ar.marker) ar.group.removeLayer(ar.marker);
      var pa = map.latLngToLayerPoint(ar.a), pb = map.latLngToLayerPoint(ar.b);
      var len = pa.distanceTo(pb); if (len < 18) return;
      var pos = ar.atEnd ? map.layerPointToLatLng(pb.subtract(pb.subtract(pa).multiplyBy(Math.min(14, len * 0.2) / len))) : midpoint(ar.a, ar.b);
      ar.marker = arrowAt(pos, bearing(ar.a, ar.b), ar.color, ar.size);
      ar.group.addLayer(ar.marker);
    });
  }

  // ---------- labels with collision avoidance (measured text, 8 candidate positions, least-overlap fallback)
  var labelLayer = L.layerGroup().addTo(map);
  var measureCtx = document.createElement('canvas').getContext('2d');
  var FONT_FAMILY = getComputedStyle(document.documentElement).getPropertyValue('--font');
  function textWidth(text, size) { measureCtx.font = '600 ' + size + 'px ' + FONT_FAMILY; return measureCtx.measureText(text).width + 2; }
  function placeLabels() {
    labelLayer.clearLayers();
    var placed = [];
    var size = map.getSize();
    var gap = 4;
    function cand(p, w, h, dir, r) {
      switch (dir) {
        case 'left': return { x: p.x - r - gap - w, y: p.y - h / 2, w: w, h: h, dir: 'left', off: [-(r + gap), 0] };
        case 'top': return { x: p.x - w / 2, y: p.y - r - gap - h, w: w, h: h, dir: 'top', off: [0, -(r + gap)] };
        case 'bottom': return { x: p.x - w / 2, y: p.y + r + gap, w: w, h: h, dir: 'bottom', off: [0, r + gap] };
        case 'topright': return { x: p.x + r * 0.7 + gap, y: p.y - r * 0.7 - gap - h, w: w, h: h, dir: 'right', off: [r * 0.7 + gap, -(r * 0.7 + gap + h / 2)] };
        case 'bottomright': return { x: p.x + r * 0.7 + gap, y: p.y + r * 0.7 + gap, w: w, h: h, dir: 'right', off: [r * 0.7 + gap, r * 0.7 + gap + h / 2] };
        case 'topleft': return { x: p.x - r * 0.7 - gap - w, y: p.y - r * 0.7 - gap - h, w: w, h: h, dir: 'left', off: [-(r * 0.7 + gap), -(r * 0.7 + gap + h / 2)] };
        case 'bottomleft': return { x: p.x - r * 0.7 - gap - w, y: p.y + r * 0.7 + gap, w: w, h: h, dir: 'left', off: [-(r * 0.7 + gap), r * 0.7 + gap + h / 2] };
        default: return { x: p.x + r + gap, y: p.y - h / 2, w: w, h: h, dir: 'right', off: [r + gap, 0] };
      }
    }
    function cost(b) {
      var c = 0;
      if (b.x < 2) c += (2 - b.x) * 50; if (b.y < 2) c += (2 - b.y) * 50;
      if (b.x + b.w > size.x - 2) c += (b.x + b.w - size.x + 2) * 50; if (b.y + b.h > size.y - 2) c += (b.y + b.h - size.y + 2) * 50;
      placed.forEach(function (o) {
        var ix = Math.min(b.x + b.w, o.x + o.w) - Math.max(b.x, o.x), iy = Math.min(b.y + b.h, o.y + o.h) - Math.max(b.y, o.y);
        if (ix > 0 && iy > 0) c += ix * iy;
      });
      return c;
    }
    // legend and other controls are obstacles
    var mapRect = mapEl.getBoundingClientRect();
    document.querySelectorAll('.vr-legend, .leaflet-control-scale').forEach(function (el) {
      var r = el.getBoundingClientRect();
      placed.push({ x: r.left - mapRect.left - 4, y: r.top - mapRect.top - 4, w: r.width + 8, h: r.height + 8, obstacle: true });
    });
    // markers themselves are obstacles too
    labelFeatures.forEach(function (lf) { var p = map.latLngToContainerPoint(lf.latlng); placed.push({ x: p.x - lf.radius, y: p.y - lf.radius, w: lf.radius * 2, h: lf.radius * 2, obstacle: true }); });
    var ALL = ['right', 'left', 'top', 'bottom', 'topright', 'bottomright', 'topleft', 'bottomleft'];
    labelFeatures.forEach(function (lf) {
      var p = map.latLngToContainerPoint(lf.latlng);
      var w = textWidth(lf.text, lf.size), h = lf.size * 1.25;
      var order = lf.placement === 'auto' ? ALL : [lf.placement].concat(ALL.filter(function (d) { return d !== lf.placement; }));
      var best = null, bestCost = Infinity;
      for (var i = 0; i < order.length; i++) {
        var b = cand(p, w, h, order[i], lf.radius); var c = cost(b) + i * 0.5;
        if (c < bestCost) { bestCost = c; best = b; }
        if (c < 1) break;
      }
      placed.push(best);
      var tt = L.tooltip({ permanent: true, direction: best.dir, className: 'vr-label', offset: best.off, interactive: false, opacity: 1 })
        .setLatLng(lf.latlng).setContent('<span style="font-size:' + lf.size + 'px">' + escapeHtml(lf.text) + '</span>');
      labelLayer.addLayer(tt);
    });
  }
  function escapeHtml(s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }

  // ---------- legend
  function legendControl() {
    var ctl = L.control({ position: M.legend.position || 'topright' });
    ctl.onAdd = function () {
      var div = L.DomUtil.create('div', 'vr-legend');
      var html = M.legend.title ? '<h4>' + escapeHtml(M.legend.title) + '</h4>' : '';
      M.legend.entries.forEach(function (e) {
        var sw = e.shape === 'line' ? '<span style="display:inline-block;width:16px;height:3px;background:' + e.color + ';border-radius:2px"></span>' : shapeSvg(e.shape || 'circle', 14, e.color, 1, 1);
        html += '<div class="row"><span class="sw">' + sw + '</span><span>' + escapeHtml(e.label) + '</span>' + (e.count !== undefined ? '<span class="n">' + e.count + '</span>' : '') + '</div>';
      });
      div.innerHTML = html;
      L.DomEvent.disableClickPropagation(div);
      return div;
    };
    return ctl;
  }

  try {
    M.layers.forEach(function (layer) {
      if (layer.type === 'points') addPoints(layer);
      else if (layer.type === 'tracks') addTracks(layer);
      else if (layer.type === 'flows') addFlows(layer);
      else if (layer.type === 'markers') addMarkers(layer);
    });
    if (M.legend.show && M.legend.entries.length) legendControl().addTo(map);

    if (M.zoom && M.center) map.setView(M.center, M.zoom);
    else if (M.zoom && M.bounds) { map.fitBounds(M.bounds, { padding: [M.fit_padding, M.fit_padding] }); map.setZoom(M.zoom); }
    else if (M.bounds) map.fitBounds(M.bounds, { padding: [M.fit_padding, M.fit_padding], maxZoom: 16 });
    else map.setView([50.11, 8.68], 11);

    var relayout = function () { placeArrows(); placeLabels(); };
    relayout();
    map.on('zoomend moveend', relayout);
    if (!RENDER) window.addEventListener('resize', function () { map.invalidateSize(); relayout(); });

    // ready: when all tiles of the current view are loaded (plus a short settle), or after a fallback timeout
    var done = false;
    function ready() { if (done) return; done = true; relayout(); setTimeout(function () { window.__READY__ = true; }, 250); }
    tileLayer.on('load', ready);
    tileLayer.on('tileerror', function (e) { window.__TILE_ERRORS__ = (window.__TILE_ERRORS__ || 0) + 1; });
    setTimeout(ready, 20000);
  } catch (e) {
    window.__ERROR__ = String(e && e.stack || e); var er = document.getElementById('error'); er.style.display = 'flex'; er.textContent = window.__ERROR__; window.__READY__ = true;
  }
})();

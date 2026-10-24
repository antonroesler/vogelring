/* Builds the ECharts option from window.__MODEL__ (house theme). */
(function () {
  var M = window.__MODEL__;
  var fmt = new Intl.NumberFormat('de-DE', { maximumFractionDigits: 2 });
  var fmtPct = new Intl.NumberFormat('de-DE', { style: 'percent', maximumFractionDigits: 1 });
  var FONT = getComputedStyle(document.documentElement).getPropertyValue('--font');
  var TEXT = '#1f2d36', MUTED = '#5F6B73', PRIMARY = '#00436C', GRID = 'rgba(0,0,0,0.08)';

  // diagonal stripes in the second colour over the first – categories that belong to two groups
  function stripes(pattern) {
    if (!pattern || pattern.length < 2) return undefined;
    return { symbol: 'rect', color: pattern[1], dashArrayX: [1, 0], dashArrayY: [4, 5], symbolSize: 1, rotation: Math.PI / 4 };
  }
  function fmtVal(v, axis) {
    if (v === null || v === undefined) return '';
    if (axis && axis.format === 'percent') return fmtPct.format(v / 100);
    if (axis && axis.format === 'integer') return fmt.format(Math.round(v));
    return fmt.format(v);
  }

  function axisBase(axis, isCategory, data) {
    var a = {
      name: axis.title || '',
      nameLocation: 'middle',
      nameGap: isCategory ? 34 : 44,
      nameTextStyle: { color: MUTED, fontSize: 12.5, fontFamily: FONT },
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { color: '#4a5560', fontSize: 12, fontFamily: FONT },
      splitLine: { show: !isCategory, lineStyle: { type: 'dashed', color: GRID } },
    };
    if (isCategory) { a.type = 'category'; a.data = data; a.axisLabel.interval = 0; a.axisLabel.hideOverlap = true;
      if (data && data.length > 12) { a.axisLabel.rotate = 35; a.nameGap = 60; } }
    else { a.type = 'value'; a.axisLabel.formatter = function (v) { return fmtVal(v, axis); };
      if (axis.min !== null && axis.min !== undefined) a.min = axis.min; if (axis.max !== null && axis.max !== undefined) a.max = axis.max; }
    return a;
  }

  function longestLabel(arr) { return (arr || []).reduce(function (m, s) { return Math.max(m, String(s).length); }, 0); }

  function build() {
    var kind = M.kind, horizontal = !!M.horizontal;
    var legendNames = (M.series || []).map(function (s) { return s.name; });
    var showLegend = legendNames.length > 1 || kind === 'pie' || !!M.legend_title;
    var legendBottom = legendNames.length <= 8;
    var opt = {
      animation: false,
      textStyle: { fontFamily: FONT, color: TEXT },
      color: (M.series || []).map(function (s) { return s.color; }),
      tooltip: { trigger: kind === 'pie' || kind === 'scatter' || kind === 'heatmap' ? 'item' : 'axis', confine: true,
        axisPointer: { type: kind === 'line' || kind === 'area' ? 'line' : 'shadow' },
        valueFormatter: function (v) { return fmtVal(v, M.y_axis); } },
      grid: { left: 30 + (M.y_axis.title ? 14 : 0), right: 28, top: 20, bottom: 20 + (M.x_axis.title ? 10 : 0), containLabel: true },
      legend: showLegend ? {
        type: 'scroll', orient: legendBottom ? 'horizontal' : 'vertical',
        bottom: legendBottom ? 4 : undefined, right: legendBottom ? undefined : 8, top: legendBottom ? undefined : 24,
        itemWidth: 14, itemHeight: 12, textStyle: { fontSize: 12, color: TEXT, fontFamily: FONT },
        data: legendNames.length ? legendNames : undefined,
      } : { show: false },
      series: [],
    };
    if (showLegend) { if (legendBottom) opt.grid.bottom = 44; else opt.grid.right = 24 + Math.min(260, 8 * longestLabel(legendNames) + 40); }
    if (M.legend_title && showLegend && !legendBottom) { opt.legend.formatter = undefined; opt.title = [{ text: M.legend_title, right: legendBottom ? undefined : 8, top: legendBottom ? undefined : 4, bottom: legendBottom ? 24 : undefined, left: legendBottom ? 'center' : undefined, textStyle: { fontSize: 12, color: MUTED, fontWeight: 600 } }]; }

    if (kind === 'timeline') return buildTimeline(opt);
    if (kind === 'calendar') return buildCalendar(opt);
    if (kind === 'sankey') return buildSankey(opt);
    if (kind === 'boxplot') return buildBoxplot(opt);
    if (kind === 'graph') return buildGraph(opt);
    if (M.facets) return buildFacets(opt);

    if (kind === 'pie') {
      opt.series = [{ type: 'pie', radius: ['38%', '68%'], center: ['50%', '50%'], avoidLabelOverlap: true,
        itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 4 },
        label: { formatter: function (p) { return p.name + '\n' + fmtVal(p.value) + ' (' + fmt.format(p.percent) + ' %)'; }, fontSize: 12, color: TEXT },
        data: M.pie.map(function (d) { return { name: d.name, value: d.value, itemStyle: { color: d.color, decal: stripes(d.pattern) } }; }) }];
      opt.legend.data = M.pie.map(function (d) { return d.name; });
      opt.tooltip.formatter = function (p) { return p.name + ': ' + fmtVal(p.value) + ' (' + fmt.format(p.percent) + ' %)'; };
      return opt;
    }

    if (kind === 'heatmap') {
      opt.grid = { left: 24, right: 90, top: 20, bottom: 20, containLabel: true };
      opt.xAxis = axisBase(M.x_axis, true, M.categories); opt.xAxis.position = 'top'; opt.xAxis.splitArea = { show: true };
      opt.yAxis = axisBase(M.y_axis, true, M.rows); opt.yAxis.inverse = true; opt.yAxis.splitArea = { show: true };
      opt.visualMap = { min: M.heat.min, max: M.heat.max, calculable: true, orient: 'vertical', right: 10, top: 'center',
        inRange: { color: ['#f3f4f6', '#9BC8B6', '#228096', '#00436C'] }, textStyle: { color: MUTED, fontSize: 11 } };
      var mid = (M.heat.min + M.heat.max) / 2;
      var heatData = M.heat.values.map(function (v) { return { value: v, label: { color: v[2] > mid ? '#fff' : '#1f2d36' } }; });
      opt.series = [{ type: 'heatmap', data: heatData, label: { show: M.show_values, fontSize: 10.5 },
        itemStyle: { borderColor: '#fff', borderWidth: 1 }, emphasis: { itemStyle: { shadowBlur: 6, shadowColor: 'rgba(0,0,0,.3)' } } }];
      opt.tooltip.formatter = function (p) { return M.rows[p.value[1]] + ' · ' + M.categories[p.value[0]] + ': ' + fmtVal(p.value[2]); };
      return opt;
    }

    if (kind === 'scatter') {
      opt.xAxis = axisBase(M.x_axis, false); opt.xAxis.splitLine.show = true;
      opt.yAxis = axisBase(M.y_axis, false);
      opt.series = M.series.map(function (s) { return { name: s.name, type: 'scatter', symbolSize: 9, data: s.data, itemStyle: { color: s.color, opacity: 0.85 } }; });
      opt.tooltip.formatter = function (p) { return p.seriesName + '<br>' + fmtVal(p.value[0], M.x_axis) + ' / ' + fmtVal(p.value[1], M.y_axis); };
      return opt;
    }

    var catAxis = axisBase(M.x_axis, true, M.categories);
    var valAxis = axisBase(M.y_axis, false);
    if (horizontal) { opt.xAxis = valAxis; opt.yAxis = catAxis; opt.yAxis.inverse = true; opt.yAxis.axisLabel.rotate = 0; opt.yAxis.nameGap = 8 * longestLabel(M.categories) + 16; }
    else { opt.xAxis = catAxis; opt.yAxis = valAxis; }
    var isBar = kind === 'bar' || kind === 'stacked_bar';
    var stacked = !!M.stack;
    var nSeries = M.series.length;

    opt.series = M.series.map(function (s, i) {
      var base = { name: s.name, data: s.data, itemStyle: { color: s.color, decal: stripes(s.pattern) }, emphasis: { focus: 'series' } };
      if (isBar) {
        base.type = 'bar'; base.barMaxWidth = 48; base.barGap = '15%'; base.barCategoryGap = '35%';
        if (stacked) base.stack = 'total';
        if (!stacked || i === nSeries - 1) base.itemStyle.borderRadius = horizontal ? [0, 3, 3, 0] : [3, 3, 0, 0];
        if (M.show_values) base.label = { show: true, position: stacked ? 'inside' : (horizontal ? 'right' : 'top'), fontSize: 11,
          color: stacked ? '#fff' : TEXT, formatter: function (p) { return p.value ? fmtVal(p.value, M.y_axis) : ''; } };
      } else {
        base.type = 'line'; base.smooth = 0.25; base.symbol = 'circle'; base.symbolSize = 7; base.lineStyle = { width: 2.5, color: s.color };
        if (kind === 'area') { base.areaStyle = { opacity: 0.18 }; if (stacked) base.stack = 'total'; }
        if (M.show_values) base.label = { show: true, position: 'top', fontSize: 11, color: TEXT, formatter: function (p) { return fmtVal(p.value, M.y_axis); } };
      }
      return base;
    });

    if (M.show_totals && M.totals && stacked && isBar) {
      opt.series.push({ name: '__totals', type: 'bar', stack: 'total', data: M.totals.map(function () { return 0; }),
        itemStyle: { color: 'transparent' }, tooltip: { show: false }, silent: true,
        label: { show: true, position: horizontal ? 'right' : 'top', fontSize: 11.5, fontWeight: 600, color: TEXT,
          formatter: function (p) { return fmtVal(M.totals[p.dataIndex], M.y_axis); } } });
      if (opt.legend && opt.legend.data) opt.legend.data = legendNames;
    }

    // annotations: bands/lines on the category axis
    if (M.annotations && M.annotations.length && opt.series.length) {
      var areas = [], lines = [];
      M.annotations.forEach(function (a) {
        if (a.kind === 'band') {
          var key = horizontal ? 'yAxis' : 'xAxis';
          var from = {}, to = {}; from[key] = a.from; to[key] = a.to === null || a.to === undefined ? a.from : a.to;
          from.name = a.label || ''; from.itemStyle = { color: a.color, opacity: 0.13 };
          areas.push([from, to]);
        } else {
          var k2 = horizontal ? 'yAxis' : 'xAxis'; var l = {}; l[k2] = a.from; l.name = a.label || ''; l.lineStyle = { color: a.color, type: 'dashed', width: 1.5 };
          lines.push(l);
        }
      });
      var host = opt.series[0];
      if (areas.length) host.markArea = { silent: true, data: areas, label: { show: true, position: 'insideTop', color: PRIMARY, fontSize: 11.5, fontWeight: 600 } };
      if (lines.length) host.markLine = { silent: true, symbol: 'none', data: lines, label: { color: PRIMARY, fontSize: 11 } };
    }
    return opt;
  }


  // ---------- additional kinds
  var fmtDate = function (iso) { var p = String(iso).split('-'); return p.length === 3 ? p[2] + '.' + p[1] + '.' + p[0] : iso; };

  function buildTimeline(opt) {
    var T = M.timeline;
    var rows = M.rows;
    opt.grid = { left: 24, right: 28, top: 16, bottom: T.classes.length > 1 ? 48 : 28, containLabel: true };
    opt.xAxis = { type: 'time', min: T.min, max: T.max, axisLabel: { color: '#4a5560', fontSize: 12, fontFamily: FONT, hideOverlap: true }, axisLine: { show: false }, axisTick: { show: false }, splitLine: { show: true, lineStyle: { type: 'dashed', color: GRID } }, name: M.x_axis.title || '', nameLocation: 'middle', nameGap: 30, nameTextStyle: { color: MUTED, fontSize: 12.5 } };
    opt.yAxis = { type: 'category', data: rows, inverse: true, axisLabel: { color: '#4a5560', fontSize: 12, fontFamily: FONT }, axisLine: { show: false }, axisTick: { show: false }, splitLine: { show: true, lineStyle: { color: GRID } }, name: M.y_axis.title || '', nameLocation: 'middle', nameGap: 8 * longestLabel(rows) + 16, nameTextStyle: { color: MUTED, fontSize: 12.5 } };
    opt.tooltip = { trigger: 'item', confine: true, formatter: function (p) { return p.data.tip || ''; } };
    var sym = Math.max(5, Math.min(12, 420 / Math.max(rows.length, 1)));
    var series = T.classes.map(function (c) {
      var dots = T.points.filter(function (pt) { return pt.cls === c.name && !pt.end; }).map(function (pt) { return { value: [pt.t, pt.row], tip: pt.tip, itemStyle: { color: pt.color } }; });
      return { name: c.name, type: 'scatter', symbolSize: sym, data: dots, itemStyle: { color: c.color, opacity: 0.9 } };
    });
    var ranges = T.points.filter(function (pt) { return pt.end; });
    if (ranges.length) {
      series.push({ name: 'Zeitraum', type: 'custom', renderItem: function (params, api) {
        var y = api.coord([api.value(0), api.value(2)])[1], x1 = api.coord([api.value(0), 0])[0], x2 = api.coord([api.value(1), 0])[0];
        var h = Math.max(4, Math.min(18, api.size([0, 1])[1] * 0.55));
        return { type: 'rect', shape: { x: x1, y: y - h / 2, width: Math.max(2, x2 - x1), height: h }, style: { fill: api.visual('color'), opacity: 0.75 } };
      }, encode: { x: [0, 1], y: 2 }, data: ranges.map(function (pt) { return { value: [pt.t, pt.end, pt.row], tip: pt.tip, itemStyle: { color: pt.color } }; }) });
    }
    opt.series = series;
    opt.legend = T.classes.length > 1 ? { bottom: 4, itemWidth: 12, itemHeight: 12, textStyle: { fontSize: 12, color: TEXT }, data: T.classes.map(function (c) { return c.name; }) } : { show: false };
    opt.color = T.classes.map(function (c) { return c.color; });
    return opt;
  }

  function buildCalendar(opt) {
    var C = M.calendar, years = C.years, n = years.length;
    var usable = M.height - 90, cellH = Math.max(90, Math.min(150, (usable - 30 * n) / n));
    opt.tooltip = { trigger: 'item', confine: true, formatter: function (p) { return fmtDate(p.value[0]) + ': ' + fmtVal(p.value[1]) + ' ' + C.value_label; } };
    opt.visualMap = { min: 0, max: C.max, calculable: true, orient: 'horizontal', left: 'center', bottom: 0, inRange: { color: ['#eef2f5', '#9BC8B6', '#228096', '#00436C'] }, textStyle: { color: MUTED, fontSize: 11 } };
    opt.calendar = years.map(function (y, i) {
      return { top: 28 + i * (cellH + 30), left: 56, right: 24, cellSize: ['auto', Math.max(9, Math.min(20, cellH / 7))], range: String(y), orient: 'horizontal',
        dayLabel: { firstDay: 1, nameMap: ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'], color: MUTED, fontSize: 10.5 },
        monthLabel: { nameMap: ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'], color: TEXT, fontSize: 11.5 },
        yearLabel: { show: true, position: 'left', margin: 36, color: PRIMARY, fontSize: 14, fontWeight: 700 },
        itemStyle: { borderWidth: 1.5, borderColor: '#fff', color: '#f6f8fa' }, splitLine: { lineStyle: { color: '#c9d1d8', width: 1 } } };
    });
    opt.series = years.map(function (y, i) { return { type: 'heatmap', coordinateSystem: 'calendar', calendarIndex: i, data: C.values.filter(function (v) { return v[0].slice(0, 4) === String(y); }) }; });
    opt.grid = undefined; opt.legend = { show: false };
    return opt;
  }

  function buildSankey(opt) {
    var S = M.sankey;
    opt.tooltip = { trigger: 'item', confine: true, formatter: function (p) { return p.dataType === 'edge' ? p.data.source.replace(/​/g, '') + ' → ' + p.data.target.replace(/​/g, '') + ': ' + fmtVal(p.value) : p.name.replace(/​/g, '') + ': ' + fmtVal(p.value); } };
    var rightPad = Math.min(360, 7.2 * longestLabel(S.nodes.filter(function (n) { return !S.links.some(function (l) { return l.source === n.name; }); }).map(function (n) { return n.label + '  000'; })) + 24);
    opt.series = [{ type: 'sankey', left: 24, right: rightPad, top: 16, bottom: 16, nodeWidth: 16, nodeGap: 10, nodeAlign: 'justify', layoutIterations: S.keep_order ? 0 : 64, emphasis: { focus: 'adjacency' },
      data: S.nodes.map(function (n) { return { name: n.name, itemStyle: { color: n.color, borderColor: n.color } }; }),
      links: S.links.map(function (l) { return { source: l.source, target: l.target, value: l.value }; }),
      lineStyle: { color: 'gradient', opacity: 0.35, curveness: 0.5 },
      label: { fontFamily: FONT, fontSize: 12, color: TEXT, formatter: function (p) { return p.name.replace(/​/g, '') + '  ' + fmtVal(p.value); } } }];
    opt.grid = undefined; opt.legend = { show: false };
    return opt;
  }

  function buildBoxplot(opt) {
    var B = M.box;
    var cat = axisBase(M.x_axis, true, M.categories), val = axisBase(M.y_axis, false);
    if (M.horizontal) { opt.xAxis = val; opt.yAxis = cat; opt.yAxis.inverse = true; } else { opt.xAxis = cat; opt.yAxis = val; }
    opt.tooltip = { trigger: 'item', confine: true, formatter: function (p) {
      if (p.seriesType === 'scatter') return M.categories[p.value[0]] + ': Ausreißer ' + fmtVal(p.value[1], M.y_axis);
      var v = p.value; return '<b>' + p.name + '</b><br>Min ' + fmtVal(v[1]) + ' · Q1 ' + fmtVal(v[2]) + ' · <b>Median ' + fmtVal(v[3]) + '</b> · Q3 ' + fmtVal(v[4]) + ' · Max ' + fmtVal(v[5]); } };
    opt.series = [
      { name: B.name, type: 'boxplot', data: B.data, itemStyle: { color: B.color + '33', borderColor: B.color, borderWidth: 1.8 }, boxWidth: ['35%', '55%'] },
      { name: 'Ausreißer', type: 'scatter', data: B.outliers, symbolSize: 6, itemStyle: { color: B.color, opacity: 0.6 } }];
    opt.legend = { show: false };
    return opt;
  }

  function buildGraph(opt) {
    var G = M.graph;
    opt.tooltip = { trigger: 'item', confine: true, formatter: function (p) { return p.dataType === 'edge' ? (p.data.label ? '<b>' + p.data.label + '</b><br>' : '') + p.data.source + ' – ' + p.data.target + (p.data.value > 1 ? ' (' + fmtVal(p.data.value) + ')' : '') : '<b>' + p.name + '</b><br>Verbindungen: ' + fmtVal(p.value); } };
    opt.series = [{ type: 'graph', layout: 'force', roam: !window.__RENDER__, draggable: !window.__RENDER__, animation: false,
      force: { repulsion: 180, edgeLength: [50, 130], gravity: 0.12, layoutAnimation: false, initLayout: 'circular' },
      categories: G.categories.map(function (c) { return { name: c.name, itemStyle: { color: c.color } }; }),
      data: G.nodes.map(function (n) { return { name: n.name, value: n.value, category: n.category, symbolSize: n.symbolSize, label: { show: true, position: 'right', fontSize: 11.5, fontFamily: FONT, color: TEXT } }; }),
      links: G.links.map(function (l) { return { source: l.source, target: l.target, value: l.value, label: l.label, lineStyle: { color: l.color || '#8a949c', width: 1 + Math.min(4, Math.sqrt(l.value || 1)), curveness: 0.1 } }; }),
      edgeSymbol: G.directed ? ['none', 'arrow'] : ['none', 'none'], edgeSymbolSize: 7,
      itemStyle: { borderColor: '#fff', borderWidth: 1.5 }, lineStyle: { opacity: 0.7 }, emphasis: { focus: 'adjacency', lineStyle: { width: 3 } } }];
    opt.legend = { show: false };
    opt.grid = undefined; opt.xAxis = undefined; opt.yAxis = undefined;
    if (G.edge_types.length) {  // hand-made legend for edge types (bottom left)
      var items = G.edge_types.map(function (t, i) { return [
        { type: 'rect', left: 14, bottom: 12 + i * 20 + 4, shape: { width: 18, height: 4 }, style: { fill: t.color } },
        { type: 'text', left: 40, bottom: 12 + i * 20, style: { text: t.name, fill: TEXT, fontSize: 12, fontFamily: FONT } }]; });
      opt.graphic = Array.prototype.concat.apply([{ type: 'rect', left: 6, bottom: 6, shape: { width: 24 + 8 * longestLabel(G.edge_types.map(function (t) { return t.name; })) + 40, height: 20 * G.edge_types.length + 10 }, style: { fill: 'rgba(255,255,255,0.9)', stroke: '#e3e8ec' } }], items.reverse());
    }
    return opt;
  }

  function buildFacets(opt) {
    var F = M.facets, cols = M.facet_columns, n = F.length, rows = Math.ceil(n / cols);
    var legendNames = M.series.map(function (s) { return s.name; });
    var showLegend = legendNames.length > 1;
    var top = 10, bottom = showLegend ? 44 : 8, left = 16, right = 10, gapX = 34, gapY = 44;
    var W = M.width - 44, H = M.height - 40 - (M.title || M.subtitle ? 40 : 0);
    var cw = (W - left - right - gapX * (cols - 1)) / cols, ch = (H - top - bottom - gapY * (rows - 1)) / rows;
    opt.grid = []; opt.xAxis = []; opt.yAxis = []; opt.title = []; opt.series = [];
    var isBar = M.kind === 'bar' || M.kind === 'stacked_bar', stacked = !!M.stack;
    var longest = longestLabel(M.categories);
    F.forEach(function (f, i) {
      var r = Math.floor(i / cols), c = i % cols;
      var gx = left + c * (cw + gapX), gy = top + 24 + r * (ch + gapY);
      opt.grid.push({ left: gx, top: gy, width: cw, height: ch - 24, containLabel: true });
      opt.title.push({ text: f.name, left: gx + 4, top: gy - 22, textStyle: { fontSize: 13, fontWeight: 600, color: PRIMARY, fontFamily: FONT } });
      var ax = axisBase(M.x_axis, true, f.categories); ax.gridIndex = i; ax.name = ''; if (M.categories.length > 8 || longest > 6) ax.axisLabel.rotate = 35; ax.axisLabel.fontSize = 10.5;
      var ay = axisBase(M.y_axis, false); ay.gridIndex = i; ay.name = c === 0 ? (M.y_axis.title || '') : ''; ay.axisLabel.fontSize = 10.5;
      opt.xAxis.push(ax); opt.yAxis.push(ay);
      f.series.forEach(function (s) {
        var base = { name: s.name, data: s.data, xAxisIndex: i, yAxisIndex: i, itemStyle: { color: s.color, decal: stripes(s.pattern) }, emphasis: { focus: 'series' } };
        if (isBar) { base.type = 'bar'; base.barMaxWidth = 32; if (stacked) base.stack = 'total'; }
        else { base.type = 'line'; base.smooth = 0.25; base.symbol = 'circle'; base.symbolSize = 5; base.lineStyle = { width: 2, color: s.color }; if (M.kind === 'area') { base.areaStyle = { opacity: 0.18 }; if (stacked) base.stack = 'total'; } }
        opt.series.push(base);
      });
    });
    opt.legend = showLegend ? { bottom: 4, itemWidth: 14, itemHeight: 12, textStyle: { fontSize: 12, color: TEXT }, data: legendNames } : { show: false };
    opt.color = M.series.map(function (s) { return s.color; });
    opt.tooltip = { trigger: 'axis', confine: true, axisPointer: { type: isBar ? 'shadow' : 'line' }, valueFormatter: function (v) { return fmtVal(v, M.y_axis); } };
    return opt;
  }

  var el = document.getElementById('chart');
  var chart = echarts.init(el, null, { renderer: 'canvas', devicePixelRatio: window.devicePixelRatio || 1 });
  try {
    var option = build();
    chart.on('finished', function () { window.__READY__ = true; });
    chart.setOption(option);
    setTimeout(function () { window.__READY__ = true; }, 1500);
  } catch (e) { window.__ERROR__ = String(e && e.stack || e); var er = document.getElementById('error'); er.style.display = 'flex'; er.textContent = window.__ERROR__; window.__READY__ = true; }
  if (!window.__RENDER__) window.addEventListener('resize', function () { chart.resize(); });
})();

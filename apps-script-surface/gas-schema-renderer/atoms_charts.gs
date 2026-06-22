// === Batch 5: SVG Chart & Data Viz Atoms ===

// Helper for linear scale (local to this batch)
function _linScale(val, domMin, domMax, rangeMin, rangeMax) {
  if (domMax === domMin) return rangeMin;
  return rangeMin + (val - domMin) / (domMax - domMin) * (rangeMax - rangeMin);
}

// Default color palette for charts
var _CHART_PALETTE = ['#6366f1','#22d3ee','#34d399','#fb923c','#f472b6','#a78bfa','#facc15','#818cf8','#e879f9','#2dd4bf'];

// ─────────────────────────────────────────────────────────
// 1. chartjs_bar — SVG horizontal or vertical bar chart
// ─────────────────────────────────────────────────────────
_RENDERERS['chartjs_bar'] = function(b) {
  var data        = b.data || [];
  var title       = b.title || '';
  var orientation = b.orientation || 'vertical';
  var height      = parseInt(b.height) || 220;
  var width       = parseInt(b.width)  || 560;
  var showVals    = b.show_values === true || b.show_values === 'true';
  var barColor    = b.bar_color || '#6366f1';

  if (!data.length) return '<div class="a2ui-chart-empty">No data</div>';

  var vals   = data.map(function(d){ return parseFloat(d.value) || 0; });
  var maxVal = Math.max.apply(null, vals);
  if (maxVal === 0) maxVal = 1;

  var svg = '';

  if (orientation === 'horizontal') {
    // Horizontal bars
    var padL = 120, padR = 60, padT = 30, padB = 20;
    var barH     = 22;
    var barGap   = 10;
    var totalH   = padT + data.length * (barH + barGap) + padB;
    var chartW   = width - padL - padR;

    svg += '<svg viewBox="0 0 ' + width + ' ' + totalH + '" width="100%" preserveAspectRatio="xMidYMid meet">';
    if (title) svg += '<text x="' + (width/2) + '" y="18" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

    // Gridlines
    for (var g = 0; g <= 4; g++) {
      var gx = padL + (g / 4) * chartW;
      var gv = Math.round(maxVal * g / 4);
      svg += '<line x1="' + gx + '" y1="' + padT + '" x2="' + gx + '" y2="' + (totalH - padB) + '" stroke="#e2e8f0" stroke-width="1"/>';
      svg += '<text x="' + gx + '" y="' + (padT - 5) + '" text-anchor="middle" font-size="9" fill="#94a3b8">' + gv + '</text>';
    }

    data.forEach(function(d, i) {
      var val   = parseFloat(d.value) || 0;
      var bw    = _linScale(val, 0, maxVal, 0, chartW);
      var y     = padT + i * (barH + barGap);
      var color = d.color || barColor;
      svg += '<text x="' + (padL - 6) + '" y="' + (y + barH/2 + 4) + '" text-anchor="end" font-size="11" fill="#334155">' + _esc((d.label||'').substr(0,16)) + '</text>';
      svg += '<rect x="' + padL + '" y="' + y + '" width="' + bw + '" height="' + barH + '" rx="3" fill="' + _esc(color) + '"/>';
      if (showVals) {
        svg += '<text x="' + (padL + bw + 4) + '" y="' + (y + barH/2 + 4) + '" font-size="10" fill="#475569">' + val + '</text>';
      }
    });

    svg += '</svg>';
  } else {
    // Vertical bars
    var padL = 45, padR = 15, padT = 30, padB = 38;
    var chartH = height - padT - padB;
    var chartW = width  - padL - padR;
    var barW   = Math.max(8, (chartW / data.length) * 0.6);
    var barSpacing = chartW / data.length;

    svg += '<svg viewBox="0 0 ' + width + ' ' + height + '" width="100%" preserveAspectRatio="xMidYMid meet">';
    if (title) svg += '<text x="' + (width/2) + '" y="18" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

    // Horizontal gridlines
    for (var g = 0; g <= 4; g++) {
      var gy = padT + (1 - g/4) * chartH;
      var gv = Math.round(maxVal * g / 4);
      svg += '<line x1="' + padL + '" y1="' + gy + '" x2="' + (width - padR) + '" y2="' + gy + '" stroke="#e2e8f0" stroke-width="1"/>';
      svg += '<text x="' + (padL - 4) + '" y="' + (gy + 4) + '" text-anchor="end" font-size="9" fill="#94a3b8">' + gv + '</text>';
    }

    // Baseline
    svg += '<line x1="' + padL + '" y1="' + (padT + chartH) + '" x2="' + (width - padR) + '" y2="' + (padT + chartH) + '" stroke="#cbd5e1" stroke-width="1.5"/>';

    data.forEach(function(d, i) {
      var val   = parseFloat(d.value) || 0;
      var bh    = _linScale(val, 0, maxVal, 0, chartH);
      var cx    = padL + (i + 0.5) * barSpacing;
      var x     = cx - barW / 2;
      var y     = padT + chartH - bh;
      var color = d.color || barColor;
      svg += '<rect x="' + x + '" y="' + y + '" width="' + barW + '" height="' + bh + '" rx="3" fill="' + _esc(color) + '"/>';
      if (showVals && bh > 12) {
        svg += '<text x="' + cx + '" y="' + (y - 3) + '" text-anchor="middle" font-size="9" fill="#475569">' + val + '</text>';
      }
      var lbl = (d.label||'').substr(0,10);
      svg += '<text x="' + cx + '" y="' + (padT + chartH + 14) + '" text-anchor="middle" font-size="10" fill="#64748b">' + _esc(lbl) + '</text>';
    });

    svg += '</svg>';
  }

  return '<div class="a2ui-chartjs-bar">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 2. chartjs_line — SVG line/area chart
// ─────────────────────────────────────────────────────────
_RENDERERS['chartjs_line'] = function(b) {
  var title      = b.title || '';
  var height     = parseInt(b.height) || 260;
  var width      = parseInt(b.width)  || 560;
  var smooth     = b.smooth === true || b.smooth === 'true';
  var showPts    = b.show_points !== false && b.show_points !== 'false';
  var areaFill   = b.area_fill === true || b.area_fill === 'true';

  // Normalise to multi-dataset form
  var datasets, labels;
  if (b.datasets) {
    datasets = b.datasets;
    labels   = b.labels || datasets[0].data.map(function(_, i){ return String(i); });
  } else if (b.data) {
    labels   = b.data.map(function(d){ return d.label || ''; });
    datasets = [{ label: title, data: b.data.map(function(d){ return parseFloat(d.value)||0; }), color: '#6366f1' }];
    title    = '';
  } else {
    return '<div class="a2ui-chart-empty">No data</div>';
  }

  var padL = 50, padR = 20, padT = 36, padB = 50;
  var chartH = height - padT - padB;
  var chartW = width  - padL - padR;

  // Compute global min/max
  var allVals = [];
  datasets.forEach(function(ds){ ds.data.forEach(function(v){ allVals.push(parseFloat(v)||0); }); });
  var minVal = Math.min.apply(null, allVals);
  var maxVal = Math.max.apply(null, allVals);
  if (maxVal === minVal) { maxVal += 1; minVal -= 1; }

  var n = labels.length;

  function px(i)  { return padL + (n > 1 ? i / (n - 1) : 0.5) * chartW; }
  function py(v)  { return padT + (1 - (v - minVal) / (maxVal - minVal)) * chartH; }

  var svg = '<svg viewBox="0 0 ' + width + ' ' + height + '" width="100%" preserveAspectRatio="xMidYMid meet">';
  if (title) svg += '<text x="' + (width/2) + '" y="20" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

  // Gridlines
  for (var g = 0; g <= 4; g++) {
    var gy = padT + (g / 4) * chartH;
    var gv = maxVal - (maxVal - minVal) * g / 4;
    svg += '<line x1="' + padL + '" y1="' + gy + '" x2="' + (width - padR) + '" y2="' + gy + '" stroke="#e2e8f0" stroke-width="1"/>';
    svg += '<text x="' + (padL - 4) + '" y="' + (gy + 4) + '" text-anchor="end" font-size="9" fill="#94a3b8">' + Math.round(gv) + '</text>';
  }

  // X-axis labels
  labels.forEach(function(lbl, i) {
    if (n <= 12 || i % Math.ceil(n / 10) === 0) {
      svg += '<text x="' + px(i) + '" y="' + (padT + chartH + 14) + '" text-anchor="middle" font-size="9" fill="#64748b">' + _esc((lbl||'').substr(0,8)) + '</text>';
    }
  });

  // Datasets
  datasets.forEach(function(ds, di) {
    var color = ds.color || _CHART_PALETTE[di % _CHART_PALETTE.length];
    var pts   = ds.data.map(function(v, i){ return { x: px(i), y: py(parseFloat(v)||0) }; });
    if (!pts.length) return;

    // Build path
    var pathD = '';
    if (smooth && pts.length > 2) {
      pathD = 'M ' + pts[0].x + ' ' + pts[0].y;
      for (var i = 0; i < pts.length - 1; i++) {
        var cp1x = pts[i].x + (pts[i+1].x - pts[i].x) / 3;
        var cp1y = pts[i].y;
        var cp2x = pts[i+1].x - (pts[i+1].x - pts[i].x) / 3;
        var cp2y = pts[i+1].y;
        pathD += ' C ' + cp1x + ' ' + cp1y + ' ' + cp2x + ' ' + cp2y + ' ' + pts[i+1].x + ' ' + pts[i+1].y;
      }
    } else {
      pathD = pts.map(function(p, i){ return (i ? 'L' : 'M') + p.x + ' ' + p.y; }).join(' ');
    }

    // Area fill
    if (areaFill || ds.fill) {
      var areaD = pathD + ' L ' + pts[pts.length-1].x + ' ' + (padT + chartH) + ' L ' + pts[0].x + ' ' + (padT + chartH) + ' Z';
      svg += '<path d="' + areaD + '" fill="' + _esc(color) + '" fill-opacity="0.18" stroke="none"/>';
    }

    svg += '<path d="' + pathD + '" fill="none" stroke="' + _esc(color) + '" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>';

    if (showPts) {
      pts.forEach(function(p) {
        svg += '<circle cx="' + p.x + '" cy="' + p.y + '" r="3.5" fill="' + _esc(color) + '" stroke="#fff" stroke-width="1.5"/>';
      });
    }
  });

  // Legend
  if (datasets.length > 1 || (datasets.length === 1 && datasets[0].label)) {
    var legY = padT + chartH + 28;
    var legX = padL;
    datasets.forEach(function(ds, di) {
      var color = ds.color || _CHART_PALETTE[di % _CHART_PALETTE.length];
      svg += '<rect x="' + legX + '" y="' + (legY - 7) + '" width="12" height="3" rx="1.5" fill="' + _esc(color) + '"/>';
      svg += '<text x="' + (legX + 16) + '" y="' + legY + '" font-size="10" fill="#64748b">' + _esc(ds.label||'') + '</text>';
      legX += 80;
    });
  }

  svg += '</svg>';
  return '<div class="a2ui-chartjs-line">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 3. chartjs_pie — SVG pie/donut chart
// ─────────────────────────────────────────────────────────
_RENDERERS['chartjs_pie'] = function(b) {
  var data       = b.data || [];
  var title      = b.title || '';
  var donut      = b.donut === true || b.donut === 'true';
  var innerLabel = b.inner_label || '';
  var height     = parseInt(b.height) || 260;

  if (!data.length) return '<div class="a2ui-chart-empty">No data</div>';

  var total = data.reduce(function(s, d){ return s + (parseFloat(d.value)||0); }, 0);
  if (!total) return '<div class="a2ui-chart-empty">No data</div>';

  var width  = height;
  var cx     = width / 2;
  var cy     = height / 2 - 10;
  var r      = Math.min(cx, cy) - 10;

  var svg = '<svg viewBox="0 0 ' + width + ' ' + (height + 30) + '" width="100%" preserveAspectRatio="xMidYMid meet">';
  if (title) svg += '<text x="' + cx + '" y="14" text-anchor="middle" font-size="12" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

  var startAngle = -Math.PI / 2;
  var colors = _CHART_PALETTE;

  data.forEach(function(d, i) {
    var val      = parseFloat(d.value) || 0;
    var pct      = val / total;
    var endAngle = startAngle + pct * 2 * Math.PI;
    var x1       = cx + r * Math.cos(startAngle);
    var y1       = cy + r * Math.sin(startAngle);
    var x2       = cx + r * Math.cos(endAngle);
    var y2       = cy + r * Math.sin(endAngle);
    var largeArc = pct > 0.5 ? 1 : 0;
    var color    = d.color || colors[i % colors.length];

    var pathD = 'M ' + cx + ' ' + cy + ' L ' + x1 + ' ' + y1 +
                ' A ' + r + ' ' + r + ' 0 ' + largeArc + ' 1 ' + x2 + ' ' + y2 + ' Z';
    svg += '<path d="' + pathD + '" fill="' + _esc(color) + '" stroke="#fff" stroke-width="1.5"/>';
    startAngle = endAngle;
  });

  // Donut hole
  if (donut) {
    var ir = r * 0.55;
    svg += '<circle cx="' + cx + '" cy="' + cy + '" r="' + ir + '" fill="#fff"/>';
    if (innerLabel) {
      svg += '<text x="' + cx + '" y="' + (cy + 5) + '" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">' + _esc(innerLabel) + '</text>';
    }
  }

  // Legend below
  var legCols = Math.min(data.length, 3);
  var legW    = width / legCols;
  data.forEach(function(d, i) {
    var color = d.color || colors[i % colors.length];
    var lx    = (i % legCols) * legW + 4;
    var ly    = height + Math.floor(i / legCols) * 16 + 8;
    svg += '<rect x="' + lx + '" y="' + (ly - 8) + '" width="10" height="10" rx="2" fill="' + _esc(color) + '"/>';
    svg += '<text x="' + (lx + 13) + '" y="' + ly + '" font-size="9" fill="#64748b">' + _esc((d.label||'').substr(0,14)) + '</text>';
  });

  svg += '</svg>';
  return '<div class="a2ui-chartjs-pie">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 4. benchmark_comparison — horizontal bar comparison
// ─────────────────────────────────────────────────────────
_RENDERERS['benchmark_comparison'] = function(b) {
  var items = b.benchmarks || [];
  var title = b.title || '';

  if (!items.length) return '<div class="a2ui-chart-empty">No benchmarks</div>';

  var vals   = items.map(function(d){ return parseFloat(d.value)||0; });
  var globalMax = Math.max.apply(null, vals);

  var padL = 130, padR = 80, padT = 30, rowH = 36, rowGap = 4;
  var width  = 560;
  var totalH = padT + items.length * (rowH + rowGap) + 20;
  var chartW = width - padL - padR;

  var svg = '<svg viewBox="0 0 ' + width + ' ' + totalH + '" width="100%" preserveAspectRatio="xMidYMid meet">';
  if (title) svg += '<text x="' + (width/2) + '" y="20" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

  items.forEach(function(d, i) {
    var val    = parseFloat(d.value) || 0;
    var maxV   = parseFloat(d.max_value) || globalMax || 1;
    var pct    = Math.min(val / maxV, 1);
    var bw     = pct * chartW;
    var y      = padT + i * (rowH + rowGap);
    var color  = d.color || _CHART_PALETTE[i % _CHART_PALETTE.length];
    var unit   = d.unit || '';

    // Alternating row bg
    if (i % 2 === 0) {
      svg += '<rect x="0" y="' + y + '" width="' + width + '" height="' + rowH + '" fill="#f8fafc" rx="2"/>';
    }

    // Label
    svg += '<text x="' + (padL - 8) + '" y="' + (y + rowH/2 + 4) + '" text-anchor="end" font-size="11" fill="#334155">' + _esc((d.name||'').substr(0,18)) + '</text>';

    // Bar track
    svg += '<rect x="' + padL + '" y="' + (y + 8) + '" width="' + chartW + '" height="' + (rowH - 16) + '" rx="4" fill="#e2e8f0"/>';
    // Bar fill
    if (bw > 0) {
      svg += '<rect x="' + padL + '" y="' + (y + 8) + '" width="' + bw + '" height="' + (rowH - 16) + '" rx="4" fill="' + _esc(color) + '"/>';
    }

    // Value
    svg += '<text x="' + (padL + chartW + 6) + '" y="' + (y + rowH/2 + 4) + '" font-size="11" font-weight="600" fill="#1e293b">' + _esc(String(val) + (unit ? ' '+unit : '')) + '</text>';
  });

  svg += '</svg>';
  return '<div class="a2ui-benchmark-comparison">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 5. data_table_sortable — styled data table
// ─────────────────────────────────────────────────────────
_RENDERERS['data_table_sortable'] = function(b) {
  var columns = b.columns || [];
  var rows    = b.rows    || [];
  var title   = b.title   || '';
  var striped = b.striped === true || b.striped === 'true';
  var compact = b.compact === true || b.compact === 'true';
  var uid     = Math.random().toString(36).substr(2,6);

  if (!columns.length && rows.length) {
    columns = Object.keys(rows[0]).map(function(k){ return { key: k, label: k }; });
  }
  if (!columns.length) return '<div class="a2ui-chart-empty">No columns defined</div>';

  var cellPad = compact ? '4px 8px' : '8px 12px';

  var html = '';
  if (title) html += '<div class="a2ui-table-title">' + _esc(title) + '</div>';

  html += '<div class="a2ui-table-wrap" style="overflow-x:auto;">';
  html += '<table id="tbl-' + uid + '" class="a2ui-data-table' + (striped ? ' striped' : '') + '" style="width:100%;border-collapse:collapse;font-size:13px;">';

  // Header
  html += '<thead><tr>';
  columns.forEach(function(col) {
    var align = col.type === 'number' ? 'right' : 'left';
    html += '<th data-key="' + _esc(col.key||'') + '" style="background:#1e293b;color:#f1f5f9;padding:' + cellPad + ';text-align:' + align + ';cursor:pointer;user-select:none;white-space:nowrap;" onclick="(function(th){var tbl=th.closest(\'table\');var idx=Array.from(th.parentNode.children).indexOf(th);var asc=th.dataset.asc!==\'1\';th.dataset.asc=asc?\'1\':\'\';Array.from(tbl.querySelectorAll(\'th\')).forEach(function(t){t.textContent=t.textContent.replace(/ [▲▼]$/,\'\');});th.textContent+=(asc?\' ▲\':\' ▼\');var tbody=tbl.querySelector(\'tbody\');var rowsArr=Array.from(tbody.querySelectorAll(\'tr\'));rowsArr.sort(function(a,b){var av=a.cells[idx]?a.cells[idx].textContent:\'\',bv=b.cells[idx]?b.cells[idx].textContent:\'\';var an=parseFloat(av),bn=parseFloat(bv);if(!isNaN(an)&&!isNaN(bn))return asc?an-bn:bn-an;return asc?av.localeCompare(bv):bv.localeCompare(av);});rowsArr.forEach(function(r){tbody.appendChild(r);});})(this)">';
    html += _esc(col.label || col.key || '');
    html += '</th>';
  });
  html += '</tr></thead>';

  // Body
  html += '<tbody>';
  rows.forEach(function(row, ri) {
    var bg = '';
    if (striped && ri % 2 === 1) bg = 'background:#f8fafc;';
    html += '<tr style="' + bg + '">';
    columns.forEach(function(col) {
      var val   = row[col.key];
      var align = col.type === 'number' ? 'right' : 'left';
      var disp  = (val === null || val === undefined) ? '' : String(val);
      html += '<td style="padding:' + cellPad + ';text-align:' + align + ';border-bottom:1px solid #f1f5f9;color:#334155;">' + _esc(disp) + '</td>';
    });
    html += '</tr>';
  });
  html += '</tbody></table></div>';

  return '<div class="a2ui-data-table-sortable">' + html + '</div>';
};

// ─────────────────────────────────────────────────────────
// 6. metric_comparison_card — compare two metrics
// ─────────────────────────────────────────────────────────
_RENDERERS['metric_comparison_card'] = function(b) {
  var baseline   = b.baseline   || {};
  var comparison = b.comparison || {};
  var title      = b.title || '';
  var higherBetter = b.higher_is_better !== false && b.higher_is_better !== 'false';

  var bVal  = parseFloat(baseline.value)   || 0;
  var cVal  = parseFloat(comparison.value) || 0;
  var delta = bVal !== 0 ? ((cVal - bVal) / Math.abs(bVal)) * 100 : 0;
  var better = higherBetter ? (cVal >= bVal) : (cVal <= bVal);
  var deltaColor = better ? '#16a34a' : '#dc2626';
  var arrow      = cVal >= bVal ? '↑' : '↓';
  var deltaTxt   = (delta >= 0 ? '+' : '') + delta.toFixed(1) + '%';

  var html = '<div class="a2ui-metric-comparison">';
  if (title) html += '<div class="a2ui-metric-cmp-title">' + _esc(title) + '</div>';
  html += '<div class="a2ui-metric-cmp-body">';

  // Baseline
  html += '<div class="a2ui-metric-cmp-col">';
  html += '<div class="a2ui-metric-cmp-lbl">' + _esc(baseline.label || 'Baseline') + '</div>';
  html += '<div class="a2ui-metric-cmp-val">' + _esc(String(bVal)) + (baseline.unit ? ' <span class="a2ui-metric-unit">' + _esc(baseline.unit) + '</span>' : '') + '</div>';
  html += '</div>';

  // Delta badge
  html += '<div class="a2ui-metric-cmp-delta" style="color:' + deltaColor + ';border-color:' + deltaColor + ';">' + arrow + ' ' + _esc(deltaTxt) + '</div>';

  // Comparison
  html += '<div class="a2ui-metric-cmp-col">';
  html += '<div class="a2ui-metric-cmp-lbl">' + _esc(comparison.label || 'Comparison') + '</div>';
  html += '<div class="a2ui-metric-cmp-val">' + _esc(String(cVal)) + (comparison.unit ? ' <span class="a2ui-metric-unit">' + _esc(comparison.unit) + '</span>' : '') + '</div>';
  html += '</div>';

  html += '</div></div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 7. mini_sparkline_set — multiple tiny sparklines
// ─────────────────────────────────────────────────────────
_RENDERERS['mini_sparkline_set'] = function(b) {
  var sparklines = b.sparklines || [];
  if (!sparklines.length) return '<div class="a2ui-chart-empty">No sparklines</div>';

  var html = '<div class="a2ui-sparkline-set">';

  sparklines.forEach(function(sp) {
    var data  = (sp.data || []).map(function(v){ return parseFloat(v)||0; });
    var color = sp.color || '#6366f1';
    var label = sp.label || '';
    var unit  = sp.unit  || '';
    var last  = data.length ? data[data.length-1] : 0;

    var svgW = 80, svgH = 30;
    var minV = Math.min.apply(null, data);
    var maxV = Math.max.apply(null, data);
    if (maxV === minV) { maxV += 1; }
    var n    = data.length;

    var pts = data.map(function(v, i) {
      var x = n > 1 ? (i / (n-1)) * svgW : svgW/2;
      var y = _linScale(v, minV, maxV, svgH - 2, 2);
      return x + ',' + y;
    }).join(' ');

    var sparkSvg = '<svg viewBox="0 0 ' + svgW + ' ' + svgH + '" width="' + svgW + '" height="' + svgH + '" style="display:inline-block;vertical-align:middle;">';
    if (data.length > 1) {
      sparkSvg += '<polyline points="' + pts + '" fill="none" stroke="' + _esc(color) + '" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>';
    }
    sparkSvg += '</svg>';

    html += '<div class="a2ui-sparkline-row">';
    html += '<span class="a2ui-sparkline-label">' + _esc(label) + '</span>';
    html += sparkSvg;
    html += '<span class="a2ui-sparkline-val" style="color:' + _esc(color) + ';">' + _esc(String(last)) + (unit ? ' '+_esc(unit) : '') + '</span>';
    html += '</div>';
  });

  html += '</div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 8. donut_stat — large donut with center stat
// ─────────────────────────────────────────────────────────
_RENDERERS['donut_stat'] = function(b) {
  var value = Math.min(100, Math.max(0, parseFloat(b.value) || 0));
  var label = b.label || '';
  var color = b.color || '#22d3ee';
  var size  = parseInt(b.size) || 160;
  var unit  = b.unit !== undefined ? String(b.unit) : '%';
  var uid   = Math.random().toString(36).substr(2,6);

  var r         = size / 2 - 14;
  var cx        = size / 2;
  var cy        = size / 2;
  var circ      = 2 * Math.PI * r;
  var dashOffset = circ * (1 - value / 100);

  var html = '';
  html += '<style>@keyframes donut-spin-' + uid + '{from{stroke-dashoffset:' + circ.toFixed(2) + '}to{stroke-dashoffset:' + dashOffset.toFixed(2) + '}}</style>';
  html += '<div class="a2ui-donut-stat" style="display:inline-block;text-align:center;">';
  html += '<svg viewBox="0 0 ' + size + ' ' + size + '" width="' + size + '" height="' + size + '">';
  // Track
  html += '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="none" stroke="#e2e8f0" stroke-width="12"/>';
  // Arc
  html += '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="none" stroke="' + _esc(color) + '" stroke-width="12" stroke-linecap="round"' +
          ' stroke-dasharray="' + circ.toFixed(2) + '"' +
          ' stroke-dashoffset="' + circ.toFixed(2) + '"' +
          ' transform="rotate(-90 ' + cx + ' ' + cy + ')"' +
          ' style="animation:donut-spin-' + uid + ' 1s ease-out forwards;"/>';
  // Center text
  html += '<text x="' + cx + '" y="' + (cy - 4) + '" text-anchor="middle" font-size="' + Math.round(size*0.18) + '" font-weight="bold" fill="#1e293b">' + _esc(String(Math.round(value))) + '</text>';
  html += '<text x="' + cx + '" y="' + (cy + Math.round(size*0.14)) + '" text-anchor="middle" font-size="' + Math.round(size*0.1) + '" fill="#64748b">' + _esc(unit) + '</text>';
  html += '</svg>';
  if (label) html += '<div class="a2ui-donut-label" style="margin-top:4px;font-size:13px;color:#64748b;">' + _esc(label) + '</div>';
  html += '</div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 9. status_dashboard — grid of status items
// ─────────────────────────────────────────────────────────
_RENDERERS['status_dashboard'] = function(b) {
  var title = b.title || 'System Status';
  var items = b.items || [];

  var statusColors = {
    operational:  '#22c55e',
    degraded:     '#f59e0b',
    outage:       '#ef4444',
    maintenance:  '#6366f1'
  };
  var statusLabels = {
    operational: 'Operational',
    degraded:    'Degraded',
    outage:      'Outage',
    maintenance: 'Maintenance'
  };

  // Overall status
  var hasOutage      = items.some(function(i){ return i.status === 'outage'; });
  var hasDegraded    = items.some(function(i){ return i.status === 'degraded'; });
  var hasMaintenance = items.some(function(i){ return i.status === 'maintenance'; });
  var overallStatus  = hasOutage ? 'outage' : hasDegraded ? 'degraded' : hasMaintenance ? 'maintenance' : 'operational';
  var overallMessages = {
    operational: 'All systems operational',
    degraded:    'Some systems are experiencing degraded performance',
    outage:      'One or more systems are experiencing an outage',
    maintenance: 'Scheduled maintenance in progress'
  };

  var html = '<div class="a2ui-status-dashboard">';
  html += '<div class="a2ui-status-header" style="background:' + statusColors[overallStatus] + ';">';
  html += '<span class="a2ui-status-dot-lg" style="background:#fff;opacity:0.9;"></span>';
  html += '<div>';
  if (title) html += '<div class="a2ui-status-title">' + _esc(title) + '</div>';
  html += '<div class="a2ui-status-overall">' + _esc(overallMessages[overallStatus]) + '</div>';
  html += '</div></div>';

  html += '<div class="a2ui-status-list">';
  items.forEach(function(item) {
    var st    = item.status || 'operational';
    var color = statusColors[st] || '#94a3b8';
    var stLbl = statusLabels[st] || st;
    html += '<div class="a2ui-status-item">';
    html += '<span class="a2ui-status-dot" style="background:' + color + ';"></span>';
    html += '<div class="a2ui-status-info">';
    html += '<span class="a2ui-status-name">' + _esc(item.name || '') + '</span>';
    if (item.description) html += '<span class="a2ui-status-desc">' + _esc(item.description) + '</span>';
    html += '</div>';
    html += '<span class="a2ui-status-pill" style="background:' + color + '20;color:' + color + ';border:1px solid ' + color + '40;">' + _esc(stLbl) + '</span>';
    html += '</div>';
  });
  html += '</div></div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 10. uptime_timeline — horizontal uptime bar
// ─────────────────────────────────────────────────────────
_RENDERERS['uptime_timeline'] = function(b) {
  var label   = b.label || '';
  var pct     = parseFloat(b.uptime_percent) || 100;
  var period  = b.period || '';
  var days    = b.days || [];

  function dayColor(d) {
    var s = typeof d === 'object' ? (d.status !== undefined ? d.status : 1) : d;
    var v = parseFloat(s);
    if (v >= 1)   return '#22c55e';
    if (v >= 0.5) return '#f59e0b';
    return '#ef4444';
  }
  function dayTitle(d, i) {
    if (typeof d === 'object' && d.date) return d.date;
    return 'Day ' + (i+1);
  }

  var blockW = days.length > 0 ? Math.max(2, Math.min(8, Math.floor(480 / days.length))) : 6;
  var blockH = 24;
  var gap    = 1;
  var padL   = 10, padR = 70, padT = 20;
  var width  = 560;
  var svgW   = width - padL - padR;

  var html = '<div class="a2ui-uptime-row">';

  var svg = '<svg viewBox="0 0 ' + width + ' ' + (blockH + padT + 10) + '" width="100%" preserveAspectRatio="xMidYMid meet">';
  if (label) svg += '<text x="' + padL + '" y="14" font-size="12" font-weight="600" fill="#334155">' + _esc(label) + '</text>';

  var x = padL;
  days.forEach(function(d, i) {
    var color = dayColor(d);
    var ttl   = _esc(dayTitle(d, i));
    svg += '<rect x="' + x + '" y="' + padT + '" width="' + (blockW - gap) + '" height="' + blockH + '" rx="1.5" fill="' + color + '"><title>' + ttl + '</title></rect>';
    x += blockW;
  });

  // Fill remaining space gray if blocks don't fill width
  if (days.length === 0) {
    svg += '<rect x="' + padL + '" y="' + padT + '" width="' + svgW + '" height="' + blockH + '" rx="3" fill="#e2e8f0"/>';
  }

  // Uptime badge
  var badgeColor = pct >= 99 ? '#22c55e' : pct >= 95 ? '#f59e0b' : '#ef4444';
  var bx = width - padR + 4;
  svg += '<text x="' + bx + '" y="' + (padT + blockH/2 + 5) + '" font-size="12" font-weight="700" fill="' + badgeColor + '">' + pct.toFixed(2) + '%</text>';
  if (period) svg += '<text x="' + bx + '" y="' + (padT + blockH + 10) + '" font-size="9" fill="#94a3b8">' + _esc(period) + '</text>';

  svg += '</svg>';
  html += svg + '</div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 11. command_palette — searchable command list
// ─────────────────────────────────────────────────────────
_RENDERERS['command_palette'] = function(b) {
  var commands    = b.commands || [];
  var placeholder = b.placeholder || 'Search commands…';
  var uid         = Math.random().toString(36).substr(2,6);

  // Group by category
  var groups = {};
  var order  = [];
  commands.forEach(function(cmd) {
    var cat = cmd.category || 'General';
    if (!groups[cat]) { groups[cat] = []; order.push(cat); }
    groups[cat].push(cmd);
  });

  var html = '<div class="a2ui-cmd-palette" id="cp-' + uid + '">';
  html += '<div class="a2ui-cmd-search-wrap">';
  html += '<svg class="a2ui-cmd-search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>';
  html += '<input class="a2ui-cmd-input" type="text" placeholder="' + _esc(placeholder) + '"' +
          ' oninput="(function(v){var items=document.querySelectorAll(\'#cp-' + uid + ' .a2ui-cmd-item\');var cats=document.querySelectorAll(\'#cp-' + uid + ' .a2ui-cmd-cat\');' +
          'items.forEach(function(el){var t=el.textContent.toLowerCase();el.style.display=t.indexOf(v.toLowerCase())>-1?\'\':\'none\';});' +
          'cats.forEach(function(cat){var anyVis=false;var next=cat.nextElementSibling;while(next&&!next.classList.contains(\'a2ui-cmd-cat\')){if(next.classList.contains(\'a2ui-cmd-item\')&&next.style.display!==\'none\')anyVis=true;next=next.nextElementSibling;}cat.style.display=anyVis?\'\':\'none\';});' +
          '})(this.value)"/>';
  html += '</div>';
  html += '<div class="a2ui-cmd-list">';

  order.forEach(function(cat) {
    html += '<div class="a2ui-cmd-cat">' + _esc(cat) + '</div>';
    groups[cat].forEach(function(cmd) {
      html += '<div class="a2ui-cmd-item">';
      html += '<span class="a2ui-cmd-name">' + _esc(cmd.name || '') + '</span>';
      if (cmd.description) html += '<span class="a2ui-cmd-desc">' + _esc(cmd.description) + '</span>';
      if (cmd.shortcut) html += '<kbd class="a2ui-cmd-shortcut">' + _esc(cmd.shortcut) + '</kbd>';
      html += '</div>';
    });
  });

  html += '</div></div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 12. search_result_card — Google-style search result
// ─────────────────────────────────────────────────────────
_RENDERERS['search_result_card'] = function(b) {
  var title      = b.title || '';
  var url        = b.url   || '#';
  var description= b.description || '';
  var breadcrumb = b.breadcrumb || [];
  var date       = b.date || '';
  var faviconUrl = b.favicon_url || '';

  var html = '<div class="a2ui-search-result">';

  // URL / breadcrumb row
  html += '<div class="a2ui-sr-url-row">';
  if (faviconUrl) {
    html += '<img src="' + _esc(faviconUrl) + '" class="a2ui-sr-favicon" width="16" height="16" onerror="this.style.display=\'none\'"/>';
  }
  if (breadcrumb.length) {
    html += '<span class="a2ui-sr-breadcrumb">' + breadcrumb.map(function(p){ return _esc(p); }).join(' › ') + '</span>';
  } else {
    html += '<span class="a2ui-sr-breadcrumb">' + _esc(url) + '</span>';
  }
  html += '</div>';

  // Title
  html += '<a class="a2ui-sr-title" href="' + _esc(url) + '" target="_blank" rel="noopener">' + _esc(title) + '</a>';

  // Meta (date)
  if (date) html += '<span class="a2ui-sr-date">' + _esc(date) + ' — </span>';

  // Description
  if (description) html += '<p class="a2ui-sr-desc">' + _esc(description) + '</p>';

  html += '</div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 13. punch_card — day-of-week × hour heatmap
// ─────────────────────────────────────────────────────────
_RENDERERS['punch_card'] = function(b) {
  var data  = b.data  || [];
  var title = b.title || '';

  var dayLabels  = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  var hourLabels = ['0','','','','','','6','','','','','','12','','','','','','18','','','','','23'];

  // Build lookup
  var counts = {};
  var maxCount = 0;
  data.forEach(function(d) {
    var key = d.day + '-' + d.hour;
    counts[key] = (d.count || 0);
    if (d.count > maxCount) maxCount = d.count;
  });
  if (!maxCount) maxCount = 1;

  var cellW  = 18, cellH = 18, cellG = 3;
  var padL   = 36, padT = 30, padR = 10, padB = 10;
  var svgW   = padL + 24 * (cellW + cellG) + padR;
  var svgH   = padT + 7  * (cellH + cellG) + padB;

  var svg = '<svg viewBox="0 0 ' + svgW + ' ' + svgH + '" width="100%" preserveAspectRatio="xMidYMid meet">';
  if (title) svg += '<text x="' + (svgW/2) + '" y="14" text-anchor="middle" font-size="12" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

  // Hour labels
  for (var h = 0; h < 24; h++) {
    if (hourLabels[h]) {
      svg += '<text x="' + (padL + h*(cellW+cellG) + cellW/2) + '" y="' + (padT-4) + '" text-anchor="middle" font-size="8" fill="#94a3b8">' + hourLabels[h] + '</text>';
    }
  }
  // Day labels
  for (var d = 0; d < 7; d++) {
    svg += '<text x="' + (padL-4) + '" y="' + (padT + d*(cellH+cellG) + cellH/2 + 3) + '" text-anchor="end" font-size="9" fill="#64748b">' + dayLabels[d] + '</text>';
  }

  for (var day = 0; day < 7; day++) {
    for (var hour = 0; hour < 24; hour++) {
      var cnt = counts[day+'-'+hour] || 0;
      var opacity = cnt / maxCount;
      var r = 70 + Math.round(opacity * 115);
      var g = 50 + Math.round(opacity * 10);
      var bv = 200 + Math.round(opacity * 51);
      // Purple scale: light (#e9d5ff) to dark (#581c87)
      var fill = cnt === 0 ? '#f1f5f9' : 'rgb(' + Math.round(233 - opacity*152) + ',' + Math.round(213 - opacity*157) + ',' + Math.round(255 - opacity*130) + ')';
      var cx = padL + hour*(cellW+cellG);
      var cy = padT + day*(cellH+cellG);
      svg += '<rect x="' + cx + '" y="' + cy + '" width="' + cellW + '" height="' + cellH + '" rx="2" fill="' + fill + '"><title>' + dayLabels[day] + ' ' + hour + ':00 — ' + cnt + '</title></rect>';
    }
  }

  svg += '</svg>';
  return '<div class="a2ui-punch-card">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 14. sankey_flow — simple flow diagram (HTML table style)
// ─────────────────────────────────────────────────────────
_RENDERERS['sankey_flow'] = function(b) {
  var nodes = b.nodes || [];
  var links = b.links || [];
  var title = b.title || '';

  // Build node label lookup
  var nodeMap = {};
  nodes.forEach(function(n){ nodeMap[n.id] = n.label || n.id; });

  // Group links by source
  var groups = {};
  var srcOrder = [];
  links.forEach(function(lk) {
    var src = lk.source;
    if (!groups[src]) { groups[src] = []; srcOrder.push(src); }
    groups[src].push(lk);
  });

  var html = '<div class="a2ui-sankey">';
  if (title) html += '<div class="a2ui-sankey-title">' + _esc(title) + '</div>';
  html += '<div class="a2ui-sankey-rows">';

  srcOrder.forEach(function(src) {
    var lks  = groups[src];
    var total = lks.reduce(function(s, l){ return s + (parseFloat(l.value)||0); }, 0);
    html += '<div class="a2ui-sankey-group">';
    html += '<div class="a2ui-sankey-src-hdr">' + _esc(nodeMap[src] || src) + ' <span class="a2ui-sankey-total">Total: ' + total.toLocaleString() + '</span></div>';
    lks.forEach(function(lk) {
      var pct = total > 0 ? ((lk.value / total) * 100).toFixed(1) : '0';
      html += '<div class="a2ui-sankey-link">';
      html += '<span class="a2ui-sankey-from">' + _esc(nodeMap[src] || src) + '</span>';
      html += '<span class="a2ui-sankey-arrow">→</span>';
      html += '<div class="a2ui-sankey-bar-wrap"><div class="a2ui-sankey-bar" style="width:' + pct + '%;"></div></div>';
      html += '<span class="a2ui-sankey-val">' + Number(lk.value).toLocaleString() + '</span>';
      html += '<span class="a2ui-sankey-arrow">→</span>';
      html += '<span class="a2ui-sankey-to">' + _esc(nodeMap[lk.target] || lk.target) + '</span>';
      html += '</div>';
    });
    html += '</div>';
  });

  html += '</div></div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 15. cohort_retention — retention grid
// ─────────────────────────────────────────────────────────
_RENDERERS['cohort_retention'] = function(b) {
  var cohorts = b.cohorts || [];
  var title   = b.title   || '';

  if (!cohorts.length) return '<div class="a2ui-chart-empty">No cohort data</div>';

  var maxCols = 0;
  cohorts.forEach(function(c){ if ((c.data||[]).length > maxCols) maxCols = c.data.length; });

  var html = '<div class="a2ui-cohort-retention">';
  if (title) html += '<div class="a2ui-cohort-title">' + _esc(title) + '</div>';
  html += '<div style="overflow-x:auto;"><table class="a2ui-cohort-table" style="border-collapse:collapse;font-size:12px;width:100%;">';

  // Header
  html += '<thead><tr><th class="a2ui-cohort-th">Cohort</th>';
  for (var w = 0; w < maxCols; w++) {
    html += '<th class="a2ui-cohort-th">Week ' + w + '</th>';
  }
  html += '</tr></thead><tbody>';

  cohorts.forEach(function(cohort) {
    html += '<tr>';
    html += '<td class="a2ui-cohort-label">' + _esc(cohort.label || '') + '</td>';
    var data = cohort.data || [];
    for (var w = 0; w < maxCols; w++) {
      var val = data[w] !== undefined ? parseFloat(data[w]) : null;
      if (val === null) {
        html += '<td class="a2ui-cohort-cell" style="background:#f8fafc;"></td>';
      } else {
        var pct = Math.min(100, Math.max(0, val));
        var alpha = pct / 100;
        // purple: rgb(99,102,241) deep to light
        var r = Math.round(237 - alpha * 138);
        var g = Math.round(233 - alpha * 131);
        var bv = Math.round(254 - alpha * 13);
        var bg = 'rgb(' + r + ',' + g + ',' + bv + ')';
        var fg = pct > 60 ? '#fff' : '#334155';
        html += '<td class="a2ui-cohort-cell" style="background:' + bg + ';color:' + fg + ';">' + pct.toFixed(0) + '%</td>';
      }
    }
    html += '</tr>';
  });

  html += '</tbody></table></div></div>';
  return html;
};

// ─────────────────────────────────────────────────────────
// 16. heatmap — generic 2D heatmap
// ─────────────────────────────────────────────────────────
_RENDERERS['heatmap'] = function(b) {
  var rowLabels   = b.rows  || [];
  var colLabels   = b.cols  || [];
  var data        = b.data  || [];
  var title       = b.title || '';
  var colorScheme = b.color_scheme || 'purple';

  if (!rowLabels.length || !colLabels.length) return '<div class="a2ui-chart-empty">No heatmap data</div>';

  // Color schemes: [lightR,lightG,lightB, darkR,darkG,darkB]
  var schemes = {
    purple: [237,233,254, 88,28,135],
    blue:   [219,234,254, 30,58,138],
    green:  [220,252,231, 22,101,52],
    red:    [254,226,226, 127,29,29]
  };
  var cs = schemes[colorScheme] || schemes.purple;

  // Flatten to find min/max
  var allVals = [];
  data.forEach(function(row){ row.forEach(function(v){ allVals.push(parseFloat(v)||0); }); });
  var minV = Math.min.apply(null, allVals);
  var maxV = Math.max.apply(null, allVals);
  if (maxV === minV) maxV += 1;

  var padL = 80, padT = 30, cellW = Math.min(60, Math.max(28, Math.floor(480/colLabels.length))), cellH = 28;
  var svgW = padL + colLabels.length * cellW + 10;
  var svgH = padT + rowLabels.length * cellH + 16;

  var svg = '<svg viewBox="0 0 ' + svgW + ' ' + svgH + '" width="100%" preserveAspectRatio="xMidYMid meet">';
  if (title) svg += '<text x="' + (svgW/2) + '" y="16" text-anchor="middle" font-size="12" font-weight="bold" fill="#1e293b">' + _esc(title) + '</text>';

  // Column labels
  colLabels.forEach(function(cl, ci) {
    svg += '<text x="' + (padL + ci*cellW + cellW/2) + '" y="' + (padT - 4) + '" text-anchor="middle" font-size="9" fill="#64748b">' + _esc(String(cl).substr(0,8)) + '</text>';
  });

  // Rows
  rowLabels.forEach(function(rl, ri) {
    svg += '<text x="' + (padL - 4) + '" y="' + (padT + ri*cellH + cellH/2 + 4) + '" text-anchor="end" font-size="9" fill="#64748b">' + _esc(String(rl).substr(0,12)) + '</text>';
    var rowData = data[ri] || [];
    colLabels.forEach(function(cl, ci) {
      var val   = parseFloat(rowData[ci]) || 0;
      var alpha = (val - minV) / (maxV - minV);
      var r = Math.round(cs[0] + alpha * (cs[3] - cs[0]));
      var g = Math.round(cs[1] + alpha * (cs[4] - cs[1]));
      var bv= Math.round(cs[2] + alpha * (cs[5] - cs[2]));
      var bg = 'rgb(' + r + ',' + g + ',' + bv + ')';
      var fg = alpha > 0.55 ? '#fff' : '#334155';
      var cx = padL + ci * cellW;
      var cy = padT + ri * cellH;
      svg += '<rect x="' + cx + '" y="' + cy + '" width="' + (cellW-1) + '" height="' + (cellH-1) + '" fill="' + bg + '"><title>' + _esc(String(rl)) + ' / ' + _esc(String(cl)) + ': ' + val + '</title></rect>';
      if (cellW > 30) {
        svg += '<text x="' + (cx+cellW/2) + '" y="' + (cy+cellH/2+4) + '" text-anchor="middle" font-size="9" fill="' + fg + '">' + val + '</text>';
      }
    });
  });

  svg += '</svg>';
  return '<div class="a2ui-heatmap">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 17. github_activity_grid — contribution graph
// ─────────────────────────────────────────────────────────
_RENDERERS['github_activity_grid'] = function(b) {
  var weeks = b.weeks || [];
  var title = b.title || '';
  var year  = b.year  || '';

  var cellS = 11, cellG = 2;
  var padL  = 24, padT = 24, padR = 6, padB = 6;
  var colors = ['#161b22','#0e4429','#006d32','#26a641','#39d353'];
  // 0 commits = light grey in our light-mode rendering
  var emptyColor = '#ebedf0';

  var dayLabels = {1:'Mon', 3:'Wed', 5:'Fri'};
  var svgW = padL + (weeks.length || 53) * (cellS + cellG) + padR;
  var svgH = padT + 7 * (cellS + cellG) + padB;

  var svg = '<svg viewBox="0 0 ' + svgW + ' ' + svgH + '" width="100%" preserveAspectRatio="xMidYMid meet" style="background:#fff;">';
  if (title || year) svg += '<text x="' + padL + '" y="14" font-size="11" font-weight="600" fill="#24292e">' + _esc(title + (year ? ' '+year : '')) + '</text>';

  // Day labels (left)
  [1,3,5].forEach(function(d) {
    svg += '<text x="' + (padL-2) + '" y="' + (padT + d*(cellS+cellG) + cellS/2 + 3) + '" text-anchor="end" font-size="8" fill="#57606a">' + dayLabels[d] + '</text>';
  });

  // Month labels (top) — detect first day of each month from data
  var lastMonth = '';
  weeks.forEach(function(week, wi) {
    if (week && week[0] && week[0].date) {
      var mo = week[0].date.substr(0,7); // YYYY-MM
      if (mo !== lastMonth) {
        var monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
        var mIdx = parseInt(mo.substr(5,2)) - 1;
        svg += '<text x="' + (padL + wi*(cellS+cellG)) + '" y="' + (padT-4) + '" font-size="8" fill="#57606a">' + (monthNames[mIdx]||'') + '</text>';
        lastMonth = mo;
      }
    }
  });

  // All data — find max count for quartile
  var allCounts = [];
  weeks.forEach(function(week){ (week||[]).forEach(function(d){ if(d) allCounts.push(d.count||0); }); });
  allCounts.sort(function(a,b){return a-b;});
  var q = allCounts.length;
  function getLevel(count) {
    if (!count) return 0;
    var rank = allCounts.indexOf(count);
    if (rank < 0) rank = allCounts.filter(function(c){return c<=count;}).length - 1;
    var pct = rank / (q-1||1);
    return pct < 0.25 ? 1 : pct < 0.5 ? 2 : pct < 0.75 ? 3 : 4;
  }

  weeks.forEach(function(week, wi) {
    (week||[]).forEach(function(day, di) {
      if (!day) return;
      var cnt   = day.count || 0;
      var lvl   = getLevel(cnt);
      var color = cnt === 0 ? emptyColor : colors[lvl];
      var cx    = padL + wi*(cellS+cellG);
      var cy    = padT + di*(cellS+cellG);
      var ttl   = (day.date || ('Week '+(wi+1)+' Day '+(di+1))) + ': ' + cnt + ' contribution' + (cnt!==1?'s':'');
      svg += '<rect x="' + cx + '" y="' + cy + '" width="' + cellS + '" height="' + cellS + '" rx="2" fill="' + color + '"><title>' + _esc(ttl) + '</title></rect>';
    });
  });

  svg += '</svg>';
  return '<div class="a2ui-github-grid">' + svg + '</div>';
};

// ─────────────────────────────────────────────────────────
// 18. entity_list — structured entity/person list
// ─────────────────────────────────────────────────────────
_RENDERERS['entity_list'] = function(b) {
  var entities = b.entities || [];
  var title    = b.title    || '';

  var typeColors = {
    person:       '#6366f1',
    organization: '#22d3ee',
    location:     '#34d399',
    product:      '#fb923c',
    event:        '#f472b6'
  };

  var html = '<div class="a2ui-entity-list">';
  if (title) html += '<div class="a2ui-entity-list-title">' + _esc(title) + '</div>';
  html += '<div class="a2ui-entity-grid">';

  entities.forEach(function(entity) {
    var typeColor = typeColors[(entity.type||'').toLowerCase()] || '#94a3b8';
    var item = '';

    if (entity.link) {
      item += '<a class="a2ui-entity-card" href="' + _esc(entity.link) + '" target="_blank" rel="noopener" style="text-decoration:none;">';
    } else {
      item += '<div class="a2ui-entity-card">';
    }

    // Avatar
    item += '<div class="a2ui-entity-avatar">';
    if (entity.avatar_url) {
      item += '<img src="' + _esc(entity.avatar_url) + '" width="40" height="40" style="border-radius:50%;object-fit:cover;" onerror="this.style.display=\'none\';this.nextSibling.style.display=\'flex\'"/>';
      item += '<div class="a2ui-entity-initials" style="display:none;background:' + typeColor + ';">' + _esc((entity.name||'?').charAt(0).toUpperCase()) + '</div>';
    } else {
      item += '<div class="a2ui-entity-initials" style="background:' + typeColor + ';">' + _esc((entity.name||'?').charAt(0).toUpperCase()) + '</div>';
    }
    item += '</div>';

    // Info
    item += '<div class="a2ui-entity-info">';
    item += '<div class="a2ui-entity-name">' + _esc(entity.name || '') + '</div>';
    if (entity.type) item += '<span class="a2ui-entity-type" style="background:' + typeColor + '20;color:' + typeColor + ';border:1px solid ' + typeColor + '40;">' + _esc(entity.type) + '</span>';
    if (entity.description) item += '<div class="a2ui-entity-desc">' + _esc(entity.description) + '</div>';
    if (entity.meta) item += '<div class="a2ui-entity-meta">' + _esc(entity.meta) + '</div>';
    item += '</div>';

    item += entity.link ? '</a>' : '</div>';
    html += item;
  });

  html += '</div></div>';
  return html;
};



// === Batch 6: Misc Atoms + Animation Degraded Fallbacks ===

_RENDERERS['markdown_block'] = function(b) {
  var content = b.content || '';
  var html = _markdownToHtml(content);
  return '<div class="asw-markdown-block">' + html + '</div>';
};

_RENDERERS['bento_grid'] = function(b) {
  var items = b.items || [];
  var cols = b.cols || 3;
  var uid = Math.random().toString(36).substr(2, 6);
  var id = 'bento-' + uid;
  var colorSchemes = [
    {bg:'#f3f0ff',border:'#ede9fe'},
    {bg:'#fdf4ff',border:'#fae8ff'},
    {bg:'#f0fdf4',border:'#dcfce7'},
    {bg:'#eff6ff',border:'#dbeafe'},
    {bg:'#fff7ed',border:'#fed7aa'},
    {bg:'#fafafa',border:'#e5e7eb'}
  ];
  var itemsHtml = '';
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    var span = Math.min(Math.max(parseInt(item.span) || 1, 1), cols);
    var scheme = colorSchemes[i % colorSchemes.length];
    if (item.color_scheme === 'purple') { scheme = {bg:'#f3f0ff',border:'#ede9fe'}; }
    else if (item.color_scheme === 'green') { scheme = {bg:'#f0fdf4',border:'#dcfce7'}; }
    else if (item.color_scheme === 'blue') { scheme = {bg:'#eff6ff',border:'#dbeafe'}; }
    else if (item.color_scheme === 'orange') { scheme = {bg:'#fff7ed',border:'#fed7aa'}; }
    var iconHtml = item.icon ? '<div style="font-size:1.8rem;margin-bottom:8px;">' + _esc(item.icon) + '</div>' : '';
    var titleHtml = item.title ? '<div style="font-weight:700;font-size:1rem;color:#111827;margin-bottom:6px;">' + _esc(item.title) + '</div>' : '';
    var bodyHtml = item.body ? '<div style="font-size:0.875rem;color:#4b5563;line-height:1.5;">' + _esc(item.body) + '</div>' : '';
    itemsHtml += '<div style="grid-column:span ' + span + ';background:' + scheme.bg + ';border:1px solid ' + scheme.border + ';border-radius:14px;padding:20px;box-sizing:border-box;">' + iconHtml + titleHtml + bodyHtml + '</div>';
  }
  return '<div id="' + id + '" style="display:grid;grid-template-columns:repeat(' + cols + ',1fr);gap:14px;margin:1rem 0;">' + itemsHtml + '</div>';
};

_RENDERERS['cta_section'] = function(b) {
  var headline = b.headline || '';
  var subheadline = b.subheadline || '';
  var primaryLabel = b.primary_label || '';
  var primaryUrl = b.primary_url || '#';
  var secondaryLabel = b.secondary_label || '';
  var secondaryUrl = b.secondary_url || '#';
  var alignment = b.alignment === 'left' ? 'left' : 'center';
  var btnPrimary = primaryLabel ? '<a href="' + _esc(primaryUrl) + '" style="display:inline-block;background:#7c3aed;color:#fff;font-weight:600;padding:12px 28px;border-radius:8px;text-decoration:none;font-size:0.95rem;margin:6px;">' + _esc(primaryLabel) + '</a>' : '';
  var btnSecondary = secondaryLabel ? '<a href="' + _esc(secondaryUrl) + '" style="display:inline-block;background:transparent;color:#7c3aed;font-weight:600;padding:11px 27px;border-radius:8px;text-decoration:none;font-size:0.95rem;border:1.5px solid #7c3aed;margin:6px;">' + _esc(secondaryLabel) + '</a>' : '';
  return '<div style="background:linear-gradient(135deg,#f5f3ff,#faf5ff);border:1px solid #ede9fe;border-radius:16px;padding:40px 32px;margin:1rem 0;text-align:' + alignment + ';">'
    + (headline ? '<h2 style="margin:0 0 12px;font-size:1.75rem;font-weight:800;color:#111827;">' + _esc(headline) + '</h2>' : '')
    + (subheadline ? '<p style="margin:0 0 24px;font-size:1.05rem;color:#4b5563;">' + _esc(subheadline) + '</p>' : '')
    + '<div>' + btnPrimary + btnSecondary + '</div>'
    + '</div>';
};

_RENDERERS['lozenge'] = function(b) {
  var text = b.text || '';
  var color = b.color || 'default';
  var colorMap = {
    'default': {bg:'#f3f4f6',fg:'#374151'},
    'success':  {bg:'#dcfce7',fg:'#166534'},
    'warning':  {bg:'#fef3c7',fg:'#92400e'},
    'danger':   {bg:'#fee2e2',fg:'#991b1b'},
    'info':     {bg:'#dbeafe',fg:'#1d4ed8'}
  };
  var c = colorMap[color] || colorMap['default'];
  return '<span style="display:inline-block;background:' + c.bg + ';color:' + c.fg + ';font-size:0.78rem;font-weight:600;padding:3px 10px;border-radius:999px;letter-spacing:0.02em;">' + _esc(text) + '</span>';
};

_RENDERERS['task_list'] = function(b) {
  var items = b.items || [];
  var priorityColors = {high:'#ef4444', medium:'#f59e0b', low:'#9ca3af'};
  var rows = '';
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    var dot = item.priority ? '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:' + (priorityColors[item.priority] || '#9ca3af') + ';margin-right:8px;flex-shrink:0;"></span>' : '';
    var textStyle = item.done ? 'text-decoration:line-through;color:#9ca3af;' : 'color:#111827;';
    var checkIcon = item.done
      ? '<svg width="16" height="16" viewBox="0 0 16 16" style="flex-shrink:0;"><circle cx="8" cy="8" r="7" fill="#7c3aed"/><polyline points="4,8 7,11 12,5" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
      : '<svg width="16" height="16" viewBox="0 0 16 16" style="flex-shrink:0;"><circle cx="8" cy="8" r="7" fill="none" stroke="#d1d5db" stroke-width="1.5"/></svg>';
    rows += '<li style="display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid #f3f4f6;">'
      + checkIcon
      + '<span style="' + textStyle + 'flex:1;font-size:0.9rem;">' + _esc(item.text || '') + '</span>'
      + dot
      + '</li>';
  }
  return '<ul style="list-style:none;margin:0.5rem 0;padding:0;">' + rows + '</ul>';
};

_RENDERERS['vote_button_group'] = function(b) {
  var options = b.options || [];
  var question = b.question || '';
  var uid = Math.random().toString(36).substr(2, 6);
  var rows = '';
  for (var i = 0; i < options.length; i++) {
    var opt = options[i];
    var id = 'vote-' + uid + '-' + i;
    rows += '<label for="' + id + '" style="display:flex;align-items:center;gap:12px;padding:12px 16px;border:1.5px solid #e5e7eb;border-radius:10px;cursor:pointer;background:#fff;transition:border-color 0.15s;">'
      + '<input type="radio" name="vote-' + uid + '" id="' + id + '" value="' + i + '" style="accent-color:#7c3aed;">'
      + '<span style="flex:1;font-size:0.9rem;color:#111827;font-weight:500;">' + _esc(opt.label || '') + '</span>'
      + '<span style="font-size:0.82rem;color:#6b7280;background:#f3f4f6;padding:2px 8px;border-radius:999px;">' + (opt.votes || 0) + ' votes</span>'
      + '</label>';
  }
  return '<div style="margin:1rem 0;">'
    + (question ? '<p style="margin:0 0 12px;font-weight:700;color:#111827;font-size:1rem;">' + _esc(question) + '</p>' : '')
    + '<div style="display:flex;flex-direction:column;gap:8px;">' + rows + '</div>'
    + '</div>';
};

_RENDERERS['sprint_board'] = function(b) {
  var columns = b.columns || [];
  var colsHtml = '';
  var priorityColors = {high:'#ef4444', medium:'#f59e0b', low:'#10b981', null:'#d1d5db'};
  for (var c = 0; c < columns.length; c++) {
    var col = columns[c];
    var items = col.items || [];
    var cardsHtml = '';
    for (var i = 0; i < items.length; i++) {
      var item = items[i];
      var pcolor = priorityColors[item.priority] || '#d1d5db';
      var assigneeHtml = item.assignee ? '<div style="width:24px;height:24px;border-radius:50%;background:#7c3aed;color:#fff;font-size:0.7rem;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;">' + _esc(item.assignee.charAt(0).toUpperCase()) + '</div>' : '';
      var labelsHtml = '';
      if (item.labels && item.labels.length) {
        for (var l = 0; l < item.labels.length; l++) {
          labelsHtml += '<span style="background:#ede9fe;color:#5b21b6;font-size:0.7rem;padding:1px 6px;border-radius:999px;">' + _esc(item.labels[l]) + '</span>';
        }
      }
      cardsHtml += '<div style="background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:12px;margin-bottom:8px;">'
        + '<div style="display:flex;align-items:flex-start;gap:8px;">'
        + '<div style="width:8px;height:8px;border-radius:50%;background:' + pcolor + ';flex-shrink:0;margin-top:5px;"></div>'
        + '<div style="flex:1;">'
        + (item.id ? '<div style="font-size:0.72rem;color:#9ca3af;margin-bottom:3px;">' + _esc(item.id) + '</div>' : '')
        + '<div style="font-size:0.87rem;font-weight:600;color:#111827;">' + _esc(item.title || '') + '</div>'
        + (labelsHtml ? '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:6px;">' + labelsHtml + '</div>' : '')
        + '</div>'
        + assigneeHtml
        + '</div>'
        + '</div>';
    }
    colsHtml += '<div style="flex:1;min-width:200px;background:#f9fafb;border-radius:12px;padding:14px;">'
      + '<div style="font-weight:700;font-size:0.85rem;color:#374151;margin-bottom:12px;text-transform:uppercase;letter-spacing:0.05em;">' + _esc(col.title || '') + ' <span style="background:#e5e7eb;color:#6b7280;border-radius:999px;padding:1px 7px;font-size:0.75rem;">' + items.length + '</span></div>'
      + cardsHtml
      + '</div>';
  }
  return '<div style="display:flex;gap:12px;overflow-x:auto;margin:1rem 0;padding-bottom:4px;">' + colsHtml + '</div>';
};

_RENDERERS['jira_ticket'] = function(b) {
  var typeIcons = {bug:'🐛', story:'📖', task:'✅', epic:'⚡'};
  var typeColors = {bug:'#fee2e2', story:'#dbeafe', task:'#f0fdf4', epic:'#faf5ff'};
  var statusColors = {
    'To Do':'#f3f4f6','In Progress':'#dbeafe','Done':'#dcfce7',
    'Blocked':'#fee2e2','Review':'#fef3c7'
  };
  var type = b.type || 'task';
  var status = b.status || 'To Do';
  var icon = typeIcons[type] || '📋';
  var bgColor = typeColors[type] || '#f9fafb';
  var statusBg = statusColors[status] || '#f3f4f6';
  var labelsHtml = '';
  if (b.labels && b.labels.length) {
    for (var l = 0; l < b.labels.length; l++) {
      labelsHtml += '<span style="background:#ede9fe;color:#5b21b6;font-size:0.72rem;padding:2px 8px;border-radius:999px;">' + _esc(b.labels[l]) + '</span>';
    }
  }
  var assigneeHtml = b.assignee ? '<div style="display:flex;align-items:center;gap:6px;font-size:0.82rem;color:#6b7280;"><div style="width:22px;height:22px;border-radius:50%;background:#7c3aed;color:#fff;font-size:0.7rem;font-weight:700;display:flex;align-items:center;justify-content:center;">' + _esc(b.assignee.charAt(0).toUpperCase()) + '</div>' + _esc(b.assignee) + '</div>' : '';
  return '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:18px;margin:0.75rem 0;background:#fff;box-shadow:0 1px 4px rgba(0,0,0,0.06);">'
    + '<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">'
    + '<span style="font-size:1.2rem;background:' + bgColor + ';padding:6px;border-radius:8px;">' + icon + '</span>'
    + '<span style="font-size:0.82rem;font-weight:700;color:#6b7280;font-family:monospace;">' + _esc(b.key || '') + '</span>'
    + '<span style="margin-left:auto;background:' + statusBg + ';font-size:0.78rem;font-weight:600;padding:3px 10px;border-radius:999px;color:#374151;">' + _esc(status) + '</span>'
    + '</div>'
    + '<div style="font-size:1rem;font-weight:600;color:#111827;margin-bottom:10px;">' + _esc(b.summary || '') + '</div>'
    + (labelsHtml ? '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-bottom:10px;">' + labelsHtml + '</div>' : '')
    + (assigneeHtml ? '<div style="margin-top:8px;">' + assigneeHtml + '</div>' : '')
    + '</div>';
};

_RENDERERS['feature_grid'] = function(b) {
  var features = b.features || [];
  var cols = b.cols || 3;
  var cardsHtml = '';
  for (var i = 0; i < features.length; i++) {
    var f = features[i];
    cardsHtml += '<div style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:20px;">'
      + (f.icon ? '<div style="font-size:2rem;margin-bottom:12px;">' + _esc(f.icon) + '</div>' : '')
      + (f.title ? '<div style="font-weight:700;font-size:1rem;color:#111827;margin-bottom:8px;">' + _esc(f.title) + '</div>' : '')
      + (f.description ? '<div style="font-size:0.875rem;color:#4b5563;line-height:1.6;">' + _esc(f.description) + '</div>' : '')
      + '</div>';
  }
  return '<div style="display:grid;grid-template-columns:repeat(' + cols + ',1fr);gap:14px;margin:1rem 0;">' + cardsHtml + '</div>';
};

_RENDERERS['navigation_menu'] = function(b) {
  var items = b.items || [];
  var itemsHtml = '';
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    var iconHtml = item.icon ? '<span style="margin-right:6px;">' + _esc(item.icon) + '</span>' : '';
    if (item.children && item.children.length) {
      var subItems = '';
      for (var j = 0; j < item.children.length; j++) {
        var child = item.children[j];
        subItems += '<li><a href="' + _esc(child.url || '#') + '" style="display:block;padding:8px 16px;font-size:0.875rem;color:#374151;text-decoration:none;white-space:nowrap;">' + _esc(child.label || '') + '</a></li>';
      }
      itemsHtml += '<li style="position:relative;">'
        + '<details style="display:inline;">'
        + '<summary style="display:flex;align-items:center;gap:4px;padding:8px 12px;font-size:0.9rem;font-weight:500;color:#111827;cursor:pointer;list-style:none;border-radius:6px;">' + iconHtml + _esc(item.label || '') + ' <span style="font-size:0.7rem;">▾</span></summary>'
        + '<ul style="position:absolute;top:100%;left:0;background:#fff;border:1px solid #e5e7eb;border-radius:10px;box-shadow:0 4px 16px rgba(0,0,0,0.1);list-style:none;margin:4px 0 0;padding:6px 0;min-width:180px;z-index:10;">' + subItems + '</ul>'
        + '</details>'
        + '</li>';
    } else {
      itemsHtml += '<li><a href="' + _esc(item.url || '#') + '" style="display:flex;align-items:center;padding:8px 12px;font-size:0.9rem;font-weight:500;color:#111827;text-decoration:none;border-radius:6px;">' + iconHtml + _esc(item.label || '') + '</a></li>';
    }
  }
  return '<nav style="margin:0.75rem 0;"><ul style="display:flex;list-style:none;margin:0;padding:8px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:12px;gap:4px;flex-wrap:wrap;">' + itemsHtml + '</ul></nav>';
};

_RENDERERS['order_status_card'] = function(b) {
  var steps = ['Placed', 'Processing', 'Shipped', 'Delivered'];
  var statusIndex = {placed:0, processing:1, shipped:2, delivered:3, cancelled:-1};
  var currentStep = statusIndex[b.status] !== undefined ? statusIndex[b.status] : 0;
  var cancelled = b.status === 'cancelled';
  var stepperHtml = '<div style="display:flex;align-items:center;margin:16px 0 24px;">';
  for (var s = 0; s < steps.length; s++) {
    var done = !cancelled && s <= currentStep;
    var active = !cancelled && s === currentStep;
    var dotBg = cancelled ? '#fee2e2' : (done ? '#7c3aed' : '#e5e7eb');
    var dotColor = cancelled ? '#991b1b' : (done ? '#fff' : '#9ca3af');
    stepperHtml += '<div style="display:flex;flex-direction:column;align-items:center;flex:1;">'
      + '<div style="width:28px;height:28px;border-radius:50%;background:' + dotBg + ';color:' + dotColor + ';font-size:0.75rem;font-weight:700;display:flex;align-items:center;justify-content:center;">' + (done && !active ? '✓' : (s + 1)) + '</div>'
      + '<div style="font-size:0.72rem;margin-top:4px;color:' + (active ? '#7c3aed' : '#6b7280') + ';font-weight:' + (active ? '700' : '400') + ';text-align:center;">' + steps[s] + '</div>'
      + '</div>';
    if (s < steps.length - 1) {
      stepperHtml += '<div style="flex:1;height:2px;background:' + (!cancelled && s < currentStep ? '#7c3aed' : '#e5e7eb') + ';margin-bottom:16px;"></div>';
    }
  }
  stepperHtml += '</div>';
  var itemsHtml = '';
  var items = b.items || [];
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    itemsHtml += '<tr><td style="padding:8px 4px;font-size:0.875rem;color:#111827;">' + _esc(item.name || '') + '</td><td style="padding:8px 4px;font-size:0.875rem;color:#6b7280;text-align:center;">×' + (item.qty || 1) + '</td><td style="padding:8px 4px;font-size:0.875rem;color:#111827;text-align:right;">' + _esc(item.price || '') + '</td></tr>';
  }
  return '<div style="border:1px solid #e5e7eb;border-radius:14px;padding:20px;margin:1rem 0;background:#fff;">'
    + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
    + '<span style="font-weight:700;color:#111827;font-size:1rem;">Order ' + _esc(b.order_id || '') + '</span>'
    + (cancelled ? '<span style="background:#fee2e2;color:#991b1b;font-size:0.78rem;font-weight:600;padding:3px 10px;border-radius:999px;">Cancelled</span>' : '')
    + '</div>'
    + stepperHtml
    + '<table style="width:100%;border-collapse:collapse;border-top:1px solid #f3f4f6;">' + itemsHtml + '</table>'
    + '<div style="display:flex;justify-content:space-between;padding-top:10px;border-top:1px solid #e5e7eb;margin-top:8px;font-weight:700;color:#111827;">'
    + '<span>Total</span><span>' + _esc(b.total || '') + '</span>'
    + '</div>'
    + (b.estimated_delivery ? '<div style="margin-top:10px;font-size:0.82rem;color:#6b7280;">Estimated delivery: <strong style="color:#111827;">' + _esc(b.estimated_delivery) + '</strong></div>' : '')
    + '</div>';
};

_RENDERERS['roadmap_card'] = function(b) {
  var statusColors = {
    'planned':     {bg:'#f3f4f6',fg:'#374151'},
    'in-progress': {bg:'#dbeafe',fg:'#1d4ed8'},
    'done':        {bg:'#dcfce7',fg:'#166534'},
    'deferred':    {bg:'#fef3c7',fg:'#92400e'}
  };
  var sc = statusColors[b.status] || statusColors['planned'];
  var itemsHtml = '';
  if (b.items && b.items.length) {
    for (var i = 0; i < b.items.length; i++) {
      itemsHtml += '<li style="font-size:0.875rem;color:#374151;padding:3px 0;">• ' + _esc(b.items[i]) + '</li>';
    }
  }
  return '<div style="border:1px solid #e5e7eb;border-radius:14px;padding:20px;margin:0.75rem 0;background:#fff;">'
    + '<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">'
    + (b.quarter ? '<span style="font-size:0.82rem;font-weight:700;color:#7c3aed;background:#f3f0ff;padding:3px 10px;border-radius:999px;">' + _esc(b.quarter) + '</span>' : '')
    + '<span style="background:' + sc.bg + ';color:' + sc.fg + ';font-size:0.78rem;font-weight:600;padding:3px 10px;border-radius:999px;">' + _esc(b.status || '') + '</span>'
    + '</div>'
    + (b.title ? '<div style="font-weight:700;font-size:1.05rem;color:#111827;margin-bottom:8px;">' + _esc(b.title) + '</div>' : '')
    + (b.description ? '<p style="font-size:0.875rem;color:#4b5563;margin:0 0 12px;line-height:1.5;">' + _esc(b.description) + '</p>' : '')
    + (itemsHtml ? '<ul style="list-style:none;margin:0;padding:0;">' + itemsHtml + '</ul>' : '')
    + '</div>';
};

_RENDERERS['notification_stack'] = function(b) {
  var notifications = b.notifications || [];
  var typeConfig = {
    info:    {bg:'#eff6ff',border:'#93c5fd',icon:'ℹ️',color:'#1d4ed8'},
    success: {bg:'#f0fdf4',border:'#86efac',icon:'✅',color:'#166534'},
    warning: {bg:'#fffbeb',border:'#fcd34d',icon:'⚠️',color:'#92400e'},
    error:   {bg:'#fef2f2',border:'#fca5a5',icon:'❌',color:'#991b1b'}
  };
  var html = '<div style="display:flex;flex-direction:column;gap:8px;margin:1rem 0;">';
  for (var i = 0; i < notifications.length; i++) {
    var n = notifications[i];
    var tc = typeConfig[n.type] || typeConfig['info'];
    html += '<div style="background:' + tc.bg + ';border:1px solid ' + tc.border + ';border-radius:10px;padding:14px 16px;display:flex;gap:12px;align-items:flex-start;">'
      + '<span style="font-size:1rem;flex-shrink:0;">' + tc.icon + '</span>'
      + '<div style="flex:1;">'
      + (n.title ? '<div style="font-weight:700;font-size:0.875rem;color:#111827;">' + _esc(n.title) + '</div>' : '')
      + (n.body ? '<div style="font-size:0.82rem;color:#374151;margin-top:2px;">' + _esc(n.body) + '</div>' : '')
      + '</div>'
      + (n.time ? '<span style="font-size:0.72rem;color:#9ca3af;flex-shrink:0;">' + _esc(n.time) + '</span>' : '')
      + '<button style="background:none;border:none;cursor:pointer;color:#9ca3af;font-size:1rem;padding:0;line-height:1;flex-shrink:0;" aria-label="Dismiss">×</button>'
      + '</div>';
  }
  html += '</div>';
  return html;
};

_RENDERERS['inline_alert'] = function(b) {
  var typeConfig = {
    info:    {bg:'#eff6ff',border:'#3b82f6',fg:'#1d4ed8',icon:'ℹ️'},
    success: {bg:'#f0fdf4',border:'#22c55e',fg:'#166534',icon:'✅'},
    warning: {bg:'#fffbeb',border:'#f59e0b',fg:'#92400e',icon:'⚠️'},
    error:   {bg:'#fef2f2',border:'#ef4444',fg:'#991b1b',icon:'❌'}
  };
  var tc = typeConfig[b.type] || typeConfig['info'];
  return '<div style="display:flex;align-items:flex-start;gap:10px;background:' + tc.bg + ';border-left:4px solid ' + tc.border + ';border-radius:0 8px 8px 0;padding:12px 16px;margin:0.75rem 0;">'
    + '<span style="font-size:0.95rem;flex-shrink:0;">' + tc.icon + '</span>'
    + '<div style="flex:1;font-size:0.875rem;color:' + tc.fg + ';">' + _esc(b.message || '') + '</div>'
    + (b.dismissible ? '<button style="background:none;border:none;cursor:pointer;color:#9ca3af;font-size:1rem;padding:0;line-height:1;" aria-label="Dismiss">×</button>' : '')
    + '</div>';
};

_RENDERERS['source_citation'] = function(b) {
  var authorsHtml = '';
  if (b.authors && b.authors.length) {
    var escapedAuthors = [];
    for (var i = 0; i < b.authors.length; i++) {
      escapedAuthors.push(_esc(b.authors[i]));
    }
    authorsHtml = '<span style="font-size:0.82rem;color:#374151;">' + escapedAuthors.join(', ') + '</span>';
    if (b.year) { authorsHtml += '<span style="font-size:0.82rem;color:#6b7280;"> (' + _esc(b.year) + ')</span>'; }
  }
  var titleHtml = b.url
    ? '<a href="' + _esc(b.url) + '" style="font-weight:600;color:#1d4ed8;text-decoration:none;font-size:0.9rem;">' + _esc(b.title || '') + '</a>'
    : '<span style="font-weight:600;color:#111827;font-size:0.9rem;">' + _esc(b.title || '') + '</span>';
  return '<div style="border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;margin:0.75rem 0;background:#fafafa;display:flex;gap:12px;">'
    + '<div style="width:28px;height:28px;border-radius:50%;background:#7c3aed;color:#fff;font-size:0.78rem;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;">①</div>'
    + '<div>'
    + titleHtml
    + (authorsHtml ? '<div style="margin-top:3px;">' + authorsHtml + '</div>' : '')
    + (b.publisher ? '<div style="font-size:0.8rem;color:#6b7280;margin-top:2px;font-style:italic;">' + _esc(b.publisher) + '</div>' : '')
    + (b.note ? '<div style="font-size:0.8rem;color:#4b5563;margin-top:5px;background:#f3f4f6;padding:5px 8px;border-radius:6px;">' + _esc(b.note) + '</div>' : '')
    + '</div>'
    + '</div>';
};

_RENDERERS['llm_comparison_table'] = function(b) {
  var models = b.models || [];
  var title = b.title || 'Model Comparison';
  var rows = '';
  for (var i = 0; i < models.length; i++) {
    var m = models[i];
    var strengths = m.strengths ? m.strengths.join(', ') : '';
    var weaknesses = m.weaknesses ? m.weaknesses.join(', ') : '';
    var rowBg = i % 2 === 0 ? '#fff' : '#f9fafb';
    rows += '<tr style="background:' + rowBg + ';">'
      + '<td style="padding:10px 12px;font-weight:600;color:#111827;font-size:0.875rem;">' + _esc(m.name || '') + '</td>'
      + '<td style="padding:10px 12px;font-size:0.82rem;color:#374151;">' + _esc(m.params || '—') + '</td>'
      + '<td style="padding:10px 12px;font-size:0.82rem;color:#374151;">' + _esc(m.context_window ? String(m.context_window) : '—') + '</td>'
      + '<td style="padding:10px 12px;font-size:0.82rem;color:#374151;">' + _esc(m.price_per_1m_tokens ? String(m.price_per_1m_tokens) : '—') + '</td>'
      + '<td style="padding:10px 12px;font-size:0.78rem;color:#166534;">' + _esc(strengths) + '</td>'
      + '<td style="padding:10px 12px;font-size:0.78rem;color:#991b1b;">' + _esc(weaknesses) + '</td>'
      + '</tr>';
  }
  return '<div style="margin:1rem 0;overflow-x:auto;">'
    + (title ? '<div style="font-weight:700;font-size:1rem;color:#111827;margin-bottom:10px;">' + _esc(title) + '</div>' : '')
    + '<table style="width:100%;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;font-size:0.875rem;">'
    + '<thead><tr style="background:#f3f4f6;"><th style="padding:10px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Model</th><th style="padding:10px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Params</th><th style="padding:10px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Context</th><th style="padding:10px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">$/1M tokens</th><th style="padding:10px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Strengths</th><th style="padding:10px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Weaknesses</th></tr></thead>'
    + '<tbody>' + rows + '</tbody>'
    + '</table></div>';
};

_RENDERERS['confidence_bar'] = function(b) {
  var value = Math.min(Math.max(parseFloat(b.value) || 0, 0), 1);
  var pct = Math.round(value * 100);
  var color = b.color || '#7c3aed';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="margin:0.75rem 0;">'
    + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
    + '<span style="font-size:0.875rem;font-weight:500;color:#374151;">' + _esc(b.label || '') + '</span>'
    + '<span style="font-size:0.875rem;font-weight:700;color:' + color + ';">' + pct + '%</span>'
    + '</div>'
    + '<div style="background:#f3f4f6;border-radius:999px;height:8px;overflow:hidden;">'
    + '<div style="width:' + pct + '%;height:100%;background:' + color + ';border-radius:999px;transition:width 0.6s ease;"></div>'
    + '</div>'
    + '</div>';
};

_RENDERERS['token_budget_meter'] = function(b) {
  var used = parseInt(b.used) || 0;
  var total = parseInt(b.total) || 1;
  var unit = b.unit || 'tokens';
  var pct = Math.min(Math.round((used / total) * 100), 100);
  var color = pct < 70 ? '#22c55e' : (pct < 90 ? '#f59e0b' : '#ef4444');
  var label = pct < 70 ? 'On track' : (pct < 90 ? 'Nearing limit' : 'Critical');
  return '<div style="margin:0.75rem 0;">'
    + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
    + '<span style="font-size:0.875rem;font-weight:600;color:#374151;">Token Budget</span>'
    + '<span style="font-size:0.82rem;color:#6b7280;">' + used.toLocaleString() + ' / ' + total.toLocaleString() + ' ' + _esc(unit) + '</span>'
    + '</div>'
    + '<div style="background:#f3f4f6;border-radius:999px;height:10px;overflow:hidden;">'
    + '<div style="width:' + pct + '%;height:100%;background:' + color + ';border-radius:999px;transition:width 0.6s ease;"></div>'
    + '</div>'
    + '<div style="display:flex;justify-content:space-between;margin-top:5px;">'
    + '<span style="font-size:0.72rem;color:' + color + ';font-weight:600;">' + label + '</span>'
    + '<span style="font-size:0.72rem;color:#6b7280;">' + pct + '% used</span>'
    + '</div>'
    + '</div>';
};

_RENDERERS['text_callout'] = function(b) {
  var text = b.text || '';
  var style = b.style || 'highlight';
  if (style === 'quote') {
    return '<blockquote style="border-left:4px solid #7c3aed;padding:12px 16px;margin:1rem 0;color:#4b5563;font-style:italic;background:#fafafa;border-radius:0 8px 8px 0;">' + _esc(text) + '</blockquote>';
  } else if (style === 'bold') {
    return '<div style="font-weight:700;color:#7c3aed;font-size:1.05rem;margin:0.75rem 0;">' + _esc(text) + '</div>';
  } else {
    return '<mark style="background:#fef9c3;color:#111827;padding:2px 6px;border-radius:4px;">' + _esc(text) + '</mark>';
  }
};

_RENDERERS['tag_block'] = function(b) {
  var tags = b.tags || [];
  var pillsHtml = '';
  for (var i = 0; i < tags.length; i++) {
    var tag = tags[i];
    var text, color, url;
    if (typeof tag === 'string') {
      text = tag; color = null; url = null;
    } else {
      text = tag.text || ''; color = tag.color || null; url = tag.url || null;
    }
    var bg = color || '#f3f4f6';
    var fg = color ? '#fff' : '#374151';
    var pill = '<span style="display:inline-flex;align-items:center;background:' + _esc(bg) + ';color:' + fg + ';font-size:0.78rem;font-weight:500;padding:4px 12px;border-radius:999px;white-space:nowrap;">' + _esc(text) + '</span>';
    if (url) {
      pillsHtml += '<a href="' + _esc(url) + '" style="text-decoration:none;">' + pill + '</a>';
    } else {
      pillsHtml += pill;
    }
  }
  return '<div style="display:flex;flex-wrap:wrap;gap:6px;margin:0.5rem 0;">' + pillsHtml + '</div>';
};

_RENDERERS['variant_selector'] = function(b) {
  var label = b.label || '';
  var variants = b.variants || [];
  var uid = Math.random().toString(36).substr(2, 6);
  var variantsHtml = '';
  for (var i = 0; i < variants.length; i++) {
    var v = variants[i];
    var id = 'variant-' + uid + '-' + i;
    if (v.color) {
      variantsHtml += '<label for="' + id + '" title="' + _esc(v.label || v.value || '') + '" style="cursor:pointer;">'
        + '<input type="radio" name="variant-' + uid + '" id="' + id + '" value="' + _esc(v.value || '') + '" style="display:none;"' + (v.disabled ? ' disabled' : '') + '>'
        + '<span style="display:inline-block;width:28px;height:28px;border-radius:50%;background:' + _esc(v.color) + ';border:2px solid #fff;box-shadow:0 0 0 2px #d1d5db;' + (v.disabled ? 'opacity:0.4;' : '') + '"></span>'
        + '</label>';
    } else {
      variantsHtml += '<label for="' + id + '" style="cursor:pointer;">'
        + '<input type="radio" name="variant-' + uid + '" id="' + id + '" value="' + _esc(v.value || '') + '" style="display:none;"' + (v.disabled ? ' disabled' : '') + '>'
        + '<span style="display:inline-block;padding:6px 14px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:0.82rem;font-weight:500;color:#374151;' + (v.disabled ? 'opacity:0.4;' : '') + '">' + _esc(v.label || v.value || '') + '</span>'
        + '</label>';
    }
  }
  return '<div style="margin:0.75rem 0;">'
    + (label ? '<div style="font-size:0.875rem;font-weight:600;color:#111827;margin-bottom:10px;">' + _esc(label) + '</div>' : '')
    + '<div style="display:flex;flex-wrap:wrap;gap:8px;">' + variantsHtml + '</div>'
    + '</div>';
};

_RENDERERS['shortcut_legend'] = function(b) {
  var shortcuts = b.shortcuts || [];
  var rows = '';
  for (var i = 0; i < shortcuts.length; i++) {
    var sc = shortcuts[i];
    var keys = sc.keys || [];
    var keysHtml = '';
    for (var k = 0; k < keys.length; k++) {
      if (k > 0) { keysHtml += '<span style="color:#9ca3af;font-size:0.8rem;margin:0 3px;">+</span>'; }
      keysHtml += '<kbd style="display:inline-block;background:#fff;border:1px solid #d1d5db;border-bottom:2px solid #9ca3af;border-radius:5px;padding:2px 7px;font-size:0.78rem;font-family:monospace;color:#111827;box-shadow:0 1px 0 rgba(0,0,0,0.1);">' + _esc(keys[k]) + '</kbd>';
    }
    rows += '<tr style="' + (i % 2 === 0 ? '' : 'background:#f9fafb;') + '">'
      + '<td style="padding:9px 12px;">' + keysHtml + '</td>'
      + '<td style="padding:9px 12px;font-size:0.875rem;color:#374151;">' + _esc(sc.description || '') + '</td>'
      + '</tr>';
  }
  return '<div style="margin:1rem 0;overflow-x:auto;">'
    + '<table style="width:100%;border-collapse:collapse;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;">'
    + '<thead><tr style="background:#f3f4f6;"><th style="padding:9px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Shortcut</th><th style="padding:9px 12px;text-align:left;font-size:0.78rem;font-weight:700;color:#6b7280;text-transform:uppercase;">Description</th></tr></thead>'
    + '<tbody>' + rows + '</tbody>'
    + '</table></div>';
};

_RENDERERS['rating_summary_bar'] = function(b) {
  var overall = parseFloat(b.overall) || 0;
  var totalReviews = b.total_reviews || 0;
  var dist = b.distribution || {};
  var starsHtml = '';
  var fullStars = Math.floor(overall);
  var halfStar = (overall - fullStars) >= 0.5;
  for (var s = 1; s <= 5; s++) {
    if (s <= fullStars) { starsHtml += '★'; }
    else if (s === fullStars + 1 && halfStar) { starsHtml += '½'; }
    else { starsHtml += '☆'; }
  }
  var barsHtml = '';
  for (var r = 5; r >= 1; r--) {
    var count = dist[String(r)] || 0;
    var pct = totalReviews > 0 ? Math.round((count / totalReviews) * 100) : 0;
    barsHtml += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">'
      + '<span style="font-size:0.78rem;color:#6b7280;width:10px;">' + r + '</span>'
      + '<span style="color:#f59e0b;font-size:0.78rem;">★</span>'
      + '<div style="flex:1;background:#f3f4f6;border-radius:999px;height:8px;overflow:hidden;">'
      + '<div style="width:' + pct + '%;height:100%;background:#f59e0b;border-radius:999px;"></div>'
      + '</div>'
      + '<span style="font-size:0.72rem;color:#6b7280;width:28px;text-align:right;">' + count + '</span>'
      + '</div>';
  }
  return '<div style="display:flex;gap:24px;align-items:flex-start;border:1px solid #e5e7eb;border-radius:14px;padding:20px;margin:1rem 0;background:#fff;">'
    + '<div style="text-align:center;min-width:80px;">'
    + '<div style="font-size:2.5rem;font-weight:800;color:#111827;line-height:1;">' + overall.toFixed(1) + '</div>'
    + '<div style="color:#f59e0b;font-size:1.1rem;letter-spacing:2px;">' + starsHtml + '</div>'
    + '<div style="font-size:0.78rem;color:#6b7280;margin-top:4px;">' + totalReviews.toLocaleString() + ' reviews</div>'
    + '</div>'
    + '<div style="flex:1;">' + barsHtml + '</div>'
    + '</div>';
};

_RENDERERS['model_card'] = function(b) {
  var metricsHtml = '';
  if (b.metrics && b.metrics.length) {
    for (var i = 0; i < b.metrics.length; i++) {
      var m = b.metrics[i];
      metricsHtml += '<div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:10px;text-align:center;">'
        + '<div style="font-size:1.1rem;font-weight:700;color:#7c3aed;">' + _esc(m.value || '') + '</div>'
        + '<div style="font-size:0.72rem;color:#6b7280;margin-top:2px;">' + _esc(m.label || '') + '</div>'
        + '</div>';
    }
  }
  var tagsHtml = '';
  if (b.tags && b.tags.length) {
    for (var t = 0; t < b.tags.length; t++) {
      tagsHtml += '<span style="background:#ede9fe;color:#5b21b6;font-size:0.72rem;padding:2px 8px;border-radius:999px;">' + _esc(b.tags[t]) + '</span>';
    }
  }
  return '<div style="border:1px solid #e5e7eb;border-radius:14px;padding:20px;margin:1rem 0;background:#fff;">'
    + '<div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:14px;">'
    + '<div style="flex:1;">'
    + (b.name ? '<div style="font-weight:800;font-size:1.1rem;color:#111827;">' + _esc(b.name) + (b.version ? ' <span style="font-size:0.78rem;color:#6b7280;font-weight:400;">v' + _esc(b.version) + '</span>' : '') + '</div>' : '')
    + (b.type ? '<div style="font-size:0.8rem;color:#7c3aed;font-weight:600;margin-top:2px;">' + _esc(b.type) + '</div>' : '')
    + '</div>'
    + (b.license ? '<span style="background:#f3f4f6;color:#374151;font-size:0.72rem;padding:3px 8px;border-radius:6px;">' + _esc(b.license) + '</span>' : '')
    + '</div>'
    + (b.description ? '<p style="font-size:0.875rem;color:#4b5563;margin:0 0 14px;line-height:1.6;">' + _esc(b.description) + '</p>' : '')
    + (metricsHtml ? '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:8px;margin-bottom:14px;">' + metricsHtml + '</div>' : '')
    + (tagsHtml ? '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-bottom:12px;">' + tagsHtml + '</div>' : '')
    + (b.link ? '<a href="' + _esc(b.link) + '" style="font-size:0.82rem;color:#7c3aed;text-decoration:none;font-weight:600;">View model →</a>' : '')
    + '</div>';
};

_RENDERERS['conversation_snippet'] = function(b) {
  var messages = b.messages || [];
  var html = '<div style="display:flex;flex-direction:column;gap:10px;margin:1rem 0;">';
  for (var i = 0; i < messages.length; i++) {
    var msg = messages[i];
    var role = msg.role || 'user';
    if (role === 'system') {
      html += '<div style="background:#f3f4f6;border-radius:8px;padding:8px 14px;font-size:0.8rem;color:#6b7280;font-style:italic;text-align:center;">' + _esc(msg.content || '') + '</div>';
    } else if (role === 'user') {
      html += '<div style="display:flex;justify-content:flex-end;">'
        + '<div style="background:#ede9fe;color:#111827;border-radius:16px 16px 4px 16px;padding:10px 14px;max-width:75%;font-size:0.875rem;">' + _esc(msg.content || '') + '</div>'
        + '</div>';
    } else {
      html += '<div style="display:flex;justify-content:flex-start;">'
        + '<div style="background:#fff;border:1px solid #e5e7eb;color:#111827;border-radius:16px 16px 16px 4px;padding:10px 14px;max-width:75%;font-size:0.875rem;">' + _esc(msg.content || '') + '</div>'
        + '</div>';
    }
  }
  html += '</div>';
  return html;
};

_RENDERERS['prompt_template'] = function(b) {
  var template = b.template || '';
  var variables = b.variables || [];
  var highlighted = _esc(template).replace(/\{\{([^}]+)\}\}/g, '<mark style="background:#fef9c3;color:#92400e;border-radius:3px;padding:1px 4px;">{{$1}}</mark>');
  var varsHtml = '';
  for (var i = 0; i < variables.length; i++) {
    var v = variables[i];
    varsHtml += '<tr style="' + (i % 2 === 0 ? '' : 'background:#f9fafb;') + '">'
      + '<td style="padding:8px 10px;font-family:monospace;font-size:0.82rem;color:#7c3aed;white-space:nowrap;">{{' + _esc(v.name || '') + '}}</td>'
      + '<td style="padding:8px 10px;font-size:0.82rem;color:#374151;">' + _esc(v.description || '') + '</td>'
      + '<td style="padding:8px 10px;font-size:0.78rem;color:#6b7280;font-style:italic;">' + _esc(v.example || '') + '</td>'
      + '</tr>';
  }
  return '<div style="border:1px solid #e5e7eb;border-radius:14px;overflow:hidden;margin:1rem 0;">'
    + '<div style="background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;">'
    + '<span style="font-weight:700;font-size:0.9rem;color:#111827;">' + _esc(b.title || 'Prompt Template') + '</span>'
    + (b.use_case ? '<span style="font-size:0.78rem;color:#6b7280;">' + _esc(b.use_case) + '</span>' : '')
    + '</div>'
    + '<pre style="margin:0;padding:16px;background:#1e1e2e;color:#cdd6f4;font-size:0.82rem;line-height:1.6;white-space:pre-wrap;overflow-x:auto;"><code>' + highlighted + '</code></pre>'
    + (varsHtml ? '<div style="padding:14px 16px;border-top:1px solid #e5e7eb;"><div style="font-size:0.8rem;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Variables</div><table style="width:100%;border-collapse:collapse;font-size:0.82rem;"><thead><tr style="background:#f3f4f6;"><th style="padding:7px 10px;text-align:left;font-size:0.75rem;color:#6b7280;">Variable</th><th style="padding:7px 10px;text-align:left;font-size:0.75rem;color:#6b7280;">Description</th><th style="padding:7px 10px;text-align:left;font-size:0.75rem;color:#6b7280;">Example</th></tr></thead><tbody>' + varsHtml + '</tbody></table></div>' : '')
    + '</div>';
};

// === Animation atoms — GAS-native implementations ===
// All use CSS @keyframes or inline <script> vanilla JS. No external CDN required.

// Keep fallback only for atoms that genuinely need canvas/physics engines
function _animFallback(atomName, label) {
  return '<div style="border:1px dashed #d1d5db;border-radius:10px;padding:16px;margin:1rem 0;background:#fafafa;text-align:center;color:#9ca3af;font-size:0.82rem;">[' + atomName + ' — requires canvas/physics engine]' + (label ? '<br><strong style=\'color:#374151;\'>' + _esc(label) + '</strong>' : '') + '</div>';
}

// ── CSS @keyframes only ──────────────────────────────────────────────────────

_RENDERERS['sonar_pulse'] = function(b) {
  var label = b.label || b.title || b.text || 'Live';
  var color = b.color || '#22c55e';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.sp-wrap-' + uid + '{display:flex;flex-direction:column;align-items:center;padding:32px;margin:1rem 0;}'
    + '.sp-dot-' + uid + '{position:relative;width:16px;height:16px;border-radius:50%;background:' + _esc(color) + ';}'
    + '.sp-ring-' + uid + '{position:absolute;border-radius:50%;border:2px solid ' + _esc(color) + ';opacity:0;top:50%;left:50%;transform:translate(-50%,-50%);animation:sp-' + uid + ' 2s ease-out infinite;}'
    + '.sp-ring-' + uid + ':nth-child(2){animation-delay:0.65s;}'
    + '.sp-ring-' + uid + ':nth-child(3){animation-delay:1.3s;}'
    + '@keyframes sp-' + uid + '{0%{width:16px;height:16px;opacity:0.9;}100%{width:90px;height:90px;opacity:0;}}'
    + '</style>'
    + '<div class="sp-wrap-' + uid + '">'
    + '<div class="sp-dot-' + uid + '">'
    + '<div class="sp-ring-' + uid + '"></div><div class="sp-ring-' + uid + '"></div><div class="sp-ring-' + uid + '"></div>'
    + '</div>'
    + (label ? '<div style="margin-top:22px;font-size:0.85rem;font-weight:600;color:' + _esc(color) + ';">' + _esc(label) + '</div>' : '')
    + '</div>';
};

_RENDERERS['typing_indicator'] = function(b) {
  var label = b.label || b.text || '';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.ti-wrap-' + uid + '{display:inline-flex;align-items:center;gap:6px;background:#f3f4f6;border-radius:18px;padding:10px 16px;}'
    + '.ti-dot-' + uid + '{width:8px;height:8px;border-radius:50%;background:#9ca3af;animation:ti-' + uid + ' 1.2s ease-in-out infinite;}'
    + '.ti-dot-' + uid + ':nth-child(2){animation-delay:0.2s;}'
    + '.ti-dot-' + uid + ':nth-child(3){animation-delay:0.4s;}'
    + '@keyframes ti-' + uid + '{0%,60%,100%{transform:translateY(0);}30%{transform:translateY(-7px);}}'
    + '</style>'
    + '<div style="margin:1rem 0;display:flex;align-items:center;gap:10px;">'
    + '<div class="ti-wrap-' + uid + '"><div class="ti-dot-' + uid + '"></div><div class="ti-dot-' + uid + '"></div><div class="ti-dot-' + uid + '"></div></div>'
    + (label ? '<span style="font-size:0.85rem;color:#6b7280;">' + _esc(label) + '</span>' : '')
    + '</div>';
};

_RENDERERS['blur_fade_in'] = function(b) {
  var text = b.text || b.content || '';
  var title = b.title || '';
  var delay = parseFloat(b.delay || 0);
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>@keyframes bfi-' + uid + '{from{opacity:0;filter:blur(10px);transform:translateY(14px);}to{opacity:1;filter:blur(0);transform:translateY(0);}}</style>'
    + '<div style="margin:1rem 0;animation:bfi-' + uid + ' 0.9s ease-out ' + delay + 's both;">'
    + (title ? '<div style="font-size:1.1rem;font-weight:700;color:#111827;margin-bottom:8px;">' + _esc(title) + '</div>' : '')
    + (text ? '<div style="color:#374151;line-height:1.7;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div>';
};

_RENDERERS['dot_grid_background'] = function(b) {
  var title = b.title || '';
  var text = b.text || b.content || '';
  var color = b.color || '#6366f1';
  var bg = b.bg || '#0f172a';
  return '<div style="position:relative;border-radius:16px;overflow:hidden;padding:40px 32px;margin:1rem 0;background:' + _esc(bg) + ';background-image:radial-gradient(' + _esc(color) + '33 1.5px,transparent 1.5px);background-size:22px 22px;">'
    + (title ? '<div style="position:relative;z-index:1;font-size:1.25rem;font-weight:700;color:#fff;margin-bottom:10px;">' + _esc(title) + '</div>' : '')
    + (text ? '<div style="position:relative;z-index:1;color:rgba(255,255,255,0.8);line-height:1.7;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div>';
};
_RENDERERS['pattern_background'] = _RENDERERS['dot_grid_background'];

_RENDERERS['animated_border_card'] = function(b) {
  var title = b.title || '';
  var text = b.text || b.content || '';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.abc-' + uid + '{position:relative;border-radius:16px;padding:2px;margin:1rem 0;}'
    + '.abc-' + uid + '::before{content:"";position:absolute;inset:-2px;border-radius:16px;background:conic-gradient(from 0deg,#6366f1,#a855f7,#ec4899,#f59e0b,#6366f1);z-index:0;animation:abc-spin-' + uid + ' 3s linear infinite;}'
    + '.abc-inner-' + uid + '{position:relative;z-index:1;background:#fff;border-radius:14px;padding:24px;}'
    + '@keyframes abc-spin-' + uid + '{to{transform:rotate(360deg);}}'
    + '</style>'
    + '<div class="abc-' + uid + '"><div class="abc-inner-' + uid + '">'
    + (title ? '<div style="font-size:1rem;font-weight:700;color:#111827;margin-bottom:8px;">' + _esc(title) + '</div>' : '')
    + (text ? '<div style="color:#374151;font-size:0.9rem;line-height:1.6;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div></div>';
};

_RENDERERS['aurora_background'] = function(b) {
  var title = b.title || '';
  var text = b.text || b.content || '';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.aur-' + uid + '{position:relative;border-radius:20px;overflow:hidden;padding:44px 36px;margin:1rem 0;background:#060617;}'
    + '.aur-' + uid + '::before{content:"";position:absolute;width:360px;height:360px;top:-80px;left:-80px;border-radius:50%;background:radial-gradient(circle,#6366f188,#a855f744);filter:blur(60px);animation:aur-a-' + uid + ' 9s ease-in-out infinite alternate;}'
    + '.aur-' + uid + '::after{content:"";position:absolute;width:300px;height:300px;bottom:-60px;right:-60px;border-radius:50%;background:radial-gradient(circle,#ec489944,#3b82f666);filter:blur(60px);animation:aur-a-' + uid + ' 9s ease-in-out infinite alternate-reverse;}'
    + '@keyframes aur-a-' + uid + '{from{transform:translate(0,0);}to{transform:translate(70px,50px);}}'
    + '</style>'
    + '<div class="aur-' + uid + '"><div style="position:relative;z-index:1;">'
    + (title ? '<div style="font-size:1.4rem;font-weight:800;color:#fff;margin-bottom:12px;">' + _esc(title) + '</div>' : '')
    + (text ? '<div style="color:rgba(255,255,255,0.82);line-height:1.75;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div></div>';
};
_RENDERERS['ambient_gradient'] = _RENDERERS['aurora_background'];

_RENDERERS['card_stack'] = function(b) {
  var cards = b.cards || b.items || [];
  var title = b.title || (cards[0] && cards[0].title) || '';
  var text  = b.text  || (cards[0] && cards[0].text)  || '';
  var count = cards.length || b.count || 1;
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.cs-' + uid + '{position:relative;margin:1rem 0;padding-bottom:18px;}'
    + '.cs-bg2-' + uid + '{position:absolute;bottom:0;left:16px;right:16px;height:56px;background:#e5e7eb;border-radius:12px;}'
    + '.cs-bg1-' + uid + '{position:absolute;bottom:8px;left:8px;right:8px;height:56px;background:#f3f4f6;border-radius:12px;}'
    + '.cs-front-' + uid + '{position:relative;z-index:2;background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:22px;box-shadow:0 4px 16px rgba(0,0,0,0.07);}'
    + '.cs-badge-' + uid + '{display:inline-block;margin-bottom:10px;background:#6366f1;color:#fff;font-size:0.72rem;font-weight:700;padding:2px 10px;border-radius:20px;}'
    + '</style>'
    + '<div class="cs-' + uid + '">'
    + (count > 1 ? '<div class="cs-bg2-' + uid + '"></div><div class="cs-bg1-' + uid + '"></div>' : '')
    + '<div class="cs-front-' + uid + '">'
    + (count > 1 ? '<div class="cs-badge-' + uid + '">' + count + ' items</div>' : '')
    + (title ? '<div style="font-size:1rem;font-weight:700;color:#111827;margin-bottom:8px;">' + _esc(title) + '</div>' : '')
    + (text  ? '<div style="font-size:0.875rem;color:#6b7280;line-height:1.6;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div></div>';
};
_RENDERERS['depth_stack'] = _RENDERERS['card_stack'];

_RENDERERS['shimmer_button'] = function(b) {
  var label = b.text || b.label || b.title || 'Action';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.sb-' + uid + '{position:relative;overflow:hidden;background:#7c3aed;color:#fff;font-weight:700;font-size:0.95rem;padding:12px 28px;border:none;border-radius:10px;cursor:pointer;}'
    + '.sb-' + uid + '::after{content:"";position:absolute;top:0;left:-100%;width:60%;height:100%;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.28),transparent);transform:skewX(-20deg);animation:sb-shine-' + uid + ' 2s infinite;}'
    + '@keyframes sb-shine-' + uid + '{0%{left:-100%;}100%{left:160%;}}'
    + '</style>'
    + '<div style="margin:1rem 0;text-align:center;"><button class="sb-' + uid + '">' + _esc(label) + '</button></div>';
};

_RENDERERS['glow_button'] = function(b) {
  var label = b.text || b.label || b.title || 'Action';
  var color = b.color || '#7c3aed';
  return '<div style="margin:1rem 0;text-align:center;">'
    + '<button style="background:' + _esc(color) + ';color:#fff;font-weight:700;font-size:0.95rem;padding:12px 28px;border:none;border-radius:10px;cursor:pointer;box-shadow:0 0 16px ' + _esc(color) + '88,0 0 36px ' + _esc(color) + '44;letter-spacing:0.02em;">' + _esc(label) + '</button>'
    + '</div>';
};

_RENDERERS['gradient_text'] = function(b) {
  var text = b.text || b.label || b.title || '';
  var grad = b.gradient || 'linear-gradient(135deg,#6366f1,#a855f7,#ec4899)';
  return '<div style="margin:0.5rem 0;"><span style="background:' + _esc(grad) + ';-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;font-weight:800;font-size:' + _esc(b.size || '1.5rem') + ';">' + _esc(text) + '</span></div>';
};

_RENDERERS['glitch_text'] = function(b) {
  var text = b.text || b.title || b.label || '';
  var size = b.size || '2rem';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.gl-' + uid + '{position:relative;font-size:' + _esc(size) + ';font-weight:800;color:#22d3ee;display:inline-block;letter-spacing:0.04em;}'
    + '.gl-' + uid + '::before{content:attr(data-t);position:absolute;top:0;left:-2px;color:#f43f5e;clip-path:polygon(0 0,100% 0,100% 38%,0 38%);animation:gl-a-' + uid + ' 3.5s infinite;}'
    + '.gl-' + uid + '::after{content:attr(data-t);position:absolute;top:0;left:2px;color:#3b82f6;clip-path:polygon(0 62%,100% 62%,100% 100%,0 100%);animation:gl-b-' + uid + ' 3.5s infinite;}'
    + '@keyframes gl-a-' + uid + '{0%,88%,100%{transform:none;}89%{transform:translateX(-3px);}92%{transform:translateX(3px);}95%{transform:translateX(-1px);}}'
    + '@keyframes gl-b-' + uid + '{0%,88%,100%{transform:none;}89%{transform:translateX(3px);}92%{transform:translateX(-3px);}95%{transform:translateX(1px);}}'
    + '</style>'
    + '<div style="margin:1rem 0;"><span class="gl-' + uid + '" data-t="' + _esc(text) + '">' + _esc(text) + '</span></div>';
};

_RENDERERS['neon_glow'] = function(b) {
  var text = b.text || b.title || b.label || '';
  var color = b.color || '#22d3ee';
  var size  = b.size  || '2rem';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.ng-' + uid + '{font-size:' + _esc(size) + ';font-weight:800;color:' + _esc(color) + ';text-shadow:0 0 8px ' + _esc(color) + ',0 0 24px ' + _esc(color) + ';animation:ng-pulse-' + uid + ' 2.2s ease-in-out infinite alternate;display:inline-block;}'
    + '@keyframes ng-pulse-' + uid + '{from{text-shadow:0 0 4px ' + _esc(color) + ',0 0 10px ' + _esc(color) + ';}to{text-shadow:0 0 10px ' + _esc(color) + ',0 0 32px ' + _esc(color) + ',0 0 64px ' + _esc(color) + ';opacity:0.88;}}'
    + '</style>'
    + '<div style="background:#090909;border-radius:12px;padding:28px;text-align:center;margin:1rem 0;"><span class="ng-' + uid + '">' + _esc(text) + '</span></div>';
};

_RENDERERS['skeleton_stage_card'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>@keyframes sk-' + uid + '{0%,100%{opacity:0.4;}50%{opacity:1;}}</style>'
    + '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:20px;margin:1rem 0;background:#fff;">'
    + ['100%','80%','90%','60%'].map(function(w, i) {
        return '<div style="height:' + (i===0?'18px':'13px') + ';width:' + w + ';background:#e5e7eb;border-radius:6px;margin-bottom:10px;animation:sk-' + uid + ' 1.4s ease-in-out ' + (i*0.15) + 's infinite;"></div>';
      }).join('')
    + '</div>';
};

_RENDERERS['svg_path_draw'] = function(b) {
  var path  = b.path  || 'M10 50 Q 100 10 190 50 T 380 50';
  var label = b.label || b.title || '';
  var color = b.color || '#6366f1';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="margin:1rem 0;">'
    + '<style>@keyframes draw-' + uid + '{to{stroke-dashoffset:0;}}</style>'
    + (label ? '<div style="font-size:0.85rem;font-weight:600;color:#6b7280;margin-bottom:8px;">' + _esc(label) + '</div>' : '')
    + '<svg viewBox="0 0 400 80" style="width:100%;height:80px;" xmlns="http://www.w3.org/2000/svg">'
    + '<path d="' + _esc(path) + '" stroke="' + _esc(color) + '" stroke-width="3" fill="none" stroke-linecap="round" stroke-dasharray="1000" stroke-dashoffset="1000" style="animation:draw-' + uid + ' 2s ease-out 0.2s forwards;"/>'
    + '</svg></div>';
};

// ── Inline JS atoms ──────────────────────────────────────────────────────────

_RENDERERS['typewriter_text'] = function(b) {
  var text  = b.text || b.content || b.label || '';
  var speed = parseInt(b.speed || 38, 10);
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="border:1px solid #374151;border-radius:10px;padding:16px;margin:1rem 0;background:#1e1e2e;">'
    + '<style>@keyframes blink-' + uid + '{0%,100%{opacity:1;}50%{opacity:0;}}</style>'
    + '<pre id="tw-' + uid + '" data-text="' + _esc(text) + '" style="margin:0;font-family:\'Courier New\',monospace;font-size:0.875rem;color:#cdd6f4;white-space:pre-wrap;line-height:1.6;min-height:1.4em;"></pre>'
    + '<span id="twc-' + uid + '" style="display:inline-block;width:2px;height:1em;background:#a855f7;vertical-align:text-bottom;animation:blink-' + uid + ' 1s step-end infinite;margin-left:2px;"></span>'
    + '<script>(function(){'
    + 'var el=document.getElementById("tw-' + uid + '");'
    + 'var t=el.getAttribute("data-text");var i=0;'
    + 'function next(){if(i<t.length){el.textContent+=t[i++];setTimeout(next,' + speed + ');}else{var c=document.getElementById("twc-' + uid + '");if(c)c.style.display="none";}}'
    + 'next();'
    + '})();<\/script>'
    + '</div>';
};
_RENDERERS['typewriter'] = _RENDERERS['typewriter_text'];

_RENDERERS['animated_counter'] = function(b) {
  var end   = parseFloat(b.value !== undefined ? b.value : (b.end !== undefined ? b.end : 0));
  var start = parseFloat(b.start !== undefined ? b.start : 0);
  var dur   = parseInt(b.duration || 1600, 10);
  var pre   = b.prefix || '';
  var suf   = b.suffix || '';
  var label = b.label || b.title || '';
  var dec   = b.decimals !== undefined ? parseInt(b.decimals, 10) : (String(end).indexOf('.') > -1 ? String(end).split('.')[1].length : 0);
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div id="ac-wrap-' + uid + '" style="border:1px solid #e5e7eb;border-radius:12px;padding:28px;margin:1rem 0;text-align:center;background:#fff;">'
    + '<div id="ac-' + uid + '" style="font-size:2.6rem;font-weight:800;color:#1f2937;">' + _esc(pre) + start.toFixed(dec) + _esc(suf) + '</div>'
    + (label ? '<div style="font-size:0.85rem;color:#6b7280;margin-top:6px;font-weight:500;">' + _esc(label) + '</div>' : '')
    + '<script>(function(){'
    + 'var el=document.getElementById("ac-' + uid + '");'
    + 'var wrap=document.getElementById("ac-wrap-' + uid + '");'
    + 'var s=' + start + ',e=' + end + ',d=' + dur + ',dec=' + dec + ';'
    + 'var pre="' + _esc(pre).replace(/\\/g,'\\\\').replace(/"/g,'\\"') + '",suf="' + _esc(suf).replace(/\\/g,'\\\\').replace(/"/g,'\\"') + '";'
    + 'var done=false;'
    + 'function run(){if(done)return;done=true;var t0=null;'
    + 'function step(ts){if(!t0)t0=ts;var p=Math.min((ts-t0)/d,1);var ease=p<0.5?2*p*p:1-Math.pow(-2*p+2,2)/2;'
    + 'el.textContent=pre+(s+(e-s)*ease).toFixed(dec)+suf;if(p<1)requestAnimationFrame(step);}'
    + 'requestAnimationFrame(step);}'
    + 'if("IntersectionObserver" in window){new IntersectionObserver(function(es,ob){if(es[0].isIntersecting){run();ob.disconnect();}},{threshold:0.3}).observe(wrap);}else{run();}'
    + '})();<\/script>'
    + '</div>';
};
_RENDERERS['live_metric'] = _RENDERERS['animated_counter'];
_RENDERERS['number_odometer'] = _RENDERERS['animated_counter'];

_RENDERERS['countdown_timer'] = function(b) {
  var target = b.target_date || b.target || '';
  var label  = b.label || b.title || '';
  var uid = Math.random().toString(36).substr(2, 6);
  if (!target) {
    return '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:20px;margin:1rem 0;text-align:center;background:#fff;">'
      + (label ? '<div style="font-size:0.78rem;font-weight:600;color:#9ca3af;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">⏱ ' + _esc(label) + '</div>' : '')
      + '<div id="cd-' + uid + '" style="font-size:2.2rem;font-weight:800;color:#1f2937;font-family:monospace;">00:00:00</div>'
      + '<script>(function(){var s=0,el=document.getElementById("cd-' + uid + '");setInterval(function(){s++;var h=Math.floor(s/3600),m=Math.floor((s%3600)/60),sec=s%60;el.textContent=[h,m,sec].map(function(n){return n<10?"0"+n:n}).join(":");},1000);})();<\/script>'
      + '</div>';
  }
  return '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:22px;margin:1rem 0;background:#fff;">'
    + (label ? '<div style="font-size:0.78rem;font-weight:600;color:#9ca3af;text-transform:uppercase;letter-spacing:0.08em;text-align:center;margin-bottom:16px;">' + _esc(label) + '</div>' : '')
    + '<div style="display:flex;justify-content:center;gap:12px;">'
    + ['days','hrs','min','sec'].map(function(u) {
        return '<div style="text-align:center;min-width:60px;background:#f9fafb;border-radius:10px;padding:12px 8px;">'
          + '<div id="cd-' + uid + '-' + u + '" style="font-size:1.9rem;font-weight:800;color:#1f2937;font-family:monospace;line-height:1;">--</div>'
          + '<div style="font-size:0.68rem;color:#9ca3af;font-weight:700;margin-top:4px;text-transform:uppercase;letter-spacing:0.06em;">' + u + '</div>'
          + '</div>';
      }).join('')
    + '</div>'
    + '<script>(function(){'
    + 'var end=new Date("' + _esc(target) + '").getTime();'
    + 'function set(id,v){var el=document.getElementById(id);if(el)el.textContent=v<10?"0"+v:v;}'
    + 'function tick(){var diff=Math.max(end-Date.now(),0);'
    + 'set("cd-' + uid + '-days",Math.floor(diff/86400000));'
    + 'set("cd-' + uid + '-hrs",Math.floor((diff%86400000)/3600000));'
    + 'set("cd-' + uid + '-min",Math.floor((diff%3600000)/60000));'
    + 'set("cd-' + uid + '-sec",Math.floor((diff%60000)/1000));'
    + 'if(diff>0)setTimeout(tick,1000);}'
    + 'tick();'
    + '})();<\/script>'
    + '</div>';
};
_RENDERERS['deadline_ticker'] = _RENDERERS['countdown_timer'];

_RENDERERS['encrypted_reveal'] = function(b) {
  var text  = b.text || b.content || b.label || '';
  var title = b.title || '';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="border:1px solid #1f2937;border-radius:12px;padding:20px;margin:1rem 0;background:#0f172a;">'
    + (title ? '<div style="font-size:0.75rem;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;">' + _esc(title) + '</div>' : '')
    + '<div id="er-' + uid + '" data-text="' + _esc(text) + '" style="font-family:\'Courier New\',monospace;font-size:1.05rem;font-weight:600;color:#22d3ee;line-height:1.6;min-height:1.5em;cursor:pointer;" title="click to reveal"></div>'
    + '<div style="font-size:0.7rem;color:#475569;margin-top:8px;">↑ click to reveal</div>'
    + '<script>(function(){'
    + 'var el=document.getElementById("er-' + uid + '");'
    + 'var target=el.getAttribute("data-text");'
    + 'var chars="!<>-_\\/[]{}=+*^?#@";var itr=0,iv,done=false;'
    + 'function scramble(){el.textContent=target.split("").map(function(c,i){return c===" "?" ":(i<Math.floor(itr)?target[i]:chars[Math.floor(Math.random()*chars.length)]);}).join("");'
    + 'if(itr>=target.length){clearInterval(iv);el.textContent=target;done=true;}itr+=0.5;}'
    + 'function start(){if(done)return;if(iv)clearInterval(iv);itr=0;iv=setInterval(scramble,30);}'
    + 'el.addEventListener("click",start);'
    + 'setTimeout(start,600);'
    + '})();<\/script>'
    + '</div>';
};
_RENDERERS['scramble_reveal'] = _RENDERERS['encrypted_reveal'];

_RENDERERS['word_flip'] = function(b) {
  var words    = b.words || b.items || ['One','Two','Three'];
  var prefix   = b.prefix || b.text || '';
  var suffix   = b.suffix || '';
  var interval = parseInt(b.interval || 2200, 10);
  var color    = b.color || '#6366f1';
  var uid = Math.random().toString(36).substr(2, 6);
  var wordsJson = JSON.stringify(words.map(function(w) { return String(w); }));
  return '<div style="margin:1rem 0;font-size:1.3rem;font-weight:700;color:#1f2937;line-height:1.5;">'
    + (prefix ? '<span>' + _esc(prefix) + ' </span>' : '')
    + '<span id="wf-' + uid + '" style="color:' + _esc(color) + ';transition:opacity 0.28s ease;">' + _esc(String(words[0] || '')) + '</span>'
    + (suffix ? '<span> ' + _esc(suffix) + '</span>' : '')
    + '<script>(function(){'
    + 'var el=document.getElementById("wf-' + uid + '");'
    + 'var words=' + wordsJson + ';var i=0;'
    + 'setInterval(function(){el.style.opacity="0";setTimeout(function(){i=(i+1)%words.length;el.textContent=words[i];el.style.opacity="1";},280);},' + interval + ');'
    + '})();<\/script>'
    + '</div>';
};

_RENDERERS['word_scramble'] = function(b) {
  var words = b.words || b.items || ['HELLO','WORLD'];
  var uid = Math.random().toString(36).substr(2, 6);
  var wordsJson = JSON.stringify(words.map(function(w) { return String(w).toUpperCase(); }));
  return '<div style="border:1px solid #1e293b;border-radius:12px;padding:28px;margin:1rem 0;background:#0f172a;text-align:center;">'
    + '<div id="ws-' + uid + '" style="font-family:\'Courier New\',monospace;font-size:1.6rem;font-weight:800;color:#22d3ee;letter-spacing:0.12em;min-height:2rem;"></div>'
    + '<script>(function(){'
    + 'var el=document.getElementById("ws-' + uid + '");'
    + 'var words=' + wordsJson + ';var chars="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";var wi=0,itr=0,iv;'
    + 'function tick(){var t=words[wi];el.textContent=t.split("").map(function(c,i){return i<Math.floor(itr)?c:chars[Math.floor(Math.random()*chars.length)];}).join("");'
    + 'itr+=0.4;if(itr>=t.length+4){clearInterval(iv);setTimeout(function(){wi=(wi+1)%words.length;itr=0;iv=setInterval(tick,40);},1400);}}'
    + 'iv=setInterval(tick,40);'
    + '})();<\/script>'
    + '</div>';
};

_RENDERERS['reveal_on_scroll'] = function(b) {
  var text  = b.text || b.content || '';
  var title = b.title || '';
  var delay = parseFloat(b.delay || 0);
  var dir   = b.direction || 'up';
  var uid = Math.random().toString(36).substr(2, 6);
  var startT = dir==='left'?'translateX(-28px)':dir==='right'?'translateX(28px)':dir==='down'?'translateY(-18px)':'translateY(20px)';
  return '<div id="ros-' + uid + '" style="margin:1rem 0;opacity:0;transform:' + startT + ';transition:opacity 0.65s ease ' + delay + 's,transform 0.65s ease ' + delay + 's;">'
    + (title ? '<div style="font-size:1.1rem;font-weight:700;color:#111827;margin-bottom:8px;">' + _esc(title) + '</div>' : '')
    + (text  ? '<div style="color:#374151;line-height:1.7;">' + _markdownToHtml(text) + '</div>' : '')
    + '<script>(function(){'
    + 'var el=document.getElementById("ros-' + uid + '");'
    + 'function show(){el.style.opacity="1";el.style.transform="none";}'
    + 'if("IntersectionObserver" in window){new IntersectionObserver(function(es,ob){if(es[0].isIntersecting){show();ob.disconnect();}},{threshold:0.12}).observe(el);}else{show();}'
    + '})();<\/script>'
    + '</div>';
};
_RENDERERS['scroll_trigger'] = _RENDERERS['reveal_on_scroll'];

_RENDERERS['magnetic_button'] = function(b) {
  var label = b.text || b.label || b.title || 'Click me';
  var color = b.color || '#6366f1';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="margin:1rem 0;text-align:center;">'
    + '<button id="mag-' + uid + '" style="background:' + _esc(color) + ';color:#fff;font-weight:700;font-size:1rem;padding:14px 36px;border:none;border-radius:50px;cursor:pointer;transition:transform 0.12s ease,box-shadow 0.12s ease;box-shadow:0 4px 24px rgba(0,0,0,0.14);">' + _esc(label) + '</button>'
    + '<script>(function(){'
    + 'var el=document.getElementById("mag-' + uid + '");'
    + 'el.addEventListener("mousemove",function(e){var r=el.getBoundingClientRect();var x=(e.clientX-r.left-r.width/2)*0.28;var y=(e.clientY-r.top-r.height/2)*0.28;el.style.transform="translate("+x+"px,"+y+"px)";});'
    + 'el.addEventListener("mouseleave",function(){el.style.transform="";});'
    + '})();<\/script>'
    + '</div>';
};

_RENDERERS['animated_beam'] = function(b) {
  var from  = b.from  || 'Source';
  var to    = b.to    || 'Target';
  var label = b.label || b.text || '';
  var color = b.color || '#6366f1';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>@keyframes beam-' + uid + '{to{stroke-dashoffset:-20;}}</style>'
    + '<div style="margin:1rem 0;display:flex;align-items:center;gap:0;">'
    + '<div style="flex-shrink:0;background:#fff;border:2px solid ' + _esc(color) + ';border-radius:8px;padding:8px 14px;font-size:0.85rem;font-weight:600;color:#1f2937;">' + _esc(from) + '</div>'
    + '<div style="flex:1;position:relative;height:32px;">'
    + '<svg width="100%" height="32" xmlns="http://www.w3.org/2000/svg" style="position:absolute;top:0;left:0;overflow:visible;">'
    + '<line x1="0" y1="16" x2="100%" y2="16" stroke="' + _esc(color) + '" stroke-width="2.5" stroke-dasharray="7 5" style="animation:beam-' + uid + ' 0.7s linear infinite;"/>'
    + '<polygon points="-6,-5 4,0 -6,5" fill="' + _esc(color) + '" transform="translate(100%,16)"/>'
    + '</svg>'
    + (label ? '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);background:#fff;border:1px solid #e5e7eb;border-radius:20px;padding:2px 10px;font-size:0.72rem;color:#6b7280;white-space:nowrap;">' + _esc(label) + '</div>' : '')
    + '</div>'
    + '<div style="flex-shrink:0;background:#fff;border:2px solid ' + _esc(color) + ';border-radius:8px;padding:8px 14px;font-size:0.85rem;font-weight:600;color:#1f2937;">' + _esc(to) + '</div>'
    + '</div>';
};
_RENDERERS['flow_connector'] = _RENDERERS['animated_beam'];

_RENDERERS['confetti_burst'] = function(b) {
  var label  = b.label || b.text || b.title || '🎉 Achievement Unlocked!';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>@keyframes cf-' + uid + '{0%{opacity:1;transform:translate(var(--tx),0) rotate(0deg);}100%{opacity:0;transform:translate(var(--tx),var(--ty)) rotate(720deg);}}</style>'
    + '<div id="cfb-' + uid + '" style="position:relative;overflow:hidden;border-radius:16px;padding:36px;margin:1rem 0;background:linear-gradient(135deg,#1e1b4b,#312e81);text-align:center;">'
    + '<div style="position:relative;z-index:1;font-size:1.2rem;font-weight:700;color:#fff;">' + _esc(label) + '</div>'
    + '</div>'
    + '<script>(function(){'
    + 'var wrap=document.getElementById("cfb-' + uid + '");'
    + 'var colors=["#f43f5e","#f59e0b","#10b981","#3b82f6","#a855f7","#ec4899"];'
    + 'for(var i=0;i<40;i++){var p=document.createElement("span");var c=colors[i%colors.length];var sz=6+Math.random()*9;var tx=(Math.random()*200-100);var ty=120+Math.random()*80;var del=Math.random()*0.5;var dur=0.85+Math.random()*0.65;'
    + 'p.style.cssText="position:absolute;left:"+Math.random()*100+"%;top:20%;width:"+sz+"px;height:"+sz+"px;background:"+c+";border-radius:"+(Math.random()>0.5?"50%":"2px")+";pointer-events:none;animation:cf-' + uid + ' "+dur+"s ease-in "+del+"s both;--tx:"+tx+"px;--ty:"+ty+"px;";'
    + 'wrap.appendChild(p);}'
    + '})();<\/script>';
};

_RENDERERS['confetti_trigger'] = function(b) {
  var label   = b.label  || b.text  || '🎉 Congratulations!';
  var trigger = b.trigger || b.button || 'Celebrate';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>@keyframes cft-' + uid + '{0%{opacity:1;transform:translate(var(--tx),0) rotate(0deg);}100%{opacity:0;transform:translate(var(--tx),var(--ty)) rotate(720deg);}}</style>'
    + '<div id="cft-wrap-' + uid + '" style="position:relative;overflow:hidden;border-radius:16px;padding:32px;margin:1rem 0;background:#f9fafb;border:1px solid #e5e7eb;text-align:center;transition:background 0.5s;">'
    + '<button id="cft-btn-' + uid + '" style="background:#6366f1;color:#fff;font-weight:700;padding:12px 28px;border:none;border-radius:10px;font-size:0.95rem;cursor:pointer;">' + _esc(trigger) + '</button>'
    + '<div id="cft-msg-' + uid + '" style="display:none;font-size:1.2rem;font-weight:700;color:#fff;">' + _esc(label) + '</div>'
    + '</div>'
    + '<script>(function(){'
    + 'var wrap=document.getElementById("cft-wrap-' + uid + '");'
    + 'document.getElementById("cft-btn-' + uid + '").addEventListener("click",function(){'
    + 'this.style.display="none";'
    + 'document.getElementById("cft-msg-' + uid + '").style.display="block";'
    + 'wrap.style.background="linear-gradient(135deg,#1e1b4b,#312e81)";'
    + 'var colors=["#f43f5e","#f59e0b","#10b981","#3b82f6","#a855f7","#ec4899"];'
    + 'for(var i=0;i<44;i++){var p=document.createElement("span");var c=colors[i%colors.length];var sz=6+Math.random()*9;var tx=(Math.random()*200-100);var ty=100+Math.random()*90;var del=Math.random()*0.55;var dur=0.9+Math.random()*0.65;'
    + 'p.style.cssText="position:absolute;left:"+Math.random()*100+"%;top:20%;width:"+sz+"px;height:"+sz+"px;background:"+c+";border-radius:"+(Math.random()>0.5?"50%":"2px")+";pointer-events:none;animation:cft-' + uid + ' "+dur+"s ease-in "+del+"s both;--tx:"+tx+"px;--ty:"+ty+"px;";'
    + 'wrap.appendChild(p);}});'
    + '})();<\/script>';
};

// Atoms that genuinely require canvas or physics — kept as informational placeholders
_RENDERERS['meteor_shower'] = function(b) {
  return _animFallback('meteor shower', b.title || b.label || b.text || '');
};
_RENDERERS['floating_particles'] = function(b) {
  return _animFallback('floating particles', b.title || b.label || b.text || '');
};
_RENDERERS['parallax_section'] = function(b) {
  return _animFallback('parallax section', b.title || b.label || b.text || '');
};
_RENDERERS['effect_overlay'] = function(b) {
  return _animFallback('effect overlay', b.title || b.label || b.text || '');
};

// ── New GAS-native atoms ─────────────────────────────────────────────────────

_RENDERERS['scroll_progress'] = function(b) {
  var color  = b.color  || '#6366f1';
  var height = parseInt(b.height || 3, 10);
  return '<style>#a2ui-sp-bar{position:fixed;top:0;left:0;width:0%;height:' + height + 'px;background:' + _esc(color) + ';z-index:9999;transition:width 0.08s linear;pointer-events:none;}</style>'
    + '<div id="a2ui-sp-bar"></div>'
    + '<script>(function(){if(document.getElementById("a2ui-sp-bar-init"))return;var m=document.createElement("meta");m.id="a2ui-sp-bar-init";document.head.appendChild(m);var bar=document.getElementById("a2ui-sp-bar");window.addEventListener("scroll",function(){var s=document.documentElement.scrollTop||document.body.scrollTop;var h=document.documentElement.scrollHeight-document.documentElement.clientHeight;bar.style.width=(h>0?Math.min(s/h*100,100):0)+"%";},{passive:true});})();<\/script>';
};

_RENDERERS['live_clock'] = function(b) {
  var label  = b.label || b.title || '';
  var format = b.format || '24h';
  var tz     = b.timezone || '';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="display:inline-flex;flex-direction:column;align-items:center;background:#0f172a;border-radius:16px;padding:24px 36px;margin:1rem 0;">'
    + (label ? '<div style="font-size:0.72rem;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:10px;">' + _esc(label) + '</div>' : '')
    + '<div id="lc-' + uid + '" style="font-size:2.6rem;font-weight:800;font-family:monospace;color:#22d3ee;letter-spacing:0.07em;">--:--:--</div>'
    + (tz ? '<div style="font-size:0.7rem;color:#475569;margin-top:6px;">' + _esc(tz) + '</div>' : '')
    + '<script>(function(){'
    + 'var el=document.getElementById("lc-' + uid + '");var f="' + format + '";'
    + 'function tick(){var now=new Date();var h=now.getHours(),m=now.getMinutes(),s=now.getSeconds(),suf="";'
    + 'if(f==="12h"){suf=h>=12?" PM":" AM";h=h%12||12;}'
    + 'el.textContent=[h,m,s].map(function(n){return n<10?"0"+n:n}).join(":")+suf;}'
    + 'tick();setInterval(tick,1000);'
    + '})();<\/script>'
    + '</div>';
};

_RENDERERS['decision_tree'] = function(b) {
  var nodes = b.nodes || b.tree || [];
  var title = b.title || '';

  function renderNode(node, depth) {
    depth = depth || 0;
    var children = node.children || node.branches || [];
    if (!children.length) {
      return '<div style="padding:10px 14px;margin:4px 0;background:#f0fdf4;border:1px solid #86efac;border-radius:8px;font-size:0.875rem;color:#166534;font-weight:500;">✓ ' + _esc(node.text || node.label || '') + '</div>';
    }
    return '<details style="margin:4px 0;"' + (depth === 0 ? ' open' : '') + '>'
      + '<summary style="cursor:pointer;list-style:none;padding:10px 14px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;font-size:0.875rem;font-weight:600;color:#0f172a;user-select:none;">'
      + '▸ ' + _esc(node.text || node.label || node.question || '')
      + '</summary>'
      + '<div style="padding-left:20px;border-left:2px solid #e2e8f0;margin-left:14px;margin-top:4px;">'
      + children.map(function(c) { return renderNode(c, depth + 1); }).join('')
      + '</div></details>';
  }

  return '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:20px;margin:1rem 0;">'
    + (title ? '<div style="font-size:1rem;font-weight:700;color:#111827;margin-bottom:14px;">' + _esc(title) + '</div>' : '')
    + nodes.map(function(n) { return renderNode(n, 0); }).join('')
    + '</div>';
};

_RENDERERS['step_reveal_sequence'] = function(b) {
  var steps = b.steps || [];
  if (!steps.length) return '';
  var uid = Math.random().toString(36).substr(2, 6);
  var css = '<style>';
  steps.forEach(function(_, i) {
    css += '#srs-' + uid + '-' + i + ':checked ~ .srs-nav-' + uid + ' .srs-lbl-' + uid + ':nth-child(' + (i+1) + '){background:#6366f1;color:#fff;border-color:#6366f1;}';
    css += '#srs-' + uid + '-' + i + ':checked ~ .srs-body-' + uid + ' .srs-panel-' + uid + ':nth-child(' + (i+1) + '){display:block;}';
  });
  css += '.srs-panel-' + uid + '{display:none;padding:20px;animation:srs-in-' + uid + ' 0.3s ease;}';
  css += '@keyframes srs-in-' + uid + '{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:none;}}';
  css += '</style>';
  var inputs = steps.map(function(_, i) {
    return '<input type="radio" id="srs-' + uid + '-' + i + '" name="srs-' + uid + '"' + (i===0?' checked':'') + ' style="display:none;">';
  }).join('');
  var nav = '<div class="srs-nav-' + uid + '" style="display:flex;gap:6px;flex-wrap:wrap;padding:12px 16px;border-bottom:1px solid #e5e7eb;">'
    + steps.map(function(s, i) {
        return '<label for="srs-' + uid + '-' + i + '" class="srs-lbl-' + uid + '" style="cursor:pointer;padding:6px 14px;border-radius:20px;border:1px solid #e5e7eb;font-size:0.8rem;font-weight:600;color:#6b7280;transition:all 0.15s;">' + (i+1) + (s.title ? '. ' + _esc(s.title) : '') + '</label>';
      }).join('')
    + '</div>';
  var body = '<div class="srs-body-' + uid + '">'
    + steps.map(function(s) {
        return '<div class="srs-panel-' + uid + '">'
          + (s.title ? '<div style="font-size:1rem;font-weight:700;color:#111827;margin-bottom:10px;">' + _esc(s.title) + '</div>' : '')
          + (s.text || s.content ? '<div style="color:#374151;line-height:1.7;">' + _markdownToHtml(s.text || s.content || '') + '</div>' : '')
          + '</div>';
      }).join('')
    + '</div>';
  return css + '<div style="border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;margin:1rem 0;">'
    + inputs + nav + body + '</div>';
};

_RENDERERS['chat_sequence'] = function(b) {
  var messages = b.messages || [];
  if (!messages.length) return '';
  var html = '<style>@keyframes chat-in{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:none;}}</style>'
    + '<div style="border:1px solid #e5e7eb;border-radius:16px;padding:16px;margin:1rem 0;background:#f9fafb;display:flex;flex-direction:column;gap:12px;">';
  messages.forEach(function(msg, i) {
    var isUser = msg.role === 'user' || msg.align === 'right';
    var delay  = (i * 0.28) + 's';
    html += '<div style="display:flex;flex-direction:column;align-items:' + (isUser?'flex-end':'flex-start') + ';animation:chat-in 0.4s ease ' + delay + ' both;">'
      + '<div style="font-size:0.7rem;color:#9ca3af;margin-bottom:4px;">' + _esc(msg.name || (isUser ? 'You' : 'Assistant')) + '</div>'
      + '<div style="max-width:82%;background:' + (isUser?'#6366f1':'#fff') + ';color:' + (isUser?'#fff':'#1f2937') + ';border-radius:' + (isUser?'16px 4px 16px 16px':'4px 16px 16px 16px') + ';padding:10px 14px;font-size:0.875rem;line-height:1.55;' + (isUser?'':'box-shadow:0 1px 4px rgba(0,0,0,0.07);') + '">' + _markdownToHtml(msg.text || msg.content || '') + '</div>'
      + '</div>';
  });
  return html + '</div>';
};

_RENDERERS['tooltip_glossary'] = function(b) {
  var terms = b.terms || b.items || [];
  var intro = b.text || b.intro || '';
  return '<style>.tg-term{position:relative;cursor:help;color:#6366f1;font-weight:600;border-bottom:1px dashed #6366f1;}'
    + '.tg-tip{display:none;position:absolute;bottom:120%;left:50%;transform:translateX(-50%);background:#1f2937;color:#fff;font-size:0.78rem;padding:6px 12px;border-radius:8px;white-space:nowrap;z-index:20;box-shadow:0 4px 14px rgba(0,0,0,0.22);}'
    + '.tg-tip::after{content:"";position:absolute;top:100%;left:50%;transform:translateX(-50%);border:5px solid transparent;border-top-color:#1f2937;}'
    + '.tg-term:hover .tg-tip{display:block;}</style>'
    + '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:20px;margin:1rem 0;">'
    + (intro ? '<div style="color:#374151;line-height:1.7;margin-bottom:14px;">' + _markdownToHtml(intro) + '</div>' : '')
    + terms.map(function(t) {
        return '<div style="display:flex;gap:14px;align-items:baseline;padding:10px 0;border-bottom:1px solid #f3f4f6;">'
          + '<span class="tg-term" style="flex-shrink:0;min-width:100px;">' + _esc(t.term || t.word || '') + '<span class="tg-tip">' + _esc(t.definition || t.def || '') + '</span></span>'
          + '<span style="color:#6b7280;font-size:0.875rem;">' + _markdownToHtml(t.definition || t.def || '') + '</span>'
          + '</div>';
      }).join('')
    + '</div>';
};

_RENDERERS['focus_lens'] = function(b) {
  var title = b.title || '';
  var text  = b.text || b.content || '';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.fl-wrap-' + uid + '{position:relative;border-radius:16px;overflow:hidden;margin:1rem 0;min-height:140px;}'
    + '.fl-bg-' + uid + '{filter:blur(4px);padding:30px;background:#f3f4f6;opacity:0.7;user-select:none;font-size:0.82rem;color:#9ca3af;line-height:1.8;}'
    + '.fl-lens-' + uid + '{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(255,255,255,0.96);border-radius:14px;padding:22px 30px;box-shadow:0 6px 40px rgba(0,0,0,0.16);max-width:80%;text-align:center;z-index:2;}'
    + '</style>'
    + '<div class="fl-wrap-' + uid + '">'
    + '<div class="fl-bg-' + uid + '">Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam quis nostrud exercitation ullamco laboris.</div>'
    + '<div class="fl-lens-' + uid + '">'
    + (title ? '<div style="font-size:1rem;font-weight:700;color:#111827;margin-bottom:8px;">' + _esc(title) + '</div>' : '')
    + (text  ? '<div style="font-size:0.875rem;color:#374151;line-height:1.6;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div></div>';
};

// ── Gap atoms ────────────────────────────────────────────────────────────────

_RENDERERS['terminal_boot'] = function(b) {
  var lines = b.lines || [];
  var title = b.title || '';
  var speed = parseInt(b.speed || 380, 10);
  var uid = Math.random().toString(36).substr(2, 6);
  var linesHtml = lines.map(function(line, i) {
    var l = String(line);
    var isOk  = l.indexOf('✓') > -1 || l.indexOf('OK') > -1 || l.indexOf('ok') > -1;
    var isErr = l.indexOf('✗') > -1 || l.indexOf('ERR') > -1 || l.indexOf('FAIL') > -1;
    var col   = isOk ? '#22c55e' : isErr ? '#f87171' : '#94a3b8';
    return '<div id="tb-' + uid + '-' + i + '" style="opacity:0;line-height:1.9;color:' + col + ';">'
      + '<span style="color:#475569;margin-right:10px;user-select:none;">$</span>' + _esc(l) + '</div>';
  }).join('');
  return '<div style="background:#0a0f1e;border:1px solid #1e293b;border-radius:12px;padding:20px 24px;margin:1rem 0;font-family:\'Courier New\',monospace;font-size:0.84rem;">'
    + (title ? '<div style="font-size:0.7rem;font-weight:700;color:#334155;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:14px;">' + _esc(title) + '</div>' : '')
    + '<div>' + linesHtml + '</div>'
    + '<span id="tb-cur-' + uid + '" style="display:inline-block;width:8px;height:14px;background:#22c55e;vertical-align:middle;margin-left:2px;animation:tb-bl-' + uid + ' 1s step-end infinite;"></span>'
    + '<style>@keyframes tb-bl-' + uid + '{0%,100%{opacity:1;}50%{opacity:0;}}</style>'
    + '<script>(function(){'
    + 'var els=[];for(var i=0;i<' + lines.length + ';i++){var el=document.getElementById("tb-' + uid + '-"+i);if(el)els.push(el);}'
    + 'var cur=document.getElementById("tb-cur-' + uid + '");var i=0;'
    + 'function next(){if(i<els.length){els[i].style.opacity="1";i++;setTimeout(next,' + speed + ');}else if(cur){cur.style.display="none";}}'
    + 'setTimeout(next,400);'
    + '})();<\/script>'
    + '</div>';
};

_RENDERERS['stagger_list'] = function(b) {
  var items = b.items || [];
  var dir   = b.direction || 'up';
  var gap   = parseFloat(b.stagger !== undefined ? b.stagger : 0.1);
  var uid = Math.random().toString(36).substr(2, 6);
  var startT = dir==='left'?'translateX(-22px)':dir==='right'?'translateX(22px)':dir==='down'?'translateY(-14px)':'translateY(16px)';
  return '<style>@keyframes sl-' + uid + '{from{opacity:0;transform:' + startT + ';}to{opacity:1;transform:none;}}</style>'
    + '<div style="margin:1rem 0;display:flex;flex-direction:column;gap:8px;">'
    + items.map(function(item, i) {
        var delay = (i * gap) + 's';
        var base  = 'opacity:0;animation:sl-' + uid + ' 0.45s ease ' + delay + ' both;';
        if (typeof item === 'string') {
          return '<div style="' + base + 'padding:10px 14px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;font-size:0.9rem;color:#374151;">' + _markdownToHtml(item) + '</div>';
        }
        var icon = item.icon || '•';
        var text = item.text || item.label || '';
        var sub  = item.sub  || item.description || '';
        return '<div style="' + base + 'padding:12px 16px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;display:flex;gap:12px;align-items:flex-start;">'
          + '<span style="font-size:1.2rem;flex-shrink:0;line-height:1.4;">' + _esc(icon) + '</span>'
          + '<div><div style="font-size:0.9rem;font-weight:600;color:#111827;">' + _esc(text) + '</div>'
          + (sub ? '<div style="font-size:0.8rem;color:#6b7280;margin-top:2px;">' + _esc(sub) + '</div>' : '')
          + '</div></div>';
      }).join('')
    + '</div>';
};

_RENDERERS['liquid_button'] = function(b) {
  var label = b.text || b.label || b.title || 'Action';
  var color = b.color || '#6366f1';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.lq-' + uid + '{background:' + _esc(color) + ';color:#fff;font-weight:700;font-size:0.95rem;padding:14px 36px;border:none;border-radius:50%;cursor:pointer;transition:border-radius 0.45s cubic-bezier(0.34,1.56,0.64,1),transform 0.2s ease,box-shadow 0.2s ease;box-shadow:0 4px 22px ' + _esc(color) + '55;}'
    + '.lq-' + uid + ':hover{border-radius:14px;transform:scale(1.05);box-shadow:0 6px 30px ' + _esc(color) + '77;}'
    + '.lq-' + uid + ':active{transform:scale(0.96);border-radius:50%;}'
    + '</style>'
    + '<div style="margin:1rem 0;text-align:center;"><button class="lq-' + uid + '">' + _esc(label) + '</button></div>';
};

_RENDERERS['highlight_sweep'] = function(b) {
  var text  = b.text  || b.content || '';
  var color = b.color || '#fef08a';
  var delay = parseFloat(b.delay !== undefined ? b.delay : 0.4);
  var size  = b.size  || '1.05rem';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.hs-' + uid + '{background:linear-gradient(90deg,' + _esc(color) + ' 50%,transparent 50%);background-size:201% 100%;background-position:100% 0;animation:hs-' + uid + ' 0.75s ease ' + delay + 's forwards;padding:1px 3px;border-radius:3px;}'
    + '@keyframes hs-' + uid + '{to{background-position:0% 0;}}'
    + '</style>'
    + '<div style="margin:1rem 0;font-size:' + _esc(size) + ';line-height:1.75;color:#1f2937;">'
    + '<span class="hs-' + uid + '">' + _esc(text) + '</span>'
    + '</div>';
};

_RENDERERS['progress_reveal'] = function(b) {
  var value  = parseFloat(b.value !== undefined ? b.value : (b.percent !== undefined ? b.percent : 0));
  var label  = b.label || b.title || '';
  var color  = b.color || '#6366f1';
  var suffix = b.suffix !== undefined ? b.suffix : '%';
  var height = parseInt(b.height || 10, 10);
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div id="pr-wrap-' + uid + '" style="margin:1rem 0;">'
    + '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px;">'
    + (label ? '<span style="font-size:0.875rem;font-weight:600;color:#374151;">' + _esc(label) + '</span>' : '<span></span>')
    + '<span id="pr-val-' + uid + '" style="font-size:0.875rem;font-weight:700;color:' + _esc(color) + ';">0' + _esc(String(suffix)) + '</span>'
    + '</div>'
    + '<div style="height:' + height + 'px;background:#f3f4f6;border-radius:999px;overflow:hidden;">'
    + '<div id="pr-bar-' + uid + '" style="height:100%;width:0%;background:' + _esc(color) + ';border-radius:999px;transition:width 1.3s cubic-bezier(0.34,1.1,0.64,1);"></div>'
    + '</div>'
    + '<script>(function(){'
    + 'var wrap=document.getElementById("pr-wrap-' + uid + '");'
    + 'var bar=document.getElementById("pr-bar-' + uid + '");'
    + 'var val=document.getElementById("pr-val-' + uid + '");'
    + 'var target=' + value + ';var suf="' + _esc(String(suffix)).replace(/"/g,'\\"') + '";var done=false;'
    + 'function run(){if(done)return;done=true;'
    + 'bar.style.width=Math.min(target,100)+"%";'
    + 'var t0=null,dur=1300;'
    + 'function step(ts){if(!t0)t0=ts;var p=Math.min((ts-t0)/dur,1);val.textContent=Math.round(target*p)+suf;if(p<1)requestAnimationFrame(step);}'
    + 'requestAnimationFrame(step);}'
    + 'if("IntersectionObserver" in window){new IntersectionObserver(function(es,ob){if(es[0].isIntersecting){run();ob.disconnect();}},{threshold:0.3}).observe(wrap);}else{run();}'
    + '})();<\/script>'
    + '</div>';
};

// ── High-impact visual atoms ─────────────────────────────────────────────────

_RENDERERS['big_reveal'] = function(b) {
  var text  = b.text  || b.value || b.label || '';
  var sub   = b.sub   || b.subtitle || '';
  var color = b.color || '#1f2937';
  var size  = b.size  || '5rem';
  var delay = parseFloat(b.delay !== undefined ? b.delay : 0.1);
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>@keyframes br-' + uid + '{from{opacity:0;transform:scale(0.35);}to{opacity:1;transform:scale(1);}}</style>'
    + '<div style="text-align:center;padding:44px 24px;margin:1rem 0;">'
    + '<div style="font-size:' + _esc(size) + ';font-weight:900;color:' + _esc(color) + ';line-height:1.05;animation:br-' + uid + ' 0.75s cubic-bezier(0.34,1.56,0.64,1) ' + delay + 's both;">' + _esc(text) + '</div>'
    + (sub ? '<div style="font-size:1.05rem;color:#6b7280;margin-top:14px;font-weight:500;animation:br-' + uid + ' 0.75s cubic-bezier(0.34,1.56,0.64,1) ' + (delay+0.18) + 's both;">' + _esc(sub) + '</div>' : '')
    + '</div>';
};

_RENDERERS['kinetic_headline'] = function(b) {
  var text  = b.text || b.title || '';
  var size  = b.size  || '2.6rem';
  var color = b.color || '#111827';
  var gap   = parseFloat(b.stagger !== undefined ? b.stagger : 0.08);
  var style = b.style || 'up';
  var uid = Math.random().toString(36).substr(2, 6);
  var fromT = style==='down'?'translateY(-22px)':style==='scale'?'scale(0.5)':style==='fade'?'none':'translateY(26px)';
  var words = text.split(' ');
  return '<style>@keyframes kh-' + uid + '{from{opacity:0;transform:' + fromT + ';}to{opacity:1;transform:none;}}</style>'
    + '<div style="margin:1rem 0;font-size:' + _esc(size) + ';font-weight:800;color:' + _esc(color) + ';line-height:1.2;">'
    + words.map(function(w, i) {
        return '<span style="display:inline-block;opacity:0;animation:kh-' + uid + ' 0.55s ease ' + (i*gap) + 's both;margin-right:0.22em;">' + _esc(w) + '</span>';
      }).join('')
    + '</div>';
};

_RENDERERS['text_reveal_mask'] = function(b) {
  var text  = b.text  || b.title || '';
  var size  = b.size  || '2rem';
  var color = b.color || '#111827';
  var delay = parseFloat(b.delay !== undefined ? b.delay : 0.2);
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>@keyframes trm-' + uid + '{from{clip-path:inset(0 100% 0 0);}to{clip-path:inset(0 0% 0 0);}}</style>'
    + '<div style="margin:1rem 0;overflow:hidden;">'
    + '<div style="font-size:' + _esc(size) + ';font-weight:800;color:' + _esc(color) + ';line-height:1.3;animation:trm-' + uid + ' 1s cubic-bezier(0.77,0,0.175,1) ' + delay + 's both;">' + _esc(text) + '</div>'
    + '</div>';
};

_RENDERERS['split_reveal'] = function(b) {
  var title = b.title || '';
  var text  = b.text  || b.content || '';
  var color = b.color || '#6366f1';
  var delay = parseFloat(b.delay !== undefined ? b.delay : 0.2);
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.sr-t-' + uid + '{position:absolute;top:0;left:0;right:0;height:51%;background:' + _esc(color) + ';z-index:2;animation:sr-top-' + uid + ' 0.75s cubic-bezier(0.77,0,0.175,1) ' + delay + 's both;}'
    + '.sr-b-' + uid + '{position:absolute;bottom:0;left:0;right:0;height:51%;background:' + _esc(color) + ';z-index:2;animation:sr-bot-' + uid + ' 0.75s cubic-bezier(0.77,0,0.175,1) ' + delay + 's both;}'
    + '@keyframes sr-top-' + uid + '{from{transform:translateY(0);}to{transform:translateY(-100%);}}'
    + '@keyframes sr-bot-' + uid + '{from{transform:translateY(0);}to{transform:translateY(100%);}}'
    + '</style>'
    + '<div style="position:relative;border-radius:16px;overflow:hidden;margin:1rem 0;">'
    + '<div style="padding:32px;background:#fff;border:1px solid #e5e7eb;border-radius:16px;">'
    + (title ? '<div style="font-size:1.2rem;font-weight:700;color:#111827;margin-bottom:10px;">' + _esc(title) + '</div>' : '')
    + (text  ? '<div style="color:#374151;line-height:1.7;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div>'
    + '<div class="sr-t-' + uid + '"></div>'
    + '<div class="sr-b-' + uid + '"></div>'
    + '</div>';
};

_RENDERERS['mesh_gradient'] = function(b) {
  var title  = b.title  || '';
  var text   = b.text   || b.content || '';
  var bg     = b.bg     || '#0f0a1e';
  var colors = b.colors || ['#f43f5e','#6366f1','#22d3ee','#f59e0b'];
  var positions = ['12% 18%','82% 8%','18% 82%','78% 78%','50% 45%'];
  var gradients = colors.map(function(c, i) {
    return 'radial-gradient(ellipse 55% 45% at ' + positions[i % positions.length] + ',' + _esc(c) + '44,transparent)';
  }).join(',');
  return '<div style="border-radius:20px;overflow:hidden;padding:44px 36px;margin:1rem 0;background:' + _esc(bg) + ';background-image:' + gradients + ';">'
    + (title ? '<div style="font-size:1.3rem;font-weight:800;color:#fff;margin-bottom:12px;">' + _esc(title) + '</div>' : '')
    + (text  ? '<div style="color:rgba(255,255,255,0.82);line-height:1.75;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div>';
};

_RENDERERS['marquee_strip'] = function(b) {
  var items = b.items || b.tags || b.words || [];
  var speed = parseInt(b.speed || 28, 10);
  var bg    = b.bg    || '#0f172a';
  var color = b.color || '#94a3b8';
  var sep   = b.separator || '·';
  var uid = Math.random().toString(36).substr(2, 6);
  var itemHtml = items.map(function(item) {
    var label = typeof item === 'string' ? item : (item.text || item.label || '');
    var icon  = typeof item === 'object' ? (item.icon || '') : '';
    return '<span style="padding:0 24px;white-space:nowrap;">' + (icon ? _esc(icon) + ' ' : '') + _esc(label) + ' <span style="opacity:0.3;margin-left:24px;">' + _esc(sep) + '</span></span>';
  }).join('');
  return '<style>'
    + '.mq-' + uid + '{display:flex;width:max-content;animation:mq-' + uid + ' ' + speed + 's linear infinite;}'
    + '.mq-' + uid + ':hover{animation-play-state:paused;}'
    + '@keyframes mq-' + uid + '{from{transform:translateX(0);}to{transform:translateX(-50%);}}'
    + '</style>'
    + '<div style="background:' + _esc(bg) + ';border-radius:12px;padding:14px 0;margin:1rem 0;overflow:hidden;color:' + _esc(color) + ';font-size:0.9rem;font-weight:500;">'
    + '<div class="mq-' + uid + '">' + itemHtml + itemHtml + '</div>'
    + '</div>';
};

_RENDERERS['stripe_background'] = function(b) {
  var title  = b.title  || '';
  var text   = b.text   || b.content || '';
  var color1 = b.color1 || '#6366f1';
  var color2 = b.color2 || '#4f46e5';
  var speed  = parseInt(b.speed || 5, 10);
  var uid = Math.random().toString(36).substr(2, 6);
  return '<style>'
    + '.strp-' + uid + '{background:repeating-linear-gradient(45deg,' + _esc(color1) + ',' + _esc(color1) + ' 10px,' + _esc(color2) + ' 10px,' + _esc(color2) + ' 20px);background-size:28px 28px;animation:strp-' + uid + ' ' + speed + 's linear infinite;}'
    + '@keyframes strp-' + uid + '{from{background-position:0 0;}to{background-position:56px 56px;}}'
    + '</style>'
    + '<div class="strp-' + uid + '" style="border-radius:16px;overflow:hidden;padding:40px 32px;margin:1rem 0;">'
    + '<div style="background:rgba(0,0,0,0.38);backdrop-filter:blur(2px);border-radius:12px;padding:24px;">'
    + (title ? '<div style="font-size:1.3rem;font-weight:700;color:#fff;margin-bottom:10px;">' + _esc(title) + '</div>' : '')
    + (text  ? '<div style="color:rgba(255,255,255,0.92);line-height:1.7;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div>'
    + '</div>';
};

_RENDERERS['status_timeline'] = function(b) {
  var events = b.events || b.items || [];
  var title  = b.title || '';
  var uid = Math.random().toString(36).substr(2, 6);
  var dotColors = { done:'#22c55e', active:'#3b82f6', pending:'#d1d5db', error:'#ef4444', warning:'#f59e0b' };
  var bgColors  = { done:'#f0fdf4', active:'#eff6ff', pending:'#f9fafb', error:'#fef2f2', warning:'#fffbeb' };
  var bdColors  = { done:'#86efac', active:'#93c5fd', pending:'#e5e7eb', error:'#fecaca', warning:'#fde68a' };
  var evHtml = events.map(function(ev, i) {
    var status = ev.status || 'pending';
    var dot = dotColors[status] || dotColors.pending;
    var bg  = bgColors[status]  || bgColors.pending;
    var bd  = bdColors[status]  || bdColors.pending;
    var isLast = i === events.length - 1;
    var delay  = (i * 0.14) + 's';
    return '<div style="display:flex;gap:16px;opacity:0;animation:st-' + uid + ' 0.4s ease ' + delay + ' both;">'
      + '<div style="display:flex;flex-direction:column;align-items:center;flex-shrink:0;width:16px;">'
      + '<div style="width:14px;height:14px;border-radius:50%;background:' + dot + ';flex-shrink:0;margin-top:5px;' + (status==='active'?'box-shadow:0 0 0 4px '+dot+'33;':'') + '"></div>'
      + (!isLast ? '<div style="width:2px;flex:1;background:#e5e7eb;margin:4px 0;min-height:16px;"></div>' : '')
      + '</div>'
      + '<div style="background:' + bg + ';border:1px solid ' + bd + ';border-radius:10px;padding:12px 16px;flex:1;margin-bottom:' + (isLast?'0':'10px') + ';">'
      + (ev.title ? '<div style="font-size:0.9rem;font-weight:600;color:#111827;">' + _esc(ev.title) + '</div>' : '')
      + (ev.date  ? '<div style="font-size:0.72rem;color:' + dot + ';font-weight:600;text-transform:uppercase;letter-spacing:0.06em;margin-top:2px;">' + _esc(ev.date) + '</div>' : '')
      + (ev.text  ? '<div style="font-size:0.82rem;color:#6b7280;line-height:1.5;margin-top:5px;">' + _esc(ev.text) + '</div>' : '')
      + '</div>'
      + '</div>';
  }).join('');
  return '<style>@keyframes st-' + uid + '{from{opacity:0;transform:translateX(-14px);}to{opacity:1;transform:none;}}</style>'
    + '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:20px;margin:1rem 0;">'
    + (title ? '<div style="font-size:1rem;font-weight:700;color:#111827;margin-bottom:16px;">' + _esc(title) + '</div>' : '')
    + evHtml + '</div>';
};

_RENDERERS['counter_group'] = function(b) {
  var stats = b.stats || b.items || [];
  var uid = Math.random().toString(36).substr(2, 6);
  var cellsHtml = stats.map(function(stat, i) {
    var val   = parseFloat(stat.value || stat.end || 0);
    var dec   = stat.decimals !== undefined ? parseInt(stat.decimals, 10) : (String(val).indexOf('.')>-1?String(val).split('.')[1].length:0);
    var pre   = stat.prefix  || '';
    var suf   = stat.suffix  || '';
    var label = stat.label   || stat.title || '';
    var color = stat.color   || '#6366f1';
    var notLast = i < stats.length - 1;
    return '<div style="flex:1;min-width:90px;text-align:center;padding:0 16px;' + (notLast?'border-right:1px solid #e5e7eb;':'') + '">'
      + '<div id="cg-' + uid + '-' + i + '" data-e="' + val + '" data-d="' + dec + '" data-p="' + _esc(pre) + '" data-s="' + _esc(suf) + '" style="font-size:2.4rem;font-weight:800;color:' + _esc(color) + ';line-height:1;">' + _esc(pre) + '0' + _esc(suf) + '</div>'
      + (label ? '<div style="font-size:0.78rem;color:#6b7280;font-weight:500;margin-top:6px;">' + _esc(label) + '</div>' : '')
      + '</div>';
  }).join('');
  return '<div id="cg-wrap-' + uid + '" style="border:1px solid #e5e7eb;border-radius:16px;padding:28px 8px;margin:1rem 0;display:flex;flex-wrap:wrap;gap:0;background:#fff;align-items:center;">'
    + cellsHtml
    + '</div>'
    + '<script>(function(){'
    + 'var wrap=document.getElementById("cg-wrap-' + uid + '");'
    + 'var n=' + stats.length + ';var els=[];for(var i=0;i<n;i++){var el=document.getElementById("cg-' + uid + '-"+i);if(el)els.push(el);}'
    + 'var done=false,dur=1600;'
    + 'function run(){if(done)return;done=true;var t0=null;'
    + 'function step(ts){if(!t0)t0=ts;var p=Math.min((ts-t0)/dur,1);var ease=p<0.5?2*p*p:1-Math.pow(-2*p+2,2)/2;'
    + 'els.forEach(function(el){var e=parseFloat(el.dataset.e||0),d=parseInt(el.dataset.d||0),p2=el.dataset.p||"",s=el.dataset.s||"";el.textContent=p2+(e*ease).toFixed(d)+s;});'
    + 'if(p<1)requestAnimationFrame(step);}'
    + 'requestAnimationFrame(step);}'
    + 'if("IntersectionObserver" in window){new IntersectionObserver(function(es,ob){if(es[0].isIntersecting){run();ob.disconnect();}},{threshold:0.3}).observe(wrap);}else{run();}'
    + '})();<\/script>';
};

_RENDERERS['orbit_diagram'] = function(b) {
  var center = b.center || 'Core';
  var nodes  = b.nodes  || b.items || [];
  var color  = b.color  || '#6366f1';
  var speed  = parseInt(b.speed || 10, 10);
  var uid = Math.random().toString(36).substr(2, 6);
  var n = Math.max(nodes.length, 1);
  var radius = 95;
  var size = 280;
  var cx = size / 2, cy = size / 2;
  var nodeElems = nodes.map(function(node, i) {
    var angle = (i / n) * 2 * Math.PI - Math.PI / 2;
    var x = Math.round(cx + Math.cos(angle) * radius);
    var y = Math.round(cy + Math.sin(angle) * radius);
    var label  = typeof node === 'string' ? node : (node.label || node.text || '');
    var nc     = typeof node === 'object' && node.color ? node.color : color;
    return '<div style="position:absolute;left:' + x + 'px;top:' + y + 'px;transform:translate(-50%,-50%);background:' + _esc(nc) + ';color:#fff;font-size:0.7rem;font-weight:700;padding:5px 11px;border-radius:20px;white-space:nowrap;box-shadow:0 2px 10px rgba(0,0,0,0.15);z-index:3;">' + _esc(label) + '</div>';
  }).join('');
  var svgLines = nodes.map(function(_, i) {
    var angle = (i / n) * 2 * Math.PI - Math.PI / 2;
    return '<line x1="' + cx + '" y1="' + cy + '" x2="' + Math.round(cx+Math.cos(angle)*radius) + '" y2="' + Math.round(cy+Math.sin(angle)*radius) + '" stroke="' + _esc(color) + '" stroke-width="1" opacity="0.18"/>';
  }).join('');
  return '<style>@keyframes orb-dash-' + uid + '{to{stroke-dashoffset:-24;}}</style>'
    + '<div style="display:flex;justify-content:center;margin:1rem 0;">'
    + '<div style="position:relative;width:' + size + 'px;height:' + size + 'px;">'
    + '<svg style="position:absolute;inset:0;width:100%;height:100%;" viewBox="0 0 ' + size + ' ' + size + '" xmlns="http://www.w3.org/2000/svg">'
    + svgLines
    + '<circle cx="' + cx + '" cy="' + cy + '" r="' + radius + '" fill="none" stroke="' + _esc(color) + '" stroke-width="1.5" stroke-dasharray="5 7" opacity="0.4" style="animation:orb-dash-' + uid + ' ' + (speed/4) + 's linear infinite;"/>'
    + '</svg>'
    + nodeElems
    + '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);background:' + _esc(color) + ';color:#fff;font-weight:700;font-size:0.85rem;width:68px;height:68px;border-radius:50%;display:flex;align-items:center;justify-content:center;text-align:center;box-shadow:0 4px 22px ' + _esc(color) + '55;z-index:5;">' + _esc(center) + '</div>'
    + '</div></div>';
};

_RENDERERS['noise_card'] = function(b) {
  var title = b.title || '';
  var text  = b.text  || b.content || '';
  var bg    = b.bg    || '#1e1b4b';
  var color = b.color || '#fff';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="position:relative;border-radius:16px;overflow:hidden;padding:28px;margin:1rem 0;background:' + _esc(bg) + ';">'
    + '<svg width="0" height="0" style="position:absolute;pointer-events:none;">'
    + '<defs><filter id="nf-' + uid + '" x="0%" y="0%" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.7" numOctaves="4" stitchTiles="stitch" result="noise"/><feColorMatrix in="noise" type="saturate" values="0" result="grey"/><feBlend in="SourceGraphic" in2="grey" mode="overlay" result="blend"/><feComposite in="blend" in2="SourceGraphic" operator="in"/></filter></defs>'
    + '</svg>'
    + '<div style="position:absolute;inset:0;opacity:0.055;background:#aaa;filter:url(#nf-' + uid + ');pointer-events:none;"></div>'
    + '<div style="position:relative;z-index:1;">'
    + (title ? '<div style="font-size:1.1rem;font-weight:700;color:' + _esc(color) + ';margin-bottom:10px;">' + _esc(title) + '</div>' : '')
    + (text  ? '<div style="color:' + _esc(color) + 'cc;line-height:1.7;font-size:0.9rem;">' + _markdownToHtml(text) + '</div>' : '')
    + '</div>'
    + '</div>';
};

_RENDERERS['comparison_morph'] = function(b) {
  var before = b.before || {};
  var after  = b.after  || {};
  var title  = b.title  || '';
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="margin:1rem 0;">'
    + (title ? '<div style="font-size:1rem;font-weight:700;color:#111827;margin-bottom:12px;">' + _esc(title) + '</div>' : '')
    + '<style>'
    + '.cm-after-' + uid + '{position:absolute;top:0;left:0;width:100%;height:100%;padding:22px;background:#f0fdf4;border:2px solid #86efac;border-radius:12px;clip-path:inset(0 50% 0 0);box-sizing:border-box;overflow:hidden;}'
    + '.cm-hdl-' + uid + '{position:absolute;top:0;left:50%;transform:translateX(-50%);height:100%;width:2px;background:#6366f1;pointer-events:none;}'
    + '.cm-hdl-' + uid + '::after{content:"\\u29FA";position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);background:#6366f1;color:#fff;font-size:0.75rem;padding:4px 8px;border-radius:20px;white-space:nowrap;}'
    + '</style>'
    + '<div style="position:relative;border-radius:12px;overflow:hidden;">'
    + '<div style="padding:22px;background:#fef2f2;border:2px solid #fecaca;border-radius:12px;">'
    + '<div style="font-size:0.72rem;font-weight:700;color:#dc2626;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">' + _esc(before.label || 'Before') + '</div>'
    + '<div style="font-size:0.9rem;color:#374151;line-height:1.65;">' + _markdownToHtml(before.text || '') + '</div>'
    + '</div>'
    + '<div class="cm-after-' + uid + '" id="cm-after-' + uid + '">'
    + '<div style="font-size:0.72rem;font-weight:700;color:#16a34a;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">' + _esc(after.label || 'After') + '</div>'
    + '<div style="font-size:0.9rem;color:#374151;line-height:1.65;">' + _markdownToHtml(after.text || '') + '</div>'
    + '</div>'
    + '<div class="cm-hdl-' + uid + '" id="cm-hdl-' + uid + '"></div>'
    + '</div>'
    + '<input type="range" min="0" max="100" value="50" style="width:100%;margin-top:10px;accent-color:#6366f1;cursor:pointer;"'
    + ' oninput="(function(v){document.getElementById(\'cm-after-' + uid + '\').style.clipPath=\'inset(0 \'+(100-v)+\'% 0 0)\';document.getElementById(\'cm-hdl-' + uid + '\').style.left=v+\'%\';})(this.value)">'
    + '</div>';
};

// word_cloud — static, local-input, or live Google Sheets backed
// Schema: { type:"word_cloud", words:[{text,weight}], sheet_url:"...", write_url:"...", poll:5, palette:["#..."], placeholder:"..." }
_RENDERERS['word_cloud'] = function(b) {
  var uid         = Math.random().toString(36).substr(2, 6);
  var palette     = b.palette || ['#6366f1','#8b5cf6','#ec4899','#f59e0b','#10b981','#3b82f6','#ef4444','#14b8a6'];
  var poll        = parseInt(b.poll || 5, 10) * 1000;
  var sheetUrl    = b.sheet_url || '';
  var writeUrl    = b.write_url || '';
  var ph          = b.placeholder || 'Type a word…';
  var accent      = b.accent || '#6366f1';
  var staticWords = b.words || [];
  var paletteJson = JSON.stringify(palette);
  var staticJson  = JSON.stringify(staticWords.map(function(w) {
    return { text: String(w.text || w.word || w.label || ''), weight: Number(w.weight || w.count || w.size || 1) };
  }));

  return '<style>'
    // cloud canvas: relative container, words absolutely placed
    + '#wc-' + uid + '{position:relative;width:100%;min-height:calc(100vh - 80px);overflow:hidden;}'
    + '#wc-' + uid + ' span{position:absolute;display:inline-block;border-radius:6px;padding:3px 10px;cursor:default;transition:transform 0.25s,opacity 0.25s;white-space:nowrap;}'
    + '#wc-' + uid + ' span:hover{transform:scale(1.22) rotate(0deg)!important;opacity:0.85;z-index:10;}'
    + '@keyframes wc-in-' + uid + '{from{opacity:0;transform:scale(0.3) rotate(var(--r));}to{opacity:1;transform:scale(1) rotate(var(--r));}}'
    // fixed bottom input bar — same purple as accent
    + '#wc-bar-' + uid + '{position:fixed;bottom:0;left:0;right:0;display:flex;gap:10px;padding:14px 20px;'
    + 'background:' + accent + ';z-index:9999;box-shadow:0 -4px 24px rgba(0,0,0,0.18);}'
    + '#wc-inp-' + uid + '{flex:1;padding:11px 16px;border:none;border-radius:10px;font-size:1rem;outline:none;'
    + 'background:rgba(255,255,255,0.18);color:#fff;caret-color:#fff;}'
    + '#wc-inp-' + uid + '::placeholder{color:rgba(255,255,255,0.6);}'
    + '#wc-inp-' + uid + ':focus{background:rgba(255,255,255,0.28);}'
    + '#wc-btn-' + uid + '{padding:11px 22px;background:#fff;color:' + accent + ';border:none;border-radius:10px;'
    + 'font-size:1rem;font-weight:700;cursor:pointer;transition:opacity 0.2s;white-space:nowrap;}'
    + '#wc-btn-' + uid + ':hover{opacity:0.88;}'
    + (sheetUrl ? '#wc-badge-' + uid + '{position:fixed;top:10px;right:14px;font-size:0.68rem;color:#9ca3af;z-index:9999;}' : '')
    + '</style>'
    + '<div id="wc-' + uid + '" data-static=\'' + staticJson.replace(/'/g, '&#39;') + '\' data-palette=\'' + paletteJson.replace(/'/g, '&#39;') + '\'></div>'
    + (sheetUrl ? '<div id="wc-badge-' + uid + '">● live</div>' : '')
    + '<div id="wc-bar-' + uid + '">'
    + '<input id="wc-inp-' + uid + '" type="text" placeholder="' + _esc(ph) + '" maxlength="40" autocomplete="off">'
    + '<button id="wc-btn-' + uid + '">Add ↵</button>'
    + '</div>'
    + '<script>(function(){'
    + 'var el=document.getElementById("wc-' + uid + '");'
    + 'var inp=document.getElementById("wc-inp-' + uid + '");'
    + 'var btn=document.getElementById("wc-btn-' + uid + '");'
    + 'var palette=JSON.parse(el.getAttribute("data-palette"));'
    + 'var staticWords=JSON.parse(el.getAttribute("data-static"));'
    + 'var sheetUrl=' + JSON.stringify(sheetUrl) + ';'
    + 'var writeUrl=' + JSON.stringify(writeUrl) + ';'
    + 'var poll=' + poll + ';'
    + 'var localWords=[];'

    + 'function rnd(min,max){return min+Math.random()*(max-min);}'

    + 'function render(words){'
    + '  if(!words||!words.length)return;'
    + '  var max=words.reduce(function(m,w){return Math.max(m,w.weight);},1);'
    + '  el.innerHTML="";'
    + '  var W=el.offsetWidth||window.innerWidth;'
    + '  var H=el.offsetHeight||Math.max(400,window.innerHeight-100);'
    + '  words.forEach(function(w,i){'
    + '    var norm=w.weight/max;'
    + '    var size=(0.8+norm*2.8).toFixed(2);'         // wider range: 0.8–3.6rem
    + '    var rot=rnd(-42,42).toFixed(1);'              // ±42° rotation
    + '    var col=palette[Math.floor(Math.random()*palette.length)];' // fully random color
    + '    var opacity=(0.55+Math.random()*0.45).toFixed(2);'          // random opacity 0.55–1
    + '    var left=rnd(3,88).toFixed(1);'
    + '    var top=rnd(2,88).toFixed(1);'
    + '    var sp=document.createElement("span");'
    + '    sp.textContent=w.text;'
    + '    sp.style.cssText="font-size:"+size+"rem;font-weight:"+(norm>0.5?"700":"400")+";color:"+col'
    + '      +";--r:"+rot+"deg;background:"+col+"22;opacity:"+opacity'
    + '      +";left:"+left+"%;top:"+top+"%;transform:rotate("+rot+"deg)"'
    + '      +";animation:wc-in-' + uid + ' 0.55s cubic-bezier(0.34,1.56,0.64,1) "+(i*0.035).toFixed(2)+"s both;";'
    + '    el.appendChild(sp);'
    + '  });'
    + '}'

    + 'function mergeLocal(remote){'
    + '  var map={};'
    + '  remote.forEach(function(w){map[w.text.toLowerCase()]=w;});'
    + '  localWords.forEach(function(w){'
    + '    var k=w.text.toLowerCase();'
    + '    if(!map[k])map[k]={text:w.text,weight:1};'
    + '  });'
    + '  return Object.values(map).sort(function(a,b){return b.weight-a.weight;});'
    + '}'

    + 'function parseCSV(csv){'
    + '  var lines=csv.trim().split("\\n").slice(1);'
    + '  var map={};'
    + '  lines.forEach(function(l){'
    + '    var cols=l.split(",");'
    + '    var word=(cols[0]||"").trim().replace(/^"|"$/g,"");'
    + '    var cnt=cols[1]?parseInt(cols[1].trim(),10):1;'
    + '    if(word)map[word]=(map[word]||0)+cnt;'
    + '  });'
    + '  return Object.keys(map).map(function(k){return{text:k,weight:map[k]};}).sort(function(a,b){return b.weight-a.weight;});'
    + '}'

    + 'function parseJSON(data){'
    + '  var arr=Array.isArray(data)?data:(data.words||[]);'
    + '  return arr.map(function(w){return{text:String(w.text||w.word||""),weight:Number(w.weight||w.count||1)};});'
    + '}'

    + 'function fetchAndRender(){'
    + '  fetch(sheetUrl)'
    + '  .then(function(r){var ct=r.headers.get("content-type")||"";return ct.indexOf("json")>-1?r.json().then(parseJSON):r.text().then(parseCSV);})'
    + '  .then(function(words){render(mergeLocal(words));})'
    + '  .catch(function(){});'
    + '}'

    + 'function submit(){'
    + '  var word=inp.value.trim();'
    + '  if(!word)return;'
    + '  inp.value="";inp.focus();'
    + '  localWords.push({text:word,weight:1});'
    + '  var cur=[];'
    + '  el.querySelectorAll("span").forEach(function(s){cur.push({text:s.textContent,weight:1});});'
    + '  render(mergeLocal(cur));'
    + '  if(writeUrl){'
    + '    fetch(writeUrl+"?word="+encodeURIComponent(word),{method:"GET",mode:"no-cors"}).catch(function(){});'
    + '  }'
    + '}'

    + 'btn.addEventListener("click",submit);'
    + 'inp.addEventListener("keydown",function(e){if(e.key==="Enter")submit();});'
    + 'if(staticWords.length){render(staticWords);}'
    + 'if(sheetUrl){fetchAndRender();setInterval(fetchAndRender,poll);}'
    + '})();<\/script>';
};

// quiz_set — multi-question MCQ with score, pass/fail result, badge, and URL branching
// Schema: { type:"quiz_set", title:"...", pass_score:70, accent:"#6366f1",
//   questions:[{question,options:[],correct(0-idx),explanation}],
//   on_pass:{title,message,badge,icon,url}, on_fail:{title,message,url} }
// on_pass.url / on_fail.url: navigate to a different encoded schema URL on result — enables static branching
_RENDERERS['quiz_set'] = function(b) {
  var uid       = Math.random().toString(36).substr(2, 6);
  var title     = b.title || 'Knowledge Check';
  var questions = b.questions || [];
  var passScore = parseInt(b.pass_score || 70, 10);
  var accent    = b.accent || '#6366f1';
  var onPass    = b.on_pass || {};
  var onFail    = b.on_fail || {};
  var qJson     = JSON.stringify(questions);
  var onPassJ   = JSON.stringify(onPass);
  var onFailJ   = JSON.stringify(onFail);

  return '<style>'
    + '#qs-wrap-' + uid + '{max-width:680px;margin:1.5rem auto;padding:28px;background:#fff;border-radius:14px;box-shadow:0 2px 24px rgba(0,0,0,0.07);}'
    + '#qs-title-' + uid + '{font-size:0.7rem;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:14px;}'
    + '#qs-prog-' + uid + '{height:5px;background:#e5e7eb;border-radius:3px;margin-bottom:22px;}'
    + '#qs-bar-' + uid + '{height:100%;background:' + accent + ';border-radius:3px;width:0%;transition:width 0.45s cubic-bezier(0.4,0,0.2,1);}'
    + '#qs-num-' + uid + '{font-size:0.72rem;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;}'
    + '#qs-q-' + uid + '{font-size:1.08rem;font-weight:700;color:#111827;line-height:1.55;margin-bottom:18px;}'
    + '.qs-o-' + uid + '{display:block;width:100%;text-align:left;padding:12px 16px;margin-bottom:8px;background:#f9fafb;border:2px solid #e5e7eb;border-radius:10px;font-size:0.95rem;cursor:pointer;transition:all 0.15s;font-family:inherit;color:#374151;}'
    + '.qs-o-' + uid + ':hover:not([disabled]){border-color:' + accent + ';background:' + accent + '0d;}'
    + '.qs-ok-' + uid + '{border-color:#10b981!important;background:#ecfdf5!important;color:#065f46!important;font-weight:600;}'
    + '.qs-no-' + uid + '{border-color:#ef4444!important;background:#fef2f2!important;color:#991b1b!important;}'
    + '#qs-exp-' + uid + '{display:none;padding:12px 16px;background:#f0f9ff;border-left:3px solid ' + accent + ';font-size:0.875rem;color:#374151;line-height:1.65;margin:10px 0 14px;border-radius:0 8px 8px 0;}'
    + '#qs-next-' + uid + '{display:none;padding:10px 28px;background:' + accent + ';color:#fff;border:none;border-radius:8px;font-size:0.95rem;font-weight:600;cursor:pointer;font-family:inherit;transition:opacity 0.2s;}'
    + '#qs-next-' + uid + ':hover{opacity:0.87;}'
    + '#qs-result-' + uid + '{display:none;text-align:center;padding:8px 0;}'
    + '.qs-ring-' + uid + '{width:112px;height:112px;border-radius:50%;margin:0 auto 18px;display:flex;align-items:center;justify-content:center;font-size:1.9rem;font-weight:800;}'
    + '#qs-retry-' + uid + '{padding:9px 22px;background:transparent;color:#9ca3af;border:2px solid #e5e7eb;border-radius:8px;font-size:0.88rem;font-weight:600;cursor:pointer;font-family:inherit;margin-top:8px;transition:all 0.2s;}'
    + '#qs-retry-' + uid + ':hover{border-color:#9ca3af;color:#374151;}'
    + '</style>'
    + '<div id="qs-wrap-' + uid + '">'
    + '<div id="qs-title-' + uid + '">' + _esc(title) + '</div>'
    + '<div id="qs-prog-' + uid + '"><div id="qs-bar-' + uid + '"></div></div>'
    + '<div id="qs-num-' + uid + '"></div>'
    + '<div id="qs-q-' + uid + '"></div>'
    + '<div id="qs-opts-' + uid + '"></div>'
    + '<div id="qs-exp-' + uid + '"></div>'
    + '<button id="qs-next-' + uid + '">Next →</button>'
    + '<div id="qs-result-' + uid + '"></div>'
    + '</div>'
    + '<script>(function(){'
    + 'var questions=' + qJson + ';'
    + 'var passScore=' + passScore + ';'
    + 'var accent=' + JSON.stringify(accent) + ';'
    + 'var onPass=' + onPassJ + ';'
    + 'var onFail=' + onFailJ + ';'
    + 'var idx=0,score=0,answered=false;'
    + 'var bar=document.getElementById("qs-bar-' + uid + '");'
    + 'var numEl=document.getElementById("qs-num-' + uid + '");'
    + 'var qEl=document.getElementById("qs-q-' + uid + '");'
    + 'var optsEl=document.getElementById("qs-opts-' + uid + '");'
    + 'var expEl=document.getElementById("qs-exp-' + uid + '");'
    + 'var nextBtn=document.getElementById("qs-next-' + uid + '");'
    + 'var resultEl=document.getElementById("qs-result-' + uid + '");'

    + 'function reset(){'
    + '  idx=0;score=0;answered=false;'
    + '  [numEl,qEl,optsEl].forEach(function(e){e.style.display="";});'
    + '  nextBtn.style.display="none";expEl.style.display="none";'
    + '  resultEl.style.display="none";resultEl.innerHTML="";'
    + '  showQ(0);'
    + '}'

    + 'function showQ(i){'
    + '  answered=false;'
    + '  var q=questions[i];'
    + '  bar.style.width=Math.round((i/questions.length)*100)+"%";'
    + '  numEl.textContent="Question "+(i+1)+" of "+questions.length;'
    + '  qEl.textContent=q.question;'
    + '  expEl.style.display="none";nextBtn.style.display="none";optsEl.innerHTML="";'
    + '  q.options.forEach(function(opt,oi){'
    + '    var btn=document.createElement("button");'
    + '    btn.className="qs-o-' + uid + '";'
    + '    btn.textContent=opt;'
    + '    btn.addEventListener("click",function(){'
    + '      if(answered)return;answered=true;'
    + '      var ok=oi===q.correct;if(ok)score++;'
    + '      btn.classList.add(ok?"qs-ok-' + uid + '":"qs-no-' + uid + '");'
    + '      optsEl.querySelectorAll("button").forEach(function(b,bi){b.disabled=true;if(bi===q.correct)b.classList.add("qs-ok-' + uid + '");});'
    + '      if(q.explanation){expEl.textContent=q.explanation;expEl.style.display="block";}'
    + '      nextBtn.style.display="inline-block";'
    + '      nextBtn.textContent=i===questions.length-1?"See Results →":"Next →";'
    + '    });'
    + '    optsEl.appendChild(btn);'
    + '  });'
    + '}'

    + 'function showResult(){'
    + '  var pct=Math.round((score/questions.length)*100);'
    + '  var pass=pct>=passScore;'
    + '  var col=pass?"#10b981":"#ef4444";'
    + '  var cfg=pass?onPass:onFail;'
    + '  bar.style.width="100%";'
    + '  [numEl,qEl,optsEl,expEl,nextBtn].forEach(function(e){e.style.display="none";});'
    + '  resultEl.style.display="block";'
    + '  resultEl.innerHTML='
    + '    "<div class=\'qs-ring-' + uid + '\' style=\'background:"+col+"1a;color:"+col+";border:3px solid "+col+";\'>"+pct+"%</div>"'
    + '    +"<div style=\'font-size:1.22rem;font-weight:800;color:#111827;margin-bottom:6px;\'>"+(cfg.title||(pass?"Well done!":"Keep going!"))+"</div>"'
    + '    +"<div style=\'font-size:0.88rem;color:#6b7280;margin-bottom:18px;\'>"+score+" of "+questions.length+" correct"+(pass?" · Pass ✓":" · "+passScore+"% needed")+"</div>"'
    + '    +(cfg.message?"<div style=\'font-size:0.88rem;color:#374151;padding:12px 16px;background:#f9fafb;border-radius:8px;margin-bottom:16px;\'>"+cfg.message+"</div>":"")'
    + '    +(pass&&cfg.badge?"<div style=\'display:inline-flex;align-items:center;gap:8px;padding:10px 20px;background:"+col+"1a;border:2px solid "+col+";border-radius:10px;font-weight:700;color:"+col+";font-size:0.95rem;margin-bottom:18px;\'>"+(cfg.icon||"🏆")+" "+cfg.badge+"</div><br>":"")'
    // branch URL button (pass or fail) — if set, show a "Continue →" button that navigates to the next schema URL
    + '    +(cfg.url?"<a href=\'"+cfg.url+"\' style=\'display:inline-block;padding:10px 28px;background:"+col+";color:#fff;border-radius:8px;font-weight:700;font-size:0.95rem;text-decoration:none;margin-bottom:10px;\'>Continue →</a><br>":"")'
    + '    +"<button id=\'qs-retry-' + uid + '\' style=\'margin-top:8px;\'>Try again</button>";'
    + '  var rb=document.getElementById("qs-retry-' + uid + '");'
    + '  if(rb)rb.addEventListener("click",reset);'
    // also save pass/fail to localStorage keyed by title for lightweight progress
    + '  try{var k="qs-"+btoa(unescape(encodeURIComponent(' + JSON.stringify(title) + ')));localStorage.setItem(k,JSON.stringify({pct:pct,pass:pass,ts:Date.now()}));}catch(e){}'
    + '}'

    + 'nextBtn.addEventListener("click",function(){'
    + '  idx++;'
    + '  if(idx<questions.length){showQ(idx);}else{showResult();}'
    + '});'
    + 'showQ(0);'
    + '})();<\/script>';
};
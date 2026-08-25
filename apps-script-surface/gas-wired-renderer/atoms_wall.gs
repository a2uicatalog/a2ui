// atoms_wall.gs — wall_elevation: a deterministic, AI-free masonry wall
// elevation diagram (courses, running/stack bond, cost/weight/build-time
// estimates). Ported from a real prior agent's tested math
// (wall-builder-agent, a Gemini Enterprise A2A demo, found in the
// static-hangout-500821-d3 GCP project's Cloud Run sources, 2026-08-25) --
// see renderers/web_article.py's own wall_elevation section for the
// Python mirror; the two must produce identical numbers for identical
// inputs, not just a similar-looking diagram.
//
// Deliberately AI-free: real semantic parameters in (height_m, width_m,
// block_id, pattern, load_bearing, include_dpc, builders), deterministic
// layout code out. No LLM call anywhere in this render path -- unlike
// freeform_canvas (this file's sibling), which exists specifically for
// content no fixed schema anticipated, a wall elevation is a well-defined,
// recurring shape that doesn't need free-form authoring at all.
//
// _pyRound below matters more than it looks: Python's round() is
// round-half-to-even (banker's rounding), JS's Math.round() always rounds
// half away from zero -- these silently DISAGREE on exact .5 ties (e.g.
// round(2.5): Python gives 2, Math.round gives 3). A parallel Python
// effort ports this same math independently; using plain Math.round here
// risks the two renderers producing different numbers for the same input
// on tie values, which would be a real, hard-to-spot correctness bug, not
// just a style mismatch.

function _pyRound(value, ndigits) {
  ndigits = ndigits || 0;
  var factor = Math.pow(10, ndigits);
  var scaled = value * factor;
  var floor = Math.floor(scaled);
  var diff = scaled - floor;
  var rounded;
  if (diff < 0.5 - 1e-9) rounded = floor;
  else if (diff > 0.5 + 1e-9) rounded = floor + 1;
  else rounded = (floor % 2 === 0) ? floor : floor + 1; // round half to even
  return rounded / factor;
}

var _WALL_BLOCKS = {
  parpaing200: {label: 'Parpaing 500×200×200', unitL: 510, courseH: 210, weight: 18.0, colour: '#8d9499', price: 1.80},
  parpaing150: {label: 'Parpaing 500×200×150', unitL: 510, courseH: 210, weight: 13.5, colour: '#9aa0a6', price: 1.40},
  brique:      {label: 'Brique 220×105×55',    unitL: 230, courseH: 65,  weight: 2.3,  colour: '#c1440e', price: 0.45}
};
var _WALL_PATTERN_LABEL = {running: 'Running bond', stack: 'Stack bond'};
var _WALL_DIM_MIN_M = 0.2, _WALL_DIM_MAX_M = 20.0, _WALL_DIM_STEP_M = 0.2;
var _WALL_ADVISORY_HEIGHT_M = 2.0;
var _WALL_LOAD_BEARING_MIN_WEIGHT_KG = 10.0;
var _WALL_BUILDERS_MIN = 1, _WALL_BUILDERS_MAX = 6;
var _WALL_BLOCKS_PER_BUILDER_HOUR = 12;
var _WALL_HOURS_PER_DAY = 6;
var _WALL_DEFAULT_HEIGHT_M = 2.0;
var _WALL_DEFAULT_WIDTH_M = 3.0;

// Dimension snapping to _WALL_DIM_STEP_M increments, clamped to
// [MIN,MAX] -- mirrors _wall_snap in the Python reference exactly.
function _wallSnap(valueM) {
  var snapped = _pyRound(valueM / _WALL_DIM_STEP_M, 0) * _WALL_DIM_STEP_M;
  var clamped = Math.max(_WALL_DIM_MIN_M, Math.min(_WALL_DIM_MAX_M, snapped));
  return _pyRound(clamped, 1);
}

function _wallSnapBuilders(value) {
  var n = parseFloat(value);
  if (isNaN(n)) n = 2;
  else n = _pyRound(n, 0);
  return Math.max(_WALL_BUILDERS_MIN, Math.min(_WALL_BUILDERS_MAX, n));
}

// Deterministic days-to-build for builder counts 1.._WALL_BUILDERS_MAX.
// Index 0 = 1 builder, etc.
function _wallBuildDaysCurve(totalUnits) {
  var out = [];
  for (var n = _WALL_BUILDERS_MIN; n <= _WALL_BUILDERS_MAX; n++) {
    var days = totalUnits / (_WALL_BLOCKS_PER_BUILDER_HOUR * n) / _WALL_HOURS_PER_DAY;
    out.push(_pyRound(days, 1));
  }
  return out;
}

function _wallCalc(blockId, heightM, widthM, pattern, loadBearing, includeDpc, builders) {
  var b = _WALL_BLOCKS[blockId] || _WALL_BLOCKS.parpaing200;
  heightM = _wallSnap(heightM);
  widthM = _wallSnap(widthM);
  var heightMm = Math.round(_pyRound(heightM * 1000, 0));
  var widthMm = Math.round(_pyRound(widthM * 1000, 0));
  var courses = Math.max(1, Math.ceil(heightMm / b.courseH));
  var perCourse = Math.max(1, Math.ceil(widthMm / b.unitL));
  var total = courses * perCourse;
  var dpcLengthM = includeDpc ? widthM : 0.0;
  var mortarBags = Math.max(1, Math.ceil(total / 30));
  var loadBearingAdvisory = !!loadBearing && b.weight < _WALL_LOAD_BEARING_MIN_WEIGHT_KG;
  var heightAdvisory = heightM > _WALL_ADVISORY_HEIGHT_M;
  var buildersSnapped = _wallSnapBuilders(builders);
  var buildDaysCurve = _wallBuildDaysCurve(total);
  return {
    block: b, blockId: blockId, pattern: pattern,
    heightM: heightM, widthM: widthM, heightMm: heightMm, widthMm: widthMm,
    courses: courses, perCourse: perCourse, totalUnits: total,
    totalWeightKg: _pyRound(total * b.weight, 1),
    totalCost: _pyRound(total * b.price, 2),
    actualHMm: courses * b.courseH, actualWMm: perCourse * b.unitL,
    loadBearing: !!loadBearing, includeDpc: !!includeDpc,
    dpcLengthM: dpcLengthM, mortarBags: mortarBags,
    loadBearingAdvisory: loadBearingAdvisory, heightAdvisory: heightAdvisory,
    builders: buildersSnapped, buildDaysCurve: buildDaysCurve,
    buildDaysSelected: buildDaysCurve[buildersSnapped - _WALL_BUILDERS_MIN]
  };
}

// Deterministic elevation to scale; running vs stack bond honoured.
// Mirrors _wall_svg in the Python reference -- same algorithm, same
// numbers, ported statement-for-statement.
function _wallSvg(calc) {
  var W = 660, H = 400;
  var mx = 40, top = 52, bottom = 344;
  var drawW = W - 2 * mx, drawH = bottom - top;
  var scale = Math.min(drawW / calc.actualWMm, drawH / calc.actualHMm);
  var unitPx = calc.block.unitL * scale;
  var coursePx = calc.block.courseH * scale;
  var wallW = calc.actualWMm * scale;
  var x0 = mx + (drawW - wallW) / 2;
  var gap = Math.max(1.0, Math.min(2.5, coursePx * 0.08));
  var colour = calc.block.colour;

  var parts = [];
  parts.push('<svg xmlns="http://www.w3.org/2000/svg" width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + ' ' + H + '">');
  parts.push('<rect width="' + W + '" height="' + H + '" fill="#f5f6f8"/>');
  parts.push('<rect x="' + x0.toFixed(1) + '" y="' + (bottom - calc.courses * coursePx).toFixed(1) +
    '" width="' + wallW.toFixed(1) + '" height="' + (calc.courses * coursePx).toFixed(1) + '" fill="#d9dbe0"/>');

  for (var c = 0; c < calc.courses; c++) {
    var y = bottom - (c + 1) * coursePx;
    var offset = (calc.pattern === 'running' && c % 2) ? unitPx / 2 : 0.0;
    var x = x0 - offset;
    while (x < x0 + wallW - 0.5) {
      var bx = Math.max(x, x0);
      var bw = Math.min(x + unitPx, x0 + wallW) - bx - gap;
      if (bw > 1) {
        parts.push('<rect x="' + bx.toFixed(1) + '" y="' + (y + gap).toFixed(1) + '" width="' + bw.toFixed(1) +
          '" height="' + (coursePx - gap).toFixed(1) + '" rx="1.5" fill="' + colour + '"/>');
      }
      x += unitPx;
    }
  }

  parts.push('<line x1="' + (x0 - 8).toFixed(1) + '" y1="' + bottom.toFixed(1) + '" x2="' + (x0 + wallW + 8).toFixed(1) +
    '" y2="' + bottom.toFixed(1) + '" stroke="#3c4043" stroke-width="2"/>');
  parts.push('<text x="' + (W / 2).toFixed(0) + '" y="30" text-anchor="middle" ' +
    'font-family="Roboto,Arial,sans-serif" font-size="17" font-weight="700" fill="#202124">' +
    _esc(calc.block.label) + ' · ' + _esc(_WALL_PATTERN_LABEL[calc.pattern]) + '</text>');
  parts.push('<text x="' + (W / 2).toFixed(0) + '" y="' + (bottom + 30).toFixed(0) + '" text-anchor="middle" ' +
    'font-family="Roboto,Arial,sans-serif" font-size="15" fill="#3c4043">' +
    (calc.actualWMm / 1000).toFixed(2) + ' m × ' + (calc.actualHMm / 1000).toFixed(2) + ' m · ' +
    calc.totalUnits + ' units · ' + calc.totalWeightKg.toFixed(0) + ' kg</text>');
  parts.push('</svg>');
  return parts.join('');
}

// A real-data summary row, same purpose as tool_call_card.gs's own
// `block()` helper: legible stats OUTSIDE the SVG, not just the diagram's
// own baked-in title/summary line.
function _wallStatRow(label, value) {
  return '<div style="display:flex;justify-content:space-between;gap:12px;padding:3px 0;font-size:0.82rem;">' +
    '<span style="color:var(--muted,#94a3b8);">' + _esc(label) + '</span>' +
    '<span style="color:var(--text);font-weight:600;">' + _esc(value) + '</span></div>';
}

_RENDERERS['wall_elevation'] = function(b) {
  var blockId = b.block_id || 'parpaing200';
  var pattern = (b.pattern === 'stack') ? 'stack' : 'running';
  var loadBearing = !!b.load_bearing;
  var includeDpc = !!b.include_dpc;
  var heightM = parseFloat(b.height_m);
  var widthM = parseFloat(b.width_m);
  if (isNaN(heightM)) heightM = _WALL_DEFAULT_HEIGHT_M;
  if (isNaN(widthM)) widthM = _WALL_DEFAULT_WIDTH_M;

  var calc = _wallCalc(blockId, heightM, widthM, pattern, loadBearing, includeDpc,
    b.builders !== undefined ? b.builders : 2);

  var advisories = '';
  if (calc.loadBearingAdvisory) {
    advisories += '<div style="margin-top:8px;padding:6px 10px;background:var(--surface2,#f8fafc);' +
      'border-left:3px solid var(--red);border-radius:4px;font-size:0.78rem;color:var(--text);">' +
      'Load-bearing was selected, but ' + _esc(calc.block.label) + ' is a light block for that use -- worth checking with a structural reference.</div>';
  }
  if (calc.heightAdvisory) {
    advisories += '<div style="margin-top:8px;padding:6px 10px;background:var(--surface2,#f8fafc);' +
      'border-left:3px solid var(--accent,#6366f1);border-radius:4px;font-size:0.78rem;color:var(--text);">' +
      'Walls over ' + _WALL_ADVISORY_HEIGHT_M.toFixed(1) + ' m are often subject to local planning/building-control rules -- worth checking.</div>';
  }

  var stats = _wallStatRow('Courses', String(calc.courses)) +
    _wallStatRow('Units per course', String(calc.perCourse)) +
    _wallStatRow('Total units', String(calc.totalUnits)) +
    _wallStatRow('Total weight', calc.totalWeightKg.toFixed(1) + ' kg') +
    _wallStatRow('Estimated cost', calc.totalCost.toFixed(2)) +
    _wallStatRow('Mortar', calc.mortarBags + ' bag' + (calc.mortarBags === 1 ? '' : 's')) +
    (calc.includeDpc ? _wallStatRow('DPC length', calc.dpcLengthM.toFixed(1) + ' m') : '') +
    _wallStatRow('Build time (' + calc.builders + ' builder' + (calc.builders === 1 ? '' : 's') + ')',
      calc.buildDaysSelected.toFixed(1) + ' day' + (calc.buildDaysSelected === 1 ? '' : 's'));

  return '<div style="margin:1rem 0;padding:14px 16px;border:1px solid var(--border,#e2e8f0);border-radius:8px;background:var(--surface,#fff);">' +
    _wallSvg(calc) +
    '<div style="margin-top:10px;">' + stats + '</div>' +
    advisories +
    '</div>';
};

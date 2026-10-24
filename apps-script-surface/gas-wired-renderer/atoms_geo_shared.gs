// Shared scale/reading helpers that choropleth_map needs. Same names and bodies as atoms_chart_reading.gs and atoms_d3radial.gs on the round-one branch (this base predates them);
// redefining an identical var/function is harmless in Apps Script, so the round-one merge may keep both or drop this file. Twin of the block before the choropleth block in renderers/web_article.py.
var _CR_ACC = 'var(--a2ui-accent,#4f46e5)';
var _CR_ACC2 = 'var(--a2ui-accent2,#0e7490)';
var _CR_SURF = 'var(--a2ui-surface,#ffffff)';
var _CR_TEXT = 'var(--a2ui-text,var(--text,#171717))';
var _CR_MUTED = 'var(--a2ui-muted,var(--muted,#595959))';
var _CR_SCHEMES = { 'sequential': ['accent', 'accent2'], 'diverging': ['accent_pair'], 'categorical': ['accent_cycle'] };
function _crMix(a, pa, b) { return 'color-mix(in srgb,' + a + ' ' + pa + '%,' + b + ')'; }
var _CR_SR = 'position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;';
var _CR_BORDER = '1px solid var(--a2ui-muted,var(--muted,#595959))';
var _CR_CB_CSS = '<style>[data-cb-root] .cb-fade{opacity:var(--k,1);}</style>';
function _crCb(kind, i, n, style, key) {
  return ' data-cb="' + kind + '"' + (key === undefined || key === null ? '' : ' data-key="' + key + '"') + ' class="cb-fade" style="' + (style || '') + '--k:clamp(0,calc(var(--p,1)*' + (n + 1) + ' - ' + i + '),1);"';
}
function _crS(v, mx) { return typeof v === 'string' ? _esc(v.slice(0, mx)) : ''; }
function _crId(parts) {
  var s = parts.join('\x1f'), h = 2166136261;
  for (var i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619) >>> 0;
  return h.toString(36);
}
function _crFixed(x, d) { return x.toFixed(d); }
function _crTrim(x) {
  var s = _crFixed(x, 3).replace(/(\.\d*?)0+$/, '$1').replace(/\.$/, '');
  return s === '-0' ? '0' : s;
}
function _crNum(v) { return (typeof v === 'number' && isFinite(v) && Math.abs(v) <= 1e15) ? v : null; }

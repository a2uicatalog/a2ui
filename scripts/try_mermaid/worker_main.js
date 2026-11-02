// Worker entry, appended after the converter modules by scripts/gen_try_mermaid.py (no imports: one classic script).
// The limits are enforced HERE as well as in the page: a page that skips its own checks still cannot hand the converter more than this.
var TM_MAX_CHARS = 20000, TM_MAX_LINE = 500, TM_MAX_NODES = 12, TM_MAX_EDGES = 16;
var TM_PACES = { slow: 1, normal: 1, fast: 1 }, TM_DIRS = { LR: 1, TB: 1, RL: 1, BT: 1 };
function tmFmt(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
self.onmessage = function (ev) {
  var d = ev && ev.data && typeof ev.data === 'object' ? ev.data : {};
  var out = { id: d.id, ok: false, errors: [], warnings: [], counts: null };
  try {
    var text = typeof d.text === 'string' ? d.text : '';
    if (text.length > TM_MAX_CHARS) throw new ArchError(['The input is ' + tmFmt(text.length) + ' characters; the limit is ' + tmFmt(TM_MAX_CHARS) + '.']);
    var rows = text.split('\n');
    for (var i = 0; i < rows.length; i++) {
      if (rows[i].length > TM_MAX_LINE) throw new ArchError(['line ' + (i + 1) + ' is ' + tmFmt(rows[i].length) + ' characters; the limit is ' + TM_MAX_LINE + ' per line.']);
    }
    var mode = d.mode === 'd2' ? 'd2' : 'mermaid';
    var opts = { film: true, numbered: true, hint: 'web', relationColumn: d.relation === true, pace: Object.prototype.hasOwnProperty.call(TM_PACES, d.pace) ? d.pace : 'normal' };
    if (typeof d.direction === 'string' && Object.prototype.hasOwnProperty.call(TM_DIRS, d.direction)) opts.direction = d.direction;
    checkOptions(opts);
    var parsed = mode === 'd2' ? parseD2(text, opts) : parseMermaid(text, opts);
    var nodes = parsed.graph.nodes.length, edges = parsed.graph.edges.length;
    out.counts = { nodes: nodes, edges: edges };
    out.warnings = parsed.warnings.slice();
    var over = [];
    if (nodes > TM_MAX_NODES) over.push('The diagram has ' + nodes + ' nodes; the limit is ' + TM_MAX_NODES + '. Remove or merge nodes, or split it into two diagrams.');
    if (edges > TM_MAX_EDGES) over.push('The diagram has ' + edges + ' edges; the limit is ' + TM_MAX_EDGES + '. Remove or merge edges, or split it into two diagrams.');
    if (over.length) throw new ArchError(over, parsed.warnings);
    var r = graphToArch(parsed.graph, Object.assign({}, opts, { direction: opts.direction }));
    out.ok = true;
    out.payload = r.payload;
    out.warnings = Array.from(new Set(parsed.warnings.concat(r.warnings)));
    out.durationSeconds = r.durationSeconds;
    out.steps = (r.steps || []).map(function (s) { return { step: s.step, activity: String(s.activity || '') }; });
    out.messages = (r.textMessages || []).map(function (m) { return { step: m.step, text: String(m.text || ''), from: String(m.from || ''), to: String(m.to || '') }; });
  } catch (e) {
    out.ok = false;
    if (e && e.name === 'ArchError' && Array.isArray(e.errors)) {
      out.errors = e.errors.map(String).slice(0, 20);
      out.warnings = Array.isArray(e.warnings) && e.warnings.length ? e.warnings.map(String) : out.warnings;
    } else out.errors = ['This input could not be converted. Check the first line names a flowchart (for example "flowchart LR") or switch to D2.'];
  }
  self.postMessage(out);
};

/**
 * roadmap_parser.gs — Apps Script port of scripts/parse_roadmap_md.py.
 *
 * MUST stay deep-equal to the Python reference (parity harness:
 * scripts/test_roadmap_parity.mjs, wired into pytest). Pure JS by design —
 * no GAS APIs — so the same file runs under node (harness) and in GAS
 * (the parser service). Implements spec/roadmap-md-v0.1.md.
 *
 * API: parseRoadmapMd(text, knownAtoms?) -> { payload, report }
 *   payload = a2ui_wired_surface object, or null when lint errors exist
 *   report  = { errors: [], warnings: [], coverage: 'N/4 sections (…)',
 *               phases: n, items: n, backlog: n, risks: n }
 */

var RP_REQUIRED_FM  = ['id', 'domain', 'name', 'source', 'license'];
var RP_OPTIONAL_FM  = ['horizon', 'velocity_basis', 'as_of'];
var RP_FORBIDDEN_FM = ['render', 'layout', 'atoms', 'theme', 'accent'];
var RP_ITEM_KEYS    = ['status', 'below', 'above', 'unlocks', 'note'];
var RP_STATUSES     = ['done', 'in-progress', 'planned'];
var RP_RISK_LEVELS  = ['critical', 'high', 'medium', 'low'];
var RP_KNOWN_SECTIONS = ['Phases', 'Timeline', 'Backlog', 'Risks'];
var RP_STATUS_CLASSES = { 'status-shipped': 'shipped', 'status-active': 'active',
                          'status-designed': 'designed', 'status-planned': 'planned' };
var RP_STATUS_LABEL = { shipped: 'SHIPPED', active: 'IN PROGRESS',
                        designed: 'DESIGNED', planned: 'PLANNED' };

function parseRoadmapMd(text, knownAtoms) {
  var lint = { errors: [], warnings: [] };
  function err(code, msg)  { lint.errors.push(code + ': ' + msg); }
  function warn(code, msg) { lint.warnings.push(code + ': ' + msg); }

  // --- strip wrapping code fence (mirror _strip_fence) ----------------------
  var lines = text.trim().split('\n');
  if (lines.length && /^```(markdown)?\s*$/.test(lines[0]) &&
      lines[lines.length - 1].replace(/\s+$/, '') === '```') {
    text = lines.slice(1, -1).join('\n');
  }

  // --- frontmatter -----------------------------------------------------------
  var m = text.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  if (!m) {
    err('E01', 'missing YAML frontmatter block');
    return { payload: null, report: rpReport_(null, lint) };
  }
  var fm = {};
  m[1].split('\n').forEach(function(line) {
    if (!line.trim() || /^\s/.test(line)) return;
    var km = line.match(/^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$/);
    if (!km) { err('E01', 'frontmatter is not valid YAML: ' + line.slice(0, 50)); return; }
    var val = km[2].trim();
    // strip surrounding quotes (YAML scalar quoting)
    if ((val.charAt(0) === '"' && val.slice(-1) === '"') ||
        (val.charAt(0) === "'" && val.slice(-1) === "'")) {
      val = val.slice(1, -1);
    }
    fm[km[1]] = val;
  });
  RP_REQUIRED_FM.forEach(function(k) {
    if (!fm[k]) err('E01', "missing required frontmatter key '" + k + "'");
  });
  if (fm.domain !== undefined && fm.domain !== 'roadmap') {
    err('E01', "domain must be 'roadmap', got '" + fm.domain + "'");
  }
  RP_FORBIDDEN_FM.forEach(function(k) {
    if (k in fm) err('E02', "forbidden frontmatter key '" + k + "' — presentation lives in the parser");
  });
  Object.keys(fm).sort().forEach(function(k) {
    if (RP_REQUIRED_FM.indexOf(k) === -1 && RP_OPTIONAL_FM.indexOf(k) === -1) {
      warn('W01', "unknown frontmatter key '" + k + "' (ignored)");
    }
  });

  // --- section split (mirror _split_sections) --------------------------------
  var bodyLines = m[2].split('\n');
  var intro = [], sections = {}, sectionOrderSeen = {}, current = null;
  bodyLines.forEach(function(ln) {
    if (ln.indexOf('# ') === 0) {
      var pa = rpParseAttrs_(ln.slice(2));
      var name = pa.title;
      if (RP_KNOWN_SECTIONS.indexOf(name) === -1) {
        err('E04', "unknown section heading '# " + name + "'");
      }
      current = name;
      if (!(current in sections)) sections[current] = [];
    } else if (current !== null) {
      sections[current].push(ln);
    } else {
      intro.push(ln);
    }
  });

  var parsed = { fm: fm };
  parsed.intro = intro.map(function(l) { return l.trim(); })
                      .filter(function(l) { return l; }).join(' ');

  // --- phases ----------------------------------------------------------------
  parsed.phases = rpParsePhases_(sections['Phases'] || [], err, warn);

  // --- timeline --------------------------------------------------------------
  parsed.timeline = rpParseSepBullets_(sections['Timeline'] || [], err, 'Timeline', 2, 3);

  // --- backlog ---------------------------------------------------------------
  parsed.backlog = [];
  (sections['Backlog'] || []).forEach(function(ln) {
    var s = ln.trim();
    var cm = s.match(/^- \[([ xX])\]\s+(.*)$/);
    if (cm) {
      parsed.backlog.push({ text: cm[2].trim(), done: cm[1] !== ' ' });
    } else if (s.indexOf('- ') === 0) {
      parsed.backlog.push({ text: s.slice(2).trim(), done: false });
    }
  });

  // --- risks -----------------------------------------------------------------
  parsed.risks = [];
  rpParseSepBullets_(sections['Risks'] || [], err, 'Risks', 2, 4).forEach(function(f) {
    if (RP_RISK_LEVELS.indexOf(f[0]) === -1) {
      err('E07', "invalid risk level '" + f[0] + "' (must be one of " + RP_RISK_LEVELS.join('|') + ')');
      return;
    }
    var risk = { level: f[0], title: f[1] };
    if (f.length > 2 && f[2]) risk.description = f[2];
    if (f.length > 3 && f[3]) risk.mitigation = f[3];
    parsed.risks.push(risk);
  });

  ['Timeline', 'Backlog', 'Risks'].forEach(function(sec) {
    if (!(sec in sections)) warn('W03', "optional section '# " + sec + "' absent");
  });

  if (lint.errors.length) return { payload: null, report: rpReport_(parsed, lint) };

  var payload = rpEmit_(parsed);
  if (knownAtoms) {
    var atomSet = {};
    knownAtoms.forEach(function(a) { atomSet[a] = true; });
    ['jump_nav', 'subheading', 'body', 'divider'].forEach(function(a) { atomSet[a] = true; });
    payload.layout.forEach(function(node) {
      if (!atomSet[node.atom]) warn('W01', "atom '" + node.atom + "' not in schema");
    });
  }
  return { payload: payload, report: rpReport_(parsed, lint) };
}

// Strip and parse a trailing {#hint .class} attribute block.
function rpParseAttrs_(heading) {
  var attrs = { hint: null, cls: [] };
  var m = heading.match(/\s*\{([^}]*)\}\s*$/);
  if (!m) return { title: heading.trim(), attrs: attrs };
  var title = heading.slice(0, m.index).trim();
  m[1].split(/\s+/).forEach(function(tok) {
    if (!tok) return;
    if (tok.charAt(0) === '#') attrs.hint = tok.slice(1);
    else if (tok.charAt(0) === '.') attrs.cls.push(tok.slice(1));
  });
  return { title: title, attrs: attrs };
}

function rpParsePhases_(secLines, err, warn) {
  var phases = [], phase = null;
  secLines.forEach(function(ln) {
    if (ln.indexOf('## ') === 0) {
      var pa = rpParseAttrs_(ln.slice(3));
      var status = 'planned';
      pa.attrs.cls.forEach(function(c) {
        if (c in RP_STATUS_CLASSES) status = RP_STATUS_CLASSES[c];
        else warn('W02', "unknown status class '." + c + "' on phase '" + pa.title + "'");
      });
      phase = { title: pa.title, status: status, summary: [], items: [] };
      phases.push(phase);
      return;
    }
    if (phase === null) {
      if (ln.trim()) err('E03', 'content before first \'## phase\' heading: ' + ln.trim().slice(0, 60));
      return;
    }
    var indented = ln.charAt(0) === ' ' || ln.charAt(0) === '\t';
    var im = !indented ? ln.trim().match(/^(\d+)\.\s+(.*)$/) : null;
    if (im) {
      phase.items.push({ title: im[2].trim(), kv: {} });
      return;
    }
    if (indented && phase.items.length) {
      var last = phase.items[phase.items.length - 1];
      var km = ln.trim().match(/^([a-z_]+):\s?(.*)$/);
      if (km) {
        if (RP_ITEM_KEYS.indexOf(km[1]) === -1) {
          err('E05', "unknown item key '" + km[1] + ":' under '" + last.title + "'");
        } else {
          last.kv[km[1]] = km[2].trim();
        }
        return;
      }
      // continuation line of the previous value
      var kvKeys = Object.keys(last.kv);
      if (kvKeys.length) {
        var lk = kvKeys[kvKeys.length - 1];
        last.kv[lk] += ' ' + ln.trim();
      }
      return;
    }
    if (ln.trim()) phase.summary.push(ln.trim());
  });
  phases.forEach(function(ph) {
    ph.items.forEach(function(it) {
      var st = it.kv.status;
      if (RP_STATUSES.indexOf(st) === -1) {
        err('E06', "item '" + it.title + "' has " +
            (st === undefined ? 'missing status' : "invalid status '" + st + "'"));
      }
    });
  });
  var anyItems = phases.some(function(ph) { return ph.items.length > 0; });
  if (!phases.length || !anyItems) {
    err('E03', "'# Phases' missing, empty, or has no items");
  }
  return phases;
}

function rpParseSepBullets_(secLines, err, section, minFields, maxFields) {
  var out = [];
  secLines.forEach(function(ln) {
    var s = ln.trim();
    if (s.indexOf('- ') !== 0) return;
    var fields = s.slice(2).split('::').map(function(f) { return f.trim(); });
    if (fields.length < minFields) {
      err('E04', section + ": bullet needs at least " + minFields + " '::' fields: " + s.slice(0, 60));
      return;
    }
    out.push(fields.slice(0, maxFields));
  });
  return out;
}

function rpSlug_(text) {
  var s = String(text).toLowerCase().replace(/[^a-z0-9-]+/g, '-')
                      .replace(/^-+|-+$/g, '').replace(/-+/g, '-');
  return s || 'x';
}

function rpEmit_(parsed) {
  var fm = parsed.fm;
  var layout = [{ id: 'title-heading', atom: 'subheading', props: { text: fm.name } }];

  var navLinks = [], phaseHeads = [];
  parsed.phases.forEach(function(ph) {
    var hid = 'phase-' + rpSlug_(ph.title) + '-heading';
    phaseHeads.push(hid);
    navLinks.push({ label: ph.title, target: hid });
  });
  if (parsed.timeline.length) navLinks.push({ label: 'Timeline', target: 'timeline-heading' });
  if (parsed.backlog.length)  navLinks.push({ label: 'Backlog', target: 'backlog-heading' });
  if (parsed.risks.length)    navLinks.push({ label: 'Risks', target: 'risks-heading' });
  layout.push({ id: 'nav', atom: 'jump_nav', props: { links: navLinks } });
  if (parsed.intro) layout.push({ id: 'intro', atom: 'body', props: { text: parsed.intro } });

  var periods = parsed.phases.map(function(ph) {
    var label = ph.title;
    var tag = RP_STATUS_LABEL[ph.status];
    if (tag) label += ' — ' + tag;
    return { label: label,
             items: ph.items.map(function(it) {
               return { text: it.title, status: it.kv.status };
             }) };
  });
  layout.push({ id: 'overview', atom: 'roadmap_card',
                props: { title: 'Capability phases', periods: periods } });
  layout.push({ id: 'div-overview', atom: 'divider' });

  parsed.phases.forEach(function(ph, i) {
    layout.push({ id: phaseHeads[i], atom: 'subheading', props: { text: ph.title } });
    if (ph.summary.length) {
      layout.push({ id: 'phase-' + i + '-summary', atom: 'body',
                    props: { text: ph.summary.join(' ') } });
    }
    var rows = ph.items.map(function(it) {
      return [it.title, it.kv.below || '', it.kv.above || '',
              it.kv.status, it.kv.unlocks || ''];
    });
    layout.push({ id: 'phase-' + i + '-matrix', atom: 'data_table_sortable',
                  props: { headers: ['Item', 'Below the surface', 'Above the surface',
                                     'Status', 'Unlocks'],
                           rows: rows } });
    var notes = [];
    ph.items.forEach(function(it) {
      if (it.kv.note) notes.push(it.title + ': ' + it.kv.note);
    });
    if (notes.length) {
      layout.push({ id: 'phase-' + i + '-notes', atom: 'body',
                    props: { text: notes.join('  |  ') } });
    }
    layout.push({ id: 'div-phase-' + i, atom: 'divider' });
  });

  if (parsed.timeline.length) {
    layout.push({ id: 'timeline-heading', atom: 'subheading', props: { text: 'Timeline' } });
    var events = parsed.timeline.map(function(f) {
      var ev = { date: f[0], title: f[1] };
      if (f.length > 2 && f[2]) ev.desc = f[2];
      return ev;
    });
    var vb = fm.velocity_basis;
    layout.push({ id: 'timeline', atom: 'brevet_timeline',
                  props: { title: vb ? 'Velocity basis: ' + vb : 'Delivery timeline',
                           events: events } });
    layout.push({ id: 'div-timeline', atom: 'divider' });
  }

  if (parsed.backlog.length) {
    layout.push({ id: 'backlog-heading', atom: 'subheading', props: { text: 'Backlog' } });
    layout.push({ id: 'backlog', atom: 'checklist_interactive',
                  props: { items: parsed.backlog.map(function(b) {
                    return (b.done ? '✓ ' : '') + b.text;
                  }) } });
    layout.push({ id: 'div-backlog', atom: 'divider' });
  }

  if (parsed.risks.length) {
    layout.push({ id: 'risks-heading', atom: 'subheading', props: { text: 'Risks' } });
    layout.push({ id: 'risks', atom: 'risk_flag',
                  props: { title: 'Delivery risks', risks: parsed.risks } });
  }

  var payload = { type: 'a2ui_wired_surface', title: fm.name,
                  state_primitives: [], actions: [], layout: layout };
  if (String(fm.license || '').toLowerCase() === 'private') payload.private = true;
  return payload;
}

function rpReport_(parsed, lint) {
  var report = { errors: lint.errors, warnings: lint.warnings,
                 coverage: '', phases: 0, items: 0, backlog: 0, risks: 0 };
  if (parsed) {
    var present = [];
    ['Phases', 'Timeline', 'Backlog', 'Risks'].forEach(function(s) {
      var key = s.toLowerCase();
      if (s === 'Phases' || (parsed[key] && parsed[key].length)) present.push(s);
    });
    report.coverage = 'coverage: ' + present.length + '/4 sections (' + present.join(', ') + ')';
    report.phases = (parsed.phases || []).length;
    report.items = (parsed.phases || []).reduce(function(n, ph) { return n + ph.items.length; }, 0);
    report.backlog = (parsed.backlog || []).length;
    report.risks = (parsed.risks || []).length;
  }
  return report;
}

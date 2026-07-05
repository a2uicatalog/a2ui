/**
 * training_parser.gs — deterministic training.md → a2ui_wired_surface payload.
 *
 * Apps Script port of scripts/parse_training_md.py (the reference
 * implementation). Pure JS, no GAS APIs — the node parity harness
 * (scripts/test_parser_parity.mjs) runs this same file against the Python
 * output for the fixture pair. Spec: spec/training-md-v0.1.md.
 *
 * parseTrainingMd(text, knownAtoms?) → { payload: Object|null, report: Object }
 *   knownAtoms: optional array of valid atom type names for W01 hint
 *   validation (in the renderer pass Object.keys(_RENDERERS)); when omitted,
 *   hint validation is skipped.
 */

var TP_REQUIRED_FM  = ['id', 'domain', 'name', 'source', 'license'];
var TP_OPTIONAL_FM  = ['subtype', 'audience', 'est_minutes', 'source_url'];
var TP_FORBIDDEN_FM = ['render', 'layout', 'atoms', 'theme', 'accent'];
var TP_STEP_KEYS    = ['cmd', 'do', 'expect', 'note', 'verify'];
var TP_KNOWN_SECTIONS = ['Prerequisites', 'Concepts', 'Steps', 'Checkpoints',
                         'Troubleshooting', 'References'];

function parseTrainingMd(text, knownAtoms) {
  var lint = { errors: [], warnings: [] };
  var atomSet = knownAtoms ? {} : null;
  if (knownAtoms) knownAtoms.forEach(function(a) { atomSet[a] = true; });

  function err(code, msg)  { lint.errors.push(code + ': ' + msg); }
  function warn(code, msg) { lint.warnings.push(code + ': ' + msg); }

  // Strip a wrapping code fence (spec asks the model to fence its output
  // so it copies losslessly from chat UIs)
  var stripped = text.trim();
  if (stripped.indexOf('```') === 0) {
    stripped = stripped.slice(stripped.indexOf('\n') + 1);
    if (/```\s*$/.test(stripped)) stripped = stripped.replace(/```\s*$/, '');
    text = stripped.trim() + '\n';
  }

  // Normalize asterisk bullets — both are legal markdown; section parsers
  // match "- " only
  text = text.replace(/^(\s*)\* /gm, '$1- ');

  // --- frontmatter ---------------------------------------------------------
  var fmMatch = text.match(/^---\n([\s\S]*?)\n---\n/);
  if (!fmMatch) {
    err('E01', 'missing or malformed frontmatter (--- block). If this was copied from Gemini\'s rendered reply, use the copy button / raw view — rendered copies collapse the frontmatter into one line');
    return { payload: null, report: tpReport_(lint, [], 0) };
  }
  var fm = {};
  fmMatch[1].split('\n').forEach(function(line) {
    if (!line.trim() || /^\s/.test(line)) return;
    var m = line.match(/^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$/);
    if (!m) { err('E01', 'frontmatter line not key: value — ' + line.slice(0, 50)); return; }
    var v = m[2].trim();
    if (/^".*"$/.test(v) || /^'.*'$/.test(v)) v = v.slice(1, -1);
    fm[m[1]] = v;
  });
  TP_REQUIRED_FM.forEach(function(k) {
    if (!fm[k]) err('E02', "missing required frontmatter key '" + k + "'");
  });
  if (fm.domain && fm.domain !== 'training') {
    err('E03', "domain is '" + fm.domain + "', expected 'training'");
  }
  Object.keys(fm).forEach(function(k) {
    if (TP_FORBIDDEN_FM.indexOf(k) !== -1) {
      err('E09', "forbidden frontmatter key '" + k + "' — presentation lives in the runbook");
    } else if (TP_REQUIRED_FM.indexOf(k) === -1 && TP_OPTIONAL_FM.indexOf(k) === -1) {
      err('E09', "unknown frontmatter key '" + k + "'");
    }
  });
  if (String(fm.license || '').indexOf('Unknown') === 0) {
    warn('W04', 'license is unverified — confirm before publishing');
  }

  var body = text.slice(fmMatch[0].length);
  var lines = body.split('\n');

  // --- split into intro + top-level sections -------------------------------
  var introLines = [];
  var sections = [];   // {title, attrs, lines}
  var current = null;
  lines.forEach(function(line) {
    if (line.indexOf('# ') === 0 && line.indexOf('##') !== 0) {
      var ta = tpParseAttrs_(line.slice(2));
      current = { title: ta.title, attrs: ta.attrs, lines: [] };
      sections.push(current);
    } else if (current === null) {
      introLines.push(line);
    } else {
      current.lines.push(line);
    }
  });
  var intro = introLines.map(function(l) { return l.trim(); })
                        .filter(function(l) { return l; }).join(' ');

  var sectionNames = sections.map(function(s) { return s.title; });
  sections.forEach(function(s) {
    if (TP_KNOWN_SECTIONS.indexOf(s.title) === -1) {
      err('E12', "unknown top-level section '# " + s.title + "'");
    }
    if (s.attrs.hint && atomSet && !atomSet[s.attrs.hint]) {
      warn('W01', "unknown atom hint '#" + s.attrs.hint + "' on '# " + s.title + "' — default atom used");
    }
  });
  if (sectionNames.indexOf('Steps') === -1) err('E04', "no '# Steps' section");

  // --- parse sections -------------------------------------------------------
  var parsed = {};
  var phases = [];
  var stepCount = 0;
  sections.forEach(function(s) {
    if (s.title === 'Steps') {
      var res = tpParseSteps_(s.lines, lint, atomSet, err, warn);
      phases = res.phases;
      stepCount = res.stepCount;
    } else if (s.title === 'Prerequisites') {
      parsed.Prerequisites = s.lines.filter(function(l) { return l.indexOf('- ') === 0; })
                                    .map(function(l) { return l.slice(2).trim(); });
    } else if (s.title === 'Concepts') {
      parsed.Concepts = tpParseTermBullets_(s.lines, err);
    } else if (s.title === 'Checkpoints') {
      parsed.Checkpoints = tpParseQa_(s.lines, err);
    } else if (s.title === 'Troubleshooting') {
      parsed.Troubleshooting = tpParseSepBullets_(s.lines, err, 'Troubleshooting');
    } else if (s.title === 'References') {
      parsed.References = tpParseReferences_(s.lines);
    }
  });
  if (sectionNames.indexOf('Steps') !== -1 && stepCount === 0) {
    err('E04', "'# Steps' contains zero steps");
  }

  var report = tpReport_(lint, sectionNames, stepCount);
  if (lint.errors.length) return { payload: null, report: report };

  return { payload: tpEmit_(fm, intro, sectionNames, parsed, phases, stepCount),
           report: report };
}

// --- helpers ----------------------------------------------------------------

function tpParseAttrs_(heading) {
  var attrs = { hint: null, weight: null, nav: null };
  var m = heading.match(/\s*\{([^}]*)\}\s*$/);
  if (!m) return { title: heading.trim(), attrs: attrs };
  var title = heading.slice(0, m.index).trim();
  var toks = m[1].match(/nav="[^"]*"|\S+/g) || [];
  toks.forEach(function(tok) {
    if (tok.charAt(0) === '#') attrs.hint = tok.slice(1);
    else if (tok.indexOf('.weight-') === 0) attrs.weight = tok.slice(8);
    else if (tok.indexOf('nav="') === 0 && tok.charAt(tok.length - 1) === '"') {
      attrs.nav = tok.slice(5, -1);
    }
  });
  return { title: title, attrs: attrs };
}

function tpParseTermBullets_(secLines, err) {
  var items = [];
  secLines.forEach(function(l) {
    if (l.indexOf('- ') !== 0) return;
    var m = l.slice(2).trim().match(/^\*\*(.+?)\*\*\s+—\s+(.*)$/);
    if (m) items.push({ key: m[1], description: m[2] });
    else err('E08', "Concepts entry not in '**term** — definition' form: " + l.slice(0, 60));
  });
  return items;
}

function tpParseSepBullets_(secLines, err, section) {
  var items = [];
  secLines.forEach(function(l) {
    if (l.indexOf('- ') !== 0) return;
    if (l.indexOf(' :: ') === -1) {
      err('E08', section + " entry without ' :: ' separator: " + l.slice(0, 60));
      return;
    }
    var idx = l.slice(2).indexOf(' :: ');
    var entry = l.slice(2);
    items.push({ key: entry.slice(0, idx).trim(), description: entry.slice(idx + 4).trim() });
  });
  return items;
}

function tpParseQa_(secLines, err) {
  var pairs = [], q = null;
  secLines.forEach(function(l) {
    var s = l.trim();
    if (s.indexOf('Q:') === 0) {
      if (q !== null) err('E10', "Checkpoints 'Q:' without matching 'A:': " + q.slice(0, 50));
      q = s.slice(2).trim();
    } else if (s.indexOf('A:') === 0) {
      if (q === null) err('E10', "Checkpoints 'A:' without preceding 'Q:': " + s.slice(0, 50));
      else { pairs.push({ q: q, a: s.slice(2).trim() }); q = null; }
    }
  });
  if (q !== null) err('E10', "Checkpoints 'Q:' without matching 'A:': " + q.slice(0, 50));
  return pairs;
}

function tpParseReferences_(secLines) {
  var items = [];
  secLines.forEach(function(l) {
    if (l.indexOf('- ') !== 0) return;
    var entry = l.slice(2).trim();
    var idx = entry.lastIndexOf(' — ');
    if (idx !== -1) items.push({ title: entry.slice(0, idx).trim(), url: entry.slice(idx + 3).trim() });
    else items.push({ title: entry, url: entry });
  });
  return items;
}

function tpParseSteps_(secLines, lint, atomSet, err, warn) {
  var h2 = secLines.filter(function(l) { return l.indexOf('## ') === 0 && l.indexOf('###') !== 0; });
  var h2Titles = h2.map(function(l) { return tpParseAttrs_(l.slice(3)).title; });
  var h2Steppy = h2Titles.map(function(t) { return /^\d+\.\s/.test(t); });
  var hasH3 = secLines.some(function(l) { return l.indexOf('### ') === 0; });
  var anySteppy = h2Steppy.some(function(x) { return x; });
  var allSteppy = h2Steppy.length > 0 && h2Steppy.every(function(x) { return x; });

  if (h2.length && anySteppy && (hasH3 || !allSteppy)) {
    err('E11', "flat and phased shapes mixed inside '# Steps'");
    return { phases: [], stepCount: 0 };
  }
  var flat = h2.length > 0 && allSteppy && !hasH3;

  var phases = [];
  if (flat) phases.push({ title: null, nav: null, numbered: false, lines: [] });
  var stepLevel = flat ? '## ' : '### ';

  var current = flat ? phases[0] : null;
  secLines.forEach(function(line) {
    if (!flat && line.indexOf('## ') === 0 && line.indexOf('###') !== 0) {
      var ta = tpParseAttrs_(line.slice(3));
      current = { title: ta.title, nav: ta.attrs.nav,
                  numbered: /^\d+\s+·/.test(ta.title), lines: [] };
      phases.push(current);
      return;
    }
    if (current === null) {
      if (line.trim()) err('E11', "content before first phase heading in '# Steps': " + line.slice(0, 50));
      return;
    }
    current.lines.push(line);
  });

  var stepCount = 0;
  phases.forEach(function(phase) {
    phase.elements = tpParsePhaseElements_(phase.lines, stepLevel, atomSet, err, warn);
    delete phase.lines;
    stepCount += phase.elements.filter(function(e) { return e.kind === 'step'; }).length;
  });
  return { phases: phases, stepCount: stepCount };
}

function tpParsePhaseElements_(pLines, stepLevel, atomSet, err, warn) {
  var elements = [];
  var i = 0;
  var expectedN = 1;
  while (i < pLines.length) {
    var line = pLines[i];
    if (!line.trim()) { i++; continue; }
    if (line.indexOf(stepLevel) === 0) {
      var ta = tpParseAttrs_(line.slice(stepLevel.length));
      var m = ta.title.match(/^(\d+)\.\s+(.*)$/);
      if (!m) { err('E06', "step heading not '<n>. <title>': " + ta.title.slice(0, 60)); i++; continue; }
      if (parseInt(m[1], 10) !== expectedN) {
        err('E06', 'step numbering not sequential: got ' + m[1] + ', expected ' + expectedN + ' (' + ta.title.slice(0, 50) + ')');
      }
      expectedN++;
      if (ta.attrs.hint && atomSet && !atomSet[ta.attrs.hint]) {
        warn('W01', "unknown atom hint '#" + ta.attrs.hint + "' on step '" + m[2].slice(0, 40) + "'");
      }
      var step = { kind: 'step', title: m[2] };
      i++;
      while (i < pLines.length) {
        var l = pLines[i];
        if (!l.trim()) break;
        var km = l.match(/^([a-z_]+):\s?(.*)$/);
        if (!km) break;
        if (TP_STEP_KEYS.indexOf(km[1]) === -1) {
          err('E07', "unknown key '" + km[1] + ":' in step '" + step.title.slice(0, 40) + "'");
        } else {
          step[km[1]] = km[2];
        }
        i++;
      }
      var hasCmd = 'cmd' in step, hasDo = 'do' in step;
      if (hasCmd === hasDo) err('E05', "step '" + step.title.slice(0, 40) + "' must have exactly one of cmd/do");
      if (!('verify' in step)) warn('W03', "step '" + step.title.slice(0, 40) + "' has no verify — done-checkbox is self-report");
      elements.push(step);
      continue;
    }
    if (line.indexOf('> ') === 0) {
      var quote = [];
      while (i < pLines.length && pLines[i].charAt(0) === '>') {
        quote.push(pLines[i].replace(/^>+\s?/, '').trim());
        i++;
      }
      elements.push({ kind: 'callout', text: quote.filter(function(q) { return q; }).join(' ') });
      continue;
    }
    var lm = line.trim().match(/^\*\*(.+)\*\*\s*$/);
    if (lm) {
      var items = [];
      i++;
      while (i < pLines.length && pLines[i].indexOf('- ') === 0) {
        var entry = pLines[i].slice(2);
        var sepIdx = entry.indexOf(' :: ');
        if (sepIdx === -1) err('E08', "info-block entry without ' :: ' separator: " + entry.slice(0, 60));
        else items.push({ key: entry.slice(0, sepIdx).trim(), description: entry.slice(sepIdx + 4).trim() });
        i++;
      }
      elements.push({ kind: 'info', title: lm[1], items: items });
      continue;
    }
    var para = [];
    while (i < pLines.length && pLines[i].trim() &&
           '#>-*'.indexOf(pLines[i].charAt(0)) === -1 && pLines[i].indexOf('**') !== 0) {
      para.push(pLines[i].trim());
      i++;
    }
    if (para.length) elements.push({ kind: 'body', text: para.join(' ') });
    else i++;
  }
  return elements;
}

function tpLetters_(n) {
  var out = [];
  var az = 'abcdefghijklmnopqrstuvwxyz';
  for (var i = 0; i < az.length && out.length < n; i++) out.push(az[i]);
  for (var a = 0; a < az.length && out.length < n; a++) {
    for (var b = 0; b < az.length && out.length < n; b++) out.push(az[a] + az[b]);
  }
  return out;
}

function tpEmit_(fm, intro, sectionNames, parsed, phases, stepCount) {
  var layout = [];
  var state = [];
  var stepIdx = 0;
  var divIdx = 0;
  var blk = 0;
  function bid(prefix) { blk++; return prefix + '-' + blk; }

  layout.push({ id: 'title-heading', atom: 'subheading', props: { text: fm.name } });

  var navLinks = [];
  var phaseHeadingIds = {};
  phases.forEach(function(phase, pI) {
    if (phase.title !== null) {
      phaseHeadingIds[pI] = 'phase-' + pI + '-heading';
      if (phase.numbered) {
        navLinks.push({ label: phase.nav || phase.title, target: phaseHeadingIds[pI] });
      }
    }
  });
  if (navLinks.length) layout.push({ id: 'nav', atom: 'jump_nav', props: { links: navLinks } });
  if (intro) layout.push({ id: 'intro', atom: 'body', props: { text: intro } });

  function emitOptional(name) {
    var data = parsed[name];
    if (!data || !data.length) return;
    if (name === 'Prerequisites') {
      layout.push({ id: bid('prereq'), atom: 'prerequisite_checklist',
                    props: { title: 'Prerequisites', items: data } });
    } else if (name === 'Concepts') {
      layout.push({ id: bid('concepts'), atom: 'key_value',
                    props: { title: 'Concepts', items: data } });
    } else if (name === 'Checkpoints') {
      data.forEach(function(pair) {
        layout.push({ id: bid('check'), atom: 'accordion_item',
                      props: { header: pair.q, content: pair.a } });
      });
    } else if (name === 'Troubleshooting') {
      data.forEach(function(item) {
        layout.push({ id: bid('trouble'), atom: 'accordion_item',
                      props: { header: item.key, content: item.description } });
      });
    } else if (name === 'References') {
      layout.push({ id: bid('refs'), atom: 'resources_list', props: { items: data } });
    }
  }

  var stepsPos = sectionNames.indexOf('Steps');
  if (stepsPos === -1) stepsPos = sectionNames.length;
  sectionNames.slice(0, stepsPos).forEach(emitOptional);

  phases.forEach(function(phase, pI) {
    if (phase.title !== null) {
      layout.push({ id: 'div' + divIdx, atom: 'divider' });
      divIdx++;
      layout.push({ id: phaseHeadingIds[pI], atom: 'subheading', props: { text: phase.title } });
    }
    phase.elements.forEach(function(el) {
      if (el.kind === 'step') {
        var storeId = 's_' + (stepIdx + 1);
        state.push({ id: storeId, primitive: 'ValueStore', props: { defaultValue: false, persist: true } });
        var props = { label: el.title, command: 'cmd' in el ? el.cmd : (el['do'] || '') };
        var hintParts = [];
        if (el.note) hintParts.push(el.note);
        if (el.expect) hintParts.push('Expect: ' + el.expect);
        if (el.verify) hintParts.push('Verify: ' + el.verify);
        if (hintParts.length) props.hint = hintParts.join(' — ');
        layout.push({ id: 'cmd-' + (stepIdx + 1), atom: 'command_step', props: props,
                      wire: { done: '#' + storeId + '.value', setDone: '#' + storeId + '.setValue' } });
        stepIdx++;
      } else if (el.kind === 'callout') {
        layout.push({ id: bid('callout'), atom: 'callout',
                      props: { type: 'warning', text: el.text } });
      } else if (el.kind === 'info') {
        layout.push({ id: bid('info'), atom: 'key_value',
                      props: { title: el.title, items: el.items } });
      } else if (el.kind === 'body') {
        layout.push({ id: bid('body'), atom: 'body', props: { text: el.text } });
      }
    });
  });

  sectionNames.slice(stepsPos + 1).forEach(emitOptional);

  var attrSrc = String(fm.source || '').trim();
  var attrLic = String(fm.license || '').trim();
  var attrUrl = String(fm.source_url || '').trim();
  var attribution = 'Source: ' + (attrUrl ? '[' + attrSrc + '](' + attrUrl + ')' : attrSrc);
  if (attrLic) attribution += ' · License: ' + attrLic;
  layout.push({ id: 'attribution', atom: 'body',
                props: { text: '*' + attribution + '*' } });

  if (stepCount) {
    var letters = tpLetters_(stepCount);
    var inputs = {};
    for (var i = 0; i < stepCount; i++) inputs[letters[i]] = '#s_' + (i + 1) + '.value';
    state.push({ id: 'done_count', primitive: 'Computed',
                 props: { expr: letters.slice(0, stepCount).join('+'), inputs: inputs } });
    state.push({ id: 'progress_pct', primitive: 'Computed',
                 props: { expr: 'n/' + stepCount + '*100', inputs: { n: '#done_count.value' } } });
  }

  return { type: 'a2ui_wired_surface', title: fm.name,
           state_primitives: state, actions: [], layout: layout };
}

function tpReport_(lint, sectionNames, stepCount) {
  var optional = TP_KNOWN_SECTIONS.filter(function(s) { return s !== 'Steps'; });
  var absent = optional.filter(function(s) { return sectionNames.indexOf(s) === -1; });
  absent.forEach(function(s) { lint.warnings.push('W02: optional section absent: ' + s); });
  var present = sectionNames.filter(function(s) { return TP_KNOWN_SECTIONS.indexOf(s) !== -1; });
  return {
    errors: lint.errors,
    warnings: lint.warnings,
    sections_present: present,
    sections_absent: absent,
    step_count: stepCount,
    coverage: present.length + '/' + TP_KNOWN_SECTIONS.length + ' sections'
  };
}

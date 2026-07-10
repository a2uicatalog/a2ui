// atoms_wired_expand.gs — server-side template expansion for the WIRED dialect.
//
// The ChildList template decode (atoms_v1_decode.gs) married into wired
// surfaces: a payload may declare `variants` (named data sets, selected by
// URL ?n=<key>) and `wired_templates` — repeat templates that expand into
// concrete state_primitives / actions / layout BEFORE rendering. The client
// engine never changes: it only ever sees the expanded, concrete schema.
// Pure string/JSON work (no DOM, no GAS services) — Node-testable, and ships
// in the MCP Apps bundle by concatenation like the v1.0 decoder.
//
// Payload contract:
//   variants:        { "8": {rounds: [...], courts: 2, ...}, "12": {...} }
//   default_variant: "8"
//   wired_templates: { state: [...], actions: [...], layout: [...] }
//     — each array may contain plain entries (copied through, tokens
//       substituted against the variant data) or repeat entries:
//       { "repeat": "<variantDataKey>", "template": [ ...entries... ] }
//     — inside a repeat, tokens resolve per item:
//         {{i}} 1-based index · {{i0}} 0-based · {{item.field}} item value
//       plus {{variant}} (the selected key), {{self_url}} (this page's stable
//       ?p= URL, for variant-switch links) and {{data.field}} (variant data).
//     — an entry with "if": "item.<field>" is included only when that field
//       is truthy on the current item (ragged data, e.g. courts per round).
//     — "step": "{{i0}}" coerces back to an integer after substitution.
//
// Honesty: an unknown ?n= falls back to default_variant — never a blank page.

function _a2uiSubstitute(value, ctx) {
  if (typeof value === 'string') {
    var replaced = value.replace(/\{\{([\w.]+)\}\}/g, function(_, path) {
      if (path === 'i')  return String(ctx.i);
      if (path === 'i0') return String(ctx.i0);
      if (path === 'variant')  return String(ctx.variant);
      if (path === 'self_url') return String(ctx.self_url || '');
      var parts = path.split('.');
      var root = parts[0] === 'item' ? ctx.item : parts[0] === 'data' ? ctx.data : null;
      if (!root) return '';
      var cur = root;
      for (var i = 1; i < parts.length; i++) {
        cur = (cur === null || cur === undefined) ? undefined : cur[parts[i]];
      }
      return (cur === undefined || cur === null) ? '' : String(cur);
    });
    return replaced;
  }
  if (Array.isArray(value)) {
    return value.map(function(v) { return _a2uiSubstitute(v, ctx); });
  }
  if (value && typeof value === 'object') {
    var out = {};
    for (var k in value) out[k] = _a2uiSubstitute(value[k], ctx);
    return out;
  }
  return value;
}

function _a2uiItemTruthy(item, ref) {
  if (typeof ref !== 'string' || ref.indexOf('item.') !== 0) return true;
  var cur = item;
  var parts = ref.slice(5).split('.');
  for (var i = 0; i < parts.length; i++) {
    cur = (cur === null || cur === undefined) ? undefined : cur[parts[i]];
  }
  return !(cur === undefined || cur === null || cur === '' || cur === false);
}

function _a2uiExpandList(entries, data, baseCtx) {
  var out = [];
  (entries || []).forEach(function(entry) {
    if (entry && typeof entry === 'object' && entry.repeat) {
      var arr = data[entry.repeat];
      if (!Array.isArray(arr)) return;              // data absent: expand to nothing
      arr.forEach(function(item, idx) {
        var ctx = { i: idx + 1, i0: idx, item: item, data: data,
                    variant: baseCtx.variant, self_url: baseCtx.self_url };
        (entry.template || []).forEach(function(tpl) {
          if (!_a2uiItemTruthy(item, tpl['if'])) return;
          var el = _a2uiSubstitute(tpl, ctx);
          delete el['if'];
          if (typeof el.step === 'string' && /^\d+$/.test(el.step)) el.step = parseInt(el.step, 10);
          out.push(el);
        });
      });
    } else if (entry) {
      var ctx0 = { i: 0, i0: 0, item: {}, data: data,
                   variant: baseCtx.variant, self_url: baseCtx.self_url };
      var plain = _a2uiSubstitute(entry, ctx0);
      if (typeof plain.step === 'string' && /^\d+$/.test(plain.step)) plain.step = parseInt(plain.step, 10);
      out.push(plain);
    }
  });
  return out;
}

function _expandWiredSurface(payload, variantKey, selfUrl) {
  var variants = payload.variants || {};
  var key = (variantKey && variants[variantKey]) ? variantKey
          : (payload.default_variant && variants[payload.default_variant]) ? payload.default_variant
          : Object.keys(variants)[0];
  var data = variants[key] || {};
  var tpl  = payload.wired_templates || {};
  var base = { variant: key || '', self_url: selfUrl || '' };

  var out = {};
  for (var k in payload) {
    if (k === 'variants' || k === 'wired_templates' || k === 'default_variant') continue;
    out[k] = payload[k];
  }
  out.state_primitives = (payload.state_primitives || []).concat(_a2uiExpandList(tpl.state, data, base));
  out.actions          = (payload.actions          || []).concat(_a2uiExpandList(tpl.actions, data, base));
  out.layout           = (payload.layout           || []).concat(_a2uiExpandList(tpl.layout, data, base));
  // substitute tokens in the STATIC portions too ({{variant}}, {{self_url}},
  // {{data.*}} in headings, stepBinding-adjacent labels, etc.)
  var ctx0 = { i: 0, i0: 0, item: {}, data: data, variant: base.variant, self_url: base.self_url };
  out.layout = out.layout.map(function(el) { return _a2uiSubstitute(el, ctx0); });
  if (typeof out.title === 'string') out.title = _a2uiSubstitute(out.title, ctx0);
  return out;
}

// atoms_freeform.gs — freeform_canvas: a sanitized, one-shot SVG diagram
// escape hatch. mcp-apps/browser-bundle port of the security-reviewed
// Python reference in renderers/web_article.py -- read that file's
// "freeform_canvas" section (search "_FREEFORM_TAG_ATTRS") before touching
// this one; the two must stay in lockstep on the allowlist and every hard
// security block, not just visual output.
//
// Security model (identical to the Python reference): ONE allowlist covers
// BOTH authoring forms -- structured `elements[]` JSON and raw `svg`
// markup -- so capability never depends on which form an agent picks.
// _freeformValidateElement is the single gate either form must pass
// through; _freeformRenderElement is the single renderer either form's
// VALIDATED output goes through. A violation ANYWHERE in the tree fails
// the WHOLE payload -- no partial render of "the parts that were safe".
//
// No DOMParser/innerHTML anywhere in this file, on purpose, not just
// because this code also has to run in GAS's server-side V8 (no DOM) and
// survive this repo's own Node-based mcp-apps sweep test (no DOM either):
// building a live DOM node from attacker-authored text and reading it back
// is itself the mutation-XSS pattern this whole design exists to avoid, in
// ANY environment. _freeformParseXml below is a hand-rolled, allowlist-only
// tokenizer -- it has NO entity-declaration/DTD mechanism at all (structural,
// not a runtime check that could be bypassed), so billion-laughs-style
// entity expansion is impossible here, and any `<!DOCTYPE`/`<!ENTITY` is
// rejected outright rather than silently skipped.

var _FREEFORM_MAX_DEPTH = 64; // defense-in-depth against pathological nesting DoS

var _FREEFORM_COMMON_ATTRS = {
  fill: 'fill', stroke: 'stroke', opacity: 'opacity',
  transform: 'transform', id: 'id',
  stroke_width: 'stroke-width', stroke_dasharray: 'stroke-dasharray',
  clip_path: 'clip-path', mask: 'mask',
  // A completeness pass, 2026-08-25 -- mirrors the identical fix in the
  // Python reference (renderers/web_article.py); see that file for the
  // full story. Every value here is a plain number, percentage, or closed
  // keyword enum, same as opacity/stroke-width already allowed -- a
  // mechanical expansion, not a change to the security model.
  fill_opacity: 'fill-opacity', stroke_opacity: 'stroke-opacity',
  stroke_linecap: 'stroke-linecap', stroke_linejoin: 'stroke-linejoin',
  stroke_miterlimit: 'stroke-miterlimit', stroke_dashoffset: 'stroke-dashoffset',
  fill_rule: 'fill-rule', visibility: 'visibility', display: 'display',
  // Arrowheads -- same url(#fragment)-only value shape as fill/stroke/
  // clip_path/mask, added to _FREEFORM_URL_ATTR_CANONICALS below.
  marker_start: 'marker-start', marker_mid: 'marker-mid', marker_end: 'marker-end'
};

var _FREEFORM_TAG_EXTRA_ATTRS = {
  rect:      {x: 'x', y: 'y', width: 'width', height: 'height', rx: 'rx', ry: 'ry'},
  circle:    {cx: 'cx', cy: 'cy', r: 'r'},
  ellipse:   {cx: 'cx', cy: 'cy', rx: 'rx', ry: 'ry'},
  line:      {x1: 'x1', y1: 'y1', x2: 'x2', y2: 'y2'},
  polyline:  {points: 'points'},
  polygon:   {points: 'points'},
  path:      {d: 'd'},
  g:         {},
  text:      {x: 'x', y: 'y', font_size: 'font-size', font_weight: 'font-weight',
              font_family: 'font-family', text_anchor: 'text-anchor',
              font_style: 'font-style', letter_spacing: 'letter-spacing',
              word_spacing: 'word-spacing', text_decoration: 'text-decoration',
              dominant_baseline: 'dominant-baseline'},
  tspan:     {x: 'x', y: 'y', font_size: 'font-size', font_weight: 'font-weight',
              font_family: 'font-family', text_anchor: 'text-anchor',
              font_style: 'font-style', letter_spacing: 'letter-spacing',
              word_spacing: 'word-spacing', text_decoration: 'text-decoration',
              dominant_baseline: 'dominant-baseline'},
  use:       {x: 'x', y: 'y', width: 'width', height: 'height', href: 'href'},
  defs:      {},
  clipPath:  {clip_path_units: 'clipPathUnits'},
  mask:      {mask_units: 'maskUnits'},
  // Mirrors the identical completeness fix in the Python reference --
  // gradientTransform/patternTransform/spreadMethod/fx/fy/fr/markerUnits.
  // See that file for the full story.
  linearGradient: {x1: 'x1', y1: 'y1', x2: 'x2', y2: 'y2',
                    gradient_units: 'gradientUnits', href: 'href',
                    gradient_transform: 'gradientTransform', spread_method: 'spreadMethod'},
  radialGradient: {cx: 'cx', cy: 'cy', r: 'r',
                    gradient_units: 'gradientUnits', href: 'href',
                    gradient_transform: 'gradientTransform', spread_method: 'spreadMethod',
                    fx: 'fx', fy: 'fy', fr: 'fr'},
  stop:      {offset: 'offset', stop_color: 'stop-color', stop_opacity: 'stop-opacity'},
  marker:    {marker_width: 'markerWidth', marker_height: 'markerHeight',
              ref_x: 'refX', ref_y: 'refY', orient: 'orient', viewbox: 'viewBox',
              marker_units: 'markerUnits'},
  pattern:   {x: 'x', y: 'y', width: 'width', height: 'height',
              pattern_units: 'patternUnits', viewbox: 'viewBox',
              pattern_transform: 'patternTransform'}
};

var _FREEFORM_CONTAINER_TAGS = {g:1, defs:1, clipPath:1, mask:1, linearGradient:1,
                                 radialGradient:1, marker:1, pattern:1};
var _FREEFORM_TEXT_TAGS = {text:1, tspan:1};
var _FREEFORM_FORBIDDEN_TAGS = {script:1, foreignObject:1, image:1, iframe:1, object:1, embed:1};

var _FREEFORM_TAG_ATTRS = (function() {
  var out = {};
  for (var tag in _FREEFORM_TAG_EXTRA_ATTRS) {
    var merged = {};
    for (var k1 in _FREEFORM_COMMON_ATTRS) merged[k1] = _FREEFORM_COMMON_ATTRS[k1];
    var extra = _FREEFORM_TAG_EXTRA_ATTRS[tag];
    for (var k2 in extra) merged[k2] = extra[k2];
    out[tag] = merged;
  }
  return out;
})();

var _FREEFORM_URL_ATTR_CANONICALS = {fill:1, stroke:1, clip_path:1, mask:1,
  marker_start:1, marker_mid:1, marker_end:1};
var _FREEFORM_LOCAL_URL_RE = /^url\(\s*#([\w-]+)\s*\)$/;

// real SVG attr name -> canonical snake_case, inverse of _FREEFORM_TAG_ATTRS
var _FREEFORM_SVG_ATTR_TO_CANONICAL = (function() {
  var out = {};
  for (var tag in _FREEFORM_TAG_ATTRS) {
    var map = _FREEFORM_TAG_ATTRS[tag];
    for (var canon in map) {
      var svgAttr = map[canon];
      if (!(svgAttr in out)) out[svgAttr] = canon;
    }
  }
  return out;
})();

function FreeformCanvasError(message) {
  this.message = message;
  this.name = 'FreeformCanvasError';
}
FreeformCanvasError.prototype = Object.create(Error.prototype);

function _freeformCheckValueSafety(value) {
  // Defense in depth across EVERY attribute value, not just href/url() ones.
  // Blocks any scheme-like prefix (word chars followed by ':'), not just a
  // javascript:/data: substring -- a bare fill="http://evil.example/x.png"
  // isn't a valid SVG <paint> value so no current browser fetches it, but
  // that safety depends on today's UA parsing behaviour, not this atom's
  // own policy. url(#fragment) is the one legitimate colon-bearing form,
  // exempted here by its 'url(' prefix and checked separately below.
  var v = String(value).trim().toLowerCase();
  if (v.indexOf('javascript:') !== -1 || v.indexOf('data:') !== -1) {
    throw new FreeformCanvasError('disallowed value scheme in ' + JSON.stringify(value));
  }
  if (v.indexOf(':') !== -1 && v.indexOf('url(') !== 0) {
    var scheme = v.split(':')[0];
    if (/^[a-z]{2,}$/.test(scheme)) {
      throw new FreeformCanvasError('disallowed scheme-like value in ' + JSON.stringify(value));
    }
  }
}

function _freeformValidateUrlValue(value) {
  var v = String(value).trim();
  if (v.toLowerCase().indexOf('url(') !== -1 && !_FREEFORM_LOCAL_URL_RE.test(v)) {
    throw new FreeformCanvasError('url() references must be a local #fragment, got ' + JSON.stringify(value));
  }
}

function _freeformValidateHrefValue(value) {
  var v = String(value).trim();
  if (v.indexOf('#') !== 0) {
    throw new FreeformCanvasError('href/xlink:href must be a local #fragment reference, got ' + JSON.stringify(value));
  }
}

function _freeformValidateElement(el, depth) {
  depth = depth || 0;
  if (depth > _FREEFORM_MAX_DEPTH) {
    throw new FreeformCanvasError('element nesting exceeds max depth ' + _FREEFORM_MAX_DEPTH);
  }
  if (!el || typeof el !== 'object') {
    throw new FreeformCanvasError('element must be an object, got ' + typeof el);
  }
  var tag = el.tag;
  if (_FREEFORM_FORBIDDEN_TAGS[tag]) {
    throw new FreeformCanvasError('forbidden tag: ' + JSON.stringify(tag));
  }
  var allowedAttrs = _FREEFORM_TAG_ATTRS[tag];
  if (!allowedAttrs) {
    throw new FreeformCanvasError('tag not in allowlist: ' + JSON.stringify(tag));
  }

  var cleanAttrs = {};
  for (var k in el) {
    if (k === 'tag' || k === 'children' || k === 'text') continue;
    // __proto__/constructor/prototype: `k in allowedAttrs` checks the whole
    // prototype chain, not just own keys, so '__proto__' reads as "present"
    // on ANY plain object even though no allowlist ever defines it -- and a
    // later `cleanAttrs[k] = v` with k='__proto__' and an object-typed v
    // reassigns cleanAttrs's actual prototype (confirmed with a live repro,
    // Gemini security review follow-up, 2026-08-25). Rejected explicitly,
    // first, before any allowlist lookup -- the Python reference has no
    // equivalent gap (dict membership doesn't walk a prototype chain), so
    // this fix has no sibling to mirror on that side.
    if (k === '__proto__' || k === 'constructor' || k === 'prototype') {
      throw new FreeformCanvasError('attribute ' + JSON.stringify(k) + ' is never permitted');
    }
    if (k === 'style') {
      throw new FreeformCanvasError('the style attribute is never permitted');
    }
    if (/^on/i.test(k)) {
      throw new FreeformCanvasError('event-handler-like attribute rejected: ' + JSON.stringify(k));
    }
    if (!Object.prototype.hasOwnProperty.call(allowedAttrs, k)) {
      throw new FreeformCanvasError('attribute ' + JSON.stringify(k) + ' not allowed on <' + tag + '>');
    }
    var v = el[k];
    _freeformCheckValueSafety(v);
    if (k === 'href') _freeformValidateHrefValue(v);
    if (_FREEFORM_URL_ATTR_CANONICALS[k]) _freeformValidateUrlValue(v);
    cleanAttrs[k] = v;
  }

  var text = (el.text !== undefined) ? el.text : null;
  if (text !== null && !_FREEFORM_TEXT_TAGS[tag]) {
    throw new FreeformCanvasError('<' + tag + '> may not carry text content');
  }

  var childrenIn = el.children || [];
  if (childrenIn.length && !_FREEFORM_CONTAINER_TAGS[tag]) {
    throw new FreeformCanvasError('<' + tag + '> may not have children');
  }
  var children = [];
  for (var i = 0; i < childrenIn.length; i++) {
    children.push(_freeformValidateElement(childrenIn[i], depth + 1));
  }

  return {tag: tag, attrs: cleanAttrs, text: text, children: children};
}

function _freeformValidateElements(elements) {
  if (!Array.isArray(elements) || elements.length === 0) {
    throw new FreeformCanvasError('elements must be a non-empty list');
  }
  var out = [];
  for (var i = 0; i < elements.length; i++) {
    out.push(_freeformValidateElement(elements[i], 0));
  }
  return out;
}

// ── hand-rolled XML tokenizer (no DOM anywhere -- see file header) ────────

function _freeformDecodeEntities(s) {
  return s.replace(/&(amp|lt|gt|quot|apos|#x[0-9a-fA-F]+|#[0-9]+);/g, function(m, e) {
    if (e === 'amp') return '&';
    if (e === 'lt') return '<';
    if (e === 'gt') return '>';
    if (e === 'quot') return '"';
    if (e === 'apos') return "'";
    var code = (e.charAt(0) === '#')
      ? (e.charAt(1) === 'x' ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10))
      : NaN;
    if (!isFinite(code) || code < 0 || code > 0x10FFFF) {
      throw new FreeformCanvasError('bad numeric character reference &' + e + ';');
    }
    return String.fromCodePoint(code);
  });
}

function _freeformParseXml(str) {
  var i = 0, n = str.length;

  function err(msg) { throw new FreeformCanvasError(msg + ' at position ' + i); }
  function skipWs() { while (i < n && /\s/.test(str.charAt(i))) i++; }

  function parseName() {
    var start = i;
    while (i < n && !/[\s\/>=]/.test(str.charAt(i))) i++;
    if (i === start) err('expected a name');
    return str.slice(start, i);
  }

  function parseAttrValue() {
    var quote = str.charAt(i);
    if (quote !== '"' && quote !== "'") err('expected quoted attribute value');
    i++;
    var start = i;
    while (i < n && str.charAt(i) !== quote) i++;
    if (i >= n) err('unterminated attribute value');
    var raw = str.slice(start, i);
    i++;
    return _freeformDecodeEntities(raw);
  }

  function parseAttrs() {
    var attrs = {};
    while (true) {
      skipWs();
      if (i >= n) err('unexpected end of input in tag');
      var c = str.charAt(i);
      if (c === '/' || c === '>') break;
      var name = parseName();
      // __proto__/constructor/prototype rejected explicitly here too, not
      // just in _freeformValidateElement -- Gemini security review
      // follow-up, 2026-08-25. Verified this specific spot isn't currently
      // exploitable (attrs[name] = <string> for name='__proto__' is a
      // documented no-op: SVG attribute values are always strings here,
      // and the __proto__ setter silently ignores non-object/null values
      // -- confirmed with a live repro, ownProperty stays false, for-in
      // yields nothing). Rejecting explicitly anyway rather than relying
      // on that as the only safety net: it's an implicit language quirk,
      // not a policy this code actually states, and this atom's whole
      // design principle is explicit allowlisting over incidental
      // behaviour holding up by accident.
      if (name === '__proto__' || name === 'constructor' || name === 'prototype') {
        err('attribute ' + JSON.stringify(name) + ' is never permitted');
      }
      skipWs();
      if (str.charAt(i) !== '=') err('expected = after attribute name ' + name);
      i++;
      skipWs();
      attrs[name] = parseAttrValue();
    }
    return attrs;
  }

  // Comments/processing-instructions are skipped harmlessly. DOCTYPE/any
  // other markup declaration is REJECTED outright, not skipped -- a
  // DOCTYPE is exactly the vector real XXE/entity-expansion attacks arrive
  // through in other parsers, and this tokenizer implements no
  // entity-declaration mechanism at all, so there is nothing safe to do
  // with one except refuse it.
  function skipMisc() {
    while (true) {
      skipWs();
      if (str.substr(i, 4) === '<!--') {
        var end = str.indexOf('-->', i + 4);
        if (end === -1) err('unterminated comment');
        i = end + 3;
      } else if (str.substr(i, 2) === '<?') {
        var end2 = str.indexOf('?>', i + 2);
        if (end2 === -1) err('unterminated processing instruction');
        i = end2 + 2;
      } else if (str.substr(i, 2) === '<!') {
        err('DOCTYPE / markup declarations are never permitted');
      } else {
        break;
      }
    }
  }

  function parseElement(depth) {
    if (depth > _FREEFORM_MAX_DEPTH) err('element nesting exceeds max depth ' + _FREEFORM_MAX_DEPTH);
    skipMisc();
    if (str.charAt(i) !== '<') err('expected <');
    i++;
    var tag = parseName();
    skipWs();
    var attrs = parseAttrs();
    skipWs();
    if (str.charAt(i) === '/') {
      i++;
      if (str.charAt(i) !== '>') err('expected />');
      i++;
      return {tag: tag, attrs: attrs, children: [], text: ''};
    }
    if (str.charAt(i) !== '>') err('expected >');
    i++;
    var children = [];
    var text = '';
    while (true) {
      skipMisc();
      if (i >= n) err('unterminated element <' + tag + '>');
      if (str.substr(i, 2) === '</') {
        i += 2;
        var closeName = parseName();
        skipWs();
        if (str.charAt(i) !== '>') err('expected > in closing tag');
        i++;
        if (closeName !== tag) err('mismatched closing tag: expected ' + tag + ', got ' + closeName);
        break;
      } else if (str.charAt(i) === '<') {
        children.push(parseElement(depth + 1));
      } else {
        var start = i;
        while (i < n && str.charAt(i) !== '<') i++;
        text += _freeformDecodeEntities(str.slice(start, i));
      }
    }
    return {tag: tag, attrs: attrs, children: children, text: text.trim()};
  }

  skipMisc();
  var root = parseElement(0);
  return root;
}

function _freeformStripNs(name) {
  var idx = name.indexOf(':');
  return idx === -1 ? name : name.slice(idx + 1);
}

function _freeformXmlNodeToDict(node) {
  var tag = _freeformStripNs(node.tag);
  var el = {tag: tag};
  for (var k in node.attrs) {
    var stripped = _freeformStripNs(k);
    var canonical = (stripped in _FREEFORM_SVG_ATTR_TO_CANONICAL)
      ? _FREEFORM_SVG_ATTR_TO_CANONICAL[stripped] : stripped;
    el[canonical] = node.attrs[k];
  }
  if (node.text) el.text = node.text;
  if (node.children && node.children.length) {
    var children = [];
    for (var i = 0; i < node.children.length; i++) {
      children.push(_freeformXmlNodeToDict(node.children[i]));
    }
    el.children = children;
  }
  return el;
}

function _freeformParseSvg(svgString) {
  var root;
  try {
    root = _freeformParseXml(svgString);
  } catch (e) {
    if (e instanceof FreeformCanvasError) throw e;
    throw new FreeformCanvasError('could not parse svg: ' + e.message);
  }
  if (_freeformStripNs(root.tag) !== 'svg') {
    throw new FreeformCanvasError('root element must be <svg>, got <' + _freeformStripNs(root.tag) + '>');
  }
  var out = [];
  for (var i = 0; i < root.children.length; i++) {
    out.push(_freeformXmlNodeToDict(root.children[i]));
  }
  return out;
}

// ── id-namespacing ──────────────────────────────────────────────────────

// This file's OWN ambient convention elsewhere is `Math.random().toString(36)
// .substr(2,6)` -- deliberately NOT reused here. That's the same
// non-deterministic pattern the Python reference (_wa_uid) moved away from
// specifically because identical content producing different output on every
// render hides real diffs in noise. freeform_canvas's Python sibling already
// made that call for this atom; matching it here keeps the same diagram
// producing the same ids on both surfaces, not just avoiding a bug pattern
// this codebase has already paid to learn once.
function _freeformUid(b) {
  var s = JSON.stringify(b);
  var h = 5381;
  for (var i = 0; i < s.length; i++) {
    h = ((h * 33) ^ s.charCodeAt(i)) >>> 0;
  }
  return ('00000000' + h.toString(16)).slice(-8);
}

function _freeformNamespaceElement(el, prefix) {
  var attrs = {};
  for (var k in el.attrs) attrs[k] = el.attrs[k];
  if ('id' in attrs) attrs.id = prefix + '-' + attrs.id;
  var refAttrs = ['clip_path', 'mask', 'fill', 'stroke',
                  'marker_start', 'marker_mid', 'marker_end'];
  for (var j = 0; j < refAttrs.length; j++) {
    var rk = refAttrs[j];
    var v = attrs[rk];
    if (v) {
      var m = _FREEFORM_LOCAL_URL_RE.exec(v);
      if (m) attrs[rk] = 'url(#' + prefix + '-' + m[1] + ')';
    }
  }
  if (attrs.href && attrs.href.indexOf('#') === 0) {
    attrs.href = '#' + prefix + '-' + attrs.href.slice(1);
  }
  var children = [];
  for (var c = 0; c < (el.children || []).length; c++) {
    children.push(_freeformNamespaceElement(el.children[c], prefix));
  }
  return {tag: el.tag, attrs: attrs, text: el.text, children: children};
}

// ── rendering ────────────────────────────────────────────────────────────

function _freeformRenderElement(el) {
  var svgAttrMap = _FREEFORM_TAG_ATTRS[el.tag];
  var attrStr = '';
  for (var k in el.attrs) {
    attrStr += ' ' + svgAttrMap[k] + '="' + _esc(el.attrs[k]) + '"';
  }
  var inner = '';
  if (el.text) inner += _esc(el.text);
  for (var i = 0; i < (el.children || []).length; i++) {
    inner += _freeformRenderElement(el.children[i]);
  }
  return inner
    ? '<' + el.tag + attrStr + '>' + inner + '</' + el.tag + '>'
    : '<' + el.tag + attrStr + '/>';
}

function _freeformRenderFallback(b, reason) {
  var summary = _esc(b.summary || 'Diagram unavailable');
  return '<div style="margin:1.2rem 0;padding:14px 16px;border:1px solid #dadce0;' +
    'border-radius:8px;background:#f8f9fa;">' +
    '<div style="font-size:0.85rem;color:#202124;">' + summary + '</div>' +
    '<div style="margin-top:6px;font-size:0.75rem;color:#c5221f;">' +
    'Diagram content was rejected by the safety policy (' + _esc(reason) + ').</div>' +
    '</div>';
}

_RENDERERS['freeform_canvas'] = function(b) {
  var summary = b.summary;
  if (!summary || typeof summary !== 'string') {
    return _freeformRenderFallback(b, 'summary is required');
  }
  var justification = b.justification;
  if (!justification || typeof justification !== 'string' || justification.length < 20) {
    return _freeformRenderFallback(b, 'justification is required (minimum 20 characters)');
  }
  var hasElements = b.elements !== undefined && b.elements !== null;
  var hasSvg = b.svg !== undefined && b.svg !== null;
  if (hasElements === hasSvg) {
    return _freeformRenderFallback(b, 'exactly one of elements or svg is required');
  }

  var viewbox = b.viewbox || '0 0 800 500';
  var background = b.background;
  var validated;
  try {
    _freeformCheckValueSafety(viewbox);
    if (!/^[\d\s.\-]+$/.test(viewbox)) {
      throw new FreeformCanvasError('invalid viewbox format: ' + JSON.stringify(viewbox));
    }
    if (background) {
      _freeformCheckValueSafety(background);
      if (!/^(#[0-9a-fA-F]{3,8}|[a-zA-Z]+)$/.test(background)) {
        throw new FreeformCanvasError('invalid background format: ' + JSON.stringify(background));
      }
    }
    var rawElements = hasElements ? b.elements : _freeformParseSvg(b.svg);
    validated = _freeformValidateElements(rawElements);
  } catch (e) {
    if (e instanceof FreeformCanvasError) return _freeformRenderFallback(b, e.message);
    throw e;
  }

  var prefix = _freeformUid(b);
  var namespaced = [];
  for (var i = 0; i < validated.length; i++) {
    namespaced.push(_freeformNamespaceElement(validated[i], prefix));
  }
  var bgRect = background ? '<rect width="100%" height="100%" fill="' + _esc(background) + '"/>' : '';
  var body = '';
  for (var j = 0; j < namespaced.length; j++) {
    body += _freeformRenderElement(namespaced[j]);
  }

  return '<div style="margin:1.2rem 0;padding:14px 16px;border:1px solid #dadce0;' +
    'border-radius:8px;background:var(--surface,#ffffff);">' +
    '<svg viewBox="' + _esc(viewbox) + '" role="img" aria-label="' + _esc(summary) + '" ' +
    'style="width:100%;height:auto;display:block;">' +
    bgRect + body +
    '</svg>' +
    '</div>';
};

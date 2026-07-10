// atoms_v1_decode.gs — A2UI v1.0 → legacy-dialect rehydration (dual-decode shim)
//
// Phase 1 (2026-07-09) lived in Code.gs and resolved only the ARRAY variant of
// ChildList. Phase 2 (2026-07-10) moves it HERE so the MCP Apps bundle gets it
// by concatenation (Code.gs is excluded from the bundle; atoms_*.gs are not),
// and adds the TEMPLATE variant per the upstream spec
// (a2ui-private/spec/a2ui-v1.0-upstream/): {componentId, path} over the
// surface dataModel, JSON Pointer resolution (RFC 6901), Child Scope for
// relative paths, the @index system function, DataBinding ({path}) property
// resolution, and spec type-conversion rules. Pure string/JSON work — no DOM,
// no GAS services — so the bundle's Node-tested core block can execute it.
//
// Dialect note: the estate's emitters flatten properties onto the component
// (see renderers/a2ui_v1.py); strict upstream payloads nest them under
// `properties`. Both decode: a `properties` object is merged onto the node.

// RFC 6901 JSON Pointer lookup. '' → whole doc; '/a/0/b' → nested.
// Returns undefined on any miss (progressive-render grace, per spec).
function _a2uiPtrGet(model, pointer) {
  if (pointer === '' || pointer === '/') return model;
  if (typeof pointer !== 'string' || pointer.charAt(0) !== '/') return undefined;
  var parts = pointer.slice(1).split('/');
  var cur = model;
  for (var i = 0; i < parts.length; i++) {
    if (cur === null || cur === undefined) return undefined;
    var key = parts[i].replace(/~1/g, '/').replace(/~0/g, '~');
    if (Array.isArray(cur)) {
      var idx = parseInt(key, 10);
      if (isNaN(idx)) return undefined;
      cur = cur[idx];
    } else if (typeof cur === 'object') {
      cur = cur[key];
    } else {
      return undefined;
    }
  }
  return cur;
}

// Resolve a JSON Pointer against the current evaluation scope.
// Absolute ('/x') → root. Relative ('x') → scope.base + '/x' when inside a
// Child Scope; outside any scope, degrade to root-relative rather than throw.
function _a2uiResolvePath(path, scope) {
  if (typeof path !== 'string') return undefined;
  if (path.charAt(0) === '/') return path;
  var base = scope && scope.base ? scope.base : '';
  return base + '/' + path;
}

// Resolve one DynamicValue: literals pass through; {path} binds into the data
// model; {call:'@index'} yields the Child Scope index (+ optional offset).
// Spec conversion: null/undefined bindings → '' (renderers expect strings).
function _a2uiResolveDynamic(val, model, scope) {
  if (val === null || typeof val !== 'object') return val;
  if (Array.isArray(val)) {
    return val.map(function(v) { return _a2uiResolveDynamic(v, model, scope); });
  }
  var keys = Object.keys(val);
  if (keys.length === 1 && keys[0] === 'path' && typeof val.path === 'string') {
    var out = _a2uiPtrGet(model, _a2uiResolvePath(val.path, scope));
    return (out === undefined || out === null) ? '' : out;
  }
  if (val.call === '@index') {
    if (!scope || typeof scope.index !== 'number') return '';   // spec: only valid in list context
    var offset = 0;
    if (val.args && val.args.offset !== undefined) {
      var o = _a2uiResolveDynamic(val.args.offset, model, scope);
      offset = typeof o === 'number' ? o : (parseInt(o, 10) || 0);
    }
    return scope.index + offset;
  }
  // plain object property (e.g. nested config): resolve its values in place
  var res = {};
  for (var k in val) res[k] = _a2uiResolveDynamic(val[k], model, scope);
  return res;
}

function _rehydrateV1Surface(surface) {
  var byId = {};
  (surface.components || []).forEach(function(c) { byId[c.id] = c; });
  var model = surface.dataModel || {};

  // `seen` is a prototype CHAIN, not a shared map: an id is a cycle only if it
  // appears on the CURRENT ancestor path. Object.create(seen) per child keeps
  // sibling and template re-instantiation legal (the Phase-1 shared map made a
  // template's second instantiation resolve to null).
  function resolveNode(id, seen, scope) {
    if (seen[id]) return null;               // true cycle on this path
    var childSeen = Object.create(seen);
    childSeen[id] = true;
    var src = byId[id];
    if (!src) return null;
    var node = {};
    for (var k in src) {
      if (k === 'id' || k === 'children' || k === 'properties') continue;
      node[k] = _a2uiResolveDynamic(src[k], model, scope);
    }
    if (src.properties && typeof src.properties === 'object' && !Array.isArray(src.properties)) {
      for (var pk in src.properties) node[pk] = _a2uiResolveDynamic(src.properties[pk], model, scope);
    }
    // Legacy dialect keys blocks by `type`; ~11 inline recursion sites read
    // `.type` only (found live 2026-07-09) — stamp it once here.
    if (!node.type && typeof node.component === 'string') node.type = node.component;

    var ch = src.children;
    if (Array.isArray(ch) && ch.every(function(x) { return typeof x === 'string'; })) {
      node.blocks = ch.map(function(cid) { return resolveNode(cid, childSeen, scope); }).filter(Boolean);
    } else if (ch && typeof ch === 'object' && !Array.isArray(ch) &&
               typeof ch.componentId === 'string' && typeof ch.path === 'string') {
      // TEMPLATE variant: iterate the data-model array at path, one Child
      // Scope per item; relative bindings inside resolve against the item.
      var listPtr = _a2uiResolvePath(ch.path, scope);
      var arr = _a2uiPtrGet(model, listPtr);
      node.blocks = Array.isArray(arr)
        ? arr.map(function(_, i) {
            return resolveNode(ch.componentId, childSeen, { base: listPtr + '/' + i, index: i });
          }).filter(Boolean)
        : [];                                 // data not arrived yet → render empty, not throw
    }

    if (Array.isArray(src.tabs)) {
      node.tabs = src.tabs.map(function(t) {
        var out = {};
        for (var k2 in t) { if (k2 !== 'child') out[k2] = _a2uiResolveDynamic(t[k2], model, scope); }
        if (t.child) out.blocks = [resolveNode(t.child, childSeen, scope)].filter(Boolean);
        return out;
      });
    }
    // ComponentId-typed properties (split_pane leftId etc.): a string (or
    // uniform string array) naming known component(s) resolves in place.
    for (var field in node) {
      if (field === 'blocks' || field === 'tabs') continue;
      var val = node[field];
      if (typeof val === 'string' && byId[val]) {
        node[field] = resolveNode(val, childSeen, scope);
      } else if (Array.isArray(val) && val.length && val.every(function(x) { return typeof x === 'string' && byId[x]; })) {
        node[field] = val.map(function(cid) { return resolveNode(cid, childSeen, scope); }).filter(Boolean);
      }
    }
    return node;
  }

  var root = byId['root'];
  var rootNode = root ? resolveNode('root', {}, null) : null;
  var rootChildren = (rootNode && rootNode.blocks) ? rootNode.blocks : [];
  var props = surface.surfaceProperties || {};
  // hub_slug carried through (nav-budget-pagination-v0.1.md) — see Code.gs
  // _renderFromPayload seeding trigger.
  var out = { title: props.title, theme: props.theme, blocks: rootChildren };
  if (props.hub_slug) out.hub_slug = props.hub_slug;
  return out;
}

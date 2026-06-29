/**
 * A2UI State Engine v1.0
 * Reactive state graph for wired A2UI surfaces.
 *
 * Usage:
 *   const engine = new A2UIStateEngine(spec);
 *   engine.compileWires(layoutElement, domBridge);
 *   engine.bindOutput('#amount_mem.setValue', inputValue);
 */

const VALID_ID = /^[a-zA-Z0-9_-]+$/;
const MAX_PATTERN_LENGTH = 200;

class A2UIStateEngine {
  constructor(spec) {
    this.nodes = new Map();
    this.listeners = new Map(); // "nodeId:prop" → [callback]
    this._initPrimitives(spec.state_primitives || []);
    this._resolveWires(spec.state_primitives || []);
  }

  // ─── Public API ────────────────────────────────────────────────────────────

  /**
   * Bind a visual atom's wire block to the state graph.
   * Call once per layout element after engine is constructed.
   *
   * domBridge: { setProp(id, prop, value): void }
   */
  compileWires(layoutElement, domBridge) {
    if (!layoutElement.wire || !layoutElement.id) return;

    Object.entries(layoutElement.wire).forEach(([propName, wireExpr]) => {
      if (typeof wireExpr !== 'string' || !wireExpr.startsWith('#')) {
        console.warn(`[A2UI] Malformed wire on "${layoutElement.id}.${propName}": "${wireExpr}"`);
        return;
      }
      const parsed = this._parseWire(wireExpr);
      if (!parsed) return;

      this.registerListener(parsed.nodeId, parsed.property, (val) => {
        const safeVal = typeof val === 'string' ? _sanitize(val) : val;
        domBridge.setProp(layoutElement.id, propName, safeVal);
      });
    });
  }

  /**
   * Route a user event (output wire) into the state graph.
   * wireExpr: the wire string, e.g. "#amount_mem.setValue"
   * eventValue: the value emitted by the visual atom
   */
  bindOutput(wireExpr, eventValue) {
    if (typeof wireExpr !== 'string' || !wireExpr.startsWith('#')) {
      console.warn(`[A2UI] Malformed output wire: "${wireExpr}"`);
      return;
    }
    const parsed = this._parseWire(wireExpr);
    if (!parsed) return;
    this.trigger(parsed.nodeId, parsed.property, eventValue);
  }

  /**
   * Subscribe to a state node's reactive output.
   * Fires immediately with the current value on registration.
   */
  registerListener(nodeId, property, callback) {
    const node = this.nodes.get(nodeId);
    if (!node) {
      console.warn(`[A2UI] Wire target "${nodeId}" not found`);
      return;
    }
    if (!(property in node)) {
      console.warn(`[A2UI] Node "${nodeId}" has no property "${property}"`);
      return;
    }

    const key = `${nodeId}:${property}`;
    if (!this.listeners.has(key)) this.listeners.set(key, []);
    this.listeners.get(key).push(callback);
    callback(node[property]); // fire with current value immediately
  }

  /**
   * Invoke a primitive input handler.
   * inputName maps to _inputName on the node (e.g. "setValue" → "_setValue").
   */
  trigger(nodeId, inputName, value) {
    const node = this.nodes.get(nodeId);
    if (!node) {
      console.warn(`[A2UI] Wire target "${nodeId}" not found`);
      return;
    }
    const handler = node[`_${inputName}`];
    if (typeof handler !== 'function') {
      console.warn(`[A2UI] "${nodeId}" has no input "${inputName}"`);
      return;
    }
    handler(value);
  }

  // ─── Internal ───────────────────────────────────────────────────────────────

  _set(nodeId, property, value) {
    const node = this.nodes.get(nodeId);
    if (!node) return;
    node[property] = value;
    const key = `${nodeId}:${property}`;
    (this.listeners.get(key) || []).forEach(cb => cb(value));
  }

  _validateId(id) {
    if (!VALID_ID.test(id)) {
      throw new Error(`[A2UI] Invalid node ID: "${id}". Only [a-zA-Z0-9_-] allowed.`);
    }
  }

  _parseWire(expr) {
    const inner = expr.slice(1); // strip leading #
    const dot = inner.indexOf('.');
    if (dot === -1) {
      console.warn(`[A2UI] Malformed wire expression: "${expr}" — missing "."`);
      return null;
    }
    return { nodeId: inner.slice(0, dot), property: inner.slice(dot + 1) };
  }

  _initPrimitives(primitives) {
    primitives.forEach(p => {
      this._validateId(p.id);
      switch (p.primitive) {
        case 'ValueStore':      this._initValueStore(p);      break;
        case 'ArrayFilter':     this._initArrayFilter(p);     break;
        case 'StringValidator': this._initStringValidator(p); break;
        case 'NumericThreshold':this._initNumericThreshold(p);break;
        case 'StepNavigator':   this._initStepNavigator(p);   break;
        default:
          console.warn(`[A2UI] Unknown primitive: "${p.primitive}"`);
      }
    });
  }

  _resolveWires(primitives) {
    primitives.forEach(p => {
      const node = this.nodes.get(p.id);
      if (!node) return;

      // props.source as a wire expression (StringValidator, NumericThreshold)
      if (typeof p.props?.source === 'string' && p.props.source.startsWith('#')) {
        const parsed = this._parseWire(p.props.source);
        if (parsed) {
          this.registerListener(parsed.nodeId, parsed.property, val => {
            node._recompute && node._recompute(val);
          });
        }
      }

      // wire block on primitives (ArrayFilter.query, ArrayFilter.source)
      if (p.wire) {
        Object.entries(p.wire).forEach(([inputName, wireExpr]) => {
          if (typeof wireExpr !== 'string' || !wireExpr.startsWith('#')) return;
          const parsed = this._parseWire(wireExpr);
          if (!parsed) return;
          this.registerListener(parsed.nodeId, parsed.property, val => {
            if (p.primitive === 'ArrayFilter') {
              if (inputName === 'query')  { node._query = val;       node._recompute(); }
              if (inputName === 'source') { node._sourceData = val;  node._recompute(); }
            } else {
              this.trigger(p.id, inputName, val);
            }
          });
        });
      }
    });
  }

  // ─── Primitive constructors ─────────────────────────────────────────────────

  _initValueStore(p) {
    const node = { value: p.props?.initialValue ?? null };
    node._setValue = (val) => this._set(p.id, 'value', val);
    this.nodes.set(p.id, node);
  }

  _initArrayFilter(p) {
    const filterKey = p.props?.filterKey || 'label';
    const staticSource = Array.isArray(p.props?.source) ? p.props.source : [];

    const node = {
      output: [...staticSource],
      _sourceData: staticSource,
      _query: '',
    };
    node._recompute = () => {
      const q = (node._query || '').toLowerCase().trim();
      const result = q
        ? node._sourceData.filter(item =>
            String(item[filterKey] ?? '').toLowerCase().includes(q))
        : [...node._sourceData];
      this._set(p.id, 'output', result);
    };
    this.nodes.set(p.id, node);
  }

  _initStringValidator(p) {
    let pattern;
    const raw = p.props?.pattern || '';
    if (raw.length > MAX_PATTERN_LENGTH) {
      console.warn(`[A2UI] StringValidator "${p.id}" pattern exceeds ${MAX_PATTERN_LENGTH} chars — using passthrough`);
      pattern = /.*/;
    } else {
      try {
        pattern = new RegExp(raw);
      } catch (e) {
        console.warn(`[A2UI] StringValidator "${p.id}" invalid pattern: ${e.message} — using passthrough`);
        pattern = /.*/;
      }
    }

    const errMsg = p.props?.errorMessage || 'Invalid value';
    const node = {
      isValid: false,
      isInvalid: true,
      errorMessage: errMsg,
    };
    node._recompute = (source) => {
      const valid = typeof source === 'string' && source.length > 0 && pattern.test(source);
      node.isValid = valid;
      node.isInvalid = !valid;
      this._set(p.id, 'isValid', valid);
      this._set(p.id, 'isInvalid', !valid);
      this._set(p.id, 'errorMessage', valid ? '' : errMsg);
    };
    this.nodes.set(p.id, node);
  }

  _initNumericThreshold(p) {
    const ops = {
      gt:  (a, b) => a > b,
      gte: (a, b) => a >= b,
      lt:  (a, b) => a < b,
      lte: (a, b) => a <= b,
      eq:  (a, b) => a === b,
    };
    const compare = ops[p.props?.operator] ?? ops.gte;
    const threshold = p.props?.threshold ?? 0;

    const node = {
      isTriggered: false,
      isNotTriggered: true,
    };
    node._recompute = (source) => {
      const triggered = compare(Number(source), threshold);
      this._set(p.id, 'isTriggered', triggered);
      this._set(p.id, 'isNotTriggered', !triggered);
    };
    this.nodes.set(p.id, node);
  }

  _initStepNavigator(p) {
    const total = p.props?.totalSteps ?? 2;
    const node = { activeIndex: 0 };
    node._next   = ()  => { if (node.activeIndex < total - 1) this._set(p.id, 'activeIndex', node.activeIndex + 1); };
    node._prev   = ()  => { if (node.activeIndex > 0)         this._set(p.id, 'activeIndex', node.activeIndex - 1); };
    node._jumpTo = (i) => { if (i >= 0 && i < total)          this._set(p.id, 'activeIndex', i); };
    this.nodes.set(p.id, node);
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function _sanitize(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

if (typeof module !== 'undefined') {
  module.exports = { A2UIStateEngine };
}

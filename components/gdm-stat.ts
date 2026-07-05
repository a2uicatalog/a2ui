import { LitElement, css, html } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

/**
 * gdm-stat — generic metric atom: label · big value · optional delta.
 *
 * Optional `countUp` rolls the numeric part of `value` from 0 → target on mount
 * (parsing out any prefix/suffix, e.g. "$1.24M", "12,480", "99.98%"), and
 * `countDelay` lets it sync to a parent tile's revealDelay so the number rolls
 * as the panel lands. Styling is static shadow CSS (CSP-safe).
 */
@customElement('gdm-stat')
export class GdmStat extends LitElement {
  @property({ type: String }) label = '';
  @property({ type: String }) value = '';
  @property({ type: String }) unit = '';
  @property({ type: String }) delta = '';        // e.g. "+1.24%" or "-0.4"
  @property({ type: Boolean }) isUp = true;
  @property({ type: String }) accent = '';        // optional CSS colour for the value
  @property({ type: String }) size = 'md';        // 'sm' | 'md' | 'lg'
  @property({ type: String }) align = 'left';
  @property({ type: Boolean }) countUp = false;   // roll the number 0 → target on mount
  @property({ type: Number }) countDelay = 0;     // seconds before the roll starts
  @property({ type: Number }) countDuration = 0.9;

  @state() private _display = '';
  private _counted = false;
  private _rafId?: number;
  private _timer?: number;

  private _parse(v: string) {
    const m = String(v).match(/^(\D*?)([\d,]*\.?\d+)(.*)$/);
    if (!m) return null;
    const numStr = m[2];
    return {
      prefix: m[1],
      suffix: m[3],
      target: parseFloat(numStr.replace(/,/g, '')),
      decimals: (numStr.split('.')[1] || '').length,
    };
  }

  private _fmt(p: { prefix: string; suffix: string; decimals: number }, n: number) {
    return p.prefix + n.toLocaleString(undefined, {
      minimumFractionDigits: p.decimals, maximumFractionDigits: p.decimals,
    }) + p.suffix;
  }

  willUpdate(changed: Map<string | number | symbol, unknown>) {
    if (changed.has('value')) {
      if (this.countUp && !this._counted) {
        const p = this._parse(this.value);
        this._display = p ? this._fmt(p, 0) : this.value; // start at zero (no pre-paint flash of final)
      } else {
        this._display = this.value;
      }
    }
  }

  firstUpdated() {
    if (this.countUp) this._startCount();
    else this._display = this.value;
  }

  private _startCount() {
    const p = this._parse(this.value);
    if (!p) { this._display = this.value; this._counted = true; return; }
    const dur = Math.max(0.1, this.countDuration) * 1000;
    const run = () => {
      const t0 = performance.now();
      const step = (now: number) => {
        const prog = Math.min(1, (now - t0) / dur);
        const eased = 1 - Math.pow(1 - prog, 3); // ease-out cubic
        this._display = this._fmt(p, p.target * eased);
        if (prog < 1) this._rafId = requestAnimationFrame(step);
        else { this._display = this.value; this._counted = true; }
      };
      this._rafId = requestAnimationFrame(step);
    };
    const delay = Math.max(0, this.countDelay) * 1000;
    if (delay > 0) this._timer = window.setTimeout(run, delay); else run();
  }

  disconnectedCallback() {
    if (this._rafId) cancelAnimationFrame(this._rafId);
    if (this._timer) clearTimeout(this._timer);
    super.disconnectedCallback();
  }

  static styles = css`
    :host { display: block; box-sizing: border-box; }
    .stat { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
    .label {
      font-family: 'Google Sans', 'Inter', sans-serif;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: rgba(255,255,255,0.45);
      white-space: nowrap;
    }
    .value-row { display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
    .value {
      font-family: 'JetBrains Mono', 'Fira Code', monospace;
      font-weight: 800;
      color: #ffffff;
      line-height: 1.05;
      font-variant-numeric: tabular-nums;
    }
    .unit { font-size: 0.5em; font-weight: 600; color: rgba(255,255,255,0.4); }
    .size-sm .value { font-size: 18px; }
    .size-md .value { font-size: 26px; }
    .size-lg .value { font-size: 40px; }

    .delta {
      display: inline-flex; align-items: center; gap: 4px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px; font-weight: 700; line-height: 1;
      padding: 3px 8px; border-radius: 6px;
      font-variant-numeric: tabular-nums;
    }
    .delta .caret { font-size: 9px; }
    .delta.up   { color: #00ff88; background: rgba(0,255,136,0.10); box-shadow: inset 0 0 0 1px rgba(0,255,136,0.18); text-shadow: 0 0 9px rgba(0,255,136,0.35); }
    .delta.down { color: #ff3b57; background: rgba(255,59,87,0.10); box-shadow: inset 0 0 0 1px rgba(255,59,87,0.18); text-shadow: 0 0 9px rgba(255,59,87,0.35); }
  `;

  render() {
    const shown = this.countUp ? this._display : this.value;
    return html`
      <div class="stat size-${this.size}" style="align-items:${this.align === 'center' ? 'center' : this.align === 'right' ? 'flex-end' : 'flex-start'}; text-align:${this.align}">
        ${this.label ? html`<span class="label">${this.label}</span>` : ''}
        <div class="value-row">
          <span class="value" style="${this.accent ? `color:${this.accent}` : ''}">${shown}${this.unit ? html`<span class="unit">${this.unit}</span>` : ''}</span>
          ${this.delta ? html`
            <span class="delta ${this.isUp ? 'up' : 'down'}">
              <span class="caret">${this.isUp ? '▲' : '▼'}</span>${this.delta}
            </span>` : ''}
        </div>
      </div>
    `;
  }
}

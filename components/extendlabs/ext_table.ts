import { LitElement, css, html } from 'lit';
import { customElement, property } from 'lit/decorators.js';

/**
 * ext-table — Data table with headers and row data passed as JSON arrays. Collapses Table/TableHeader/TableBody/TableRow/TableCell into one component.
 *
 * Original source : https://github.com/extendlabs/ui
 * License         : MIT — Copyright (c) 2024 extendui
 * Modifications   : Compound HTML table structure collapsed into single Lit element; data passed as JSON-serialisable headers + rows props.
 *
 * Props:
 *   headers    — JSON string: string[]
 *   rows       — JSON string: string[][]
 *   caption    — optional caption text
 *   fontSize   — scale preset: sm | md | lg (default md) — adjusts th/td font sizes and padding
 *   color      — hex accent overriding default cyan for th, hover, and scan gradient
 */

@customElement('ext-table')
export class ExtTable extends LitElement {
  @property({ type: String }) headers  = '';
  @property({ type: String }) rows     = '';
  @property({ type: String }) caption  = '';
  @property({ type: String }) fontSize = 'md';  // sm | md | lg
  @property({ type: String }) color    = '';    // hex accent — overrides default cyan

  private _hexToRgb(h: string): string {
    const r = parseInt(h.slice(1,3),16), g = parseInt(h.slice(3,5),16), b = parseInt(h.slice(5,7),16);
    return `${r}, ${g}, ${b}`;
  }
  override updated() {
    if (this.color && /^#[0-9a-fA-F]{6}$/.test(this.color)) {
      this.style.setProperty('--ext-color', this.color);
      this.style.setProperty('--ext-rgb', this._hexToRgb(this.color));
    }
    const scale = { sm: ['9px','10px','5px 9px'], md: ['10px','12px','7px 12px'], lg: ['12px','14px','9px 14px'] };
    const [th, td, pad] = scale[this.fontSize as keyof typeof scale] ?? scale.md;
    this.style.setProperty('--th-size', th);
    this.style.setProperty('--td-size', td);
    this.style.setProperty('--td-pad', pad);
  }

  static styles = css`
    :host { display: block; }

    @keyframes ext-table-in {
      from { opacity: 0; transform: translateY(4px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes ext-table-scan {
      0%   { transform: translateY(-100%); opacity: 0.12; }
      100% { transform: translateY(100%);  opacity: 0; }
    }

    .table-wrapper {
      overflow: auto; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);
      position: relative;
    }
    .table-wrapper::after {
      content: '';
      position: absolute; left: 0; right: 0; top: 0;
      height: 30%; pointer-events: none;
      background: linear-gradient(to bottom, rgba(var(--ext-rgb, 0, 242, 255), 0.04), transparent);
      animation: ext-table-scan 3.5s linear infinite;
    }
    .table { width: 100%; border-collapse: collapse; font-family: inherit; }
    .table caption { font-size: 11px; color: #64748b; padding: 6px; text-align: left; }
    .table th {
      background: rgba(var(--ext-rgb, 0, 242, 255), 0.07); color: var(--ext-color, #00f2ff); font-weight: 700;
      text-align: left; padding: var(--td-pad, 7px 12px); letter-spacing: 0.08em;
      text-transform: uppercase; font-size: var(--th-size, 10px); font-family: monospace;
      white-space: nowrap;
    }
    .table td {
      padding: var(--td-pad, 7px 12px); border-top: 1px solid rgba(255,255,255,0.06);
      color: #cbd5e1; font-size: var(--td-size, 12px); font-family: monospace;
      animation: ext-table-in 0.3s ease both;
    }
    .table tbody tr:nth-child(1) td  { animation-delay: 0.04s; }
    .table tbody tr:nth-child(2) td  { animation-delay: 0.08s; }
    .table tbody tr:nth-child(3) td  { animation-delay: 0.12s; }
    .table tbody tr:nth-child(4) td  { animation-delay: 0.16s; }
    .table tbody tr:nth-child(5) td  { animation-delay: 0.20s; }
    .table tbody tr:nth-child(6) td  { animation-delay: 0.24s; }
    .table tbody tr:nth-child(7) td  { animation-delay: 0.28s; }
    .table tbody tr:nth-child(8) td  { animation-delay: 0.32s; }
    .table tr:hover td { background: rgba(var(--ext-rgb, 0, 242, 255), 0.04); transition: background 0.15s; }
  `;

  private get _headers(): string[] {
    try { return JSON.parse(this.headers || '[]'); } catch { return []; }
  }
  private get _rows(): string[][] {
    try { return JSON.parse(this.rows || '[]'); } catch { return []; }
  }

  render() {
    const headers = this._headers;
    const rows = this._rows;
    return html`
      <div class="table-wrapper">
        <table class="table">
          ${this.caption ? html`<caption>${this.caption}</caption>` : ''}
          ${headers.length ? html`
            <thead>
              <tr>${headers.map(h => html`<th>${h}</th>`)}</tr>
            </thead>` : ''}
          <tbody>
            ${rows.map(row => html`
              <tr>${row.map(cell => html`<td>${cell}</td>`)}</tr>
            `)}
          </tbody>
        </table>
      </div>
    `;
  }
}

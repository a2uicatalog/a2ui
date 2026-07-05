import { LitElement, css, html } from 'lit';
import { customElement, property } from 'lit/decorators.js';

/**
 * ext-card — Content card with optional title, description, body, and footer.
 * Collapses Card/CardHeader/CardContent/CardFooter into one component.
 *
 * Original source : https://github.com/extendlabs/ui
 * License         : MIT — Copyright (c) 2024 extendui
 * Modifications   : Compound React components collapsed into single Lit element.
 *
 * Props:
 *   title       — card header title
 *   description — subtitle below title
 *   content     — main body text
 *   footer      — small footer text
 *   color       — hex accent overriding default cyan for hover border/shimmer
 */

@customElement('ext-card')
export class ExtCard extends LitElement {
  @property({ type: String }) title       = '';
  @property({ type: String }) description = '';
  @property({ type: String }) content     = '';
  @property({ type: String }) footer      = '';
  @property({ type: String }) color       = '';  // hex accent — overrides default cyan

  private _hexToRgb(h: string): string {
    const r = parseInt(h.slice(1,3),16), g = parseInt(h.slice(3,5),16), b = parseInt(h.slice(5,7),16);
    return `${r}, ${g}, ${b}`;
  }
  override updated() {
    if (this.color && /^#[0-9a-fA-F]{6}$/.test(this.color)) {
      this.style.setProperty('--ext-color', this.color);
      this.style.setProperty('--ext-rgb', this._hexToRgb(this.color));
    }
  }

  static styles = css`
    :host { display: block; }

    @keyframes ext-card-in {
      from { opacity: 0; transform: translateY(10px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes ext-card-shimmer {
      0%   { background-position: -200% center; }
      100% { background-position: 200% center; }
    }

    .card {
      background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1);
      border-radius: 10px; overflow: hidden; font-family: inherit;
      animation: ext-card-in 0.35s cubic-bezier(0.4, 0, 0.2, 1) both;
      transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
      position: relative;
    }
    .card::before {
      content: '';
      position: absolute; inset: 0; border-radius: 10px; pointer-events: none;
      background: linear-gradient(105deg, transparent 40%, rgba(var(--ext-rgb, 0, 242, 255), 0.06) 50%, transparent 60%);
      background-size: 200% 100%;
      animation: ext-card-shimmer 4s linear infinite;
      opacity: 0;
      transition: opacity 0.3s;
    }
    .card:hover { border-color: rgba(var(--ext-rgb, 0, 242, 255), 0.28); transform: translateY(-2px); box-shadow: 0 6px 24px rgba(0,0,0,0.3); }
    .card:hover::before { opacity: 1; }
    .card-header      { padding: 14px 18px 6px; }
    .card-title       { font-size: 14px; font-weight: 700; color: #f1f5f9; margin-bottom: 3px; }
    .card-description { font-size: 12px; color: #64748b; }
    .card-content     { padding: 6px 18px; font-size: 13px; color: #cbd5e1; line-height: 1.5; }
    .card-footer      { padding: 6px 18px 14px; font-size: 11px; color: #475569; }
  `;

  render() {
    return html`
      <div class="card">
        ${(this.title || this.description) ? html`
          <div class="card-header">
            ${this.title ? html`<div class="card-title">${this.title}</div>` : ''}
            ${this.description ? html`<div class="card-description">${this.description}</div>` : ''}
          </div>` : ''}
        ${this.content ? html`<div class="card-content">${this.content}</div>` : ''}
        ${this.footer ? html`<div class="card-footer">${this.footer}</div>` : ''}
      </div>
    `;
  }
}

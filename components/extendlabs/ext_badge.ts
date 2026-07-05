import { LitElement, css, html } from 'lit';
import { customElement, property } from 'lit/decorators.js';

/**
 * ext-badge — Inline status badge. Variants: default, secondary, destructive, outline.
 *
 * Original source : https://github.com/extendlabs/ui
 * License         : MIT — Copyright (c) 2024 extendui
 * Modifications   : children→text prop; React.HTMLAttributes dropped
 *
 * Props:
 *   text     — badge label
 *   variant  — default | secondary | destructive | outline
 *   color    — hex accent overriding default cyan on the 'default' variant
 */

@customElement('ext-badge')
export class ExtBadge extends LitElement {
  @property({ type: String }) text    = '';
  @property({ type: String }) variant = 'default';
  @property({ type: String }) color   = '';  // hex accent — overrides default cyan

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
    :host { display: inline-flex; vertical-align: middle; }

    @keyframes ext-badge-in {
      from { opacity: 0; transform: scale(0.8); }
      to   { opacity: 1; transform: scale(1); }
    }
    @keyframes ext-badge-pulse {
      0%, 100% { box-shadow: 0 0 0 0 rgba(255,51,102,0.5); }
      50%       { box-shadow: 0 0 0 5px rgba(255,51,102,0); }
    }
    @keyframes ext-badge-glow {
      0%, 100% { box-shadow: 0 0 4px rgba(var(--ext-rgb, 0, 242, 255), 0.3); }
      50%       { box-shadow: 0 0 10px rgba(var(--ext-rgb, 0, 242, 255), 0.7); }
    }

    .badge {
      display: inline-flex; align-items: center;
      padding: 2px 10px; border-radius: 9999px;
      font-size: 11px; font-weight: 600; letter-spacing: 0.05em;
      font-family: inherit; white-space: nowrap; line-height: 20px;
      animation: ext-badge-in 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) both;
    }
    .badge-default     { background: rgba(var(--ext-rgb, 0, 242, 255), 0.12); color: var(--ext-color, #00f2ff); border: 1px solid rgba(var(--ext-rgb, 0, 242, 255), 0.35); animation: ext-badge-in 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) both, ext-badge-glow 2.5s ease-in-out infinite; }
    .badge-secondary   { background: rgba(148,163,184,0.12); color: #94a3b8; border: 1px solid rgba(148,163,184,0.3); }
    .badge-destructive { background: rgba(255,51,102,0.12); color: #ff3366; border: 1px solid rgba(255,51,102,0.35); animation: ext-badge-in 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) both, ext-badge-pulse 1.8s ease-in-out infinite; }
    .badge-outline     { background: transparent; color: #f1f5f9; border: 1px solid rgba(241,245,249,0.25); }
  `;

  render() {
    return html`<span class="badge badge-${this.variant}">${this.text}</span>`;
  }
}

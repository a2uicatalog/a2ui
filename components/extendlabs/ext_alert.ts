import { LitElement, css, html } from 'lit';
import { customElement, property } from 'lit/decorators.js';

/**
 * ext-alert — Status alert banner. Variants: default, destructive.
 *
 * Original source : https://github.com/extendlabs/ui
 * License         : MIT — Copyright (c) 2024 extendui
 * Modifications   : Compound Alert/AlertTitle/AlertDescription collapsed to single component
 *
 * Props:
 *   title       — bold heading line
 *   description — body text
 *   variant     — default | destructive
 *   color       — hex accent overriding default cyan on the 'default' variant
 */

@customElement('ext-alert')
export class ExtAlert extends LitElement {
  @property({ type: String }) title       = '';
  @property({ type: String }) description = '';
  @property({ type: String }) variant     = 'default';
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

    @keyframes ext-alert-in {
      from { opacity: 0; transform: translateX(-12px); }
      to   { opacity: 1; transform: translateX(0); }
    }
    @keyframes ext-alert-border-pulse {
      0%, 100% { border-left-color: rgba(255,51,102,0.6); }
      50%       { border-left-color: rgba(255,51,102,1); box-shadow: -2px 0 12px rgba(255,51,102,0.4); }
    }
    @keyframes ext-alert-border-glow {
      0%, 100% { border-left-color: rgba(var(--ext-rgb, 0, 242, 255), 0.5); }
      50%       { border-left-color: rgba(var(--ext-rgb, 0, 242, 255), 0.9); box-shadow: -2px 0 10px rgba(var(--ext-rgb, 0, 242, 255), 0.3); }
    }

    .alert {
      padding: 10px 14px; border-radius: 8px; border-left: 3px solid;
      font-size: 13px; line-height: 1.5; font-family: inherit;
      animation: ext-alert-in 0.4s cubic-bezier(0.4, 0, 0.2, 1) both;
    }
    .alert-default     { background: rgba(var(--ext-rgb, 0, 242, 255), 0.06); border-color: rgba(var(--ext-rgb, 0, 242, 255), 0.5); color: #e2e8f0; animation: ext-alert-in 0.4s cubic-bezier(0.4, 0, 0.2, 1) both, ext-alert-border-glow 3s ease-in-out infinite; }
    .alert-destructive { background: rgba(255,51,102,0.08); border-color: rgba(255,51,102,0.6); color: #fca5a5; animation: ext-alert-in 0.4s cubic-bezier(0.4, 0, 0.2, 1) both, ext-alert-border-pulse 2s ease-in-out infinite; }
    .alert-title { font-weight: 700; margin-bottom: 2px; font-size: 13px; }
    .alert-desc  { opacity: 0.8; font-size: 12px; }
  `;

  render() {
    return html`
      <div role="alert" class="alert alert-${this.variant}">
        ${this.title ? html`<div class="alert-title">${this.title}</div>` : ''}
        ${this.description ? html`<div class="alert-desc">${this.description}</div>` : ''}
      </div>
    `;
  }
}

import { LitElement, css, html } from 'lit';
import { customElement, property } from 'lit/decorators.js';

/**
 * ext-switch — Toggle switch. Fires a2ui-action on change.
 *
 * Original source : https://github.com/extendlabs/ui
 * License         : MIT — Copyright (c) 2024 extendui
 * Modifications   : Radix Switch replaced with native button + CSS track/thumb; onCheckedChange wired to a2ui-action event dispatch.
 *
 * Props:
 *   checked  — controlled checked state
 *   disabled — disables interaction
 *   label    — text label beside the switch
 *   action   — A2UI action dispatched on toggle
 *   color    — hex accent overriding default cyan for the checked track
 */

type ContextValue     = { path: string } | string | number | boolean | null;
type FunctionCallAction = { functionCall: { call: string; args?: Record<string, ContextValue> } };
type EventAction        = { event: { name: string; context?: Record<string, ContextValue> } };
type Action = FunctionCallAction | EventAction;

@customElement('ext-switch')
export class ExtSwitch extends LitElement {
  @property({ type: Boolean }) checked  = false;
  @property({ type: Boolean }) disabled = false;
  @property({ type: String })  label    = '';
  @property({ type: Object })  action: Action | null = null;
  @property({ type: String })  color    = '';  // hex accent — overrides default cyan

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
    :host { display: inline-block; }

    @keyframes ext-switch-in {
      from { opacity: 0; transform: scale(0.85); }
      to   { opacity: 1; transform: scale(1); }
    }
    @keyframes ext-switch-glow {
      0%, 100% { box-shadow: 0 0 0 0 rgba(var(--ext-rgb, 0, 242, 255), 0.4); }
      50%       { box-shadow: 0 0 0 4px rgba(var(--ext-rgb, 0, 242, 255), 0); }
    }
    @keyframes ext-switch-thumb-pop {
      0%   { transform: translateX(16px) scale(1); }
      40%  { transform: translateX(16px) scale(1.25); }
      100% { transform: translateX(16px) scale(1); }
    }

    .switch-wrapper {
      display: flex; align-items: center; gap: 10px; cursor: pointer;
      animation: ext-switch-in 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) both;
    }
    .switch-track {
      position: relative; width: 38px; height: 22px; border-radius: 11px;
      background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.18);
      cursor: pointer; padding: 0;
      transition: background 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease;
      flex-shrink: 0;
    }
    .switch-track.checked {
      background: rgba(var(--ext-rgb, 0, 242, 255), 0.35); border-color: rgba(var(--ext-rgb, 0, 242, 255), 0.55);
      animation: ext-switch-glow 2s ease-in-out infinite;
    }
    .switch-track:disabled { opacity: 0.4; cursor: not-allowed; }
    .switch-thumb {
      position: absolute; top: 2px; left: 2px;
      width: 16px; height: 16px; border-radius: 50%;
      background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,0.35);
      transition: transform 0.18s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    .switch-track.checked .switch-thumb { transform: translateX(16px); }
    .switch-label {
      font-size: 13px; color: #94a3b8; font-family: inherit;
      transition: color 0.2s;
    }
    .switch-track.checked ~ .switch-label { color: #e2e8f0; }
  `;

  private _onToggle() {
    if (this.disabled) return;
    this.checked = !this.checked;
    if (this.action) {
      this.dispatchEvent(new CustomEvent('a2ui-action', {
        detail: { ...this.action, value: this.checked },
        bubbles: true, composed: true,
      }));
    }
  }

  render() {
    return html`
      <label class="switch-wrapper">
        <button
          role="switch"
          aria-checked=${this.checked ? 'true' : 'false'}
          class="switch-track ${this.checked ? 'checked' : ''}"
          ?disabled=${this.disabled}
          @click=${this._onToggle}
        >
          <span class="switch-thumb"></span>
        </button>
        ${this.label ? html`<span class="switch-label">${this.label}</span>` : ''}
      </label>
    `;
  }
}

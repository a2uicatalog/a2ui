import { LitElement, css, html } from 'lit';
import { customElement, property } from 'lit/decorators.js';

/**
 * ext-checkbox — Accessible checkbox. Fires a2ui-action event on change.
 *
 * Original source : https://github.com/extendlabs/ui
 * License         : MIT — Copyright (c) 2024 extendui
 * Modifications   : onCheckedChange wired to a2ui-action event dispatch; Radix CheckboxPrimitive replaced with native input + custom styling.
 *
 * Props:
 *   checked  — controlled checked state
 *   disabled — disables interaction
 *   label    — text label beside the box
 *   name     — native input name
 *   value    — native input value
 *   action   — A2UI action dispatched on change
 *   color    — hex accent overriding default cyan for checked state
 */

type ContextValue     = { path: string } | string | number | boolean | null;
type FunctionCallAction = { functionCall: { call: string; args?: Record<string, ContextValue> } };
type EventAction        = { event: { name: string; context?: Record<string, ContextValue> } };
type Action = FunctionCallAction | EventAction;

@customElement('ext-checkbox')
export class ExtCheckbox extends LitElement {
  @property({ type: Boolean }) checked  = false;
  @property({ type: Boolean }) disabled = false;
  @property({ type: String })  label    = '';
  @property({ type: String })  name     = '';
  @property({ type: String })  value    = '';
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
    :host { display: block; }

    @keyframes ext-cb-in {
      from { opacity: 0; transform: scale(0.8) translateX(-4px); }
      to   { opacity: 1; transform: scale(1) translateX(0); }
    }
    @keyframes ext-cb-check-pop {
      0%   { transform: scale(0.6); opacity: 0; }
      60%  { transform: scale(1.2); opacity: 1; }
      100% { transform: scale(1); opacity: 1; }
    }
    @keyframes ext-cb-glow {
      0%, 100% { box-shadow: 0 0 0 0 rgba(var(--ext-rgb, 0, 242, 255), 0.5); }
      50%       { box-shadow: 0 0 0 4px rgba(var(--ext-rgb, 0, 242, 255), 0); }
    }

    .checkbox-wrapper {
      display: flex; align-items: center; gap: 10px; cursor: pointer;
      font-family: inherit;
      animation: ext-cb-in 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) both;
    }
    .checkbox-wrapper:hover .checkbox-box { border-color: rgba(var(--ext-rgb, 0, 242, 255), 0.5); }

    input[type="checkbox"] { position: absolute; opacity: 0; width: 0; height: 0; pointer-events: none; }

    .checkbox-box {
      width: 16px; height: 16px; border-radius: 4px; flex-shrink: 0;
      border: 1.5px solid rgba(255,255,255,0.25);
      background: rgba(255,255,255,0.06);
      display: flex; align-items: center; justify-content: center;
      transition: background 0.18s ease, border-color 0.18s ease;
      position: relative; overflow: visible;
    }
    .checkbox-box.checked {
      background: rgba(var(--ext-rgb, 0, 242, 255), 0.18); border-color: rgba(var(--ext-rgb, 0, 242, 255), 0.7);
      animation: ext-cb-glow 2s ease-in-out infinite;
    }
    .checkbox-box.checked .checkbox-mark {
      display: block;
      animation: ext-cb-check-pop 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) both;
    }
    .checkbox-mark {
      display: none;
      width: 9px; height: 6px;
      border-left: 2px solid var(--ext-color, #00f2ff); border-bottom: 2px solid var(--ext-color, #00f2ff);
      transform: rotate(-45deg) translateY(-1px);
    }
    .checkbox-label {
      font-size: 13px; color: #94a3b8; line-height: 1.4;
      transition: color 0.2s;
    }
    .checkbox-box.checked ~ .checkbox-label { color: #e2e8f0; }
    .checkbox-wrapper:has(input:disabled) { opacity: 0.4; cursor: not-allowed; }
  `;

  private _onChange(e: Event) {
    this.checked = (e.target as HTMLInputElement).checked;
    if (this.action) {
      this.dispatchEvent(new CustomEvent('a2ui-action', {
        detail: { ...this.action, value: this.checked },
        bubbles: true, composed: true,
      }));
    }
  }

  render() {
    return html`
      <label class="checkbox-wrapper">
        <input
          type="checkbox"
          .checked=${this.checked}
          ?disabled=${this.disabled}
          name=${this.name || ''}
          value=${this.value || ''}
          @change=${this._onChange}
        />
        <span class="checkbox-box ${this.checked ? 'checked' : ''}">
          <span class="checkbox-mark"></span>
        </span>
        ${this.label ? html`<span class="checkbox-label">${this.label}</span>` : ''}
      </label>
    `;
  }
}

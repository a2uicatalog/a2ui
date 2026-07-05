import { LitElement, css, html } from 'lit';
import { customElement, property } from 'lit/decorators.js';

/**
 * ext-input — Text input with optional variants. Fires a2ui-action on value commit (Enter / blur).
 *
 * Original source : https://github.com/extendlabs/ui
 * License         : MIT — Copyright (c) 2024 extendui
 * Modifications   : Password toggle removed; React context replaced with direct Lit props; onChange/onBlur collapsed to action dispatch on commit.
 *
 * Props:
 *   value       — controlled value
 *   placeholder — placeholder text
 *   type        — native input type (default: text)
 *   variant     — default | filled | flushed
 *   disabled    — disables interaction
 *   required    — marks field as required
 *   error       — error message string (triggers shake animation)
 *   label       — field label above the input
 *   action      — A2UI action dispatched on commit
 *   color       — hex accent overriding default cyan for focus state
 */

type ContextValue     = { path: string } | string | number | boolean | null;
type FunctionCallAction = { functionCall: { call: string; args?: Record<string, ContextValue> } };
type EventAction        = { event: { name: string; context?: Record<string, ContextValue> } };
type Action = FunctionCallAction | EventAction;

@customElement('ext-input')
export class ExtInput extends LitElement {
  @property({ type: String })  value       = '';
  @property({ type: String })  placeholder = '';
  @property({ type: String })  type        = 'text';
  @property({ type: String })  variant     = 'default';
  @property({ type: Boolean }) disabled    = false;
  @property({ type: Boolean }) required    = false;
  @property({ type: String })  error       = '';
  @property({ type: String })  label       = '';
  @property({ type: Object })  action: Action | null = null;
  @property({ type: String })  color       = '';  // hex accent — overrides default cyan

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

    @keyframes ext-input-in {
      from { opacity: 0; transform: translateY(5px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes ext-input-focus-bloom {
      0%   { box-shadow: 0 0 0 0 rgba(var(--ext-rgb, 0, 242, 255), 0.35); }
      50%  { box-shadow: 0 0 0 4px rgba(var(--ext-rgb, 0, 242, 255), 0.12); }
      100% { box-shadow: 0 0 0 3px rgba(var(--ext-rgb, 0, 242, 255), 0.08); }
    }
    @keyframes ext-input-error-shake {
      0%, 100% { transform: translateX(0); }
      20%       { transform: translateX(-4px); }
      40%       { transform: translateX(4px); }
      60%       { transform: translateX(-3px); }
      80%       { transform: translateX(3px); }
    }

    .input-root {
      display: flex; flex-direction: column; gap: 4px; font-family: inherit;
      animation: ext-input-in 0.3s ease both;
    }
    .input-label { font-size: 11px; color: #64748b; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; }
    .input-field {
      background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.14);
      border-radius: 6px; padding: 8px 12px; font-size: 13px; color: #f1f5f9;
      outline: none; width: 100%; box-sizing: border-box; font-family: inherit;
      transition: border-color 0.18s ease, box-shadow 0.18s ease;
    }
    .input-field::placeholder { color: #475569; }
    .input-field:focus {
      border-color: rgba(var(--ext-rgb, 0, 242, 255), 0.55);
      animation: ext-input-focus-bloom 0.4s ease forwards;
    }
    .input-field:disabled { opacity: 0.4; cursor: not-allowed; }
    .input-error-text { font-size: 11px; color: #ff3366; margin-top: 2px; }
    .has-error .input-field { border-color: rgba(255,51,102,0.5); animation: ext-input-error-shake 0.4s ease; }
    .input-filled .input-field { background: rgba(255,255,255,0.09); }
    .input-flushed .input-field { border: none; border-bottom: 1px solid rgba(255,255,255,0.2); border-radius: 0; padding-left: 0; }
    .input-flushed .input-field:focus { box-shadow: 0 1px 0 rgba(var(--ext-rgb, 0, 242, 255), 0.55); }
  `;

  private _onCommit(e: KeyboardEvent | FocusEvent) {
    if (e.type === 'keydown' && (e as KeyboardEvent).key !== 'Enter') return;
    this.value = (e.target as HTMLInputElement).value;
    if (this.action) {
      this.dispatchEvent(new CustomEvent('a2ui-action', {
        detail: { ...this.action, value: this.value },
        bubbles: true, composed: true,
      }));
    }
  }

  render() {
    return html`
      <div class="input-root input-${this.variant} ${this.error ? 'has-error' : ''}">
        ${this.label ? html`<label class="input-label">${this.label}</label>` : ''}
        <input
          class="input-field"
          type=${this.type || 'text'}
          .value=${this.value}
          placeholder=${this.placeholder || ''}
          ?disabled=${this.disabled}
          ?required=${this.required}
          @keydown=${this._onCommit}
          @blur=${this._onCommit}
        />
        ${this.error ? html`<span class="input-error-text">${this.error}</span>` : ''}
      </div>
    `;
  }
}

import { LitElement, css, html } from 'lit';
import { customElement, property } from 'lit/decorators.js';

/**
 * ext-textarea — Multi-line text input. Fires a2ui-action on commit (blur or Ctrl+Enter).
 *
 * Original source : https://github.com/extendlabs/ui
 * License         : MIT — Copyright (c) 2024 extendui
 * Modifications   : React.forwardRef removed; onBlur/onChange collapsed to action dispatch on commit
 *
 * Props:
 *   value       — controlled value
 *   placeholder — placeholder text
 *   rows        — number of visible text lines
 *   disabled    — disables interaction
 *   required    — marks field as required
 *   maxLength   — max character count
 *   label       — field label above the textarea
 *   action      — A2UI action dispatched on commit
 *   color       — hex accent overriding default cyan for focus state
 */

type ContextValue     = { path: string } | string | number | boolean | null;
type FunctionCallAction = { functionCall: { call: string; args?: Record<string, ContextValue> } };
type EventAction        = { event: { name: string; context?: Record<string, ContextValue> } };
type Action = FunctionCallAction | EventAction;

@customElement('ext-textarea')
export class ExtTextarea extends LitElement {
  @property({ type: String })  value     = '';
  @property({ type: String })  placeholder = '';
  @property({ type: Number })  rows      = 0;
  @property({ type: Boolean }) disabled  = false;
  @property({ type: Boolean }) required  = false;
  @property({ type: Number })  maxLength = 0;
  @property({ type: String })  label     = '';
  @property({ type: Object })  action: Action | null = null;
  @property({ type: String })  color     = '';  // hex accent — overrides default cyan

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

    @keyframes ext-textarea-in {
      from { opacity: 0; transform: translateY(5px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes ext-textarea-focus-bloom {
      0%   { box-shadow: 0 0 0 0 rgba(var(--ext-rgb, 0, 242, 255), 0.35); }
      50%  { box-shadow: 0 0 0 4px rgba(var(--ext-rgb, 0, 242, 255), 0.12); }
      100% { box-shadow: 0 0 0 3px rgba(var(--ext-rgb, 0, 242, 255), 0.06); }
    }

    .textarea-root {
      display: flex; flex-direction: column; gap: 4px; font-family: inherit;
      animation: ext-textarea-in 0.3s ease both;
    }
    .textarea-label { font-size: 11px; color: #64748b; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; }
    .textarea-field {
      background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.14);
      border-radius: 6px; padding: 8px 12px; font-size: 13px; color: #f1f5f9;
      outline: none; resize: vertical; width: 100%; box-sizing: border-box;
      font-family: inherit; line-height: 1.5;
      transition: border-color 0.18s ease, box-shadow 0.18s ease; min-height: 60px;
    }
    .textarea-field::placeholder { color: #475569; }
    .textarea-field:focus {
      border-color: rgba(var(--ext-rgb, 0, 242, 255), 0.55);
      animation: ext-textarea-focus-bloom 0.4s ease forwards;
    }
    .textarea-field:disabled { opacity: 0.4; cursor: not-allowed; }
  `;

  private _onCommit(e: KeyboardEvent | FocusEvent) {
    if (e.type === 'keydown') {
      const ke = e as KeyboardEvent;
      if (!(ke.key === 'Enter' && ke.ctrlKey)) return;
    }
    this.value = (e.target as HTMLTextAreaElement).value;
    if (this.action) {
      this.dispatchEvent(new CustomEvent('a2ui-action', {
        detail: { ...this.action, value: this.value },
        bubbles: true, composed: true,
      }));
    }
  }

  render() {
    return html`
      <div class="textarea-root">
        ${this.label ? html`<label class="textarea-label">${this.label}</label>` : ''}
        <textarea
          class="textarea-field"
          .value=${this.value}
          placeholder=${this.placeholder || ''}
          rows=${this.rows || 3}
          ?disabled=${this.disabled}
          ?required=${this.required}
          maxlength=${this.maxLength || ''}
          @keydown=${this._onCommit}
          @blur=${this._onCommit}
        ></textarea>
      </div>
    `;
  }
}

import { LitElement, css, html } from 'lit';
import { customElement, property } from 'lit/decorators.js';

/**
 * ext-tabs — Tab navigation. Tabs defined as a JSON array of {id, label, content} objects.
 *
 * Original source : https://github.com/extendlabs/ui
 * License         : MIT — Copyright (c) 2024 extendui
 * Modifications   : Radix Tabs compound (TabsList/TabsTrigger/TabsContent) collapsed into single Lit element; tabs data passed as JSON prop; onValueChange→action dispatch.
 *
 * Props:
 *   tabs    — JSON string: Array<{id: string; label: string; content: string}>
 *   value   — id of the active tab (controlled)
 *   action  — A2UI action dispatched on tab change (value = tab id)
 *   color   — hex accent overriding default cyan for the active tab indicator
 */

type ContextValue     = { path: string } | string | number | boolean | null;
type FunctionCallAction = { functionCall: { call: string; args?: Record<string, ContextValue> } };
type EventAction        = { event: { name: string; context?: Record<string, ContextValue> } };
type Action = FunctionCallAction | EventAction;

@customElement('ext-tabs')
export class ExtTabs extends LitElement {
  @property({ type: String }) tabs   = '';
  @property({ type: String }) value  = '';
  @property({ type: Object }) action: Action | null = null;
  @property({ type: String }) color  = '';  // hex accent — overrides default cyan

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

    @keyframes ext-tabs-in {
      from { opacity: 0; transform: translateY(6px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes ext-tabs-content-in {
      from { opacity: 0; transform: translateY(4px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes ext-tabs-indicator-glow {
      0%, 100% { box-shadow: 0 1px 0 rgba(var(--ext-rgb, 0, 242, 255), 0.5); }
      50%       { box-shadow: 0 2px 8px rgba(var(--ext-rgb, 0, 242, 255), 0.6); }
    }

    .tabs-root {
      display: flex; flex-direction: column; font-family: inherit;
      animation: ext-tabs-in 0.3s ease both;
    }
    .tabs-list {
      display: flex; gap: 0;
      border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    .tabs-trigger {
      background: transparent; border: none;
      border-bottom: 2px solid transparent; margin-bottom: -1px;
      color: #475569; padding: 7px 14px; font-size: 12px; font-weight: 600;
      cursor: pointer; letter-spacing: 0.04em;
      transition: color 0.18s ease, border-color 0.18s ease, background 0.18s ease;
      font-family: inherit; white-space: nowrap; border-radius: 4px 4px 0 0;
    }
    .tabs-trigger:hover { color: #94a3b8; background: rgba(255,255,255,0.03); }
    .tabs-trigger.active {
      color: var(--ext-color, #00f2ff); border-bottom-color: var(--ext-color, #00f2ff);
      animation: ext-tabs-indicator-glow 2.5s ease-in-out infinite;
    }
    .tabs-content {
      padding: 10px 2px; font-size: 12px; color: #94a3b8; line-height: 1.6;
      animation: ext-tabs-content-in 0.2s ease both;
    }
  `;

  private get _tabs(): Array<{id: string; label: string; content: string}> {
    try { return JSON.parse(this.tabs || '[]'); } catch { return []; }
  }

  private _selectTab(id: string) {
    this.value = id;
    if (this.action) {
      this.dispatchEvent(new CustomEvent('a2ui-action', {
        detail: { ...this.action, value: id },
        bubbles: true, composed: true,
      }));
    }
  }

  render() {
    const tabs = this._tabs;
    const active = this.value || (tabs[0]?.id ?? '');
    const current = tabs.find(t => t.id === active);
    return html`
      <div class="tabs-root">
        <div class="tabs-list" role="tablist">
          ${tabs.map(t => html`
            <button
              role="tab"
              class="tabs-trigger ${t.id === active ? 'active' : ''}"
              aria-selected=${t.id === active ? 'true' : 'false'}
              @click=${() => this._selectTab(t.id)}
            >${t.label}</button>
          `)}
        </div>
        <div class="tabs-content" role="tabpanel">
          ${current?.content ?? ''}
        </div>
      </div>
    `;
  }
}

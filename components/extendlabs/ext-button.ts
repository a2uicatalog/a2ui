import { LitElement, css, html } from 'lit';
import { customElement, property } from 'lit/decorators.js';

/**
 * ext-button — Extended button with animated variants.
 *
 * Ported from extendlabs/ui `button.tsx` to Lit Web Components for the A2UI
 * stateless canvas framework. Visual variants (shimmer, glowingRing,
 * perimeterShimmer, bouncing, ringHover) are adapted from the original
 * Tailwind/CVA animations.
 *
 * Original source: https://github.com/extendlabs/ui
 * MIT License — Copyright (c) 2024 extendui
 * Modifications: React state removed; action dispatch wired to A2UI protocol.
 *
 * Props:
 *   text      — button label
 *   label     — alias for text (back-compat)
 *   variant   — default | outline | ghost | ringHover | glowingRing | shimmer | perimeterShimmer | bouncing
 *   size      — sm | md | lg | hero
 *   loading   — shows spinner, disables click
 *   disabled  — disables interaction
 *   tooltip   — native title tooltip
 *   action    — A2UI action dispatched on click
 *   targetUrl — opens URL in new tab (shorthand for openUrl functionCall)
 *   color     — hex accent overriding default cyan for all accented variants
 */

type ContextValue  = { path: string } | string | number | boolean | null;
type FunctionCallAction = { functionCall: { call: string; args?: Record<string, ContextValue> } };
type EventAction        = { event: { name: string; context?: Record<string, ContextValue> } };
type Action = FunctionCallAction | EventAction;

@customElement('ext-button')
export class ExtButton extends LitElement {
  @property({ type: String })  text      = '';
  @property({ type: String })  label     = '';         // back-compat alias for text
  @property({ type: String })  variant   = 'default'; // default | outline | ghost | ringHover | glowingRing | shimmer | perimeterShimmer | bouncing
  @property({ type: String })  size      = 'md';      // sm | md | lg | hero
  @property({ type: Boolean }) loading   = false;
  @property({ type: Boolean }) disabled  = false;
  @property({ type: String })  tooltip   = '';
  @property({ type: Object })  action: Action | null = null;
  @property({ type: String })  targetUrl = '';
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

  private _resolveAction(): Action | null {
    if (this.action) return this.action;
    if (this.targetUrl) return { functionCall: { call: 'openUrl', args: { url: this.targetUrl } } };
    return null;
  }

  private async _handleClick(e: Event) {
    if (this.disabled || this.loading) { e.preventDefault(); return; }

    const action = this._resolveAction();
    if (!action) return;

    try {
      if ('event' in action) {
        this.dispatchEvent(new CustomEvent('a2ui-action', {
          detail: { event: action.event },
          bubbles: true, composed: true,
        }));
        return;
      }

      if ('functionCall' in action) {
        const { call, args } = action.functionCall;

        if (call === 'openUrl') {
          const url = args?.url;
          if (typeof url === 'string') window.open(url, '_blank');
          return;
        }

        if (call === 'navigateTab') {
          this.dispatchEvent(new CustomEvent('a2ui-navigate-tab', {
            detail: { tabId: args?.tabId },
            bubbles: true, composed: true,
          }));
          return;
        }

        if (call === 'fireSlide') {
          this.dispatchEvent(new CustomEvent('a2ui-fire-slide', {
            detail: { slide: args?.slide },
            bubbles: true, composed: true,
          }));
          return;
        }

        if (call === 'fireEndpoint') {
          let endpoint = args?.endpoint;
          if (typeof endpoint === 'string') {
            this.loading = true;
            const params = new URLSearchParams(window.location.search);
            const ticket = params.get('ticket');
            if (ticket) {
              try {
                const u = new URL(endpoint, window.location.origin);
                u.searchParams.set('ticket', ticket);
                endpoint = u.pathname + u.search;
              } catch (_) { /* keep original */ }
            }
            await fetch(endpoint, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(args?.body ?? {}),
            });
          }
          return;
        }

        console.warn(`[ext-button] unknown functionCall.call: "${call}"`);
      }
    } catch (err) {
      console.error('[ext-button] action failed', err);
    } finally {
      this.loading = false;
    }
  }

  static styles = css`
    :host { display: inline-block; vertical-align: middle; }

    @keyframes ext-shimmer {
      0%   { background-position: 200% center; }
      100% { background-position: -200% center; }
    }
    @keyframes ext-glow {
      0%, 100% { box-shadow: 0 0 0 2px rgba(var(--ext-rgb, 0, 242, 255), 0.3), 0 0 14px rgba(var(--ext-rgb, 0, 242, 255), 0.2); }
      50%       { box-shadow: 0 0 0 3px rgba(var(--ext-rgb, 0, 242, 255), 0.7), 0 0 28px rgba(var(--ext-rgb, 0, 242, 255), 0.45); }
    }
    @keyframes ext-perimeter {
      0%   { background-position: 100%   0%;  }
      25%  { background-position: 100% 100%;  }
      50%  { background-position:   0% 100%;  }
      75%  { background-position:   0%   0%;  }
      100% { background-position: 100%   0%;  }
    }
    @keyframes ext-bounce {
      0%, 100% { transform: translateY(0);    }
      50%       { transform: translateY(-5px); }
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      white-space: nowrap;
      border-radius: 8px;
      font-family: 'JetBrains Mono', 'Fira Code', monospace;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      border: none;
      cursor: pointer;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      overflow: hidden;
      outline: none;
      box-sizing: border-box;
      user-select: none;
      line-height: 1;
    }
    button:active:not([disabled]) { transform: scale(0.96); }
    button[disabled]               { opacity: 0.4; cursor: not-allowed; pointer-events: none; }

    .size-sm   { font-size: 11px; padding:  6px 12px; border-radius: 6px; }
    .size-md   { font-size: 13px; padding:  8px 18px; }
    .size-lg   { font-size: 16px; padding: 14px 32px; border-radius: 10px; }
    .size-hero { font-size: 24px; padding: 22px 44px; border-radius: 14px; }

    .v-default {
      background: var(--ext-color, #00f2ff);
      color: #0a0f1e;
      box-shadow: 0 0 12px rgba(var(--ext-rgb, 0, 242, 255), 0.25);
    }
    .v-default:hover:not([disabled]) {
      background: rgba(var(--ext-rgb, 0, 242, 255), 0.85);
      box-shadow: 0 0 20px rgba(var(--ext-rgb, 0, 242, 255), 0.4);
    }

    .v-outline {
      background: transparent;
      color: var(--ext-color, #00f2ff);
      border: 1px solid rgba(var(--ext-rgb, 0, 242, 255), 0.45);
    }
    .v-outline:hover:not([disabled]) {
      background: rgba(var(--ext-rgb, 0, 242, 255), 0.08);
      border-color: rgba(var(--ext-rgb, 0, 242, 255), 0.75);
    }

    .v-ghost {
      background: transparent;
      color: rgba(255, 255, 255, 0.65);
      border: 1px solid transparent;
    }
    .v-ghost:hover:not([disabled]) {
      background: rgba(255, 255, 255, 0.06);
      color: #ffffff;
    }

    .v-ringHover {
      background: var(--ext-color, #00f2ff);
      color: #0a0f1e;
    }
    .v-ringHover:hover:not([disabled]) {
      background: rgba(var(--ext-rgb, 0, 242, 255), 0.88);
      box-shadow: 0 0 0 2px #0a0f1e, 0 0 0 4px rgba(var(--ext-rgb, 0, 242, 255), 0.8);
    }

    .v-glowingRing {
      background: var(--ext-color, #00f2ff);
      color: #0a0f1e;
      animation: ext-glow 2s ease-in-out infinite;
    }

    .v-shimmer {
      background: linear-gradient(
        90deg,
        var(--ext-color, #00f2ff) 0%,
        rgba(var(--ext-rgb, 0, 242, 255), 0.35) 40%,
        rgba(0, 255, 136, 0.6) 60%,
        var(--ext-color, #00f2ff) 100%
      );
      background-size: 200% 100%;
      color: #0a0f1e;
      animation: ext-shimmer 2.4s linear infinite;
    }

    .v-perimeterShimmer {
      background: rgba(var(--ext-rgb, 0, 242, 255), 0.12);
      color: var(--ext-color, #00f2ff);
      border: 1px solid rgba(var(--ext-rgb, 0, 242, 255), 0.3);
    }
    .v-perimeterShimmer::before {
      content: '';
      position: absolute;
      inset: -1px;
      border-radius: inherit;
      background: linear-gradient(
        90deg,
        transparent,
        rgba(var(--ext-rgb, 0, 242, 255), 0.9),
        transparent
      );
      background-size: 200% 100%;
      animation: ext-perimeter 1.6s linear infinite;
      pointer-events: none;
      z-index: 0;
    }
    .v-perimeterShimmer span { position: relative; z-index: 1; }

    .v-bouncing {
      background: var(--ext-color, #00f2ff);
      color: #0a0f1e;
      animation: ext-bounce 1.1s ease-in-out infinite;
    }

    .spinner {
      width: 14px; height: 14px;
      border: 2px solid currentColor;
      border-top-color: transparent;
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
      flex-shrink: 0;
    }
  `;

  render() {
    const label = this.text || this.label;
    const sizeClass    = `size-${['sm','md','lg','hero'].includes(this.size) ? this.size : 'md'}`;
    const variantClass = `v-${this.variant}`;
    const needsSpan    = this.variant === 'perimeterShimmer';

    return html`
      <button
        class="${sizeClass} ${variantClass}"
        type="button"
        ?disabled=${this.disabled || this.loading}
        title=${this.tooltip}
        @click=${this._handleClick}
      >
        ${this.loading
          ? html`<span class="spinner"></span>`
          : needsSpan
            ? html`<span>${label}</span>`
            : html`${label}`
        }
      </button>
    `;
  }
}

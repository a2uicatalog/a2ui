import { LitElement, css, html } from 'lit';
import { customElement, property } from 'lit/decorators.js';

/**
 * ext-label — Accessible form label. Associates with an input via the for prop.
 *
 * Original source : https://github.com/extendlabs/ui
 * License         : MIT — Copyright (c) 2024 extendui
 * Modifications   : Radix Label.Root replaced with native label; className dropped
 *
 * Action schema (identical to gdm-button for interoperability):
 *   action: { event:        { name, context? } }        → agent-bound
 *   action: { functionCall: { call, args? } }           → local-only
 *     call values: "openUrl" | "navigateTab" | "fireEndpoint"
 */

@customElement('ext-label')
export class ExtLabel extends LitElement {
  @property({ type: String })  text = '';
  @property({ type: String })  for = '';

  static styles = css`
    :host { display: block; }
    label {
      font-size: 11px; color: #64748b; font-weight: 600;
      letter-spacing: 0.05em; text-transform: uppercase;
      display: block; font-family: inherit;
    }
  `;

  render() {
    return html`
      <label for=${this.for || ''}>${this.text}</label>
    `;
  }
}

# Component Implementations

This directory shows three representative components from the 45-component vocabulary.

## How to Read a Component

Each Lit web component has:

1. **Properties** — the input contract (what agents can set)
2. **Shadow CSS** — scoped styling
3. **Lifecycle** — how it renders and animates
4. **Event handlers** — what it broadcasts back

## The Three Examples

- **gdm-text.ts** — Simple atom with animations (flip, glitch, pulse)
- **gdm-container.ts** — Layout primitive with flexbox and multi-column
- **gdm-stat.ts** — Data-bound component with optional count-up animation

## Implementation Pattern

All components follow the Lit pattern:

```typescript
import { LitElement, css, html } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('gdm-example')
export class GdmExample extends LitElement {
  @property({ type: String }) someProp = 'default';

  static styles = css`/* scoped CSS */`;

  render() {
    return html`<!-- shadow DOM template -->`;
  }
}
```

Each component is self-contained — no external dependencies, CSP-safe inline styles.

The full 45-component implementation is in the [Google Meet Studio add-on](https://github.com/curtiskrygier/meet-studio).

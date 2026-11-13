# Math Block

Native MathML equation typeset with the CSS `math` generic font family (STIX / Latin Modern Math) — no JavaScript, no external library. The agent emits standard MathML; the surface draws it. Great for maths and science content — fractions, roots, integrals, matrices — rendered with correct spacing and alignment.

## Surfaces

web, google-apps-script-web, google-meet-stage, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| mathml | string. MathML markup — inner content or a full <math> element. Active content (script, annotation-xml, on* handlers, javascript:) is stripped before the markup is rendered. |
| caption | string (optional). Caption shown below the equation. |
| number | string (optional). Equation number, right-aligned (e.g. "(1)"). |
| align | string (optional). 'center' (default) or 'left'. |
| size | string (optional). Equation font-size. Default clamp(1.1rem,2.5vw,1.6rem). |

## Example payload

```json
{
  "type": "math_block",
  "mathml": "Mathml"
}
```

Live page: https://a2uicatalog.ai/atoms/math_block/
Full field contract: https://a2uicatalog.ai/spec.json

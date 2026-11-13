# Gradient Heading

Gradient-fill standalone heading using CSS background-clip text. Simpler than dark_hero — just the text, no padding or CTA. Use inside content flow between other atoms.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps, android

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
| text | string. Heading text. |
| gradient | string (optional). CSS gradient value. Default indigo→violet→pink. |
| size | string (optional). Font-size. Default clamp(1.8rem,4vw,3rem). |
| weight | integer (optional). Font-weight. Default 900. |
| align | string (optional). text-align. Default left. |
| margin | string (optional). CSS margin. Default 16px 0 6px. |

## Example payload

```json
{
  "type": "gradient_heading",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/gradient_heading/
Full field contract: https://a2uicatalog.ai/spec.json

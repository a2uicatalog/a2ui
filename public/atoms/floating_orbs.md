# Floating Orbs

Decorative blurred colour orbs that float in a dark background area

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Not verified | 2026-11-13 | no visible text in the example |
| Lit | Not verified | 2026-11-13 | no visible text in the example |
| Angular | Not verified | 2026-11-13 | no visible text in the example |
| CopilotKit | Not verified | 2026-11-13 | no visible text in the example |
| a2ui-vue | Not verified | 2026-11-13 | no visible text in the example |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| orbs | array of {colour, size, x, y} (optional) |
| blur | number (optional, blur px) |
| opacity | number (optional, 0–1) |
| animate | boolean (optional) |

## Example payload

```json
{
  "type": "floating_orbs"
}
```

Live page: https://a2uicatalog.ai/atoms/floating_orbs/
Full field contract: https://a2uicatalog.ai/spec.json

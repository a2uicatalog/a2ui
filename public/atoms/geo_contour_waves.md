# Geo Contour Waves

Animated isobaric atmospheric contour wave field — fluid procedural sine/cosine curves on dark background

## Surfaces

google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Not supported | 2026-11-13 | component type unknown to the renderer |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | string (optional) |
| color | string (optional, hex, default #a78bfa) |
| intensity | number (optional, wave band count, default 4, max 8) |
| height | number (optional, px, default 350) |

## Example payload

```json
{
  "type": "geo_contour_waves"
}
```

Live page: https://a2uicatalog.ai/atoms/geo_contour_waves/
Full field contract: https://a2uicatalog.ai/spec.json

# Surface Unlocked

Game-style "NEW SURFACE UNLOCKED" achievement notification card

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| icon | string (optional, emoji, default ⚡) |
| surface | string (surface/feature name displayed large) |
| sub | string (optional, subtitle, default NEW SURFACE UNLOCKED) |
| accent | string (optional, hex) |

## Example payload

```json
{
  "type": "surface_unlocked",
  "surface": "google-apps-script-web"
}
```

Live page: https://a2uicatalog.ai/atoms/surface_unlocked/
Full field contract: https://a2uicatalog.ai/spec.json

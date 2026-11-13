# Maps Embed

Embeds a Google Maps location search in an iframe. Suitable for event location, office address, field ops context.

## Surfaces

web, google-apps-script-web, google-apps-script-side-panel, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Not verified | 2026-11-13 | no visible text in the example |
| Lit | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| Angular | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| CopilotKit | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| a2ui-vue | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| Flutter | Not supported | 2026-11-13 | component type unknown to the renderer |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| q | address or place name to search (required) |
| height | iframe height in px (default 360) |
| zoom | map zoom level 1-20 (default 14) |
| caption | optional caption below the map |

## Example payload

```json
{
  "type": "maps_embed",
  "q": "Eiffel Tower, Paris"
}
```

Live page: https://a2uicatalog.ai/atoms/maps_embed/
Full field contract: https://a2uicatalog.ai/spec.json

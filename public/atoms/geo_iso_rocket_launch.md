# Geo Iso Rocket Launch

Full-viewport isometric 3D canvas animation of an Ariane 6 rocket launch from Kourou ELA-4. Shows pad, ignition, liftoff, and ascent trajectory. HUD overlay with mission data.

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
| title | string (optional). HUD title. Default "KOUROU ELA-4 — HEAVY LIFT INJECTION PROFILE". |
| vehicle | string (optional). ARIANE_6 or ARIANE_5. Default ARIANE_6. |

## Example payload

```json
{
  "type": "geo_iso_rocket_launch"
}
```

Live page: https://a2uicatalog.ai/atoms/geo_iso_rocket_launch/
Full field contract: https://a2uicatalog.ai/spec.json

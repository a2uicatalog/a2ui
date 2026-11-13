# Motion Lower Third

A lower third: an accent bar draws, the name slides out of it behind a clip, and the role fades in under it as p goes 0 to 1. Plain CSS, no script; standalone it renders finished.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

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
| name | string (max 40). |
| role | string (optional, max 60). |
| size | integer (optional). Name px, 10-120. Default 36. |
| color | "#rrggbb" (optional). Name. Default the stage ink. |
| accent | "#rrggbb" (optional). Bar and role. Default the stage accent. |
| fill | "#rrggbb" (optional). Panel. Default near-black. |

## Example payload

```json
{
  "type": "motion_lower_third",
  "name": "Motion Lower Third"
}
```

Live page: https://a2uicatalog.ai/atoms/motion_lower_third/
Full field contract: https://a2uicatalog.ai/spec.json
